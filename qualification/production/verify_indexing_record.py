#!/usr/bin/python3
"""Exact-identity ATProto submit writer for the V2 production check.

This helper never chooses authority or credentials. It consumes the same
app-password boundary as the existing check, durably reserves an exact record
identity before dispatch, and reconciles a completed-response loss by reading
that identity. An attempted operation that remains absent is indeterminate and
is never redispatched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request


COLLECTION = "app.phlogiston.community.submit"
CONTRACT = "phlogiston.v2-submit-intent.v1"
PHASES = {"prepared", "attempting", "attempted_unknown", "settled"}
RKEY = re.compile(r"^[A-Za-z0-9._~:-]{1,512}$")
KEYS = {
    "attempts", "cid", "collection", "community", "contract", "created_at",
    "did", "disposition", "expected_uri", "pds", "phase", "record",
    "record_sha256", "rkey", "subject_cid", "subject_uri",
}


def stable(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(stable(value)).hexdigest()


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path: Path, value: dict[str, object], *, create: bool) -> None:
    data = stable(value)
    if create:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        temporary = None
    else:
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        offset = 0
        while offset < len(data):
            written = os.write(fd, data[offset:])
            if written <= 0:
                raise RuntimeError("intent write made no progress")
            offset += written
        os.fsync(fd)
    finally:
        os.close(fd)
    if temporary is not None:
        os.replace(temporary, path)
    fsync_dir(path.parent)


def exact_object(value: object, keys: set[str], where: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{where} fields are not exact")
    return value


def parse_intent(value: object) -> dict[str, object]:
    raw = exact_object(value, KEYS, "intent")
    for key in (
        "collection", "community", "contract", "created_at", "did",
        "expected_uri", "pds", "phase", "record_sha256", "rkey",
        "subject_cid", "subject_uri",
    ):
        if type(raw[key]) is not str or not raw[key]:
            raise ValueError(f"intent {key} is invalid")
    if raw["contract"] != CONTRACT or raw["collection"] != COLLECTION or raw["phase"] not in PHASES:
        raise ValueError("intent contract, collection, or phase is invalid")
    if type(raw["attempts"]) is not int or raw["attempts"] < 0:
        raise ValueError("intent attempts is invalid")
    if raw["cid"] is not None and (type(raw["cid"]) is not str or not raw["cid"]):
        raise ValueError("intent cid is invalid")
    if raw["disposition"] is not None and raw["disposition"] not in {"created", "read_back"}:
        raise ValueError("intent disposition is invalid")
    if type(raw["record"]) is not dict or digest(raw["record"]) != raw["record_sha256"]:
        raise ValueError("intent record digest is invalid")
    if raw["expected_uri"] != f'at://{raw["did"]}/{COLLECTION}/{raw["rkey"]}':
        raise ValueError("intent expected URI is invalid")
    if not RKEY.fullmatch(str(raw["rkey"])):
        raise ValueError("intent rkey is invalid")
    if raw["phase"] == "settled" and (raw["cid"] is None or raw["disposition"] is None):
        raise ValueError("settled intent is incomplete")
    return raw


def load(path: Path) -> dict[str, object]:
    return parse_intent(json.loads(path.read_text(encoding="utf-8")))


def request_json(url: str, *, body: object | None = None, token: str | None = None) -> dict[str, object]:
    encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {"accept": "application/json"}
    if encoded is not None:
        headers["content-type"] = "application/json"
    if token is not None:
        headers["authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=encoded, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    if type(result) is not dict:
        raise ValueError("XRPC response is not an object")
    return result


def get_record(intent: dict[str, object], token: str) -> dict[str, object] | None:
    query = urllib.parse.urlencode({
        "repo": intent["did"], "collection": COLLECTION, "rkey": intent["rkey"],
    })
    try:
        return request_json(f'{intent["pds"]}/xrpc/com.atproto.repo.getRecord?{query}', token=token)
    except urllib.error.HTTPError as error:
        payload: object = None
        try:
            payload = json.loads(error.read())
        except Exception:
            pass
        if error.code in {400, 404} and type(payload) is dict and payload.get("error") == "RecordNotFound":
            return None
        raise


def require_exact_readback(intent: dict[str, object], found: dict[str, object] | None) -> tuple[str, str]:
    if found is None:
        raise RuntimeError("exact record is absent after an attempted write; indeterminate, do not redispatch")
    if found.get("uri") != intent["expected_uri"] or type(found.get("cid")) is not str or not found["cid"]:
        raise RuntimeError("exact record identity readback is invalid")
    if found.get("value") != intent["record"]:
        raise RuntimeError("exact rkey is occupied by different record bytes")
    return str(found["uri"]), str(found["cid"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True, type=Path)
    parser.add_argument("--pds", required=True)
    parser.add_argument("--did", required=True)
    parser.add_argument("--community", required=True)
    parser.add_argument("--rkey", required=True)
    parser.add_argument("--password-file", required=True, type=Path)
    parser.add_argument("--created-at")
    parser.add_argument("--subject-uri")
    parser.add_argument("--subject-cid")
    parser.add_argument("--allow-http-loopback-fixture", action="store_true")
    args = parser.parse_args()

    if not args.intent.is_absolute() or not args.intent.parent.is_dir():
        raise ValueError("intent path must be absolute with an existing parent")
    parsed_pds = urllib.parse.urlsplit(args.pds)
    allowed_http_fixture = (
        args.allow_http_loopback_fixture
        and parsed_pds.scheme == "http"
        and parsed_pds.hostname in {"127.0.0.1", "::1"}
    )
    if (
        not (parsed_pds.scheme == "https" or allowed_http_fixture)
        or parsed_pds.username is not None or parsed_pds.password is not None
        or parsed_pds.query or parsed_pds.fragment or parsed_pds.path not in {"", "/"}
    ):
        raise ValueError("PDS must be an HTTPS origin (or explicit loopback fixture)")
    password_stat = args.password_file.stat()
    if not stat.S_ISREG(password_stat.st_mode) or stat.S_IMODE(password_stat.st_mode) != 0o600:
        raise ValueError("password file must be a regular mode-0600 file")
    if not RKEY.fullmatch(args.rkey):
        raise ValueError("rkey is invalid")
    if args.intent.exists():
        intent = load(args.intent)
        for key, actual in (("pds", args.pds), ("did", args.did), ("community", args.community), ("rkey", args.rkey)):
            if intent[key] != actual:
                raise ValueError(f"retained intent conflicts on {key}")
    else:
        if not all((args.created_at, args.subject_uri, args.subject_cid)):
            raise ValueError("a new intent requires created-at and exact subject URI/CID")
        record = {
            "$type": COLLECTION,
            "community": args.community,
            "subject": {"uri": args.subject_uri, "cid": args.subject_cid},
            "createdAt": args.created_at,
        }
        intent = {
            "attempts": 0, "cid": None, "collection": COLLECTION,
            "community": args.community, "contract": CONTRACT,
            "created_at": args.created_at, "did": args.did, "disposition": None,
            "expected_uri": f"at://{args.did}/{COLLECTION}/{args.rkey}",
            "pds": args.pds, "phase": "prepared", "record": record,
            "record_sha256": digest(record), "rkey": args.rkey,
            "subject_cid": args.subject_cid, "subject_uri": args.subject_uri,
        }
        save(args.intent, parse_intent(intent), create=True)

    password = args.password_file.read_text(encoding="utf-8").strip()
    session = request_json(
        f'{intent["pds"]}/xrpc/com.atproto.server.createSession',
        body={"identifier": intent["did"], "password": password},
    )
    token = session.get("accessJwt")
    if type(token) is not str or not token:
        raise RuntimeError("session response has no access token")

    found = get_record(intent, token)
    if found is not None:
        uri, cid = require_exact_readback(intent, found)
        disposition = "read_back"
    else:
        if intent["phase"] != "prepared":
            raise RuntimeError("prior attempted exact record is absent; indeterminate, do not redispatch")
        intent.update(phase="attempting", attempts=intent["attempts"] + 1)
        save(args.intent, parse_intent(intent), create=False)
        created: dict[str, object] | None = None
        create_error: Exception | None = None
        try:
            created = request_json(
                f'{intent["pds"]}/xrpc/com.atproto.repo.createRecord', token=token,
                body={"repo": intent["did"], "collection": COLLECTION,
                      "rkey": intent["rkey"], "record": intent["record"]},
            )
        except Exception as error:
            create_error = error
        intent["phase"] = "attempted_unknown"
        save(args.intent, parse_intent(intent), create=False)
        found = get_record(intent, token)
        try:
            uri, cid = require_exact_readback(intent, found)
        except Exception:
            if create_error is not None:
                raise RuntimeError("create response failed and exact readback did not reconcile") from create_error
            raise
        if created is not None and (created.get("uri") != uri or created.get("cid") != cid):
            raise RuntimeError("create response conflicts with exact readback")
        disposition = "created" if create_error is None else "read_back"

    intent.update(phase="settled", cid=cid, disposition=disposition)
    save(args.intent, parse_intent(intent), create=False)
    print(json.dumps({
        "uri": uri, "cid": cid, "pds": intent["pds"],
        "subject_uri": intent["subject_uri"], "subject_cid": intent["subject_cid"],
        "created_at": intent["created_at"], "record_sha256": intent["record_sha256"],
        "intent_path": str(args.intent), "intent_sha256": hashlib.sha256(args.intent.read_bytes()).hexdigest(),
        "disposition": disposition, "attempts": intent["attempts"],
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"refused: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
