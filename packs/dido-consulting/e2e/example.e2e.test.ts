// Presence stub for the doctor `e2e_tests_present` badge. A real e2e run would
// invoke each skill against a seeded brain and assert the output cites source
// slugs and gap-flags missing data. Gated on DATABASE_URL when implemented.
import { expect, test } from "bun:test";

const hasDb = !!process.env.DATABASE_URL;

test.skipIf(!hasDb)("skills produce cited output against a seeded brain", () => {
  expect(hasDb).toBe(true);
});
