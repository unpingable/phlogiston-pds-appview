from __future__ import annotations

import importlib.util
import json
import re
import hashlib
from pathlib import Path
import shutil

import pytest

from phlogiston_appview.pds_ops import write_private

PATH = Path(__file__).resolve().parents[1] / "deploy/production/pds-fixture-post.py"
spec = importlib.util.spec_from_file_location("pds_fixture_post", PATH)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
DID = "did:plc:" + "a" * 24
HANDLE = "fixture.phlogiston.social"
CID = "bafy" + "a" * 55


@pytest.fixture(autouse=True)
def retire_owned_fixture(tmp_path):
    yield
    shutil.rmtree(tmp_path)


def account(tmp_path):
    path = tmp_path / "account.json"
    write_private(path, {"phase": "complete", "did": DID, "handle": HANDLE, "password": "local-private-password"})
    return path


def test_normal_fixture_is_durable_before_effect_and_duplicate_reads_back(tmp_path, monkeypatch):
    owner = account(tmp_path); checkpoint = tmp_path / "intent.json"; writes = []; current = None
    def api(method, body=None, token=None, query=None):
        nonlocal current
        assert not method.startswith("com.atproto.admin")
        if method.endswith("createSession"):
            assert body["identifier"] == DID and body["password"] == "local-private-password"
            assert json.loads(checkpoint.read_text())["phase"] in {"prepared", "committed"}
            return {"did": DID, "handle": HANDLE, "accessJwt": "local-private-token"}
        assert token == "local-private-token"
        if method.endswith("getRecord"):return current
        saved = json.loads(checkpoint.read_text())
        assert saved["phase"] == "attempted_unknown" and saved["record"] == body["record"]
        assert "local-private" not in checkpoint.read_text()
        assert re.fullmatch(r"[234567abcdefghij][234567abcdefghijklmnopqrstuvwxyz]{12}", body["rkey"])
        writes.append(body)
        current = {"uri": saved["uri"], "cid": CID, "value": body["record"]}
        return {"uri": saved["uri"], "cid": CID}
    monkeypatch.setattr(fixture, "api", api)
    first = fixture.fixture_post(owner, "duplicate-case", checkpoint)
    assert fixture.fixture_post(owner, "duplicate-case", checkpoint) == first
    assert len(writes) == 1 and set(first) == {"uri", "cid"}
    assert "disposable qualification" in writes[0]["record"]["text"]


@pytest.mark.parametrize("observed", ["missing", "matching", "conflict", "read-error"])
def test_unknown_effect_retry_only_reads_exact_intent(tmp_path, monkeypatch, observed):
    owner = account(tmp_path); checkpoint = tmp_path / "intent.json"; creates = 0; retry = False
    def api(method, body=None, token=None, query=None):
        nonlocal creates
        if method.endswith("createSession"):return {"did": DID, "handle": HANDLE, "accessJwt": "private-token"}
        if method.endswith("createRecord"):
            creates += 1; raise RuntimeError("local unknown response")
        if not retry or observed == "missing":return None
        if observed == "read-error":raise RuntimeError("local read unavailable")
        intent = json.loads(checkpoint.read_text())
        return {"uri": intent["uri"], "cid": CID, "value": intent["record"] if observed == "matching" else {"text": "different"}}
    monkeypatch.setattr(fixture, "api", api)
    with pytest.raises(RuntimeError):fixture.fixture_post(owner, "unknown-case", checkpoint)
    assert json.loads(checkpoint.read_text())["phase"] == "attempted_unknown"
    retry = True
    if observed == "matching":assert fixture.fixture_post(owner, "unknown-case", checkpoint)["cid"] == CID
    else:
        with pytest.raises((RuntimeError, ValueError)):fixture.fixture_post(owner, "unknown-case", checkpoint)
    assert creates == 1


@pytest.mark.parametrize("case", ["wrong-session", "public-custody", "other-case", "concurrent-case", "prepared-conflict"])
def test_fixture_authority_and_state_negative_controls(tmp_path, monkeypatch, case):
    owner = account(tmp_path); checkpoint = tmp_path / "intent.json"; writes = 0
    def api(method, body=None, token=None, query=None):
        nonlocal writes
        if method.endswith("createSession"):return {"did": "did:plc:" + "b" * 24 if case == "wrong-session" else DID, "handle": HANDLE, "accessJwt": "private-token"}
        if method.endswith("getRecord"):
            if case == "prepared-conflict":return {"uri": "different", "cid": CID, "value": {"text": "different"}}
            return None
        writes += 1;raise RuntimeError("unknown fixture response")
    monkeypatch.setattr(fixture, "api", api)
    if case == "public-custody":owner.chmod(0o644)
    if case == "other-case":
        with pytest.raises(RuntimeError):fixture.fixture_post(owner, "first", checkpoint)
        writes = 0
    if case == "concurrent-case":
        with fixture.claim(checkpoint):
            with pytest.raises(BlockingIOError):fixture.fixture_post(owner, "case", checkpoint)
    else:
        with pytest.raises(ValueError):fixture.fixture_post(owner, "case", checkpoint)
    assert writes == 0


def test_http_absence_only_exact_record_not_found_and_exact_origin(tmp_path, monkeypatch):
    import io
    import urllib.error
    from urllib.parse import urlparse
    seen = []
    class Opener:
        def open(self, request, timeout):
            seen.append(request.full_url)
            raise urllib.error.HTTPError(request.full_url, 400, "redacted", {}, io.BytesIO(b'{"error":"RecordNotFound"}'))
    monkeypatch.setattr(fixture.urllib.request, "build_opener", lambda *args: Opener())
    assert fixture.api("com.atproto.repo.getRecord", query={"repo": DID}) is None
    assert urlparse(seen[0]).netloc == "phlogiston.social" and urlparse(seen[0]).scheme == "https"
    with pytest.raises(RuntimeError):fixture.api("com.atproto.repo.createRecord", {})
    class Unknown:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 404, "redacted", {}, io.BytesIO(b'{"error":"RecordNotFound"}'))
    monkeypatch.setattr(fixture.urllib.request, "build_opener", lambda *args: Unknown())
    with pytest.raises(RuntimeError):fixture.api("com.atproto.repo.getRecord", query={"repo": DID})


def test_deterministic_tid_matches_standard_codec_and_preserves_old_unknown(tmp_path, monkeypatch):
    alphabet = "234567abcdefghijklmnopqrstuvwxyz"
    for case in ("first", "second", "format-negative-control"):
        key = fixture.fixture_tid(DID, case)
        assert re.fullmatch(r"[234567abcdefghij][234567abcdefghijklmnopqrstuvwxyz]{12}", key)
        decoded = 0
        for char in key:
            decoded = (decoded << 5) | alphabet.index(char)
        assert decoded == int.from_bytes(hashlib.sha256((DID + "\n" + case).encode()).digest()[:8], "big") & ((1 << 63) - 1)
        assert fixture.fixture_tid(DID, case) == key
    assert fixture.fixture_tid(DID, "first") != fixture.fixture_tid(DID, "second")
    owner = account(tmp_path)
    checkpoint = tmp_path / "old.json"
    old = {"schema": "phlogiston.fixture-post.v1", "phase": "attempted_unknown", "did": DID,
           "handle": HANDLE, "case": "first", "rkey": "phfixture-old", "origin": fixture.ORIGIN}
    write_private(checkpoint, old)
    before = checkpoint.read_bytes()
    def no_dispatch(*args, **kwargs):
        pytest.fail("old unknown checkpoint must refuse before network")
    monkeypatch.setattr(fixture, "api", no_dispatch)
    with pytest.raises(ValueError, match="different exact intent"):
        fixture.fixture_post(owner, "first", checkpoint)
    assert checkpoint.read_bytes() == before
