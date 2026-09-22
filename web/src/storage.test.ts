import assert from "node:assert/strict";
import { mkdtemp, readdir, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { SecretJsonFileStore, sha256, WebSessionStore } from "./storage.js";

test("secret store persists atomically under hashed names and restrictive modes", async () => {
  const root = await mkdtemp(join(tmpdir(), "phlogiston-secret-"));
  const store = new SecretJsonFileStore<{ opaque: string }>(root);
  await store.set("plaintext-key", { opaque: "synthetic" });
  assert.deepEqual(await readdir(root), [sha256("plaintext-key")]);
  assert.equal((await stat(root)).mode & 0o777, 0o700);
  assert.equal((await stat(join(root, sha256("plaintext-key")))).mode & 0o777, 0o600);
  assert.deepEqual(await store.get("plaintext-key"), { opaque: "synthetic" });
});

test("web session persists, expires, and revokes without storing cookie plaintext", async () => {
  const root = await mkdtemp(join(tmpdir(), "phlogiston-web-session-"));
  const first = new WebSessionStore(root);
  const issued = await first.issue("did:plc:aaaaaaaaaaaaaaaaaaaaaaaa", new Date("2026-09-22T12:00:00Z"));
  assert.deepEqual(await readdir(root), [sha256(sha256(issued.token))]);
  const second = new WebSessionStore(root);
  assert.equal((await second.resolve(issued.token, new Date("2026-09-22T12:01:00Z")))?.did, "did:plc:aaaaaaaaaaaaaaaaaaaaaaaa");
  assert.equal(await second.resolve(issued.token, new Date("2026-09-22T20:00:01Z")), null);
  assert.deepEqual(await readdir(root), []);

  const active = await second.issue("did:plc:bbbbbbbbbbbbbbbbbbbbbbbb", new Date("2026-09-22T12:00:00Z"));
  await second.revoke(active.token);
  assert.equal(await second.resolve(active.token, new Date("2026-09-22T12:01:00Z")), null);
});
