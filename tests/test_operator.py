from __future__ import annotations

import io
import json
import urllib.parse

import pytest

from phlogiston_appview.operator import EffectResult, OperatorApp, SessionCodec, XrpcPdsAdminClient


ADMIN = "did:example:operator"


class FakePds:
    def __init__(self): self.calls = []
    def create_invite(self, **values):
        self.calls.append(("invite", values)); return EffectResult("pds", "create_invite", "created", detail="invite-test")
    def create_account(self, **values):
        self.calls.append(("account", values)); return EffectResult("pds", "create_account", "created", reference="did:example:new", detail=values["handle"])
    def account_info(self, did): return {"did": did, "handle": "member.test", "email": "member@example.test", "status": "active"}
    def search_accounts(self, email=None): return ({"did": "did:example:member", "handle": "member.test", "email": email or "member@example.test", "status": "active", "accessJwt": "must-not-render"},)


class FakeCommunity:
    def __init__(self): self.calls = []
    def membership(self, **values):
        self.calls.append(("membership", values)); return EffectResult("community", "membership_" + values["action"], "created", reference="at://did:example:community/member/1")
    def admit(self, **values):
        self.calls.append(("admit", values)); return EffectResult("community", "admit", "created", reference="at://did:example:community/admission/1")
    def remove(self, **values):
        self.calls.append(("remove", values)); return EffectResult("community", "remove", "created", reference="at://did:example:community/removal/1")


class FakeProjection:
    def health(self): return {"status": "stale", "projectionStatus": "complete", "reasonCodes": ["ingest_stale"]}
    def moderation_queue(self): return {"submissions": [{"uri": "redacted"}]}
    def members(self): return {"members": [{"did": "did:example:member", "status": "active"}]}
    def discussions(self): return {"discussions": [{"authorDid": "did:example:alice", "status": "visible", "post": {"text": "Hello from the actual projection"}}], "snapshot": {"generation": "g7"}}


@pytest.fixture
def app():
    codec = SessionCodec(b"k" * 32, clock=lambda: 1_000)
    pds, community = FakePds(), FakeCommunity()
    return OperatorApp(sessions=codec, operator_dids=frozenset({ADMIN}), pds=pds, community=community, projection=FakeProjection()), codec, pds, community


def request(app, codec, method, path, fields=None):
    token = codec.issue(ADMIN, "csrf-test")
    body = urllib.parse.urlencode(fields or {}).encode()
    return app.handle(method, path, cookie=f"phlogiston_operator={token}", body=body)


def test_dashboard_separates_authorities_and_reports_stale_projection(app):
    surface, codec, _, _ = app
    response = request(surface, codec, "GET", "/admin/")
    text = response.body.decode()
    assert response.status == 200
    assert "PDS custody administration" in text
    assert "Community authority" in text
    assert "ingest_stale" in text
    assert "Reading this page grants no authority" in text


def test_public_community_page_renders_projected_state_without_operator_session(app):
    surface, _, _, _ = app
    response = surface.handle("GET", "/community/")
    text = response.body.decode()
    assert response.status == 200
    assert "Hello from the actual projection" in text
    assert "Community state: <strong>visible</strong>" in text
    assert "g7" in text


def test_unenrolled_or_tampered_session_is_refused(app):
    surface, codec, _, _ = app
    token = codec.issue(ADMIN)
    response = surface.handle("GET", "/admin/", cookie=f"phlogiston_operator={token}x")
    assert response.status == 403


def test_pds_account_creation_discards_tokens_and_exposes_authority(app):
    surface, codec, pds, _ = app
    response = request(surface, codec, "POST", "/admin/pds/accounts", {"csrf": "csrf-test", "handle": "new.example", "email": "new@example.test", "password": "temporary", "invite_code": "code"})
    assert response.status == 200
    text = response.body.decode()
    assert "Authority:</strong> pds" in text
    assert "did:example:new" in text
    assert pds.calls[0][0] == "account"


def test_account_search_is_read_only_and_allowlists_rendered_fields(app):
    surface, codec, _, _ = app
    response = request(surface, codec, "POST", "/admin/pds/search", {"csrf": "csrf-test", "email": "member@example.test"})
    text = response.body.decode()
    assert response.status == 200
    assert "PDS custody state, not community membership" in text
    assert "did:example:member" in text
    assert "member@example.test" in text
    assert "must-not-render" not in text


def test_admission_is_direct_but_removal_requires_bound_confirmation(app):
    surface, codec, _, community = app
    admitted = request(surface, codec, "POST", "/admin/community/admit", {"csrf": "csrf-test", "uri": "at://did:example:alice/zone.neutral.community.submit/1", "cid": "bafy-test"})
    assert admitted.status == 200 and community.calls[-1][0] == "admit"

    review = request(surface, codec, "POST", "/admin/community/remove", {"csrf": "csrf-test", "uri": "at://did:example:community/zone.neutral.community.admission/1", "cid": "bafy-admit", "reason": "out of scope"})
    assert review.status == 200
    assert community.calls[-1][0] == "admit"
    text = review.body.decode()
    marker = 'name="confirmation" value="'
    token = text.split(marker, 1)[1].split('"', 1)[0]
    confirmed = request(surface, codec, "POST", "/admin/confirm", {"csrf": "csrf-test", "confirmation": token, "confirm": "yes", "path": "/admin/community/remove", "uri": "at://did:example:community/zone.neutral.community.admission/1", "cid": "bafy-admit", "reason": "out of scope"})
    assert confirmed.status == 200
    assert community.calls[-1][0] == "remove"
    assert "Authoritative disposition" in confirmed.body.decode()


def test_confirmation_cannot_be_retargeted(app):
    surface, codec, _, community = app
    review = request(surface, codec, "POST", "/admin/community/membership", {"csrf": "csrf-test", "subject_did": "did:example:alice", "action": "remove", "reason": "left"})
    token = review.body.decode().split('name="confirmation" value="', 1)[1].split('"', 1)[0]
    response = request(surface, codec, "POST", "/admin/confirm", {"csrf": "csrf-test", "confirmation": token, "confirm": "yes", "path": "/admin/community/membership", "subject_did": "did:example:bob", "action": "remove", "reason": "left"})
    assert response.status == 403
    assert community.calls == []


def test_xrpc_client_uses_official_endpoints_and_does_not_return_jwts():
    seen = []
    class Reply:
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, _limit): return json.dumps(self.body).encode()
    def opener(request, timeout):
        seen.append((request.full_url, request.method, dict(request.headers), request.data))
        if request.full_url.endswith("createAccount"):
            return Reply({"did": "did:example:new", "handle": "new.example", "accessJwt": "SECRET-A", "refreshJwt": "SECRET-R"})
        return Reply({"code": "invite-code"})
    client = XrpcPdsAdminClient("https://pds.test", "admin-secret", opener=opener)
    invite = client.create_invite(use_count=1, for_account=None)
    account = client.create_account(handle="new.example", email="new@example.test", password="pw", invite_code="invite-code")
    assert seen[0][0].endswith("/xrpc/com.atproto.server.createInviteCode")
    assert seen[1][0].endswith("/xrpc/com.atproto.server.createAccount")
    assert "Authorization" not in seen[1][2]
    assert "SECRET" not in repr(account)
    assert invite.authority == "pds" and account.reference == "did:example:new"
