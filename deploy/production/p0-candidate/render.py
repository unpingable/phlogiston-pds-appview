#!/usr/bin/env python3
"""Render an inert, source-pinned P0 installation packet; never install/start."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SOURCE = "3bf402e4cf4974b5319d2f2ce0ffd76476b61b28"
COMMUNITY = "did:plc:yrdhg6whfezek67fchtrmqgu"
CONFIG = "/etc/atproto-community-p0"
UNITS = ("community-live.service", "communityd.service", "communitywatch-index.service", "communitywatch-web.service")


def absolute(value: str) -> str:
    if value == "/" or not re.fullmatch(r"/[A-Za-z0-9_./-]+", value) or ".." in Path(value).parts:
        raise ValueError("absolute path without systemd/shell interpolation required")
    return value.rstrip("/")


def render(source: Path, output: Path, runtime: str, moderator: str,
           uids: tuple[int, int, int] = (42011, 42013, 42014),
           commit: str = SOURCE) -> dict:
    runtime = absolute(runtime)
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("exact community commit required")
    if moderator != COMMUNITY:
        raise ValueError("accepted curator community/moderator DID required")
    if len(set(uids)) != 3 or any(uid < 1 for uid in uids):
        raise ValueError("three distinct non-root UIDs required")
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", f"{commit}^{{commit}}"], text=True).strip()
    if revision != commit:
        raise ValueError("community source revision does not match pinned successor")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    web_uid, daemon_uid, observer_uid = uids
    replacements = {
        "/opt/atproto-community": runtime,
        "User=community-web\n": "User=community-web-p0\n",
        "User=communityd\n": "User=communityd-p0\n",
        "User=communitywatch\n": "User=communitywatch-p0\n",
        "Group=communitywatch\n": "Group=communitywatch-p0\n",
        "Group=community-authority\n": "Group=community-authority-p0\n",
        "/etc/atproto-community": CONFIG,
        "/var/lib/community-web": "/var/lib/community-web-p0",
        "/var/lib/communityd": "/var/lib/communityd-p0",
        "/var/lib/communitywatch": "/var/lib/communitywatch-p0",
        "/run/community-authority": "/run/community-authority-p0",
        "RuntimeDirectory=community-authority\n": "RuntimeDirectory=community-authority-p0\n",
        "did:plc:replacewithtestmoderator": moderator,
        "did:plc:b53udqv47g2dayvpstzdefpq": COMMUNITY,
        "https://phellinus.us-west.host.bsky.network": "https://phlogiston.social",
        "web_peer_uid = 42001": f"web_peer_uid = {web_uid}",
        "allowed_uid = 42003": f"allowed_uid = {daemon_uid}",
        "PORT=3210": "PORT=3211",
        "http://127.0.0.1:8080": "http://127.0.0.1:8081",
        "port = 8080": "port = 8081",
    }
    names = (*UNITS, "community-web.env.example", "communityd.env.example", "communityd.toml", "communitywatch.toml", "p0-site-state", "p0-admission-state", "Caddyfile.fragment")
    source_hashes = {}
    for name in names:
        original = subprocess.check_output(["git", "-C", str(source), "show", f"{commit}:deploy/public-community-pcv0/p0/{name}"])
        source_hashes[name] = hashlib.sha256(original).hexdigest()
        text = original.decode()
        for before, after in replacements.items():
            text = text.replace(before, after)
        if name == "community-web.env.example":
            text = "\n".join(line for line in text.splitlines() if not line.startswith("COMMUNITY_SNAPSHOT_SECRET=")) + "\n"
        if name == "community-web.env.example":
            if "COMMUNITY_P0_HOSTED_PDS_ORIGIN=https://phlogiston.social\n" not in text or "COMMUNITY_P0_ALLOW_BLUESKY=true\n" not in text:
                raise ValueError("source template lacks accepted combined web profile")
        if name in {"communityd.toml", "communitywatch.toml"}:
            if 'p0_hosted_pds_origin = "https://phlogiston.social"\n' not in text or "p0_allow_bluesky = true\n" not in text:
                raise ValueError("source template lacks accepted combined Python profile")
        if name == "community-live.service":
            text = text.replace(f"EnvironmentFile={CONFIG}/community-web.env\n", f"EnvironmentFile={CONFIG}/community-web.env\nEnvironmentFile={CONFIG}/community-web-secret.env\n")
        if name == "communityd.service":
            text = text.replace(runtime + "/.venv/bin/", runtime + "/.venv-authority/bin/")
        if name.startswith("communitywatch-") and name.endswith(".service"):
            text = text.replace(runtime + "/.venv/bin/", runtime + "/.venv-observer/bin/")
        if name == "community-live.service":
            text = text.replace("Restart=on-failure\n", f"Environment=PATH={runtime}/toolchain/node24/bin:/usr/local/bin:/usr/bin:/bin\nRestart=on-failure\n")
        if name.endswith(".service"):
            text = text.replace("[Unit]\n", f"[Unit]\nConditionPathExists={Path(runtime).parent}/INSTALLED.json\nConditionPathExists=!{Path(runtime).parent}/INSTALLING\n")
            text = text.replace("Restart=on-failure\n", "Restart=on-failure\nMemoryMax=512M\nTasksMax=128\nTimeoutStopSec=30\n")
        if name == "Caddyfile.fragment":
            text = text.replace("127.0.0.1:3210", "127.0.0.1:3211")
        (output / name.replace(".env.example", ".env")).write_text(text)
    schema_paths = subprocess.check_output([
        "git", "-C", str(source), "ls-tree", "-r", "--name-only", commit,
        "packages/community-lexicon-publisher/lexicons",
    ], text=True).splitlines()
    schema_hashes = {
        path: hashlib.sha256(subprocess.check_output(["git", "-C", str(source), "show", f"{commit}:{path}"])).hexdigest()
        for path in schema_paths if path.endswith(".json")
    }
    if len(schema_hashes) != 8:
        raise ValueError("exact eight canonical publisher schemas required")
    manifest = {
        "schema": "phlogiston.p0-candidate.v1", "communitySource": commit,
        "productBase": "51aa3d73a4034ae0d68d8669cbae413e78e20489",
        "runtimeRoot": runtime, "moderatorDid": moderator, "communityDid": COMMUNITY,
        "providerMode": "exact-hosted-community-plus-bluesky-authors",
        "principals": {"community-web-p0": web_uid, "communityd-p0": daemon_uid, "communitywatch-p0": observer_uid},
        "publicOrigin": "https://phlogiston.app", "webBind": "127.0.0.1:3211", "observerBind": "127.0.0.1:8081",
        "sourceTemplateHashes": source_hashes, "canonicalSchemaHashes": schema_hashes,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
        "status": "inert-not-installed", "pauseState": "paused",
        "requiredIndependentChecks": ["installed runtime/dependency inventory and exact source correspondence", "protected snapshot secret and actor credential", "actual principal/effective-unit preflight", "publisher manifest acceptance and publication readback", "installed acceptance and reserved public-cutover approval"],
    }
    (output / "candidate.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--community-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--moderator-did", default=COMMUNITY)
    parser.add_argument("--community-commit", default=SOURCE)
    parser.add_argument("--web-uid", type=int, default=42011)
    parser.add_argument("--daemon-uid", type=int, default=42013)
    parser.add_argument("--observer-uid", type=int, default=42014)
    args = parser.parse_args()
    render(args.community_source, args.output, args.runtime_root, args.moderator_did,
           (args.web_uid, args.daemon_uid, args.observer_uid), args.community_commit)
    print("inert candidate rendered; no services, credentials or route installed")


if __name__ == "__main__":
    main()
