import assert from "node:assert/strict";
import test from "node:test";
import { loadConfig } from "./config.js";

const BASE = { PHLOGISTON_PUBLIC_URL: "https://phlogiston.test", PHLOGISTON_RUNTIME_DIR: "/tmp/phlogiston", PHLOGISTON_PROJECTION_ORIGIN: "http://127.0.0.1:8093" };

test("community URL is optional and off when absent", () => {
  assert.equal(loadConfig({ ...BASE }).communityUrl, null);
  assert.equal(loadConfig({ ...BASE, PHLOGISTON_COMMUNITY_URL: "  " }).communityUrl, null);
});

test("community URL must be an absolute https URL", () => {
  assert.equal(loadConfig({ ...BASE, PHLOGISTON_COMMUNITY_URL: "https://community.test/" }).communityUrl, "https://community.test");
  assert.equal(loadConfig({ ...BASE, PHLOGISTON_COMMUNITY_URL: "https://community.test/zone/" }).communityUrl, "https://community.test/zone");
  for (const bad of ["community.test", "/relative", "http://community.test", "javascript:alert(1)", "https://user:pw@community.test", "https://community.test/?q=1", "https://community.test/#x"]) {
    assert.throws(() => loadConfig({ ...BASE, PHLOGISTON_COMMUNITY_URL: bad }), /PHLOGISTON_COMMUNITY_URL/, bad);
  }
});
