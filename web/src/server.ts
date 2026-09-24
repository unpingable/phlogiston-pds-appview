import type { OAuthSession } from "@atproto/oauth-client-node";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { join } from "node:path";
import { loadConfig, type AppConfig } from "./config.js";
import { clientMetadata, createOAuthClient, OAUTH_SCOPE } from "./oauth.js";
import { HttpMembershipProjection, type DiscussionListing, type MembershipProjection, type MembershipView } from "./projection.js";
import { WebSessionStore, type WebSession } from "./storage.js";

const COOKIE = "phlogiston_session";
const MAX_FORM_BYTES = 32 * 1024;

export interface OAuthFacade {
  authorize(input: string, options: { scope: string }): Promise<URL>;
  callback(params: URLSearchParams): Promise<{ session: OAuthSession }>;
  restore(did: string): Promise<OAuthSession>;
}

export interface Dependencies {
  config: AppConfig;
  oauth: OAuthFacade;
  sessions: WebSessionStore;
  projection: MembershipProjection;
  now(): Date;
}

export function createHandler(deps: Dependencies) {
  return async (request: IncomingMessage, response: ServerResponse): Promise<void> => {
    try {
      await route(deps, request, response);
    } catch (error) {
      const code = error instanceof AppError ? error.code : "internal_failure";
      const status = code === "not_authenticated" ? 401 : code === "request_invalid" ? 400 : 503;
      html(response, status, page("Phlogiston unavailable", `<p>${escape(message(code))}</p><p><a href="/">Return</a></p>`));
    }
  };
}

async function route(deps: Dependencies, request: IncomingMessage, response: ServerResponse): Promise<void> {
  const method = request.method ?? "GET";
  const url = new URL(request.url ?? "/", deps.config.publicUrl);
  if (method === "GET" && url.pathname === "/healthz") return text(response, 200, "ok\n");
  if (method === "GET" && url.pathname === "/oauth-client-metadata.json") return json(response, 200, clientMetadata(deps.config));
  if (method === "GET" && url.pathname === "/community/") {
    const listing = await deps.projection.discussions();
    return html(response, 200, communityPage(listing, deps.config.communityUrl));
  }
  if (method === "POST") requireSameOrigin(request, deps.config.publicUrl);

  if (method === "POST" && url.pathname === "/oauth/login") {
    const form = await readForm(request);
    const target = await deps.oauth.authorize(required(form, "handle").replace(/^@/, ""), { scope: OAUTH_SCOPE });
    return redirect(response, target.toString());
  }
  if (method === "GET" && url.pathname === "/oauth/callback") {
    const { session } = await deps.oauth.callback(url.searchParams);
    const issued = await deps.sessions.issue(session.did, deps.now());
    response.setHeader("Set-Cookie", cookie(issued.token, deps.config.publicUrl));
    return redirect(response, "/me");
  }

  const token = cookieValue(request.headers.cookie, COOKIE);
  const session = await deps.sessions.resolve(token, deps.now());
  if (method === "GET" && url.pathname === "/") return html(response, 200, home(session, deps.config.communityUrl));
  if (method === "GET" && url.pathname === "/me") {
    const authenticated = await requireOAuth(deps, response, token, session);
    const membership = await deps.projection.membership(authenticated.did);
    return html(response, 200, accountPage(authenticated, membership, deps.config.communityUrl));
  }
  if (method === "POST" && url.pathname === "/session/logout") {
    const authenticated = requireSession(session);
    const form = await readForm(request);
    requireCsrf(authenticated, form);
    await deps.sessions.revoke(token);
    response.setHeader("Set-Cookie", expiredCookie(deps.config.publicUrl));
    return redirect(response, "/");
  }
  if (method === "POST" && url.pathname === "/session/disconnect") {
    const authenticated = requireSession(session);
    const form = await readForm(request);
    requireCsrf(authenticated, form);
    try {
      const oauth = await deps.oauth.restore(authenticated.did);
      await oauth.signOut();
    } finally {
      await deps.sessions.revoke(token);
      response.setHeader("Set-Cookie", expiredCookie(deps.config.publicUrl));
    }
    return html(response, 200, page("Disconnected", "<p>Phlogiston access was revoked. PDS data and community authority records were not changed.</p><p><a href=\"/\">Return</a></p>"));
  }
  return text(response, 404, "not found\n");
}

async function requireOAuth(deps: Dependencies, response: ServerResponse, token: string | undefined, session: WebSession | null): Promise<WebSession> {
  const current = requireSession(session);
  try {
    const restored = await deps.oauth.restore(current.did);
    if (restored.did !== current.did) throw new Error("restored DID mismatch");
    return current;
  } catch {
    await deps.sessions.revoke(token);
    response.setHeader("Set-Cookie", expiredCookie(deps.config.publicUrl));
    throw new AppError("not_authenticated");
  }
}

function communityLink(communityUrl: string | null): string {
  return communityUrl ? `<p><a href="${escape(communityUrl)}">Go to the community</a></p>` : "";
}

function home(session: WebSession | null, communityUrl: string | null): string {
  const purpose = "<p>This is the Phlogiston service's account and status page. It is not the place to post or reply.</p>";
  const body = session
    ? `${purpose}<p>Signed in to Phlogiston as <code>${escape(session.did)}</code>.</p>${communityLink(communityUrl)}<p><a href="/me">View your account and session</a></p>`
    : `${purpose}${communityLink(communityUrl)}<p>Sign in with your ATProto account. Signing in here only confirms your account; taking part happens at the community site.</p><form method="post" action="/oauth/login"><label>Handle <input name="handle" autocomplete="username" required></label><button>Continue with ATProto</button></form>`;
  return page("Phlogiston", body);
}

function accountPage(session: WebSession, membership: MembershipView, communityUrl: string | null): string {
  const standing = membership.state === "active"
    ? "Added to the community"
    : membership.state === "removed" ? "Removed from the community" : null;
  const standingRow = standing ? `<dt>Community standing</dt><dd>${standing}</dd>` : "";
  const reference = standing ? `<dt>Authority record</dt><dd><code>${escape(membership.reference ?? "reference unavailable")}</code></dd>` : "";
  const technical = `<details><summary>Technical details</summary><dl>${reference}<dt>Community projection</dt><dd>${escape(membership.projection)} (${escape(membership.reason)})</dd></dl></details>`;
  return page("Your Phlogiston session", `<dl><dt>PDS identity</dt><dd><code>${escape(session.did)}</code></dd><dt>Phlogiston session</dt><dd>authenticated until ${escape(session.expiresAt)}</dd>${standingRow}</dl>${technical}${communityLink(communityUrl)}<form method="post" action="/session/logout"><input type="hidden" name="csrf" value="${escape(session.csrf)}"><button>Sign out of Phlogiston</button></form><form method="post" action="/session/disconnect"><input type="hidden" name="csrf" value="${escape(session.csrf)}"><button>Disconnect ATProto access</button></form>`);
}

function communityState(status: string): string {
  if (status === "visible") return "In the community";
  if (status === "removed") return "Removed from the community";
  return "Community state not available";
}

function communityPage(listing: DiscussionListing, communityUrl: string | null): string {
  // The projected items carry no discussion key, so only the community home is linked.
  const intro = `<p>This is a read-only mirror of posts admitted to the community. Posting and replying happen at the community site.</p>${communityLink(communityUrl)}`;
  const items = listing.discussions.map((item) => `<li><article><p>${escape(item.text)}</p><p>Posted by <code>${escape(item.authorDid)}</code></p><p>${communityState(item.status)}</p></article></li>`).join("");
  const technical = `<details><summary>Technical details</summary><p>Projection generation: <code>${escape(listing.generation)}</code></p></details>`;
  return page("Phlogiston community", `${intro}<ol>${items || "<li>No admitted discussions are currently projected.</li>"}</ol>${technical}`);
}

async function readForm(request: IncomingMessage): Promise<URLSearchParams> {
  if (request.headers["content-type"]?.split(";", 1)[0] !== "application/x-www-form-urlencoded") throw new AppError("request_invalid");
  const declared = Number(request.headers["content-length"] ?? "0");
  if (!Number.isInteger(declared) || declared < 0 || declared > MAX_FORM_BYTES) throw new AppError("request_invalid");
  const chunks: Buffer[] = [];
  let length = 0;
  for await (const chunk of request) {
    const bytes = Buffer.from(chunk);
    length += bytes.length;
    if (length > MAX_FORM_BYTES) throw new AppError("request_invalid");
    chunks.push(bytes);
  }
  return new URLSearchParams(Buffer.concat(chunks).toString("utf8"));
}

function requireSameOrigin(request: IncomingMessage, expected: string): void {
  if (request.headers.origin !== expected) throw new AppError("request_invalid");
}
function requireSession(value: WebSession | null): WebSession {
  if (!value) throw new AppError("not_authenticated");
  return value;
}
function requireCsrf(session: WebSession, form: URLSearchParams): void {
  if (form.get("csrf") !== session.csrf) throw new AppError("request_invalid");
}
function required(form: URLSearchParams, name: string): string {
  const value = form.get(name)?.trim();
  if (!value || value.includes("\0")) throw new AppError("request_invalid");
  return value;
}

class AppError extends Error { public constructor(public readonly code: string) { super(code); } }
function message(code: string): string {
  return ({ not_authenticated: "Your Phlogiston session or ATProto authorization is missing, expired, or revoked.", request_invalid: "The request was refused without changing state.", internal_failure: "The requested dependency is unavailable. No community authority was widened." } as Record<string, string>)[code] ?? "The request was refused.";
}
function cookie(value: string, origin: string): string { return `${COOKIE}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=28800${new URL(origin).protocol === "https:" ? "; Secure" : ""}`; }
function expiredCookie(origin: string): string { return `${COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0${new URL(origin).protocol === "https:" ? "; Secure" : ""}`; }
function cookieValue(header: string | undefined, name: string): string | undefined { for (const part of header?.split(";") ?? []) { const [key, ...rest] = part.trim().split("="); if (key === name) return rest.join("="); } return undefined; }
function escape(value: string): string { return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;"); }
function page(title: string, body: string): string { return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><main><h1>${escape(title)}</h1>${body}</main></html>`; }
function security(response: ServerResponse): void { response.setHeader("Content-Security-Policy", "default-src 'none'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"); response.setHeader("Referrer-Policy", "no-referrer"); response.setHeader("X-Content-Type-Options", "nosniff"); response.setHeader("Cache-Control", "no-store"); }
function html(response: ServerResponse, status: number, value: string): void { security(response); response.statusCode = status; response.setHeader("Content-Type", "text/html; charset=utf-8"); response.end(value); }
function text(response: ServerResponse, status: number, value: string): void { security(response); response.statusCode = status; response.setHeader("Content-Type", "text/plain; charset=utf-8"); response.end(value); }
function json(response: ServerResponse, status: number, value: object): void { security(response); response.statusCode = status; response.setHeader("Content-Type", "application/json; charset=utf-8"); response.end(JSON.stringify(value)); }
function redirect(response: ServerResponse, location: string): void { security(response); response.statusCode = 303; response.setHeader("Location", location); response.end(); }

if (process.argv[1] && import.meta.filename === process.argv[1]) {
  const config = loadConfig();
  const oauth = createOAuthClient(config);
  const handler = createHandler({
    config,
    oauth,
    sessions: new WebSessionStore(join(config.runtimeDirectory, "web-sessions")),
    projection: new HttpMembershipProjection(config.projectionOrigin, config.communityDid),
    now: () => new Date(),
  });
  createServer((request, response) => void handler(request, response)).listen(config.port, "127.0.0.1", () => process.stdout.write(`phlogiston_web_ready port=${config.port}\n`));
}
