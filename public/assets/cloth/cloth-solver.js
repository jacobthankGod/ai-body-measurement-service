/**
 * XPBD Cloth Solver — Complete self-contained implementation
 * Extracted from vibe-stack/vibe-human (MIT License) and adapted for global scope
 *
 * Usage:
 *   var result = XPBD.validateAndLoadGarment(gltfScene, bodyBoundingBox)
 *   var solver = new XPBD.ClothSolver(mesh, params)
 *   var frame = solver.step(collisionSnapshot)
 */
(function() {
'use strict';

var XPBD = {};

// ===== TYPES =====

function smooth01(v) { var t = v < 0 ? 0 : v > 1 ? 1 : v; return t * t * (3 - 2 * t); }
function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

// ===== CONSTRAINT SOLVERS =====

function solveDistanceConstraintsFlat(positions, invMass, set, dt, seamRestScale, seamStiffness) {
  if (seamStiffness === undefined) seamStiffness = 1;
  var dtSq = dt * dt;
  var a = set.a, b = set.b, rest = set.rest, targetRest = set.targetRest;
  var hasTargetRest = set.hasTargetRest, compliance = set.compliance, count = set.count;
  for (var i = 0; i < count; i++) {
    var aIdx = a[i], bIdx = b[i];
    var ia = aIdx * 3, ib = bIdx * 3;
    var dx = positions[ib] - positions[ia];
    var dy = positions[ib + 1] - positions[ia + 1];
    var dz = positions[ib + 2] - positions[ia + 2];
    var lengthSq = dx * dx + dy * dy + dz * dz;
    if (lengthSq < 1e-14) continue;
    var wa = invMass[aIdx], wb = invMass[bIdx];
    var wsum = wa + wb;
    if (wsum < 1e-9) continue;
    var r = rest[i];
    if (hasTargetRest[i]) {
      var tr = targetRest[i];
      var scale = seamRestScale < 0 ? 0 : seamRestScale > 1 ? 1 : seamRestScale;
      r = tr + (r - tr) * scale;
    }
    var length = Math.sqrt(lengthSq);
    var C = length - r;
    var alpha = compliance[i] / dtSq;
    var stiffness = seamStiffness < 0 ? 0 : seamStiffness > 1 ? 1 : seamStiffness;
    var lambda = (-C / (wsum + alpha)) * stiffness;
    var invLength = 1 / length;
    var gx = dx * invLength, gy = dy * invLength, gz = dz * invLength;
    if (wa > 0) { positions[ia] -= wa * lambda * gx; positions[ia + 1] -= wa * lambda * gy; positions[ia + 2] -= wa * lambda * gz; }
    if (wb > 0) { positions[ib] += wb * lambda * gx; positions[ib + 1] += wb * lambda * gy; positions[ib + 2] += wb * lambda * gz; }
  }
}

function solveBendConstraintsFlat(positions, invMass, set, dt) {
  var dtSq = dt * dt;
  var a = set.a, b = set.b, c = set.c, rest = set.rest, compliance = set.compliance, count = set.count;
  for (var i = 0; i < count; i++) {
    var aIdx = a[i], bIdx = b[i], cIdx = c[i];
    var ia = aIdx * 3, ib = bIdx * 3, ic = cIdx * 3;
    var mx = (positions[ia] + positions[ic]) * 0.5;
    var my = (positions[ia + 1] + positions[ic + 1]) * 0.5;
    var mz = (positions[ia + 2] + positions[ic + 2]) * 0.5;
    var dx = positions[ib] - mx, dy = positions[ib + 1] - my, dz = positions[ib + 2] - mz;
    var lengthSq = dx * dx + dy * dy + dz * dz;
    if (lengthSq < 1e-14) continue;
    var wa = invMass[aIdx], wb = invMass[bIdx], wc = invMass[cIdx];
    var wsum = wb + 0.25 * (wa + wc);
    if (wsum < 1e-9) continue;
    var length = Math.sqrt(lengthSq);
    var C = length - rest[i];
    var alpha = compliance[i] / dtSq;
    var lambda = -C / (wsum + alpha);
    var invLength = 1 / length;
    var gx = dx * invLength, gy = dy * invLength, gz = dz * invLength;
    if (wb > 0) { positions[ib] += wb * lambda * gx; positions[ib + 1] += wb * lambda * gy; positions[ib + 2] += wb * lambda * gz; }
    if (wa > 0) { positions[ia] -= 0.5 * wa * lambda * gx; positions[ia + 1] -= 0.5 * wa * lambda * gy; positions[ia + 2] -= 0.5 * wa * lambda * gz; }
    if (wc > 0) { positions[ic] -= 0.5 * wc * lambda * gx; positions[ic + 1] -= 0.5 * wc * lambda * gy; positions[ic + 2] -= 0.5 * wc * lambda * gz; }
  }
}

function solvePinConstraints(mesh) {
  var pinConstraints = mesh.pinConstraints, positions = mesh.positions, prevPositions = mesh.prevPositions;
  for (var i = 0; i < pinConstraints.length; i++) {
    var pin = pinConstraints[i];
    var offset = pin.particle * 3;
    var stiffness = Math.max(0, Math.min(1, pin.stiffness));
    positions[offset] += (pin.x - positions[offset]) * stiffness;
    positions[offset + 1] += (pin.y - positions[offset + 1]) * stiffness;
    positions[offset + 2] += (pin.z - positions[offset + 2]) * stiffness;
    prevPositions[offset] = positions[offset];
    prevPositions[offset + 1] = positions[offset + 1];
    prevPositions[offset + 2] = positions[offset + 2];
  }
}

// ===== COLLISION SOLVERS =====

var CONTACT_RESULT = new Float32Array(6);
var TRIANGLE_RESULT = new Float32Array(6);
var FRICTION_RESULT = new Float32Array(3);
var ROTATED_LOCAL = new Float32Array(3);
var ROTATED_SURFACE = new Float32Array(3);
var ROTATED_NORMAL = new Float32Array(3);

function solveCollisionConstraints(mesh, snapshot) {
  if (!snapshot || (snapshot.proxies.length === 0 && (snapshot.meshColliders ? snapshot.meshColliders.length : 0) === 0)) return;
  var positions = mesh.positions, prevPositions = mesh.prevPositions, invMass = mesh.invMass;
  var particleCount = mesh.particleCount, particleFrictions = mesh.particleFrictions;

  for (var particle = 0; particle < particleCount; particle++) {
    if (invMass[particle] === 0) continue;
    var garmentFriction = (particleFrictions && particleFrictions[particle]) || 1;
    var offset = particle * 3;
    var prevX = prevPositions[offset], prevY = prevPositions[offset + 1], prevZ = prevPositions[offset + 2];
    var px = positions[offset], py = positions[offset + 1], pz = positions[offset + 2];
    var hit = false;

    var meshColliders = snapshot.meshColliders || [];
    for (var mc = 0; mc < meshColliders.length; mc++) {
      var collider = meshColliders[mc];
      if (collider.bvh && pushOutOfMeshColliderBVH(collider, collider.skin + collider.thickness, prevX, prevY, prevZ, px, py, pz, CONTACT_RESULT)) {
        px = CONTACT_RESULT[0]; py = CONTACT_RESULT[1]; pz = CONTACT_RESULT[2];
        applyContactFriction(FRICTION_RESULT, prevX, prevY, prevZ, px, py, pz, CONTACT_RESULT[3], CONTACT_RESULT[4], CONTACT_RESULT[5], collider.friction * garmentFriction, collider.skin + collider.thickness);
        px = FRICTION_RESULT[0]; py = FRICTION_RESULT[1]; pz = FRICTION_RESULT[2];
        hit = true;
      }
    }

    var proxies = snapshot.proxies || [];
    for (var p = 0; p < proxies.length; p++) {
      var proxy = proxies[p];
      if (pushOut(proxy, px, py, pz, CONTACT_RESULT)) {
        px = CONTACT_RESULT[0]; py = CONTACT_RESULT[1]; pz = CONTACT_RESULT[2];
        var proxyR = proxy.kind === 'ellipsoid' ? Math.min(proxy.rx, proxy.ry, proxy.rz) + proxy.skin : proxy.r + proxy.skin;
        applyContactFriction(FRICTION_RESULT, prevX, prevY, prevZ, px, py, pz, CONTACT_RESULT[3], CONTACT_RESULT[4], CONTACT_RESULT[5], proxy.friction * garmentFriction, proxyR);
        px = FRICTION_RESULT[0]; py = FRICTION_RESULT[1]; pz = FRICTION_RESULT[2];
        hit = true;
      }
    }

    if (hit) { positions[offset] = px; positions[offset + 1] = py; positions[offset + 2] = pz; }
  }
}

function pushOutOfMeshColliderBVH(collider, target, prevX, prevY, prevZ, px, py, pz, out) {
  var bvh = collider.bvh, triangleNormals = collider.triangleNormals, vertices = collider.vertices, indices = collider.indices;
  if (!isOutsideBounds(collider.bounds, target, px, py, pz)) {
    var count = bvhQueryPointRadius(bvh, px, py, pz, target);
    var bestDistSq = Infinity, bestX = 0, bestY = 0, bestZ = 0, bestNx = 0, bestNy = 1, bestNz = 0;
    var candidates = bvh.candidates;
    for (var c = 0; c < count; c++) {
      var triangle = candidates[c];
      var nx = triangleNormals[triangle * 3], ny = triangleNormals[triangle * 3 + 1], nz = triangleNormals[triangle * 3 + 2];
      if (nx === 0 && ny === 0 && nz === 0) continue;
      var ia = indices[triangle * 3] * 3, ib = indices[triangle * 3 + 1] * 3, ic = indices[triangle * 3 + 2] * 3;
      closestPointTriangleRaw(px, py, pz, vertices[ia], vertices[ia + 1], vertices[ia + 2], vertices[ib], vertices[ib + 1], vertices[ib + 2], vertices[ic], vertices[ic + 1], vertices[ic + 2], TRIANGLE_RESULT);
      var deltaX = px - TRIANGLE_RESULT[0], deltaY = py - TRIANGLE_RESULT[1], deltaZ = pz - TRIANGLE_RESULT[2];
      var distSq = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ;
      if (distSq < bestDistSq) { bestDistSq = distSq; bestX = TRIANGLE_RESULT[0]; bestY = TRIANGLE_RESULT[1]; bestZ = TRIANGLE_RESULT[2]; bestNx = nx; bestNy = ny; bestNz = nz; }
    }
    if (bestDistSq !== Infinity) {
      var dx = px - bestX, dy = py - bestY, dz = pz - bestZ;
      var signed = dx * bestNx + dy * bestNy + dz * bestNz;
      var dist = Math.sqrt(bestDistSq);
      if (signed < 0 || dist < target) {
        var nx2, ny2, nz2, correction;
        if (signed >= 0) { if (dist > 1e-6) { var inv = 1 / dist; nx2 = dx * inv; ny2 = dy * inv; nz2 = dz * inv; } else { nx2 = bestNx; ny2 = bestNy; nz2 = bestNz; } correction = target - dist; }
        else { nx2 = bestNx; ny2 = bestNy; nz2 = bestNz; correction = target + dist; }
        out[0] = px + nx2 * correction; out[1] = py + ny2 * correction; out[2] = pz + nz2 * correction;
        out[3] = nx2; out[4] = ny2; out[5] = nz2;
        return true;
      }
    }
  }
  return false;
}

function pushOut(proxy, px, py, pz, out) {
  if (proxy.kind === 'sphere') return pushOutOfSphere(proxy, px, py, pz, out);
  if (proxy.kind === 'capsule') return pushOutOfCapsule(proxy, px, py, pz, out);
  if (proxy.kind === 'ellipsoid') return pushOutOfEllipsoid(proxy, px, py, pz, out);
  return false;
}

function pushOutOfSphere(proxy, px, py, pz, out) {
  var target = proxy.r + proxy.skin;
  var dx = px - proxy.cx, dy = py - proxy.cy, dz = pz - proxy.cz;
  if (dx <= -target || dx >= target || dy <= -target || dy >= target || dz <= -target || dz >= target) return false;
  var distSq = dx * dx + dy * dy + dz * dz;
  if (distSq >= target * target) return false;
  var dist = Math.sqrt(distSq) || 1e-6, inv = 1 / dist;
  out[0] = proxy.cx + dx * inv * target; out[1] = proxy.cy + dy * inv * target; out[2] = proxy.cz + dz * inv * target;
  out[3] = dx * inv; out[4] = dy * inv; out[5] = dz * inv;
  return true;
}

function pushOutOfCapsule(proxy, px, py, pz, out) {
  var abx = proxy.bx - proxy.ax, aby = proxy.by - proxy.ay, abz = proxy.bz - proxy.az;
  var target = proxy.r + proxy.skin;
  if (px < Math.min(proxy.ax, proxy.bx) - target || px > Math.max(proxy.ax, proxy.bx) + target) return false;
  var apx = px - proxy.ax, apy = py - proxy.ay, apz = pz - proxy.az;
  var segLenSq = abx * abx + aby * aby + abz * abz;
  var t = segLenSq < 1e-9 ? 0 : clamp01((apx * abx + apy * aby + apz * abz) / segLenSq);
  var qx = proxy.ax + abx * t, qy = proxy.ay + aby * t, qz = proxy.az + abz * t;
  var dx = px - qx, dy = py - qy, dz = pz - qz;
  var distSq = dx * dx + dy * dy + dz * dz;
  if (distSq >= target * target) return false;
  var dist = Math.sqrt(distSq) || 1e-6, inv = 1 / dist;
  out[0] = qx + dx * inv * target; out[1] = qy + dy * inv * target; out[2] = qz + dz * inv * target;
  out[3] = dx * inv; out[4] = dy * inv; out[5] = dz * inv;
  return true;
}

function pushOutOfEllipsoid(proxy, px, py, pz, out) {
  var dx = px - proxy.cx, dy = py - proxy.cy, dz = pz - proxy.cz;
  var outerR = Math.max(proxy.rx, proxy.ry, proxy.rz) + proxy.skin;
  if (Math.abs(dx) > outerR || Math.abs(dy) > outerR || Math.abs(dz) > outerR) return false;
  rotateVecInto(dx, dy, dz, -proxy.qx, -proxy.qy, -proxy.qz, proxy.qw, ROTATED_LOCAL);
  var sx = ROTATED_LOCAL[0] / proxy.rx, sy = ROTATED_LOCAL[1] / proxy.ry, sz = ROTATED_LOCAL[2] / proxy.rz;
  var scaledLen = Math.sqrt(sx * sx + sy * sy + sz * sz) || 1e-6;
  if (scaledLen >= 1 + proxy.skin / Math.min(proxy.rx, proxy.ry, proxy.rz)) return false;
  var surfScale = 1 / scaledLen;
  var slx = ROTATED_LOCAL[0] * surfScale, sly = ROTATED_LOCAL[1] * surfScale, slz = ROTATED_LOCAL[2] * surfScale;
  normalizeInto(slx / (proxy.rx * proxy.rx), sly / (proxy.ry * proxy.ry), slz / (proxy.rz * proxy.rz), ROTATED_NORMAL);
  rotateVecInto(slx, sly, slz, proxy.qx, proxy.qy, proxy.qz, proxy.qw, ROTATED_SURFACE);
  rotateVecInto(ROTATED_NORMAL[0], ROTATED_NORMAL[1], ROTATED_NORMAL[2], proxy.qx, proxy.qy, proxy.qz, proxy.qw, ROTATED_NORMAL);
  normalizeInto(ROTATED_NORMAL[0], ROTATED_NORMAL[1], ROTATED_NORMAL[2], ROTATED_NORMAL);
  out[0] = proxy.cx + ROTATED_SURFACE[0] + ROTATED_NORMAL[0] * proxy.skin;
  out[1] = proxy.cy + ROTATED_SURFACE[1] + ROTATED_NORMAL[1] * proxy.skin;
  out[2] = proxy.cz + ROTATED_SURFACE[2] + ROTATED_NORMAL[2] * proxy.skin;
  out[3] = ROTATED_NORMAL[0]; out[4] = ROTATED_NORMAL[1]; out[5] = ROTATED_NORMAL[2];
  return true;
}

function closestPointTriangleRaw(px, py, pz, ax, ay, az, bx, by, bz, cx, cy, cz, out) {
  var abx = bx - ax, aby = by - ay, abz = bz - az;
  var acx = cx - ax, acy = cy - ay, acz = cz - az;
  var apx = px - ax, apy = py - ay, apz = pz - az;
  var d1 = abx * apx + aby * apy + abz * apz;
  var d2 = acx * apx + acy * apy + acz * apz;
  if (d1 <= 0 && d2 <= 0) { out[0] = ax; out[1] = ay; out[2] = az; return; }
  var bpx = px - bx, bpy = py - by, bpz = pz - bz;
  var d3 = abx * bpx + aby * bpy + abz * bpz;
  var d4 = acx * bpx + acy * bpy + acz * bpz;
  if (d3 >= 0 && d4 <= d3) { out[0] = bx; out[1] = by; out[2] = bz; return; }
  var vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) { var v = d1 / (d1 - d3); out[0] = ax + abx * v; out[1] = ay + aby * v; out[2] = az + abz * v; return; }
  var cpx = px - cx, cpy = py - cy, cpz = pz - cz;
  var d5 = abx * cpx + aby * cpy + abz * cpz;
  var d6 = acx * cpx + acy * cpy + acz * cpz;
  if (d6 >= 0 && d5 <= d6) { out[0] = cx; out[1] = cy; out[2] = cz; return; }
  var vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) { var w = d2 / (d2 - d6); out[0] = ax + acx * w; out[1] = ay + acy * w; out[2] = az + acz * w; return; }
  var va = d3 * d6 - d5 * d4;
  if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) { var w2 = (d4 - d3) / ((d4 - d3) + (d5 - d6)); out[0] = bx + (cx - bx) * w2; out[1] = by + (cy - by) * w2; out[2] = bz + (cz - bz) * w2; return; }
  var denom = 1 / (va + vb + vc);
  var v2 = vb * denom, w3 = vc * denom;
  out[0] = ax + abx * v2 + acx * w3; out[1] = ay + aby * v2 + acy * w3; out[2] = az + abz * v2 + acz * w3;
}

function applyContactFriction(out, prevX, prevY, prevZ, px, py, pz, nx, ny, nz, friction, penDepth) {
  if (penDepth <= 1e-6) { out[0] = px; out[1] = py; out[2] = pz; return; }
  var dx = px - prevX, dy = py - prevY, dz = pz - prevZ;
  var normalDot = dx * nx + dy * ny + dz * nz;
  var tx = dx - nx * normalDot, ty = dy - ny * normalDot, tz = dz - nz * normalDot;
  var tangMagSq = tx * tx + ty * ty + tz * tz;
  var coulombLimit = friction * penDepth;
  if (tangMagSq <= coulombLimit * coulombLimit) { out[0] = px - tx; out[1] = py - ty; out[2] = pz - tz; }
  else { var tangMag = Math.sqrt(tangMagSq); var allowed = coulombLimit / tangMag; out[0] = px - tx * (1 - allowed); out[1] = py - ty * (1 - allowed); out[2] = pz - tz * (1 - allowed); }
}

function rotateVecInto(x, y, z, qx, qy, qz, qw, out) {
  var tx = 2 * (qy * z - qz * y), ty = 2 * (qz * x - qx * z), tz = 2 * (qx * y - qy * x);
  out[0] = x + qw * tx + (qy * tz - qz * ty); out[1] = y + qw * ty + (qz * tx - qx * tz); out[2] = z + qw * tz + (qx * ty - qy * tx);
}
function normalizeInto(x, y, z, out) { var l = Math.sqrt(x * x + y * y + z * z) || 1e-6; out[0] = x / l; out[1] = y / l; out[2] = z / l; }
function isOutsideBounds(bounds, margin, x, y, z) { return x < bounds.minX - margin || x > bounds.maxX + margin || y < bounds.minY - margin || y > bounds.maxY + margin || z < bounds.minZ - margin || z > bounds.maxZ + margin; }

// ===== TRIANGLE BVH =====

var STACK_SIZE = 64, LEAF_TRIANGLES = 4;

function buildTriangleBVH(vertices, indices) {
  var triangleCount = indices.length / 3;
  var cx = new Float32Array(triangleCount), cy = new Float32Array(triangleCount), cz = new Float32Array(triangleCount);
  for (var t = 0; t < triangleCount; t++) {
    var ia = indices[t * 3] * 3, ib = indices[t * 3 + 1] * 3, ic = indices[t * 3 + 2] * 3;
    cx[t] = (vertices[ia] + vertices[ib] + vertices[ic]) / 3;
    cy[t] = (vertices[ia + 1] + vertices[ib + 1] + vertices[ic + 1]) / 3;
    cz[t] = (vertices[ia + 2] + vertices[ib + 2] + vertices[ic + 2]) / 3;
  }
  var triOrder = new Uint32Array(triangleCount);
  for (var i = 0; i < triangleCount; i++) triOrder[i] = i;
  var maxNodes = Math.max(1, 2 * triangleCount);
  var bounds = new Float32Array(maxNodes * 6);
  var leftChild = new Int32Array(maxNodes).fill(-1);
  var rightChild = new Int32Array(maxNodes).fill(-1);
  var triStart = new Int32Array(maxNodes).fill(-1);
  var triCount = new Int32Array(maxNodes).fill(0);
  var nodeCount = 0;

  function build(start, end) {
    var node = nodeCount++; var count = end - start;
    if (count <= LEAF_TRIANGLES) { triStart[node] = start; triCount[node] = count; return node; }
    var minX = Infinity, minY = Infinity, minZ = Infinity, maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (var i = start; i < end; i++) {
      var t = triOrder[i];
      if (cx[t] < minX) minX = cx[t]; if (cx[t] > maxX) maxX = cx[t];
      if (cy[t] < minY) minY = cy[t]; if (cy[t] > maxY) maxY = cy[t];
      if (cz[t] < minZ) minZ = cz[t]; if (cz[t] > maxZ) maxZ = cz[t];
    }
    var extX = maxX - minX, extY = maxY - minY, extZ = maxZ - minZ;
    var axis = extX >= extY ? (extX >= extZ ? 0 : 2) : (extY >= extZ ? 1 : 2);
    var centroidAxis = axis === 0 ? cx : axis === 1 ? cy : cz;
    var mid = start + (count >> 1);
    quickselect(triOrder, start, end - 1, mid, centroidAxis);
    var left = build(start, mid), right = build(mid, end);
    leftChild[node] = left; rightChild[node] = right; triStart[node] = -1; triCount[node] = 0;
    return node;
  }
  build(0, triangleCount);

  var refitOrder = new Int32Array(nodeCount);
  var w = 0, tmp = new Int32Array(nodeCount), sp = 0;
  tmp[sp++] = 0; var out = [];
  while (sp > 0) { var n = tmp[--sp]; out.push(n); var l = leftChild[n], r = rightChild[n]; if (l >= 0) tmp[sp++] = l; if (r >= 0) tmp[sp++] = r; }
  for (var i = out.length - 1; i >= 0; i--) refitOrder[w++] = out[i];

  var bvh = { nodeCount: nodeCount, bounds: bounds, leftChild: leftChild, rightChild: rightChild, triStart: triStart, triCount: triCount, triOrder: triOrder, vertices: vertices, indices: indices, stack: new Int32Array(STACK_SIZE), refitOrder: refitOrder, candidates: new Uint32Array(triangleCount) };
  refitTriangleBVH(bvh, vertices);
  return bvh;
}

function refitTriangleBVH(bvh, vertices) {
  bvh.vertices = vertices;
  var bounds = bvh.bounds, leftChild = bvh.leftChild, rightChild = bvh.rightChild;
  var triStart = bvh.triStart, triCount = bvh.triCount, triOrder = bvh.triOrder, indices = bvh.indices, refitOrder = bvh.refitOrder;
  for (var oi = 0; oi < refitOrder.length; oi++) {
    var node = refitOrder[oi], b = node * 6;
    if (leftChild[node] < 0) {
      var minX = Infinity, minY = Infinity, minZ = Infinity, maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
      var start = triStart[node], end = start + triCount[node];
      for (var i = start; i < end; i++) { var t = triOrder[i]; for (var k = 0; k < 3; k++) { var v = indices[t * 3 + k] * 3; var x = vertices[v], y = vertices[v + 1], z = vertices[v + 2]; if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; if (z < minZ) minZ = z; if (z > maxZ) maxZ = z; } }
      bounds[b] = minX; bounds[b + 1] = minY; bounds[b + 2] = minZ; bounds[b + 3] = maxX; bounds[b + 4] = maxY; bounds[b + 5] = maxZ;
    } else {
      var l = leftChild[node] * 6, r = rightChild[node] * 6;
      bounds[b] = Math.min(bounds[l], bounds[r]); bounds[b + 1] = Math.min(bounds[l + 1], bounds[r + 1]); bounds[b + 2] = Math.min(bounds[l + 2], bounds[r + 2]);
      bounds[b + 3] = Math.max(bounds[l + 3], bounds[r + 3]); bounds[b + 4] = Math.max(bounds[l + 4], bounds[r + 4]); bounds[b + 5] = Math.max(bounds[l + 5], bounds[r + 5]);
    }
  }
}

function bvhQueryPointRadius(bvh, px, py, pz, radius) {
  var bounds = bvh.bounds, leftChild = bvh.leftChild, rightChild = bvh.rightChild;
  var triStart = bvh.triStart, triCount = bvh.triCount, triOrder = bvh.triOrder, stack = bvh.stack, candidates = bvh.candidates;
  var radiusSq = radius * radius, count = 0, sp = 0;
  stack[sp++] = 0;
  while (sp > 0) {
    var node = stack[--sp], b2 = node * 6;
    var dx = 0, dy = 0, dz = 0;
    if (px < bounds[b2]) dx = bounds[b2] - px; else if (px > bounds[b2 + 3]) dx = px - bounds[b2 + 3];
    if (py < bounds[b2 + 1]) dy = bounds[b2 + 1] - py; else if (py > bounds[b2 + 4]) dy = py - bounds[b2 + 4];
    if (pz < bounds[b2 + 2]) dz = bounds[b2 + 2] - pz; else if (pz > bounds[b2 + 5]) dz = pz - bounds[b2 + 5];
    if (dx * dx + dy * dy + dz * dz > radiusSq) continue;
    var l = leftChild[node];
    if (l < 0) { var start = triStart[node], end = start + triCount[node]; for (var i = start; i < end; i++) candidates[count++] = triOrder[i]; }
    else if (sp + 2 <= stack.length) { stack[sp++] = l; stack[sp++] = rightChild[node]; }
    else { count = collectSubtree(bvh, node, candidates, count); }
  }
  return count;
}

function collectSubtree(bvh, node, out, count) {
  var leftChild = bvh.leftChild, rightChild = bvh.rightChild, triStart = bvh.triStart, triCount = bvh.triCount, triOrder = bvh.triOrder;
  var l = leftChild[node];
  if (l < 0) { var start = triStart[node], end = start + triCount[node]; for (var i = start; i < end; i++) out[count++] = triOrder[i]; return count; }
  count = collectSubtree(bvh, l, out, count);
  count = collectSubtree(bvh, rightChild[node], out, count);
  return count;
}

function quickselect(order, lo, hi, k, key) {
  while (lo < hi) {
    var pivot = key[order[(lo + hi) >> 1]], i = lo, j = hi;
    while (i <= j) { while (key[order[i]] < pivot) i++; while (key[order[j]] > pivot) j--; if (i <= j) { var tmp = order[i]; order[i] = order[j]; order[j] = tmp; i++; j--; } }
    if (k <= j) hi = j; else if (k >= i) lo = i; else break;
  }
}

// ===== SELF-COLLISION =====

function ClothSelfCollisionSolver(mesh) {
  var bucketCount = nextPow2(Math.max(32, mesh.particleCount * 2));
  this.bucketHeads = new Int32Array(bucketCount);
  this.bucketNext = new Int32Array(mesh.particleCount);
  this.cellX = new Int32Array(mesh.particleCount);
  this.cellY = new Int32Array(mesh.particleCount);
  this.cellZ = new Int32Array(mesh.particleCount);
  this.bucketMask = bucketCount - 1;
  var adj = buildAdjacency(mesh);
  this.adjacencyOffsets = adj.offsets;
  this.adjacency = adj.neighbors;
}

ClothSelfCollisionSolver.prototype.solve = function(mesh, options) {
  // Simplified: just particle-particle spatial hash
  var radius = options.radius, stiffness = options.stiffness;
  if (mesh.particleCount < 2 || radius <= 0 || stiffness <= 0) return;
  var positions = mesh.positions, invMass = mesh.invMass, particleCount = mesh.particleCount;
  var radiusSq = radius * radius, invCellSize = 1 / radius;
  var heads = this.bucketHeads, next = this.bucketNext, mask = this.bucketMask;
  heads.fill(-1);
  for (var p = 0; p < particleCount; p++) {
    var o = p * 3;
    var cx = Math.floor(positions[o] * invCellSize), cy = Math.floor(positions[o + 1] * invCellSize), cz = Math.floor(positions[o + 2] * invCellSize);
    this.cellX[p] = cx; this.cellY[p] = cy; this.cellZ[p] = cz;
    next[p] = heads[hashCell(cx, cy, cz) & mask]; heads[hashCell(cx, cy, cz) & mask] = p;
  }
  for (var a = 0; a < particleCount; a++) {
    var wa = invMass[a]; if (wa <= 0) continue;
    for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) for (var dz = -1; dz <= 1; dz++) {
      var b = heads[hashCell(this.cellX[a] + dx, this.cellY[a] + dy, this.cellZ[a] + dz) & mask];
      while (b >= 0) { var nextB = next[b]; if (b > a && !this.areLinked(a, b)) this.solvePair(mesh, a, b, wa, radius, radiusSq, stiffness); b = nextB; }
    }
  }
};

ClothSelfCollisionSolver.prototype.solvePair = function(mesh, a, b, wa, radius, radiusSq, stiffness) {
  var positions = mesh.positions, invMass = mesh.invMass;
  var wb = invMass[b], wsum = wa + wb; if (wsum <= 1e-9) return;
  var ia = a * 3, ib = b * 3;
  var nx = positions[ib] - positions[ia], ny = positions[ib + 1] - positions[ia + 1], nz = positions[ib + 2] - positions[ia + 2];
  var distSq = nx * nx + ny * ny + nz * nz; if (distSq >= radiusSq) return;
  var dist = Math.sqrt(distSq); if (dist > 1e-7) { var inv = 1 / dist; nx *= inv; ny *= inv; nz *= inv; } else { nx = a & 1 ? 1 : -1; ny = 0; nz = 0; }
  var corr = (radius - dist) * stiffness, sA = corr * (wa / wsum), sB = corr * (wb / wsum);
  positions[ia] -= nx * sA; positions[ia + 1] -= ny * sA; positions[ia + 2] -= nz * sA;
  positions[ib] += nx * sB; positions[ib + 1] += ny * sB; positions[ib + 2] += nz * sB;
};

ClothSelfCollisionSolver.prototype.areLinked = function(a, b) {
  var start = this.adjacencyOffsets[a], end = this.adjacencyOffsets[a + 1];
  for (var i = start; i < end; i++) if (this.adjacency[i] === b) return true;
  return false;
};

function buildAdjacency(mesh) {
  var pc = mesh.particleCount, pairs = [];
  function addPair(a, b) { if (a !== b && a >= 0 && b >= 0 && a < pc && b < pc) pairs.push(a < b ? a * pc + b : b * pc + a); }
  function addDist(cs) { for (var i = 0; i < cs.length; i++) addPair(cs[i].a, cs[i].b); }
  addDist(mesh.stretchConstraints); addDist(mesh.shearConstraints); addDist(mesh.bendDistanceConstraints); addDist(mesh.seamConstraints);
  for (var i = 0; i < mesh.triangles.length; i += 3) { addPair(mesh.triangles[i], mesh.triangles[i + 1]); addPair(mesh.triangles[i + 1], mesh.triangles[i + 2]); addPair(mesh.triangles[i + 2], mesh.triangles[i]); }
  pairs.sort(function(a, b) { return a - b; });
  var uc = 0, prev = -1;
  for (var i = 0; i < pairs.length; i++) { if (pairs[i] === prev) continue; pairs[uc++] = pairs[i]; prev = pairs[i]; }
  var offsets = new Uint32Array(pc + 1);
  for (var i = 0; i < uc; i++) { var key = pairs[i], a = Math.floor(key / pc), b = key - a * pc; offsets[a + 1]++; offsets[b + 1]++; }
  for (var i = 1; i < offsets.length; i++) offsets[i] += offsets[i - 1];
  var cursor = new Uint32Array(offsets), neighbors = new Uint32Array(offsets[pc]);
  for (var i = 0; i < uc; i++) { var key = pairs[i], a = Math.floor(key / pc), b = key - a * pc; neighbors[cursor[a]++] = b; neighbors[cursor[b]++] = a; }
  return { offsets: offsets, neighbors: neighbors };
}

function nextPow2(v) { var p = 1; while (p < v) p <<= 1; return p; }
function hashCell(x, y, z) { return ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) | 0; }

// ===== MAIN SOLVER =====

function flattenDistanceConstraints(source) {
  var count = source.length;
  var a = new Uint32Array(count), b = new Uint32Array(count), rest = new Float32Array(count);
  var targetRest = new Float32Array(count), hasTargetRest = new Uint8Array(count), compliance = new Float32Array(count);
  for (var i = 0; i < count; i++) {
    var c = source[i]; a[i] = c.a; b[i] = c.b; rest[i] = c.rest;
    if (c.targetRest !== undefined) { hasTargetRest[i] = 1; targetRest[i] = c.targetRest; }
    compliance[i] = c.compliance;
  }
  return { a: a, b: b, rest: rest, targetRest: targetRest, hasTargetRest: hasTargetRest, compliance: compliance, count: count };
}

function flattenBendConstraints(source) {
  var count = source.length;
  var a = new Uint32Array(count), b = new Uint32Array(count), c = new Uint32Array(count);
  var rest = new Float32Array(count), compliance = new Float32Array(count);
  for (var i = 0; i < count; i++) { var k = source[i]; a[i] = k.a; b[i] = k.b; c[i] = k.c; rest[i] = k.rest; compliance[i] = k.compliance; }
  return { a: a, b: b, c: c, rest: rest, compliance: compliance, count: count };
}

function ClothSolver(mesh, params) {
  this.mesh = mesh;
  this.params = params;
  this.colliders = null;
  this.elapsed = 0;
  this.stretchFlat = flattenDistanceConstraints(mesh.stretchConstraints);
  this.shearFlat = flattenDistanceConstraints(mesh.shearConstraints);
  this.bendDistanceFlat = flattenDistanceConstraints(mesh.bendDistanceConstraints);
  this.seamFlat = flattenDistanceConstraints(mesh.seamConstraints);
  this.bendFlat = flattenBendConstraints(mesh.bendConstraints);
  this.grabParticle = -1;
  this.seamAccumX = new Float32Array(mesh.particleCount);
  this.seamAccumY = new Float32Array(mesh.particleCount);
  this.seamAccumZ = new Float32Array(mesh.particleCount);
  this.seamAccumW = new Float32Array(mesh.particleCount);
  this.seamTouched = new Uint8Array(mesh.particleCount);
  this.seamTouchedList = new Uint32Array(mesh.particleCount);
  this.seamTouchedCount = 0;
  this.selfCollision = new ClothSelfCollisionSolver(mesh);
}

ClothSolver.prototype.step = function(snapshot) {
  if (snapshot !== undefined) this.colliders = snapshot;
  var dt = this.params.dt / this.params.substeps;
  for (var substep = 0; substep < this.params.substeps; substep++) {
    var sp = this._sewingProgress(), gs = this._gravityProgress(), damp = this._dampingForAssembly(sp);
    this._integrate(dt, damp, this.params.gravity * gs);
    this._clampDisplacement(sp);
    var srs = 1 - sp, ss = this._seamStiffness(sp), bb = this._bendBlend(sp);
    for (var iter = 0; iter < this.params.iterations; iter++) {
      solveDistanceConstraintsFlat(this.mesh.positions, this.mesh.invMass, this.stretchFlat, dt, 0);
      solveDistanceConstraintsFlat(this.mesh.positions, this.mesh.invMass, this.shearFlat, dt, 0);
      solveDistanceConstraintsFlat(this.mesh.positions, this.mesh.invMass, this.seamFlat, dt, srs, ss);
      if (bb > 0 && (iter & 1) === 0) solveBendConstraintsFlat(this.mesh.positions, this.mesh.invMass, this.bendFlat, dt * bb);
      solvePinConstraints(this.mesh);
    }
    solveCollisionConstraints(this.mesh, this.colliders);
    this._deriveVelocities(dt, 0.05 + 0.95 * sp * sp);
    this._applyGround();
    this.elapsed += dt;
  }
  return { positions: this.mesh.positions };
};

ClothSolver.prototype._integrate = function(dt, damping, gravity) {
  var dampPerStep = Math.pow(1 - damping, dt);
  var positions = this.mesh.positions, prev = this.mesh.prevPositions, vel = this.mesh.velocities;
  var invMass = this.mesh.invMass, pc = this.mesh.particleCount, gs = gravity * dt;
  for (var p = 0; p < pc; p++) {
    var o = p * 3;
    if (invMass[p] === 0) { prev[o] = positions[o]; prev[o + 1] = positions[o + 1]; prev[o + 2] = positions[o + 2]; vel[o] = 0; vel[o + 1] = 0; vel[o + 2] = 0; continue; }
    var vx = vel[o] * dampPerStep, vy = vel[o + 1] * dampPerStep + gs, vz = vel[o + 2] * dampPerStep;
    prev[o] = positions[o]; prev[o + 1] = positions[o + 1]; prev[o + 2] = positions[o + 2];
    positions[o] += vx * dt; positions[o + 1] += vy * dt; positions[o + 2] += vz * dt;
  }
};

ClothSolver.prototype._deriveVelocities = function(dt, retention) {
  var maxV = this.params.maxVelocity || 8, maxVSq = maxV * maxV, invDt = 1 / dt;
  var positions = this.mesh.positions, prev = this.mesh.prevPositions, vel = this.mesh.velocities, pc = this.mesh.particleCount;
  for (var p = 0; p < pc; p++) {
    var o = p * 3;
    var vx = (positions[o] - prev[o]) * invDt * retention, vy = (positions[o + 1] - prev[o + 1]) * invDt * retention, vz = (positions[o + 2] - prev[o + 2]) * invDt * retention;
    var ss = vx * vx + vy * vy + vz * vz;
    if (ss > maxVSq) { var s = maxV / Math.sqrt(ss); vx *= s; vy *= s; vz *= s; prev[o] = positions[o] - vx * dt; prev[o + 1] = positions[o + 1] - vy * dt; prev[o + 2] = positions[o + 2] - vz * dt; }
    vel[o] = vx; vel[o + 1] = vy; vel[o + 2] = vz;
  }
};

ClothSolver.prototype._clampDisplacement = function(sp) {
  var skin = this.colliders && this.colliders.meshColliders && this.colliders.meshColliders[0] ? this.colliders.meshColliders[0].skin : 0.022;
  var thick = this.colliders && this.colliders.meshColliders && this.colliders.meshColliders[0] ? this.colliders.meshColliders[0].thickness : 0.008;
  var limit = Math.max(0.02, (skin + thick) * 1.35) * (0.6 + 0.4 * sp);
  var limitSq = limit * limit;
  var positions = this.mesh.positions, prev = this.mesh.prevPositions, pc = this.mesh.particleCount;
  for (var p = 0; p < pc; p++) {
    var o = p * 3;
    var dx = positions[o] - prev[o], dy = positions[o + 1] - prev[o + 1], dz = positions[o + 2] - prev[o + 2];
    var dSq = dx * dx + dy * dy + dz * dz;
    if (dSq <= limitSq) continue;
    var s = limit / Math.sqrt(dSq);
    positions[o] = prev[o] + dx * s; positions[o + 1] = prev[o + 1] + dy * s; positions[o + 2] = prev[o + 2] + dz * s;
  }
};

ClothSolver.prototype._applyGround = function() {
  var positions = this.mesh.positions, prev = this.mesh.prevPositions, pc = this.mesh.particleCount, gy = this.params.groundY;
  for (var p = 0; p < pc; p++) { var o = p * 3 + 1; if (positions[o] < gy) { positions[o] = gy; prev[o] = gy; } }
};

ClothSolver.prototype._sewingProgress = function() { var d = this.params.sewingTime || 1.2; return d <= 0 ? 1 : smooth01(this.elapsed / d); };
ClothSolver.prototype._gravityProgress = function() { var sd = this.params.sewingTime || 1.2, delay = this.params.gravityDelayTime || sd * 0.85, dur = this.params.gravityRampTime || 0.45; return dur <= 0 ? 1 : smooth01((this.elapsed - delay) / dur); };
ClothSolver.prototype._dampingForAssembly = function(sp) { var base = clamp01(this.params.damping); return base + (0.22 - base) * (1 - sp); };
ClothSolver.prototype._seamStiffness = function(sp) { return 0.2 + 0.8 * smooth01((sp - 0.2) / 0.8); };
ClothSolver.prototype._bendBlend = function(sp) { return smooth01((sp - 0.55) / 0.45); };

ClothSolver.prototype.setSolverIterations = function(substeps, iterations) {
  this.params.substeps = Math.max(1, Math.round(substeps));
  this.params.iterations = Math.max(1, Math.round(iterations));
};

// ===== GARMENT LOADER =====

function validateAndBuildClothMesh(gltfScene, bodyBoundingBox) {
  var warnings = [];
  var mesh = findLargestMesh(gltfScene);
  if (!mesh) return { ok: false, error: 'No mesh found in GLB file' };
  var geo = mesh.geometry, vertexCount = geo.attributes.position.count;
  if (vertexCount > 30000) return { ok: false, error: 'Too many vertices (' + vertexCount + '). Max 30,000.' };
  if (vertexCount > 3000) warnings.push('High vertex count (' + vertexCount + '). Use "Fast" quality for best performance.');

  var positions = new Float32Array(geo.attributes.position.array);
  var indices = geo.index ? new Uint32Array(geo.index.array) : (function() { var idx = new Uint32Array(vertexCount); for (var i = 0; i < vertexCount; i++) idx[i] = i; return idx; })();

  // Scale normalization
  var glbBox = computeBB(positions);
  var glbH = glbBox.maxY - glbBox.minY, bodyH = bodyBoundingBox.max.y - bodyBoundingBox.minY;
  if (bodyH > 0 && glbH > 0) {
    var ratio = glbH / bodyH;
    if (ratio > 5 || ratio < 0.2) {
      var sc = bodyH / glbH, cx = (glbBox.minX + glbBox.maxX) / 2, cy = (glbBox.minY + glbBox.maxY) / 2, cz = (glbBox.minZ + glbBox.maxZ) / 2;
      for (var i = 0; i < positions.length; i += 3) { positions[i] = (positions[i] - cx) * sc + cx; positions[i + 1] = (positions[i + 1] - cy) * sc + cy; positions[i + 2] = (positions[i + 2] - cz) * sc + cz; }
      warnings.push('Auto-scaled (' + ratio.toFixed(1) + 'x)');
    }
  }

  // Orientation check
  var nb = computeBB(positions);
  if ((nb.maxY - nb.minY) < (nb.maxX - nb.minX)) { for (var i = 0; i < positions.length; i += 3) { var tmp = positions[i + 1]; positions[i + 1] = positions[i + 2]; positions[i + 2] = -tmp; } warnings.push('Rotated to Y-up'); }

  // Build constraints
  var pc = vertexCount;
  var stretchC = [], shearC = [], bendC = [], bendDistC = [];
  var edgeMap = {};
  for (var t = 0; t < indices.length; t += 3) { var a = indices[t], b = indices[t + 1], c = indices[t + 2]; addEdge(edgeMap, a, b); addEdge(edgeMap, b, c); addEdge(edgeMap, c, a); }
  for (var key in edgeMap) { var e = edgeMap[key]; stretchC.push({ a: e.a, b: e.b, rest: eDist(positions, e.a, e.b), compliance: 0.001, kind: 'stretch' }); }

  var diagSet = {};
  for (var t = 0; t < indices.length; t += 3) {
    var a = indices[t], b = indices[t + 1], c = indices[t + 2];
    var k1 = Math.min(a, c) + '_' + Math.max(a, c), k2 = Math.min(b, c) + '_' + Math.max(b, c);
    if (!edgeMap[k1] && !diagSet[k1]) { diagSet[k1] = 1; shearC.push({ a: a, b: c, rest: eDist(positions, a, c), compliance: 0.01, kind: 'shear' }); }
    if (!edgeMap[k2] && !diagSet[k2]) { diagSet[k2] = 1; shearC.push({ a: b, b: c, rest: eDist(positions, b, c), compliance: 0.01, kind: 'shear' }); }
  }

  // Bend: simple dihedral for edge-adjacent triangle pairs
  var edgeToTris = {};
  for (var t = 0; t < indices.length; t += 3) {
    var tri = [indices[t], indices[t + 1], indices[t + 2]];
    for (var e = 0; e < 3; e++) { var a2 = tri[e], b2 = tri[(e + 1) % 3]; var k = Math.min(a2, b2) + '_' + Math.max(a2, b2); if (!edgeToTris[k]) edgeToTris[k] = []; edgeToTris[k].push({ a: a2, b: b2, tri: tri }); }
  }
  for (var k in edgeToTris) {
    var tris = edgeToTris[k]; if (tris.length !== 2) continue;
    var opp1 = tris[0].tri.find(function(v) { return v !== tris[0].a && v !== tris[0].b; });
    var opp2 = tris[1].tri.find(function(v) { return v !== tris[1].a && v !== tris[1].b; });
    if (opp1 === undefined || opp2 === undefined) continue;
    bendC.push({ a: opp1, b: tris[0].a, c: opp2, rest: eDist(positions, opp1, opp2) * 0.5, compliance: 0.1, kind: 'bend' });
    bendDistC.push({ a: opp1, b: opp2, rest: eDist(positions, opp1, opp2) * 0.5, compliance: 0.1, kind: 'bend' });
  }

  var prevPos = new Float32Array(positions);
  var vel = new Float32Array(pc * 3);
  var invMass = new Float32Array(pc).fill(1.0);

  // Auto-pin top 15%
  var sortedY = []; for (var i = 0; i < pc; i++) sortedY.push({ i: i, y: positions[i * 3 + 1] });
  sortedY.sort(function(a, b) { return b.y - a.y; });
  for (var i = 0; i < Math.max(1, Math.floor(pc * 0.15)); i++) invMass[sortedY[i].i] = 0;

  return {
    ok: true,
    mesh: { particleCount: pc, positions: positions, prevPositions: prevPos, velocities: vel, invMass: invMass, panelIds: ['garment'], particleFrictions: new Float32Array(pc).fill(1.0), panelUvs: new Float32Array(pc * 2), panelLocalPositions: new Float32Array(pc * 3), triangles: indices, stretchConstraints: stretchC, shearConstraints: shearC, bendDistanceConstraints: bendDistC, bendConstraints: bendC, seamConstraints: [], pinConstraints: [] },
    warnings: warnings
  };
}

function findLargestMesh(obj) { var largest = null, maxV = 0; obj.traverse(function(c) { if (c.isMesh && c.geometry) { var v = c.geometry.attributes.position.count; if (v > maxV) { maxV = v; largest = c; } } }); return largest; }
function computeBB(pos) { var minX = Infinity, minY = Infinity, minZ = Infinity, maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity; for (var i = 0; i < pos.length; i += 3) { if (pos[i] < minX) minX = pos[i]; if (pos[i] > maxX) maxX = pos[i]; if (pos[i + 1] < minY) minY = pos[i + 1]; if (pos[i + 1] > maxY) maxY = pos[i + 1]; if (pos[i + 2] < minZ) minZ = pos[i + 2]; if (pos[i + 2] > maxZ) maxZ = pos[i + 2]; } return { minX: minX, minY: minY, minZ: minZ, maxX: maxX, maxY: maxY, maxZ: maxZ }; }
function addEdge(map, a, b) { var k = Math.min(a, b) + '_' + Math.max(a, b); if (!map[k]) map[k] = { a: Math.min(a, b), b: Math.max(a, b) }; }
function eDist(pos, a, b) { var dx = pos[b * 3] - pos[a * 3], dy = pos[b * 3 + 1] - pos[a * 3 + 1], dz = pos[b * 3 + 2] - pos[a * 3 + 2]; return Math.sqrt(dx * dx + dy * dy + dz * dz); }

// ===== BODY COLLIDER =====

function BodyCollider(vertices, indices) {
  this.vertices = vertices;
  this.indices = indices;
  this.skinOffset = 0.02;
  this.thickness = 0.008;
  this.friction = 0.3;
  this.bounds = this._computeBounds();
  this.triangleNormals = this._computeNormals();
  this.bvh = buildTriangleBVH(vertices, indices);
  this.triangleVisitMarks = new Uint32Array(indices.length / 3);
  this.triangleVisitStamp = 0;
  // Spatial hash for fallback
  this.cellSize = 0.05;
  this._buildSpatialHash();
}

BodyCollider.prototype.refit = function() { refitTriangleBVH(this.bvh, this.vertices); this.bounds = this._computeBounds(); this.triangleNormals = this._computeNormals(); };

BodyCollider.prototype.buildSnapshot = function() {
  return {
    version: 1, proxies: [],
    meshColliders: [{
      kind: 'mesh', id: 'body', vertices: this.vertices, indices: this.indices,
      skin: this.skinOffset, thickness: this.thickness, friction: this.friction,
      bvh: this.bvh, triangleNormals: this.triangleNormals,
      cellSize: this.cellSize, cellKeys: this.cellKeys, cellStarts: this.cellStarts,
      cellCounts: this.cellCounts, cellTriangleIndices: this.cellTriangleIndices,
      cellIndexLookup: this.cellIndexLookup, triangleVisitMarks: this.triangleVisitMarks,
      triangleVisitStamp: this.triangleVisitStamp, bounds: this.bounds
    }]
  };
};

BodyCollider.prototype._computeBounds = function() {
  var minX = Infinity, minY = Infinity, minZ = Infinity, maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  for (var i = 0; i < this.vertices.length; i += 3) {
    var x = this.vertices[i], y = this.vertices[i + 1], z = this.vertices[i + 2];
    if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
  }
  return { minX: minX, minY: minY, minZ: minZ, maxX: maxX, maxY: maxY, maxZ: maxZ };
};

BodyCollider.prototype._computeNormals = function() {
  var tc = this.indices.length / 3, normals = new Float32Array(tc * 3);
  for (var t = 0; t < tc; t++) {
    var ia = this.indices[t * 3] * 3, ib = this.indices[t * 3 + 1] * 3, ic = this.indices[t * 3 + 2] * 3;
    var abx = this.vertices[ib] - this.vertices[ia], aby = this.vertices[ib + 1] - this.vertices[ia + 1], abz = this.vertices[ib + 2] - this.vertices[ia + 2];
    var acx = this.vertices[ic] - this.vertices[ia], acy = this.vertices[ic + 1] - this.vertices[ia + 1], acz = this.vertices[ic + 2] - this.vertices[ia + 2];
    var nx = aby * acz - abz * acy, ny = abz * acx - abx * acz, nz = abx * acy - aby * acx;
    var len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    normals[t * 3] = nx / len; normals[t * 3 + 1] = ny / len; normals[t * 3 + 2] = nz / len;
  }
  return normals;
};

BodyCollider.prototype._buildSpatialHash = function() {
  var tc = this.indices.length / 3, invCellSize = 1 / this.cellSize;
  this.triangleCentroids = new Float32Array(tc * 3);
  this.triangleRadii = new Float32Array(tc);
  var cellMap = {}, pairs = [];
  for (var t = 0; t < tc; t++) {
    var ia = this.indices[t * 3] * 3, ib = this.indices[t * 3 + 1] * 3, ic = this.indices[t * 3 + 2] * 3;
    var cx = (this.vertices[ia] + this.vertices[ib] + this.vertices[ic]) / 3;
    var cy = (this.vertices[ia + 1] + this.vertices[ib + 1] + this.vertices[ic + 1]) / 3;
    var cz = (this.vertices[ia + 2] + this.vertices[ib + 2] + this.vertices[ic + 2]) / 3;
    this.triangleCentroids[t * 3] = cx; this.triangleCentroids[t * 3 + 1] = cy; this.triangleCentroids[t * 3 + 2] = cz;
    var maxR = 0;
    for (var v of [ia, ib, ic]) { var dx = this.vertices[v] - cx, dy = this.vertices[v + 1] - cy, dz = this.vertices[v + 2] - cz; var r = Math.sqrt(dx * dx + dy * dy + dz * dz); if (r > maxR) maxR = r; }
    this.triangleRadii[t] = maxR;
    var minCX = Math.floor(Math.min(this.vertices[ia], this.vertices[ib], this.vertices[ic]) * invCellSize);
    var minCY = Math.floor(Math.min(this.vertices[ia + 1], this.vertices[ib + 1], this.vertices[ic + 1]) * invCellSize);
    var minCZ = Math.floor(Math.min(this.vertices[ia + 2], this.vertices[ib + 2], this.vertices[ic + 2]) * invCellSize);
    var maxCX = Math.floor(Math.max(this.vertices[ia], this.vertices[ib], this.vertices[ic]) * invCellSize);
    var maxCY = Math.floor(Math.max(this.vertices[ia + 1], this.vertices[ib + 1], this.vertices[ic + 1]) * invCellSize);
    var maxCZ = Math.floor(Math.max(this.vertices[ia + 2], this.vertices[ib + 2], this.vertices[ic + 2]) * invCellSize);
    for (var x = minCX; x <= maxCX; x++) for (var y = minCY; y <= maxCY; y++) for (var z = minCZ; z <= maxCZ; z++) {
      var key = hashCell(x, y, z); if (!cellMap[key]) cellMap[key] = [];
      cellMap[key].push(t); pairs.push({ key: key, tri: t });
    }
  }
  this.cellIndexLookup = cellMap;
  var keys = Object.keys(cellMap), totalTris = 0;
  this.cellKeys = new Int32Array(keys.length); this.cellStarts = new Uint32Array(keys.length); this.cellCounts = new Uint32Array(keys.length);
  for (var i = 0; i < keys.length; i++) { var k = parseInt(keys[i]); this.cellKeys[i] = k; this.cellStarts[i] = i === 0 ? 0 : this.cellStarts[i - 1] + this.cellCounts[i - 1]; this.cellCounts[i] = cellMap[k].length; totalTris += cellMap[k].length; }
  this.cellTriangleIndices = new Uint32Array(totalTris);
  var pos = 0; for (var i = 0; i < keys.length; i++) { var tris = cellMap[parseInt(keys[i])]; for (var j = 0; j < tris.length; j++) this.cellTriangleIndices[pos++] = tris[j]; }
};

// ===== BUILD CLOTH CONSTRAINTS FROM ALIGNED POSITIONS =====

function buildClothConstraints(positions, indices, vertexCount) {
  // Build constraint graph from triangle mesh topology
  var stretchC = [], shearC = [], bendC = [], bendDistC = [];

  // Extract unique edges
  var edgeMap = {};
  for (var t = 0; t < indices.length; t += 3) {
    var a = indices[t], b = indices[t + 1], c = indices[t + 2];
    addEdge(edgeMap, a, b); addEdge(edgeMap, b, c); addEdge(edgeMap, c, a);
  }

  // Stretch constraints (edges)
  for (var key in edgeMap) {
    var e = edgeMap[key];
    stretchC.push({ a: e.a, b: e.b, rest: eDist(positions, e.a, e.b), compliance: 0.001, kind: 'stretch' });
  }

  // Shear constraints (diagonals)
  var diagSet = {};
  for (var t = 0; t < indices.length; t += 3) {
    var a = indices[t], b = indices[t + 1], c = indices[t + 2];
    var k1 = Math.min(a, c) + '_' + Math.max(a, c);
    var k2 = Math.min(b, c) + '_' + Math.max(b, c);
    if (!edgeMap[k1] && !diagSet[k1]) { diagSet[k1] = 1; shearC.push({ a: a, b: c, rest: eDist(positions, a, c), compliance: 0.01, kind: 'shear' }); }
    if (!edgeMap[k2] && !diagSet[k2]) { diagSet[k2] = 1; shearC.push({ a: b, b: c, rest: eDist(positions, b, c), compliance: 0.01, kind: 'shear' }); }
  }

  // Bend constraints
  var edgeToTris = {};
  for (var t = 0; t < indices.length; t += 3) {
    var tri = [indices[t], indices[t + 1], indices[t + 2]];
    for (var e = 0; e < 3; e++) {
      var a2 = tri[e], b2 = tri[(e + 1) % 3];
      var k = Math.min(a2, b2) + '_' + Math.max(a2, b2);
      if (!edgeToTris[k]) edgeToTris[k] = [];
      edgeToTris[k].push({ a: a2, b: b2, tri: tri });
    }
  }
  for (var k in edgeToTris) {
    var tris = edgeToTris[k]; if (tris.length !== 2) continue;
    var opp1 = -1, opp2 = -1;
    for (var j = 0; j < 3; j++) { if (tris[0].tri[j] !== tris[0].a && tris[0].tri[j] !== tris[0].b) opp1 = tris[0].tri[j]; }
    for (var j = 0; j < 3; j++) { if (tris[1].tri[j] !== tris[1].a && tris[1].tri[j] !== tris[1].b) opp2 = tris[1].tri[j]; }
    if (opp1 < 0 || opp2 < 0) continue;
    bendC.push({ a: opp1, b: tris[0].a, c: opp2, rest: eDist(positions, opp1, opp2) * 0.5, compliance: 0.1, kind: 'bend' });
    bendDistC.push({ a: opp1, b: opp2, rest: eDist(positions, opp1, opp2) * 0.5, compliance: 0.1, kind: 'bend' });
  }

  // Init particle state
  var prevPos = new Float32Array(positions);
  var vel = new Float32Array(vertexCount * 3);
  var invMass = new Float32Array(vertexCount).fill(1.0);

  // Auto-pin: top 10% by Y (shoulders/collar for a jacket)
  var sortedY = [];
  for (var i = 0; i < vertexCount; i++) sortedY.push({ i: i, y: positions[i * 3 + 1] });
  sortedY.sort(function(a, b) { return b.y - a.y; });
  for (var i = 0; i < Math.max(1, Math.floor(vertexCount * 0.10)); i++) invMass[sortedY[i].i] = 0;

  return {
    particleCount: vertexCount,
    positions: positions,
    prevPositions: prevPos,
    velocities: vel,
    invMass: invMass,
    panelIds: ['garment'],
    particleFrictions: new Float32Array(vertexCount).fill(1.0),
    panelUvs: new Float32Array(vertexCount * 2),
    panelLocalPositions: new Float32Array(vertexCount * 3),
    triangles: indices,
    stretchConstraints: stretchC,
    shearConstraints: shearC,
    bendDistanceConstraints: bendDistC,
    bendConstraints: bendC,
    seamConstraints: [],
    pinConstraints: []
  };
}

// ===== EXPORT =====
XPBD.ClothSolver = ClothSolver;
XPBD.BodyCollider = BodyCollider;
XPBD.validateAndBuildClothMesh = validateAndBuildClothMesh;
XPBD.buildClothConstraints = buildClothConstraints;
XPBD.buildTriangleBVH = buildTriangleBVH;
XPBD.refitTriangleBVH = refitTriangleBVH;

window.XPBD = XPBD;

})();
