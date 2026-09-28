// Timed OAuth continuity probe. Token values are never serialized.
import { closeSync, constants, fsyncSync, openSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join } from "node:path";
import { assessContinuity, assessPrerequisites } from "./oauth-continuity-policy.mjs";

function writeJsonExclusive(path: string, value: object): void {
  const fd = openSync(path, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL, 0o600);
  try { writeFileSync(fd, JSON.stringify(value, null, 2) + "\n", { encoding: "utf8" }); fsyncSync(fd); } finally { closeSync(fd); }
  const directory = openSync(dirname(path), constants.O_RDONLY | constants.O_DIRECTORY);
  try { fsyncSync(directory); } finally { closeSync(directory); }
}

// The selected @atproto/oauth-client SDK declares TokenSet.expires_at?: string.
function tokenExpiry(tokenSet: { expires_at?: unknown }, where: string): string {
  const value = tokenSet.expires_at;
  if (typeof value !== "string" || !value || !Number.isFinite(Date.parse(value))) throw new Error(`${where} token set has no ISO expires_at string`);
  return value;
}

function exactBaseline(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error("baseline is not an object");
  const raw = value as Record<string, unknown>;
  const expected = ["check", "did", "minimum_elapsed_seconds", "observed_at", "scheduled_at", "schema", "token_expires_at"];
  if (JSON.stringify(Object.keys(raw).sort()) !== JSON.stringify(expected)) throw new Error("baseline fields are not exact");
  if (raw.schema !== "phlogiston.oauth-continuity-baseline.v1" || raw.check !== "oauth-continuity") throw new Error("baseline schema/check is invalid");
  if (typeof raw.did !== "string" || !raw.did || typeof raw.scheduled_at !== "string" || !raw.scheduled_at || typeof raw.observed_at !== "string" || !raw.observed_at || typeof raw.minimum_elapsed_seconds !== "number" || !Number.isInteger(raw.minimum_elapsed_seconds) || typeof raw.token_expires_at !== "string" || !raw.token_expires_at || !Number.isFinite(Date.parse(raw.token_expires_at))) throw new Error("baseline types are invalid");
  return raw;
}

const [mode, did, outputPath, baselinePath] = process.argv.slice(2);
if (!mode || !did || !outputPath || !["baseline", "verify"].includes(mode)) throw new Error("usage: oauth-continuity.ts baseline <did> <baseline-path> | verify <did> <result-path> <baseline-path>");
const root = process.env.COMMUNITY_LIVE_ROOT ?? "/opt/atproto-community/apps/community-live";
const scheduledAt = process.env.PHLOGISTON_VERIFY_SCHEDULED_AT ?? "";
const minimumText = process.env.PHLOGISTON_VERIFY_MIN_ELAPSED_SECONDS ?? "";
const expectedBaselineSha256 = process.env.PHLOGISTON_VERIFY_BASELINE_SHA256 ?? "";
if (!/^[0-9]+$/.test(minimumText)) throw new Error("minimum elapsed seconds is absent or invalid");
const minimumElapsedSeconds = Number(minimumText);
if (!Number.isSafeInteger(minimumElapsedSeconds) || minimumElapsedSeconds < 43200) throw new Error("minimum elapsed seconds must be a safe integer >=43200");
if (!scheduledAt || !Number.isFinite(Date.parse(scheduledAt))) throw new Error("scheduled instant is absent or invalid");

const { loadConfig } = await import(join(root, "src/config.ts"));
const { createOAuthClient } = await import(join(root, "src/oauth.ts"));
const client = createOAuthClient(loadConfig());

if (mode === "baseline") {
  if (baselinePath !== undefined) throw new Error("baseline mode has unexpected extra argument");
  const session = await client.restore(did, "auto");
  const tokenSet = await session.getTokenSet("auto");
  writeJsonExclusive(outputPath, { schema: "phlogiston.oauth-continuity-baseline.v1", check: "oauth-continuity", did, scheduled_at: scheduledAt, observed_at: new Date().toISOString(), minimum_elapsed_seconds: minimumElapsedSeconds, token_expires_at: tokenExpiry(tokenSet, "baseline") });
  process.exit(0);
}

if (!baselinePath) throw new Error("verify mode requires baseline path");
if (!/^[0-9a-f]{64}$/.test(expectedBaselineSha256)) throw new Error("verify mode requires an exact lowercase baseline SHA-256");
const result: Record<string, unknown> = { schema: "phlogiston.production-verification.v1", check: "oauth-continuity", status: "fail", fields: { did, scheduled_at: scheduledAt } };
const fields = result.fields as Record<string, unknown>;
try {
  const baselineBytes = readFileSync(baselinePath);
  const baselineSha256 = createHash("sha256").update(baselineBytes).digest("hex");
  if (baselineSha256 !== expectedBaselineSha256) throw new Error("baseline SHA-256 does not match the scheduled occurrence");
  const baseline = exactBaseline(JSON.parse(baselineBytes.toString("utf8")));
  if (baseline.did !== did || baseline.scheduled_at !== scheduledAt || baseline.minimum_elapsed_seconds !== minimumElapsedSeconds) throw new Error("baseline does not bind the scheduled DID/time/minimum");
  const preContactAt = new Date().toISOString();
  const prerequisite = assessPrerequisites({ scheduledAt, at: preContactAt, minimumElapsedSeconds, baselineObservedAt: baseline.observed_at, baselineTokenExpiresAt: baseline.token_expires_at });
  Object.assign(fields, { baseline_sha256: baselineSha256, baseline_observed_at: baseline.observed_at, baseline_token_expires_at: baseline.token_expires_at, pre_contact_at: preContactAt, actual_elapsed_seconds_before_contact: prerequisite.actualElapsedSeconds, elapsed_requirement_met_before_contact: prerequisite.elapsedRequirementMet, baseline_expires_before_probe: prerequisite.baselineExpiresBeforeProbe });
  if (!prerequisite.elapsedRequirementMet || !prerequisite.baselineExpiresBeforeProbe) throw new Error("elapsed/baseline prerequisites are not met before final session contact");
  const session = await client.restore(did, "auto");
  fields.token_expires_at_after_restore = tokenExpiry(await session.getTokenSet("auto"), "restored");
  const response = await session.fetchHandler("/xrpc/com.atproto.server.getSession", { method: "GET" });
  fields.read_status = response.status;
  const body = (await response.json()) as { did?: string };
  const readCompletedAt = new Date().toISOString();
  fields.read_completed_at = readCompletedAt;
  fields.read_did_matches = body.did === did;
  const finalExpiry = tokenExpiry(await session.getTokenSet("auto"), "final");
  fields.token_expires_at_after_read = finalExpiry;
  const policy = assessContinuity({ scheduledAt, ranAt: readCompletedAt, minimumElapsedSeconds, baselineObservedAt: baseline.observed_at, baselineTokenExpiresAt: baseline.token_expires_at, finalTokenExpiresAt: finalExpiry });
  Object.assign(fields, { actual_elapsed_seconds: policy.actualElapsedSeconds, minimum_elapsed_seconds: policy.minimumElapsedSeconds, elapsed_requirement_met: policy.elapsedRequirementMet, token_expiry_advanced: policy.tokenExpiryAdvanced, final_token_current_at_read: policy.finalTokenCurrentAtRead, refresh_provenance_met: policy.refreshProvenanceMet });
  result.status = policy.elapsedRequirementMet && policy.refreshProvenanceMet && response.status === 200 && body.did === did ? "pass" : "fail";
} catch (error) {
  fields.error = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
}
writeJsonExclusive(outputPath, result);
process.exit(result.status === "pass" ? 0 : 1);
