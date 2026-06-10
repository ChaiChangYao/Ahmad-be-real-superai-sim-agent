import assert from "node:assert/strict";
import test from "node:test";

import {
  convertPosition,
  convertQuaternion,
  GENESIS_UP_AXIS,
  RENDERER_UP_AXIS,
} from "./replay_transforms";

test("convertPosition maps origin identity for renderer-up passthrough", () => {
  const out = convertPosition([0, 0, 0], RENDERER_UP_AXIS);
  assert.deepEqual(out, [0, 0, 0]);
});

test("convertPosition maps Genesis Z-up to Three Y-up", () => {
  assert.deepEqual(convertPosition([1, 2, 3], GENESIS_UP_AXIS), [1, 3, -2]);
});

test("convertQuaternion applies fixed basis change for Genesis Z-up", () => {
  const identity = convertQuaternion([1, 0, 0, 0], GENESIS_UP_AXIS);
  assert.ok(identity);
  const [x, y, z, w] = identity!;
  assert.ok(Math.abs(w - Math.sqrt(0.5)) < 1e-6);
  assert.ok(Math.abs(x + Math.sqrt(0.5)) < 1e-6);
  assert.ok(Math.abs(y) < 1e-6);
  assert.ok(Math.abs(z) < 1e-6);
});

test("convertQuaternion passthrough for renderer-up", () => {
  const out = convertQuaternion([0.7, 0.1, 0.2, 0.3], RENDERER_UP_AXIS);
  assert.deepEqual(out, [0.1, 0.2, 0.3, 0.7]);
});
