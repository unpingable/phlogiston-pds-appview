#!/usr/bin/env python3
"""Publish one labeled disposable fixture through normal Phlogiston account APIs."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from phlogiston_appview.pds_ops import directory, private_file, stamp, write_private

ORIGIN = "https://phlogiston.social"
COLLECTION = "app.bsky.feed.post"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def api(method: str, body: dict | None = None, token: str | None = None, query: dict | None = None) -> dict | None:
    from urllib.parse import urlencode
    url = ORIGIN + "/xrpc/" + method
    if query:
        url += "?" + urlencode(query)
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=15) as response:
            content = response.read(1024 * 1024 + 1)
            if len(content) > 1024 * 1024:
                raise RuntimeError("response limit")
            result = json.loads(content)
            if not isinstance(result, dict):
                raise RuntimeError("response shape")
            return result
    except urllib.error.HTTPError as error:
        # Only the stock exact-record absence result is definite; never infer from transport/route errors.
        if method == "com.atproto.repo.getRecord" and error.code == 400:
            try:
                content = error.read(4097)
                if len(content) <= 4096 and json.loads(content).get("error") == "RecordNotFound":
                    return None
            except (ValueError, AttributeError):
                pass
        raise RuntimeError("PDS request failed; retain intent checkpoint") from None
    except Exception:
        raise RuntimeError("PDS outcome is unknown; retain intent checkpoint") from None


@contextmanager
def claim(checkpoint: Path):
    directory(checkpoint.parent)
    path = checkpoint.with_name(checkpoint.name + ".lock")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.geteuid() or info.st_nlink != 1:
            raise ValueError("owner-only regular single-link case lock required")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)  # kernel releases the claim on ordinary return or process loss


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def reference(value: dict, uri: str) -> dict:
    cid = value.get("cid", "")
    if value.get("uri") != uri or not re.fullmatch(r"bafy[a-z2-7]{20,100}", cid):
        raise ValueError("exact public record reference required")
    return {"uri": uri, "cid": cid}


def fixture_tid(did: str, case: str) -> str:
    """Encode a deterministic fixture address using the standard 63-bit TID codec.

    This is a case-address generator, not a chronological revision clock.
    https://atproto.com/specs/tid: top bit zero, 13 base32-sortable digits.
    """
    alphabet = "234567abcdefghijklmnopqrstuvwxyz"
    value = int.from_bytes(hashlib.sha256((did + "\n" + case).encode()).digest()[:8], "big") & ((1 << 63) - 1)
    return "".join(alphabet[(value >> shift) & 31] for shift in range(60, -1, -5))


def fixture_post(account: Path, case: str, checkpoint: Path) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", case):
        raise ValueError("bounded case identity required")
    owner = json.loads(private_file(account).read_text())
    did, handle, password = owner.get("did", ""), owner.get("handle", ""), owner.get("password")
    if owner.get("phase") != "complete" or not re.fullmatch(r"did:plc:[a-z2-7]{24}", did) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,61}\.phlogiston\.social", handle) or not isinstance(password, str) or not password:
        raise ValueError("completed disposable Phlogiston account custody required")
    rkey = fixture_tid(did, case)
    uri = f"at://{did}/{COLLECTION}/{rkey}"
    with claim(checkpoint):
        if checkpoint.exists():
            intent = json.loads(private_file(checkpoint).read_text())
            if intent.get("schema") != "phlogiston.fixture-post.v1" or intent.get("did") != did or intent.get("handle") != handle or intent.get("case") != case or intent.get("rkey") != rkey or intent.get("uri") != uri or intent.get("origin") != ORIGIN:
                raise ValueError("checkpoint belongs to a different exact intent")
            if intent.get("phase") not in {"prepared", "attempted_unknown", "committed"}:
                raise ValueError("unknown checkpoint transition")
            expected = intent.get("record")
            if not isinstance(expected, dict) or set(expected) != {"$type", "text", "createdAt"} or expected["$type"] != COLLECTION or expected["text"] != f"[Phlogiston disposable qualification: {case}] This is a test fixture; no real-user content." or not isinstance(expected["createdAt"], str):
                raise ValueError("checkpoint record no longer matches this fixture")
        else:
            record = {"$type": COLLECTION, "text": f"[Phlogiston disposable qualification: {case}] This is a test fixture; no real-user content.", "createdAt": stamp().replace("+00:00", "Z")}
            intent = {"schema": "phlogiston.fixture-post.v1", "phase": "prepared", "origin": ORIGIN,
                      "did": did, "handle": handle, "case": case, "rkey": rkey, "uri": uri, "record": record}
            write_private(checkpoint, intent)
        session = api("com.atproto.server.createSession", {"identifier": did, "password": password})
        if not session or session.get("did") != did or session.get("handle") != handle or not isinstance(session.get("accessJwt"), str) or not session["accessJwt"]:
            raise ValueError("normal session differs from exact account custody")
        token = session["accessJwt"]
        observed = api("com.atproto.repo.getRecord", token=token, query={"repo": did, "collection": COLLECTION, "rkey": rkey})
        if observed is not None:
            if canonical(observed.get("value")) != canonical(intent["record"]):
                raise ValueError("current record conflicts with durable exact intent")
            result = reference(observed, uri)
            if intent["phase"] == "committed" and intent.get("cid") != result["cid"]:
                raise ValueError("current reference differs from committed exact record")
        else:
            if intent["phase"] != "prepared":
                raise RuntimeError("prior effect is absent or unknown; no fresh dispatch from an attempted intent")
            intent["phase"] = "attempted_unknown"
            write_private(checkpoint, intent, replace=True)
            created = api("com.atproto.repo.createRecord", {"repo": did, "collection": COLLECTION, "rkey": rkey, "record": intent["record"], "validate": True}, token=token)
            result = reference(created or {}, uri)
        intent.update(phase="committed", cid=result["cid"])
        write_private(checkpoint, intent, replace=True)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = fixture_post(args.account, args.case, args.checkpoint)
    except Exception:
        raise SystemExit("Fixture post refused or uncertain; retain the exact checkpoint and reconcile readback. No secret/provider response emitted.") from None
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
