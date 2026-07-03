import { Design } from '@freesewing/core';
import { PATTERN_EASE } from '../measurement-mapper.mjs';

const chestEase = PATTERN_EASE.shirt.chest;
const waistEase = PATTERN_EASE.shirt.waist;
const hipEase = PATTERN_EASE.shirt.hips;
const bicepsEase = PATTERN_EASE.shirt.biceps;
const wristEase = PATTERN_EASE.shirt.wrist;

const front = {
  name: 'shirt.front',
  measurements: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips', 'bicepsCircumference'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const nw = m.neckCircumference / 6 + 5;
    const nd = m.neckCircumference / 6 + 15;
    const sd = 45;
    const hs = m.shoulderToShoulder / 2;
    const ad = m.chest / 4 + 20;
    const hc = m.chest / 4 + chestEase;
    const hw = m.waist / 4 + waistEase;
    const hh = m.hips / 4 + hipEase;
    const len = m.shoulderToWaist + m.waistToHips + 25;

    points.cfn = new Point(0, 0);
    points.neckShoulder = new Point(nw, nw * 0.7);
    points.shoulder = new Point(hs, nw * 0.7 + sd);
    points.underarm = new Point(hc, ad);
    points.waist = new Point(hw, m.shoulderToWaist);
    points.hip = new Point(hh, m.shoulderToWaist + m.waistToHips);
    points.hem = new Point(hh, len);
    points.cfhem = new Point(0, len);

    paths.neck = new Path()
      .move(points.cfn)
      .curve(new Point(0, nd * 0.6), new Point(nw * 0.6, nd * 0.25), points.neckShoulder)
      .attr('class', 'fabric');

    paths.shoulder = new Path()
      .move(points.neckShoulder)
      .line(points.shoulder)
      .attr('class', 'fabric');

    const ax = points.shoulder.x + 15;
    const ay = points.shoulder.y + ad * 0.15;
    const bx = hc + 5;
    const by = ad * 0.7;
    paths.armhole = new Path()
      .move(points.shoulder)
      .curve(new Point(ax, ay), new Point(bx, by), points.underarm)
      .attr('class', 'fabric');

    paths.side = new Path()
      .move(points.underarm)
      .line(points.waist)
      .line(points.hip)
      .line(points.hem)
      .attr('class', 'fabric');

    paths.hemLine = new Path()
      .move(points.hem)
      .line(points.cfhem)
      .attr('class', 'fabric');

    paths.cf = new Path()
      .move(points.cfhem)
      .line(points.cfn)
      .attr('class', 'fabric');

    paths.outline = new Path()
      .move(points.cfn)
      .curve(new Point(0, nd * 0.6), new Point(nw * 0.6, nd * 0.25), points.neckShoulder)
      .line(points.shoulder)
      .curve(new Point(ax, ay), new Point(bx, by), points.underarm)
      .line(points.waist)
      .line(points.hip)
      .line(points.hem)
      .line(points.cfhem)
      .line(points.cfn)
      .close()
      .attr('class', 'fabric');

    points.grainFrom = new Point(hc / 2, 40);
    points.grainTo = new Point(hc / 2, len - 40);
    paths.grainline = new Path()
      .move(points.grainFrom)
      .line(points.grainTo)
      .attr('class', 'grainline');

    points.notch1 = new Point(0, ad);
    points.notch2 = new Point(hc, ad);

    return part;
  }
};

const back = {
  name: 'shirt.back',
  measurements: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const nw = m.neckCircumference / 6 + 5;
    const nd = m.neckCircumference / 6 + 5;
    const sd = 42;
    const hs = m.shoulderToShoulder / 2;
    const ad = m.chest / 4 + 22;
    const hc = m.chest / 4 + chestEase + 5;
    const hw = m.waist / 4 + waistEase + 3;
    const hh = m.hips / 4 + hipEase + 5;
    const len = m.shoulderToWaist + m.waistToHips + 25;

    points.cbn = new Point(0, 0);
    points.neckShoulder = new Point(nw, nw * 0.65);
    points.shoulder = new Point(hs, nw * 0.65 + sd);
    points.underarm = new Point(hc, ad);
    points.waist = new Point(hw, m.shoulderToWaist);
    points.hip = new Point(hh, m.shoulderToWaist + m.waistToHips);
    points.hem = new Point(hh, len);
    points.cbhem = new Point(0, len);

    paths.neck = new Path()
      .move(points.cbn)
      .curve(new Point(0, nd * 0.5), new Point(nw * 0.5, nd * 0.2), points.neckShoulder)
      .attr('class', 'fabric');

    paths.shoulder = new Path()
      .move(points.neckShoulder)
      .line(points.shoulder)
      .attr('class', 'fabric');

    const ax = points.shoulder.x + 12;
    const ay = points.shoulder.y + ad * 0.12;
    const bx = hc + 3;
    const by = ad * 0.65;
    paths.armhole = new Path()
      .move(points.shoulder)
      .curve(new Point(ax, ay), new Point(bx, by), points.underarm)
      .attr('class', 'fabric');

    paths.side = new Path()
      .move(points.underarm)
      .line(points.waist)
      .line(points.hip)
      .line(points.hem)
      .attr('class', 'fabric');

    paths.hemLine = new Path()
      .move(points.hem)
      .line(points.cbhem)
      .attr('class', 'fabric');

    paths.cb = new Path()
      .move(points.cbhem)
      .line(points.cbn)
      .attr('class', 'fabric');

    paths.outline = new Path()
      .move(points.cbn)
      .curve(new Point(0, nd * 0.5), new Point(nw * 0.5, nd * 0.2), points.neckShoulder)
      .line(points.shoulder)
      .curve(new Point(ax, ay), new Point(bx, by), points.underarm)
      .line(points.waist)
      .line(points.hip)
      .line(points.hem)
      .line(points.cbhem)
      .line(points.cbn)
      .close()
      .attr('class', 'fabric');

    const cx = hc / 2;
    paths.grainline = new Path()
      .move(new Point(cx, 40))
      .line(new Point(cx, len - 40))
      .attr('class', 'grainline');

    return part;
  }
};

const sleeve = {
  name: 'shirt.sleeve',
  measurements: ['bicepsCircumference', 'wristCircumference', 'shoulderToWrist', 'chest'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const ad = m.chest / 4 + 20;
    const capH = ad / 3 + 20;
    const capW = m.bicepsCircumference / 2 + bicepsEase;
    const sl = m.shoulderToWrist;
    const ww = m.wristCircumference / 2 + wristEase;

    points.top = new Point(capW / 2, 0);
    points.left = new Point(0, capH);
    points.right = new Point(capW, capH);
    points.elbow = new Point(capW - (capW - ww) * 0.5, sl * 0.6);
    points.wristLeft = new Point(0, sl);
    points.wristRight = new Point(ww, sl);

    paths.cap = new Path()
      .move(points.top)
      .curve(
        new Point(points.top.x + 5, points.top.y + capH * 0.25),
        new Point(points.right.x - 10, points.right.y - capH * 0.3),
        points.right
      )
      .line(points.elbow)
      .line(points.wristRight)
      .attr('class', 'fabric');

    paths.hem = new Path()
      .move(points.wristRight)
      .line(points.wristLeft)
      .attr('class', 'fabric');

    paths.underarm = new Path()
      .move(points.wristLeft)
      .line(points.elbow)
      .line(points.left)
      .attr('class', 'fabric');

    paths.innerCap = new Path()
      .move(points.left)
      .curve(
        new Point(points.left.x + 10, points.left.y - capH * 0.3),
        new Point(points.top.x - 5, points.top.y + capH * 0.25),
        points.top
      )
      .attr('class', 'fabric');

    paths.outline = new Path()
      .move(points.top)
      .curve(
        new Point(points.top.x + 5, points.top.y + capH * 0.3),
        new Point(points.right.x - 10, points.right.y - capH * 0.3),
        points.right
      )
      .line(points.elbow)
      .line(points.wristRight)
      .line(points.wristLeft)
      .line(points.left)
      .curve(
        new Point(points.left.x + 10, points.left.y - capH * 0.3),
        new Point(points.top.x - 5, points.top.y + capH * 0.3),
        points.top
      )
      .close()
      .attr('class', 'fabric');

    paths.grainline = new Path()
      .move(new Point(capW / 2, capH + 20))
      .line(new Point(capW / 2, sl - 20))
      .attr('class', 'grainline');

    return part;
  }
};

const collar = {
  name: 'shirt.collar',
  measurements: ['neckCircumference'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const half = m.neckCircumference / 2 + 10;
    const height = 45;

    points.tl = new Point(0, 0);
    points.tr = new Point(half, 0);
    points.bl = new Point(0, height);
    points.br = new Point(half, height);

    points.tlC = new Point(half * 0.05, height * 0.3);
    points.trC = new Point(half * 0.95, height * 0.3);

    paths.outline = new Path()
      .move(points.tl)
      .curve(points.tlC, points.trC, points.tr)
      .line(points.br)
      .line(points.bl)
      .close()
      .attr('class', 'fabric');

    paths.grainline = new Path()
      .move(new Point(half / 2, 5))
      .line(new Point(half / 2, height - 5))
      .attr('class', 'grainline');

    return part;
  }
};

const collarStand = {
  name: 'shirt.collarstand',
  measurements: ['neckCircumference'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const half = m.neckCircumference / 2;
    const height = 28;

    points.tl = new Point(0, 0);
    points.tr = new Point(half, 0);
    points.bl = new Point(0, height);
    points.br = new Point(half, height);

    paths.outline = new Path()
      .move(points.tl)
      .line(points.tr)
      .line(points.br)
      .line(points.bl)
      .close()
      .attr('class', 'fabric');

    paths.grainline = new Path()
      .move(new Point(half / 2, 5))
      .line(new Point(half / 2, height - 5))
      .attr('class', 'grainline');

    return part;
  }
};

const Shirt = new Design({
  parts: [front, back, sleeve, collar, collarStand],
  data: { name: 'KORRA Shirt', version: '1.0.0', type: 'shirt' }
});

export { Shirt, front, back, sleeve, collar, collarStand };
