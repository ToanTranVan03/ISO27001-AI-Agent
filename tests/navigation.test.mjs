import test from 'node:test';
import assert from 'node:assert/strict';
import {findPath, isWalkable} from '../backend/static/navigation.mjs';

const bounds = {minX: -8, maxX: 8, minZ: -9, maxZ: 9};
const desks = [{minX: -2, maxX: 2, minZ: -1, maxZ: 1}];
test('route goes around a desk and remains inside the room', () => {
  const path = findPath({x: 0, z: 4}, {x: 0, z: -4}, bounds, desks);
  assert.ok(path.length > 0);
  assert.ok(path.every(point => isWalkable(point, bounds, desks)));
  assert.ok(path.some(point => Math.abs(point.x) > 2));
  assert.deepEqual(path.at(-1), {x: 0, z: -4});
});
test('cannot move onto desks or outside the room', () => {
  assert.equal(isWalkable({x: 0, z: 0}, bounds, desks), false);
  assert.deepEqual(findPath({x: 0, z: 4}, {x: 0, z: 0}, bounds, desks), []);
  assert.deepEqual(findPath({x: 0, z: 4}, {x: 20, z: 4}, bounds, desks), []);
});
test('a sealed route is rejected', () => {
  assert.deepEqual(findPath({x: 0, z: 4}, {x: 0, z: -4}, bounds, [{minX: -8, maxX: 8, minZ: -1, maxZ: 1}]), []);
});
