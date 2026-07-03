import express from 'express';
import { DESIGNS, DESIGN_INFO } from './designs/index.mjs';
import { korraToFreesewing, getRequiredFreesewingMeasurements, getRequiredKorraMeasurements } from './measurement-mapper.mjs';

const app = express();
const PORT = process.env.PORT || 3002;

app.use(express.json({ limit: '1mb' }));
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

function draftPattern(patternType, measurements, opts = {}) {
  const Design = DESIGNS[patternType];
  if (!Design) throw new Error(`Unknown pattern type: ${patternType}`);

  // If pre-computed Freesewing dict (mm) is provided, use directly.
  // Otherwise convert from KORRA cm → Freesewing mm.
  const fs = opts.isFS ? { ...measurements } : korraToFreesewing(measurements);
  const required = getRequiredFreesewingMeasurements(patternType);
  for (const key of required) {
    if (fs[key] == null) fs[key] = 500;
  }

  const pattern = new Design({ measurements: fs });
  pattern.draft();
  const svg = pattern.render();
  const pieces = extractPieces(pattern, patternType);
  const totalWidth = parseDimension(svg, 'width');
  const totalHeight = parseDimension(svg, 'height');

  return { svg, pieces, totalWidth, totalHeight, designConfig: Design.designConfig };
}

function parseDimension(svg, attr) {
  const match = svg.match(new RegExp(`\\s${attr}="(\\d+(\\.\\d+)?)`));
  return match ? parseFloat(match[1]) : 0;
}

function extractPieces(pattern, patternType) {
  const pieces = [];
  const info = DESIGN_INFO[patternType];
  if (!pattern.stacks) return pieces;

  let pieceIdx = 0;
  for (const [stackName, stack] of Object.entries(pattern.stacks)) {
    if (!stack.parts) continue;
    for (const part of stack.parts) {
      const pieceName = info ? info.pieces[pieceIdx] || part.name : part.name;
      const paths = {};
      for (const [pathName, path] of Object.entries(part.paths || {})) {
        const d = path.attributes.get('d');
        const cls = path.attributes.get('class') || '';
        if (d) {
          paths[pathName] = { d, class: cls };
        }
      }
      pieces.push({
        name: pieceName,
        partName: part.name,
        paths,
        pointCount: Object.keys(part.points || {}).length,
        bounds: stack.topLeft && stack.bottomRight ? {
          x: stack.topLeft.x,
          y: stack.topLeft.y,
          width: stack.bottomRight.x - stack.topLeft.x,
          height: stack.bottomRight.y - stack.topLeft.y,
        } : null,
      });
      pieceIdx++;
    }
  }
  return pieces;
}

function generateDXF(patternType, measurements, opts = {}) {
  const Design = DESIGNS[patternType];
  if (!Design) throw new Error(`Unknown pattern type: ${patternType}`);

  const fs = opts.isFS ? { ...measurements } : korraToFreesewing(measurements);
  const required = getRequiredFreesewingMeasurements(patternType);
  for (const key of required) {
    if (fs[key] == null) fs[key] = 500;
  }

  const pattern = new Design({ measurements: fs });
  pattern.draft();
  pattern.render();

  let dxf = '';
  dxf += '  0\nSECTION\n  2\nHEADER\n  9\n$ACADVER\n  1\nAC1014\n  9\n$INSUNITS\n 70\n  4\n  9\n$MEASUREMENT\n 70\n  1\n  0\nENDSEC\n';
  dxf += '  0\nSECTION\n  2\nTABLES\n  0\nTABLE\n  2\nLAYER\n 70\n  6\n';

  const layers = { CUTTING: 7, SEAM: 5, GRAIN: 4, NOTCH: 1, LABEL: 3, INTERNAL: 6 };
  let layerIdx = 0;
  for (const [name, color] of Object.entries(layers)) {
    layerIdx++;
    dxf += `  0\nLAYER\n  2\n${name}\n 70\n  0\n  6\nCONTINUOUS\n 62\n  ${color}\n`;
  }
  dxf += '  0\nENDTAB\n  0\nENDSEC\n  0\nSECTION\n  2\nENTITIES\n';

  if (pattern.stacks) {
    for (const stack of Object.values(pattern.stacks)) {
      if (!stack.parts) continue;
      for (const part of stack.parts) {
        for (const [, path] of Object.entries(part.paths || {})) {
          const d = path.attributes.get('d');
          const cls = path.attributes.get('class') || '';
          if (!d) continue;

          const layer = cls.includes('grainline') ? 'GRAIN' : 'CUTTING';
          const segments = parseSVGPath(d);

          for (const seg of segments) {
            if (seg.type === 'M' || seg.type === 'L') {
              dxf += `  0\nLINE\n  8\n${layer}\n 10\n${seg.x1.toFixed(4)}\n 20\n${(-seg.y1).toFixed(4)}\n 11\n${seg.x2.toFixed(4)}\n 21\n${(-seg.y2).toFixed(4)}\n`;
            } else if (seg.type === 'C') {
              const steps = 16;
              for (let i = 0; i < steps; i++) {
                const t1 = i / steps;
                const t2 = (i + 1) / steps;
                const [x1, y1] = bezierPoint(seg, t1);
                const [x2, y2] = bezierPoint(seg, t2);
                dxf += `  0\nLINE\n  8\n${layer}\n 10\n${x1.toFixed(4)}\n 20\n${(-y1).toFixed(4)}\n 11\n${x2.toFixed(4)}\n 21\n${(-y2).toFixed(4)}\n`;
              }
            } else if (seg.type === 'Q') {
              const steps = 12;
              for (let i = 0; i < steps; i++) {
                const t1 = i / steps;
                const t2 = (i + 1) / steps;
                const x1 = (1 - t1) * (1 - t1) * seg.x1 + 2 * (1 - t1) * t1 * seg.cx + t1 * t1 * seg.x2;
                const y1 = (1 - t1) * (1 - t1) * seg.y1 + 2 * (1 - t1) * t1 * seg.cy + t1 * t1 * seg.y2;
                const x2 = (1 - t2) * (1 - t2) * seg.x1 + 2 * (1 - t2) * t2 * seg.cx + t2 * t2 * seg.x2;
                const y2 = (1 - t2) * (1 - t2) * seg.y1 + 2 * (1 - t2) * t2 * seg.cy + t2 * t2 * seg.y2;
                dxf += `  0\nLINE\n  8\n${layer}\n 10\n${x1.toFixed(4)}\n 20\n${(-y1).toFixed(4)}\n 11\n${x2.toFixed(4)}\n 21\n${(-y2).toFixed(4)}\n`;
              }
            }
          }
        }
      }
    }
  }

  dxf += '  0\nENDSEC\n  0\nEOF\n';
  return dxf;
}

function parseSVGPath(d) {
  const segments = [];
  const re = /([MLQCZ])\s*([\d.\-e,\s]*)/gi;
  let match;
  let lastX = 0, lastY = 0;
  let startX = 0, startY = 0;

  while ((match = re.exec(d)) !== null) {
    const cmd = match[1].toUpperCase();
    const args = match[2].trim().split(/[\s,]+/).map(Number).filter(n => !isNaN(n));
    const isRelative = match[1] !== cmd;

    if (cmd === 'M' && args.length >= 2) {
      startX = isRelative ? lastX + args[0] : args[0];
      startY = isRelative ? lastY + args[1] : args[1];
      lastX = startX;
      lastY = startY;
    } else if (cmd === 'L' && args.length >= 2) {
      const nx = isRelative ? lastX + args[0] : args[0];
      const ny = isRelative ? lastY + args[1] : args[1];
      segments.push({ type: 'L', x1: lastX, y1: lastY, x2: nx, y2: ny });
      lastX = nx;
      lastY = ny;
    } else if (cmd === 'C' && args.length >= 6) {
      const cx1 = isRelative ? lastX + args[0] : args[0];
      const cy1 = isRelative ? lastY + args[1] : args[1];
      const cx2 = isRelative ? lastX + args[2] : args[2];
      const cy2 = isRelative ? lastY + args[3] : args[3];
      const nx = isRelative ? lastX + args[4] : args[4];
      const ny = isRelative ? lastY + args[5] : args[5];
      segments.push({ type: 'C', x1: lastX, y1: lastY, cx1, cy1, cx2, cy2, x2: nx, y2: ny });
      lastX = nx;
      lastY = ny;
    } else if ((cmd === 'Z' || cmd === 'z') && (segments.length > 0 || true)) {
      segments.push({ type: 'L', x1: lastX, y1: lastY, x2: startX, y2: startY });
      lastX = startX;
      lastY = startY;
    } else if (cmd === 'Q' && args.length >= 4) {
      const cx = isRelative ? lastX + args[0] : args[0];
      const cy = isRelative ? lastY + args[1] : args[1];
      const nx = isRelative ? lastX + args[2] : args[2];
      const ny = isRelative ? lastY + args[3] : args[3];
      segments.push({ type: 'Q', x1: lastX, y1: lastY, cx, cy, x2: nx, y2: ny });
      lastX = nx;
      lastY = ny;
    }
  }
  return segments;
}

function bezierPoint(seg, t) {
  const mt = 1 - t;
  const x = mt * mt * mt * seg.x1 + 3 * mt * mt * t * seg.cx1 + 3 * mt * t * t * seg.cx2 + t * t * t * seg.x2;
  const y = mt * mt * mt * seg.y1 + 3 * mt * mt * t * seg.cy1 + 3 * mt * t * t * seg.cy2 + t * t * t * seg.y2;
  return [x, y];
}

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'korra-pattern-service', version: '1.0.0' });
});

app.get('/api/patterns', (req, res) => {
  res.json({
    patterns: Object.entries(DESIGN_INFO).map(([key, info]) => ({
      id: key,
      ...info,
    })),
  });
});

app.get('/api/measurements/:patternType', (req, res) => {
  const info = DESIGN_INFO[req.params.patternType];
  if (!info) return res.status(404).json({ error: `Unknown pattern: ${req.params.patternType}` });

  const korraKeys = getRequiredKorraMeasurements(req.params.patternType);
  res.json({
    patternType: req.params.patternType,
    freesewingKeys: getRequiredFreesewingMeasurements(req.params.patternType),
    korraKeys,
  });
});

app.post('/api/pattern/draft', (req, res) => {
  try {
    const { patternType, measurements, freesewing } = req.body;
    if (!patternType) return res.status(400).json({ error: 'patternType required' });
    if (!measurements && !freesewing) return res.status(400).json({ error: 'measurements or freesewing required' });

    const result = draftPattern(patternType, freesewing || measurements, { isFS: !!freesewing });
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
    res.json({
      patternType,
      svg: result.svg,
      pieces: result.pieces,
      dimensions: { width: result.totalWidth, height: result.totalHeight },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/pattern/export', (req, res) => {
  try {
    const { patternType, measurements, freesewing, format } = req.body;
    if (!patternType) return res.status(400).json({ error: 'patternType required' });
    if (!measurements && !freesewing) return res.status(400).json({ error: 'measurements or freesewing required' });

    const format_lc = (format || 'svg').toLowerCase();
    const input = freesewing || measurements;

    if (format_lc === 'dxf' || format_lc === 'dxf-aama') {
      const dxf = generateDXF(patternType, input, { isFS: !!freesewing });
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
      res.setHeader('Content-Type', 'application/dxf');
      res.setHeader('Content-Disposition', `attachment; filename="${patternType}-pattern.dxf"`);
      res.send(dxf);
    } else {
      const result = draftPattern(patternType, input, { isFS: !!freesewing });
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
      res.json({
        patternType,
        svg: result.svg,
        pieces: result.pieces,
        dimensions: { width: result.totalWidth, height: result.totalHeight },
        format: 'svg',
      });
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(PORT, () => {
  console.log(`KORRA Pattern Service running on port ${PORT}`);
  console.log(`Available patterns: ${Object.keys(DESIGNS).join(', ')}`);
});

export default app;
