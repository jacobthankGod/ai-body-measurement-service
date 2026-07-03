import { Design } from '@freesewing/core';
import { PATTERN_EASE } from '../measurement-mapper.mjs';

const e = PATTERN_EASE.jacket;

const front = {
  name: 'jacket.front',
  measurements: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips', 'bicepsCircumference'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const nw = m.neckCircumference / 6 + 6;
    const nd = m.neckCircumference / 6 + 18;
    const sd = 50;
    const hs = m.shoulderToShoulder / 2 + 5;
    const ad = m.chest / 4 + 30;
    const hc = m.chest / 4 + e.chest;
    const hw = m.waist / 4 + e.waist;
    const hh = m.hips / 4 + e.hips;
    const len = m.shoulderToWaist + m.waistToHips + 50;

    points.cfn = new Point(0, 0);
    points.neckShoulder = new Point(nw, nw * 0.7);
    points.shoulder = new Point(hs, nw * 0.7 + sd);
    points.underarm = new Point(hc, ad);
    points.waist = new Point(hw, m.shoulderToWaist);
    points.hip = new Point(hh, m.shoulderToWaist + m.waistToHips);
    points.hem = new Point(hh, len);
    points.cfhem = new Point(0, len);
    points.lapel = new Point(hw * 0.3, m.shoulderToWaist * 0.6);
    points.lapelTop = new Point(nw * 0.15, nd * 0.5);

    paths.outline = new Path()
      .move(points.cfn)
      .curve(new Point(0, nd * 0.6), new Point(nw * 0.6, nd * 0.25), points.neckShoulder)
      .line(points.shoulder)
      .curve(
        new Point(points.shoulder.x + 18, points.shoulder.y + ad * 0.15),
        new Point(hc + 8, ad * 0.7),
        points.underarm
      )
      .line(points.waist)
      .line(points.hip)
      .line(points.hem)
      .line(points.cfhem)
      .line(points.lapel)
      .curve(
        new Point(points.lapel.x * 0.5, points.lapel.y * 0.7),
        new Point(points.lapelTop.x, points.lapelTop.y),
        points.cfn
      )
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

const back = {
  name: 'jacket.back',
  measurements: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const nw = m.neckCircumference / 6 + 6;
    const nd = m.neckCircumference / 6 + 6;
    const sd = 47;
    const hs = m.shoulderToShoulder / 2 + 5;
    const ad = m.chest / 4 + 32;
    const hc = m.chest / 4 + e.chest + 8;
    const hw = m.waist / 4 + e.waist + 5;
    const hh = m.hips / 4 + e.hips + 8;
    const len = m.shoulderToWaist + m.waistToHips + 50;

    points.cbn = new Point(0, 0);
    points.neckShoulder = new Point(nw, nw * 0.65);
    points.shoulder = new Point(hs, nw * 0.65 + sd);
    points.underarm = new Point(hc, ad);
    points.waist = new Point(hw, m.shoulderToWaist);
    points.hip = new Point(hh, m.shoulderToWaist + m.waistToHips);
    points.hem = new Point(hh, len);
    points.cbhem = new Point(0, len);

    paths.outline = new Path()
      .move(points.cbn)
      .curve(new Point(0, nd * 0.5), new Point(nw * 0.5, nd * 0.2), points.neckShoulder)
      .line(points.shoulder)
      .curve(
        new Point(points.shoulder.x + 15, points.shoulder.y + ad * 0.12),
        new Point(hc + 5, ad * 0.65),
        points.underarm
      )
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
  name: 'jacket.sleeve',
  measurements: ['bicepsCircumference', 'wristCircumference', 'shoulderToWrist', 'chest'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const ad = m.chest / 4 + 30;
    const capH = ad / 3 + 25;
    const capW = m.bicepsCircumference / 2 + e.biceps;
    const sl = m.shoulderToWrist;
    const ww = m.wristCircumference / 2 + e.wrist;

    points.top = new Point(capW / 2, 0);
    points.left = new Point(0, capH);
    points.right = new Point(capW, capH);
    points.wristLeft = new Point(0, sl);
    points.wristRight = new Point(ww, sl);

    paths.outline = new Path()
      .move(points.top)
      .curve(
        new Point(points.top.x + 8, points.top.y + capH * 0.3),
        new Point(points.right.x - 12, points.right.y - capH * 0.3),
        points.right
      )
      .line(points.wristRight)
      .line(points.wristLeft)
      .line(points.left)
      .curve(
        new Point(points.left.x + 12, points.left.y - capH * 0.3),
        new Point(points.top.x - 8, points.top.y + capH * 0.3),
        points.top
      )
      .close()
      .attr('class', 'fabric');

    const cx = capW / 2;
    paths.grainline = new Path()
      .move(new Point(cx, capH + 20))
      .line(new Point(cx, sl - 20))
      .attr('class', 'grainline');

    return part;
  }
};

const Jacket = new Design({
  parts: [front, back, sleeve],
  data: { name: 'KORRA Jacket', version: '1.0.0', type: 'jacket' }
});

export { Jacket, front, back, sleeve };
