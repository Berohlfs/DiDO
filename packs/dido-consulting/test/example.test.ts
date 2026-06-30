// Presence stub for the doctor `unit_tests_present` badge. The real
// verification for this pack is the gbrain doctor sweep plus a grounded,
// cited skill answer against the seed (authoring posture, see README).
import { expect, test } from "bun:test";

test("dido-consulting pack manifest lists three skills", () => {
  const manifest = require("../skillpack.json");
  expect(manifest.skills.length).toBe(3);
});
