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

test("inert deployment has explicit unavailable community state", async () => {
  const projection = new HttpMembershipProjection("https://projection.test", null, async () => {
    throw new Error("network must not be called");
  });
  assert.deepEqual(await projection.membership("did:plc:user"), {
    state: "indeterminate",
    projection: "unavailable",
    reason: "community_not_configured",
  });
  await assert.rejects(projection.discussions(), /community_not_configured/);
});

test("discussion projection retains only the bounded public view", async () => {
  const projection = new HttpMembershipProjection("https://projection.test", "did:plc:community", async () => response({
    communityDid: "did:plc:community",
    discussions: [{ authorDid: "did:plc:author", status: "visible", post: { text: "Hello", extra: "not retained" }, authority: { private: true } }],
    cursor: null,
    snapshot: { generation: "g1", observerSequence: 7 },
  }));
  assert.deepEqual(await projection.discussions(), {
    generation: "g1",
    discussions: [{ authorDid: "did:plc:author", text: "Hello", status: "visible" }],
  });
});

test("malformed discussion projection refuses rather than inventing content", async () => {
  const projection = new HttpMembershipProjection("https://projection.test", "did:plc:community", async () => response({
    discussions: [{ authorDid: "did:plc:author", status: "visible", post: {} }],
    snapshot: { generation: "g1" },
  }));
  await assert.rejects(projection.discussions(), /projection_invalid/);
});
