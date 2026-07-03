import { Design } from '@freesewing/core';
import { PATTERN_EASE } from '../measurement-mapper.mjs';

const e = PATTERN_EASE.pants;

const front = {
  name: 'pants.front',
  measurements: ['waist', 'hips', 'inseam', 'thighCircumference', 'calfCircumference', 'shoulderToWaist', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const rise = m.waistToHips + 30;
    const halfWaist = m.waist / 4 + e.waist;
    const halfHip = m.hips / 4 + e.hips + 5;
    const halfThigh = m.thighCircumference / 2 + e.thigh;
    const halfCalf = m.calfCircumference / 2 + e.calf;
    const kneePos = rise + m.inseam * 0.45;
    const legLen = rise + m.inseam;
    const kneeW = (halfThigh + halfCalf) / 2;
    const crotchExt = halfHip * 0.18;

    // Center front
    points.cfWaist = new Point(0, 0);
    points.cfHip = new Point(0, m.waistToHips);

    // Side points
    points.sideWaist = new Point(halfWaist, 0);
    points.sideHip = new Point(halfHip, m.waistToHips);
    points.sideThigh = new Point(halfThigh, rise);
    points.sideKnee = new Point(kneeW, kneePos);
    points.sideHem = new Point(halfCalf, legLen);

    // Inseam points
    points.inseamThigh = new Point(crotchExt, rise);
    points.inseamKnee = new Point(0, kneePos);
    points.inseamHem = new Point(0, legLen);

    // Crotch curve control
    points.crotch = new Point(crotchExt, m.waistToHips);

    paths.outline = new Path()
      .move(points.cfWaist)
      .line(points.sideWaist)
      .line(points.sideHip)
      .line(points.sideThigh)
      .line(points.sideKnee)
      .line(points.sideHem)
      .line(points.inseamHem)
      .line(points.inseamKnee)
      .line(points.inseamThigh)
      .curve(
        new Point(crotchExt * 0.7, m.waistToHips + (rise - m.waistToHips) * 0.3),
        new Point(crotchExt * 0.3, m.waistToHips),
        points.cfHip
      )
      .line(points.cfWaist)
      .close()
      .attr('class', 'fabric');

    const cx = halfWaist / 2;
    paths.grainline = new Path()
      .move(new Point(cx, 20))
      .line(new Point(cx, legLen - 20))
      .attr('class', 'grainline');

    return part;
  }
};

const back = {
  name: 'pants.back',
  measurements: ['waist', 'hips', 'inseam', 'thighCircumference', 'calfCircumference', 'shoulderToWaist', 'waistToHips'],
  draft: ({ Point, Path, points, paths, measurements, part }) => {
    const m = measurements;
    const rise = m.waistToHips + 30;
    const halfWaist = m.waist / 4 + e.waist + 10;
    const halfHip = m.hips / 4 + e.hips + 15;
    const halfThigh = m.thighCircumference / 2 + e.thigh + 15;
    const halfCalf = m.calfCircumference / 2 + e.calf + 5;
    const kneePos = rise + m.inseam * 0.45;
    const legLen = rise + m.inseam;
    const kneeW = (halfThigh + halfCalf) / 2 + 5;
    const crotchExt = halfHip * 0.22;

    points.cbWaist = new Point(0, 0);
    points.cbHip = new Point(0, m.waistToHips);

    points.sideWaist = new Point(halfWaist, -5);
    points.sideHip = new Point(halfHip, m.waistToHips);
    points.sideThigh = new Point(halfThigh, rise);
    points.sideKnee = new Point(kneeW + 5, kneePos);
    points.sideHem = new Point(halfCalf + 5, legLen);

    points.inseamThigh = new Point(crotchExt + 10, rise);
    points.inseamKnee = new Point(10, kneePos);
    points.inseamHem = new Point(5, legLen);

    points.crotch = new Point(crotchExt + 10, m.waistToHips);

    paths.outline = new Path()
      .move(points.cbWaist)
      .line(points.sideWaist)
      .line(points.sideHip)
      .line(points.sideThigh)
      .line(points.sideKnee)
      .line(points.sideHem)
      .line(points.inseamHem)
      .line(points.inseamKnee)
      .line(points.inseamThigh)
      .curve(
        new Point((crotchExt + 10) * 0.75, m.waistToHips + (rise - m.waistToHips) * 0.35),
        new Point((crotchExt + 10) * 0.2, m.waistToHips),
        points.cbHip
      )
      .line(points.cbWaist)
      .close()
      .attr('class', 'fabric');

    const cx = halfWaist / 2 + 10;
    paths.grainline = new Path()
      .move(new Point(cx, 20))
      .line(new Point(cx, legLen - 20))
      .attr('class', 'grainline');

    return part;
  }
};

const Pants = new Design({
  parts: [front, back],
  data: { name: 'KORRA Pants', version: '1.0.0', type: 'pants' }
});

export { Pants, front, back };
