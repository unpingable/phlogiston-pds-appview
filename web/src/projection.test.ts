import assert from "node:assert/strict";
import test from "node:test";
import { HttpMembershipProjection } from "./projection.js";

function response(value: object, status = 200): Response {
  return new Response(JSON.stringify(value), { status, headers: { "content-type": "application/json" } });
}

test("fresh absence is not membership and authentication cannot invent it", async () => {
  const projection = new HttpMembershipProjection("https://projection.test", "did:plc:community", async () => response({ members: [], projection: { fresh: true } }));
  assert.deepEqual(await projection.membership("did:plc:user"), { state: "not-member", projection: "fresh", reason: "no_authority_record" });
});

test("stale projection never becomes a negative membership claim", async () => {
  const projection = new HttpMembershipProjection("https://projection.test", "did:plc:community", async () => response({ members: [], projection: { fresh: false } }));
  assert.deepEqual(await projection.membership("did:plc:user"), { state: "indeterminate", projection: "stale", reason: "projection_not_fresh" });
});

test("one unavailable dependency yields indeterminate state", async () => {
  const projection = new HttpMembershipProjection("https://projection.test", "did:plc:community", async () => { throw new Error("PDS unavailable"); });
  assert.deepEqual(await projection.membership("did:plc:user"), { state: "indeterminate", projection: "unavailable", reason: "projection_unavailable" });
});
