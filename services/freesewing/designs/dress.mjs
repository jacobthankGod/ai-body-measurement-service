import { Design } from '@freesewing/core';
import { PATTERN_EASE } from '../measurement-mapper.mjs';

const e = PATTERN_EASE.dress;

const front = {
  name: 'dress.front',
  measurements: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const nw = m.neckCircumference / 6 + 5;
    const nd = m.neckCircumference / 6 + 15;
    const sd = 45;
    const hs = m.shoulderToShoulder / 2;
    const ad = m.chest / 4 + 20;
    const hc = m.chest / 4 + e.chest;
    const hw = m.waist / 4 + e.waist;
    const hh = m.hips / 4 + e.hips;
    const hipDepth = m.waistToHips;
    const bodiceLen = m.shoulderToWaist;
    const totalLen = m.shoulderToWaist + m.waistToHips * 2.5;
    const skirtFlare = (hh - hw) * 1.2 + 50;

    points.cfn = new Point(0, 0);
    points.neckShoulder = new Point(nw, nw * 0.7);
    points.shoulder = new Point(hs, nw * 0.7 + sd);
    points.underarm = new Point(hc, ad);
    points.waist = new Point(hw, bodiceLen);
    points.hip = new Point(hh, bodiceLen + hipDepth);
    points.hem = new Point(hh + skirtFlare, totalLen);
    points.cfhem = new Point(0, totalLen);

    // Bust dart
    const bustDartPos = hc * 0.45;
    const bustDartLen = ad + (bodiceLen - ad) * 0.4;
    const bustDartW = 16;
    points.dartLeft = new Point(bustDartPos - bustDartW / 2, ad);
    points.dartTip = new Point(bustDartPos, bustDartLen);
    points.dartRight = new Point(bustDartPos + bustDartW / 2, ad);

    paths.outline = new Path()
      .move(points.cfn)
      .curve(new Point(0, nd * 0.6), new Point(nw * 0.6, nd * 0.25), points.neckShoulder)
      .line(points.shoulder)
      .curve(
        new Point(points.shoulder.x + 15, points.shoulder.y + ad * 0.15),
        new Point(hc + 5, ad * 0.7),
        points.underarm
      )
      .line(points.dartRight)
      .line(points.dartTip)
      .line(points.dartLeft)
      .line(points.waist)
      .line(points.hip)
      .line(points.hem)
      .line(points.cfhem)
      .line(points.cfn)
      .close()
      .attr('class', 'fabric');

    paths.bustDart = new Path()
      .move(points.dartLeft)
      .line(points.dartTip)
      .line(points.dartRight)
      .attr('class', 'fabric');

    const cx = hc / 2;
    paths.grainline = new Path()
      .move(new Point(cx, 40))
      .line(new Point(cx, totalLen - 40))
      .attr('class', 'grainline');

    return part;
  }
};

const back = {
  name: 'dress.back',
  measurements: ['chest', 'waist', 'hips', 'neckCircumference', 'shoulderToShoulder', 'shoulderToWaist', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const nw = m.neckCircumference / 6 + 5;
    const nd = m.neckCircumference / 6 + 5;
    const sd = 42;
    const hs = m.shoulderToShoulder / 2;
    const ad = m.chest / 4 + 22;
    const hc = m.chest / 4 + e.chest + 5;
    const hw = m.waist / 4 + e.waist + 3;
    const hh = m.hips / 4 + e.hips + 5;
    const hipDepth = m.waistToHips;
    const bodiceLen = m.shoulderToWaist;
    const totalLen = m.shoulderToWaist + m.waistToHips * 2.5;
    const skirtFlare = (hh - hw) * 1.2 + 50;

    points.cbn = new Point(0, 0);
    points.neckShoulder = new Point(nw, nw * 0.65);
    points.shoulder = new Point(hs, nw * 0.65 + sd);
    points.underarm = new Point(hc, ad);
    points.waist = new Point(hw, bodiceLen);
    points.hip = new Point(hh, bodiceLen + hipDepth);
    points.hem = new Point(hh + skirtFlare, totalLen);
    points.cbhem = new Point(0, totalLen);

    // Waist dart on back
    const dartPos = hw * 0.4;
    const dartLen = (totalLen - bodiceLen) * 0.4;
    const dartW = 18;
    points.dartLeft = new Point(dartPos - dartW / 2, bodiceLen);
    points.dartTip = new Point(dartPos, bodiceLen + dartLen);
    points.dartRight = new Point(dartPos + dartW / 2, bodiceLen);

    paths.outline = new Path()
      .move(points.cbn)
      .curve(new Point(0, nd * 0.5), new Point(nw * 0.5, nd * 0.2), points.neckShoulder)
      .line(points.shoulder)
      .curve(
        new Point(points.shoulder.x + 12, points.shoulder.y + ad * 0.12),
        new Point(hc + 3, ad * 0.65),
        points.underarm
      )
      .line(points.waist)
      .line(points.dartRight)
      .line(points.dartTip)
      .line(points.dartLeft)
      .line(points.hip)
      .line(points.hem)
      .line(points.cbhem)
      .line(points.cbn)
      .close()
      .attr('class', 'fabric');

    paths.waistDart = new Path()
      .move(points.dartLeft)
      .line(points.dartTip)
      .line(points.dartRight)
      .attr('class', 'fabric');

    const cx = hc / 2;
    paths.grainline = new Path()
      .move(new Point(cx, 40))
      .line(new Point(cx, totalLen - 40))
      .attr('class', 'grainline');

    return part;
  }
};

const Dress = new Design({
  parts: [front, back],
  data: { name: 'KORRA Dress', version: '1.0.0', type: 'dress' }
});

export { Dress, front, back };
