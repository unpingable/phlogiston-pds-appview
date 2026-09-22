import assert from "node:assert/strict";
import test from "node:test";
import { loadConfig, type AppConfig } from "./config.js";
import { clientMetadata, OAUTH_SCOPE } from "./oauth.js";

const config: AppConfig = {
  publicUrl: "https://phlogiston.invalid.test",
  runtimeDirectory: "/tmp/phlogiston-runtime",
  projectionOrigin: "https://projection.invalid.test",
  communityDid: "did:plc:aaaaaaaaaaaaaaaaaaaaaaaa",
  port: 8092,
};

test("hosted OAuth metadata is DPoP-bound and requests identity enrollment only", () => {
  const metadata = clientMetadata(config);
  assert.equal(OAUTH_SCOPE, "atproto");
  assert.equal(metadata.scope, "atproto");
  assert.equal(metadata.dpop_bound_access_tokens, true);
  assert.deepEqual(metadata.redirect_uris, ["https://phlogiston.invalid.test/oauth/callback"]);
  assert.doesNotMatch(metadata.scope ?? "", /repo:|rpc:|include:/);
});

test("loopback callback is an explicit isolated-qualification mode", () => {
  const metadata = clientMetadata({ ...config, publicUrl: "http://127.0.0.1:8092" });
  assert.deepEqual(metadata.redirect_uris, ["http://127.0.0.1:8092/oauth/callback"]);
});

test("inert configuration permits no community authority identity", () => {
  const inert = loadConfig({
    PHLOGISTON_PUBLIC_URL: "https://phlogiston.app",
    PHLOGISTON_RUNTIME_DIR: "/tmp/phlogiston",
    PHLOGISTON_PROJECTION_ORIGIN: "http://127.0.0.1:8093",
    PORT: "8092",
  });
  assert.equal(inert.communityDid, null);
});
