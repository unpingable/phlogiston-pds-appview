import { isIP } from "node:net";
import { resolve } from "node:path";

export interface AppConfig {
  publicUrl: string;
  runtimeDirectory: string;
  projectionOrigin: string;
  communityDid: string | null;
  port: number;
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): AppConfig {
  return {
    publicUrl: exactOrigin(required(env.PHLOGISTON_PUBLIC_URL, "PHLOGISTON_PUBLIC_URL")),
    runtimeDirectory: resolve(required(env.PHLOGISTON_RUNTIME_DIR, "PHLOGISTON_RUNTIME_DIR")),
    projectionOrigin: exactOrigin(required(env.PHLOGISTON_PROJECTION_ORIGIN, "PHLOGISTON_PROJECTION_ORIGIN")),
    communityDid: optionalDid(env.PHLOGISTON_COMMUNITY_DID),
    port: boundedPort(env.PORT ?? "8092"),
  };
}

export function loopback(origin: string): boolean {
  const host = new URL(origin).hostname.replace(/^\[|\]$/g, "");
  return host === "localhost" || host === "::1" || (isIP(host) === 4 && host.startsWith("127."));
}

function exactOrigin(value: string): string {
  const parsed = new URL(value);
  if ((parsed.protocol !== "https:" && !loopback(parsed.origin)) || parsed.username || parsed.password) {
    throw new Error("origin must use HTTPS outside loopback");
  }
  if (parsed.pathname !== "/" || parsed.search || parsed.hash) throw new Error("origin must be a bare origin");
  return parsed.origin;
}

function did(value: string): string {
  if (!/^did:(?:plc|web):[^\s/]+$/.test(value)) throw new Error("PHLOGISTON_COMMUNITY_DID must be a DID");
  return value;
}

function optionalDid(value: string | undefined): string | null {
  const normalized = value?.trim();
  return normalized ? did(normalized) : null;
}

function boundedPort(value: string): number {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < 1 || parsed > 65_535) throw new Error("PORT is invalid");
  return parsed;
}

function required(value: string | undefined, name: string): string {
  const normalized = value?.trim();
  if (!normalized) throw new Error(`${name} is required`);
  return normalized;
}
