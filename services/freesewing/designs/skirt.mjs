import { Design } from '@freesewing/core';
import { PATTERN_EASE } from '../measurement-mapper.mjs';

const e = PATTERN_EASE.skirt;

const front = {
  name: 'skirt.front',
  measurements: ['waist', 'hips', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const halfWaist = m.waist / 4 + e.waist;
    const halfHip = m.hips / 4 + e.hips;
    const hipDepth = m.waistToHips;
    const length = m.waistToHips * 2.2;
    const flare = (halfHip - halfWaist) * 1.5 + 40;

    points.cfWaist = new Point(0, 0);
    points.sideWaist = new Point(halfWaist, 0);
    points.sideHip = new Point(halfHip, hipDepth);
    points.sideHem = new Point(halfHip + flare, length);
    points.cfHem = new Point(0, length);

    // Waist dart
    const dartPos = halfWaist * 0.4;
    const dartLen = hipDepth * 0.75;
    const dartW = 15;
    points.dartCenter = new Point(dartPos, 0);
    points.dartTip = new Point(dartPos, dartLen);
    points.dartLeft = new Point(dartPos - dartW / 2, 0);
    points.dartRight = new Point(dartPos + dartW / 2, 0);

    paths.outline = new Path()
      .move(points.cfWaist)
      .line(points.dartLeft)
      .line(points.dartTip)
      .line(points.dartRight)
      .line(points.sideWaist)
      .line(points.sideHip)
      .line(points.sideHem)
      .line(points.cfHem)
      .line(points.cfWaist)
      .close()
      .attr('class', 'fabric');

    paths.dart = new Path()
      .move(points.dartLeft)
      .line(points.dartTip)
      .line(points.dartRight)
      .attr('class', 'fabric');

    const cx = halfWaist / 2;
    paths.grainline = new Path()
      .move(new Point(cx, 20))
      .line(new Point(cx, length - 20))
      .attr('class', 'grainline');

    return part;
  }
};

const back = {
  name: 'skirt.back',
  measurements: ['waist', 'hips', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const halfWaist = m.waist / 4 + e.waist + 10;
    const halfHip = m.hips / 4 + e.hips + 5;
    const hipDepth = m.waistToHips;
    const length = m.waistToHips * 2.2;
    const flare = (halfHip - halfWaist) * 1.5 + 40;

    points.cbWaist = new Point(0, 0);
    points.sideWaist = new Point(halfWaist, 0);
    points.sideHip = new Point(halfHip, hipDepth);
    points.sideHem = new Point(halfHip + flare, length);
    points.cbHem = new Point(0, length);

    // Two darts on back
    const dart1Pos = halfWaist * 0.3;
    const dart2Pos = halfWaist * 0.65;
    const dartLen = hipDepth * 0.8;
    const dartW = 18;

    points.dart1Left = new Point(dart1Pos - dartW / 2, 0);
    points.dart1Tip = new Point(dart1Pos, dartLen);
    points.dart1Right = new Point(dart1Pos + dartW / 2, 0);

    points.dart2Left = new Point(dart2Pos - dartW / 2, 0);
    points.dart2Tip = new Point(dart2Pos, dartLen);
    points.dart2Right = new Point(dart2Pos + dartW / 2, 0);

    paths.outline = new Path()
      .move(points.cbWaist)
      .line(points.dart1Left)
      .line(points.dart1Tip)
      .line(points.dart1Right)
      .line(points.dart2Left)
      .line(points.dart2Tip)
      .line(points.dart2Right)
      .line(points.sideWaist)
      .line(points.sideHip)
      .line(points.sideHem)
      .line(points.cbHem)
      .line(points.cbWaist)
      .close()
      .attr('class', 'fabric');

    paths.dart1 = new Path()
      .move(points.dart1Left)
      .line(points.dart1Tip)
      .line(points.dart1Right)
      .attr('class', 'fabric');

    paths.dart2 = new Path()
      .move(points.dart2Left)
      .line(points.dart2Tip)
      .line(points.dart2Right)
      .attr('class', 'fabric');

    const cx = halfWaist / 2 + 10;
    paths.grainline = new Path()
      .move(new Point(cx, 20))
      .line(new Point(cx, length - 20))
      .attr('class', 'grainline');

    return part;
  }
};

const Skirt = new Design({
  parts: [front, back],
  data: { name: 'KORRA Skirt', version: '1.0.0', type: 'skirt' }
});

export { Skirt, front, back };
