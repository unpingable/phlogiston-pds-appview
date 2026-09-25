// Timed OAuth continuity probe, started by verify-oauth-continuity.sh through
// a systemd transient timer as the community-web user. It restores the stored
// OAuth session of one DID with community-live's own client construction,
// which refreshes an expired access token with the stored refresh token, and
// makes one non-mutating XRPC read with it. Tokens are never printed; only
// expiry timestamps and the read's HTTP status are recorded.
//
// usage: tsx oauth-continuity.ts <did> <result path>   (env: community-web.env; COMMUNITY_LIVE_ROOT optional)
import { writeFileSync } from "node:fs";
import { join } from "node:path";

const [did, resultPath] = process.argv.slice(2);
if (!did || !resultPath) throw new Error("usage: oauth-continuity.ts <did> <result path>");
const root = process.env.COMMUNITY_LIVE_ROOT ?? "/opt/atproto-community/apps/community-live";
const scheduledAt = process.env.PHLOGISTON_VERIFY_SCHEDULED_AT ?? "";

const result: Record<string, unknown> = {
  schema: "phlogiston.production-verification.v1",
  check: "oauth-continuity",
  status: "fail",
  fields: { did, scheduled_at: scheduledAt, ran_at: new Date().toISOString() },
};
const fields = result.fields as Record<string, unknown>;
try {
  const { loadConfig } = await import(join(root, "src/config.ts"));
  const { createOAuthClient } = await import(join(root, "src/oauth.ts"));
  const client = createOAuthClient(loadConfig());
  const session = await client.restore(did, "auto");
  const before = await session.getTokenSet("auto");
  fields.token_expires_at_after_restore = before.expires_at ?? null;
  const response = await session.fetchHandler("/xrpc/com.atproto.server.getSession", { method: "GET" });
  fields.read_status = response.status;
  const body = (await response.json()) as { did?: string };
  fields.read_did_matches = body.did === did;
  const after = await session.getTokenSet("auto");
  fields.token_expires_at_after_read = after.expires_at ?? null;
  result.status = response.status === 200 && body.did === did ? "pass" : "fail";
} catch (error) {
  fields.error = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
}
writeFileSync(resultPath, JSON.stringify(result, null, 2) + "\n", { flag: "wx", mode: 0o600 });
process.exit(result.status === "pass" ? 0 : 1);
