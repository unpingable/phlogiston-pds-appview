import assert from "node:assert/strict";
import { mkdtemp } from "node:fs/promises";
import type { IncomingMessage, ServerResponse } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Readable } from "node:stream";
import test from "node:test";
import type { OAuthSession } from "@atproto/oauth-client-node";
import type { AppConfig } from "./config.js";
import type { MembershipView } from "./projection.js";
import { createHandler, type OAuthFacade } from "./server.js";
import { WebSessionStore } from "./storage.js";

const DID = "did:plc:aaaaaaaaaaaaaaaaaaaaaaaa";
const COMMUNITY_URL = "https://community.test";

class OAuthFake implements OAuthFacade {
  public unavailable = false;
  public signOuts = 0;
  public async authorize(handle: string): Promise<URL> {
    if (this.unavailable) throw new Error("PDS unavailable");
    return new URL(`https://pds.invalid/authorize?login_hint=${encodeURIComponent(handle)}`);
  }
  public async callback(): Promise<{ session: OAuthSession }> { return { session: this.session() }; }
  public async restore(did: string): Promise<OAuthSession> {
    if (this.unavailable || did !== DID) throw new Error("session revoked");
    return this.session();
  }
  private session(): OAuthSession {
    return { did: DID, signOut: async () => { this.signOuts += 1; } } as unknown as OAuthSession;
  }
}

class RequestFixture extends Readable {
  public readonly method: string;
  public readonly url: string;
  public readonly headers: Record<string, string>;
  public constructor(method: string, path: string, body: string, cookie?: string) {
    super();
    this.method = method;
    this.url = path;
    this.headers = {
      ...(method === "POST" ? { origin: "http://127.0.0.1:8092", "content-type": "application/x-www-form-urlencoded", "content-length": String(Buffer.byteLength(body)) } : {}),
      ...(cookie ? { cookie } : {}),
    };
    this.push(body || null);
    if (body) this.push(null);
  }
}

class ResponseFixture {
  public statusCode = 200;
  public readonly headers = new Map<string, string>();
  public body = "";
  public setHeader(name: string, value: string | number | readonly string[]): this { this.headers.set(name.toLowerCase(), String(value)); return this; }
  public end(value?: string | Uint8Array): this { this.body = value === undefined ? "" : Buffer.from(value).toString(); return this; }
}

async function fixture(membership: MembershipView, communityUrl: string | null = null) {
  const root = await mkdtemp(join(tmpdir(), "phlogiston-web-test-"));
  const sessions = new WebSessionStore(join(root, "sessions"));
  const oauth = new OAuthFake();
  const config: AppConfig = { publicUrl: "http://127.0.0.1:8092", runtimeDirectory: root, projectionOrigin: "http://127.0.0.1:9", communityDid: "did:plc:communitycommunitycomm", communityUrl, port: 8092 };
  const handler = createHandler({ config, oauth, sessions, projection: {
    membership: async () => membership,
    discussions: async () => ({ generation: "g1", discussions: [{ authorDid: DID, text: "Synthetic discussion", status: "visible" }] }),
  }, now: () => new Date("2026-09-22T12:00:00Z") });
  return { sessions, oauth, invoke: async (method: string, path: string, fields: Record<string, string> = {}, cookie?: string) => {
    const body = method === "POST" ? new URLSearchParams(fields).toString() : "";
    const request = new RequestFixture(method, path, body, cookie);
    const response = new ResponseFixture();
    await handler(request as unknown as IncomingMessage, response as unknown as ServerResponse);
    return response;
  } };
}

test("public community route renders the bounded read-only projection", async () => {
  const app = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" });
  const result = await app.invoke("GET", "/community/");
  assert.equal(result.statusCode, 200);
  assert.match(result.body, /<p>Synthetic discussion<\/p><p>Posted by <code>did:plc:a+<\/code><\/p><p>In the community<\/p>/);
  assert.match(result.body, /read-only mirror/);
  assert.doesNotMatch(result.body, /<h2>/);
  assert.doesNotMatch(result.body, /visible/);
  assert.match(result.body, /<details><summary>Technical details<\/summary><p>Projection generation: <code>g1<\/code>/);
  assert.doesNotMatch(result.body, /Go to the community/);
});

test("community link appears only when the community URL is configured", async () => {
  const absent = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" });
  const present = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" }, COMMUNITY_URL);
  for (const path of ["/", "/community/"]) {
    assert.doesNotMatch((await absent.invoke("GET", path)).body, /Go to the community|community\.test/);
    assert.match((await present.invoke("GET", path)).body, /<a href="https:\/\/community\.test">Go to the community<\/a>/);
  }
  const home = (await present.invoke("GET", "/")).body;
  assert(home.indexOf("Go to the community") < home.indexOf("<form"), "community link precedes sign-in form");
  assert.match(home, /not the place to post/);
  assert.match(home, /Signing in here only confirms your account/);
  assert.doesNotMatch(home, /member/i);
  for (const app of [absent, present]) {
    const issued = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
    const me = (await app.invoke("GET", "/me", {}, `phlogiston_session=${issued.token}`)).body;
    assert.equal(/Go to the community/.test(me), app === present);
  }
});

test("security headers are unchanged on every page", async () => {
  const app = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" }, COMMUNITY_URL);
  const issued = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  for (const path of ["/", "/community/", "/me"]) {
    const result = await app.invoke("GET", path, {}, `phlogiston_session=${issued.token}`);
    assert.equal(result.statusCode, 200);
    assert.equal(result.headers.get("content-security-policy"), "default-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");
    assert.equal(result.headers.get("referrer-policy"), "no-referrer");
    assert.equal(result.headers.get("x-content-type-options"), "nosniff");
    assert.equal(result.headers.get("cache-control"), "no-store");
  }
});

test("no participation routes exist and POST routes are unchanged", async () => {
  const app = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" }, COMMUNITY_URL);
  const issued = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  for (const path of ["/", "/community/", "/me"]) {
    const body = (await app.invoke("GET", path, {}, `phlogiston_session=${issued.token}`)).body;
    const actions = [...body.matchAll(/<form method="post" action="([^"]+)"/g)].map((match) => match[1]);
    assert(actions.every((action) => ["/oauth/login", "/session/logout", "/session/disconnect"].includes(action!)), `${path}: ${actions.join(",")}`);
  }
  for (const path of ["/submit", "/reply", "/moderate", "/community/"]) {
    const result = await app.invoke("POST", path, { csrf: issued.csrf }, `phlogiston_session=${issued.token}`);
    assert.equal(result.statusCode, 404);
  }
});

test("PDS unavailability during enrollment is classified without a local session", async () => {
  const app = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" });
  app.oauth.unavailable = true;
  const result = await app.invoke("POST", "/oauth/login", { handle: "user.test" });
  assert.equal(result.statusCode, 503);
  assert.equal(result.headers.get("set-cookie"), undefined);
});

test("OAuth callback creates a persistent Phlogiston session but not membership", async () => {
  const app = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" });
  const callback = await app.invoke("GET", "/oauth/callback?code=synthetic");
  assert.equal(callback.statusCode, 303);
  const cookie = callback.headers.get("set-cookie")?.split(";", 1)[0];
  assert(cookie);
  const page = await app.invoke("GET", "/me", {}, cookie);
  assert.equal(page.statusCode, 200);
  assert.match(page.body, /PDS identity/);
  assert.doesNotMatch(page.body, /member/i);
  assert.doesNotMatch(page.body, /Community standing/);
  assert.match(page.body, /<details><summary>Technical details<\/summary><dl><dt>Community projection<\/dt><dd>fresh \(no_authority_record\)/);
  assert.match(page.body, /action="\/session\/logout"/);
  assert.match(page.body, /action="\/session\/disconnect"/);
});

test("revoked OAuth invalidates the otherwise active web session", async () => {
  const app = await fixture({ state: "active", projection: "fresh", reason: "authority_add_projected", reference: "at://did:plc:community/member/1" });
  const issued = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  app.oauth.unavailable = true;
  const result = await app.invoke("GET", "/me", {}, `phlogiston_session=${issued.token}`);
  assert.equal(result.statusCode, 401);
  assert.match(result.headers.get("set-cookie") ?? "", /Max-Age=0/);
  assert.equal(await app.sessions.resolve(issued.token, new Date("2026-09-22T12:00:01Z")), null);
});

test("stale projection remains indeterminate despite valid authentication", async () => {
  const app = await fixture({ state: "indeterminate", projection: "stale", reason: "projection_not_fresh" });
  const issued = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  const result = await app.invoke("GET", "/me", {}, `phlogiston_session=${issued.token}`);
  assert.doesNotMatch(result.body, /Community standing|member/i);
  assert.match(result.body, /Community projection<\/dt><dd>stale \(projection_not_fresh\)/);
});

test("an authority record is shown as plain community standing with a technical reference", async () => {
  const active = await fixture({ state: "active", projection: "fresh", reason: "authority_add_projected", reference: "at://did:plc:community/member/1" });
  let issued = await active.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  let body = (await active.invoke("GET", "/me", {}, `phlogiston_session=${issued.token}`)).body;
  assert.match(body, /<dt>Community standing<\/dt><dd>Added to the community<\/dd>/);
  assert.match(body, /<details><summary>Technical details<\/summary><dl><dt>Authority record<\/dt><dd><code>at:\/\/did:plc:community\/member\/1<\/code>/);
  assert.doesNotMatch(body.slice(0, body.indexOf("<details>")), /at:\/\//);

  const removed = await fixture({ state: "removed", projection: "fresh", reason: "authority_remove_projected", reference: "at://did:plc:community/member/2" });
  issued = await removed.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  body = (await removed.invoke("GET", "/me", {}, `phlogiston_session=${issued.token}`)).body;
  assert.match(body, /<dt>Community standing<\/dt><dd>Removed from the community<\/dd>/);
});

test("logout is local while disconnect revokes provider authorization", async () => {
  const app = await fixture({ state: "not-member", projection: "fresh", reason: "no_authority_record" });
  const local = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  let result = await app.invoke("POST", "/session/logout", { csrf: local.csrf }, `phlogiston_session=${local.token}`);
  assert.equal(result.statusCode, 303);
  assert.equal(app.oauth.signOuts, 0);

  const provider = await app.sessions.issue(DID, new Date("2026-09-22T12:00:00Z"));
  result = await app.invoke("POST", "/session/disconnect", { csrf: provider.csrf }, `phlogiston_session=${provider.token}`);
  assert.equal(result.statusCode, 200);
  assert.equal(app.oauth.signOuts, 1);
});
