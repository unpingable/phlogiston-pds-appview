"""Authenticated Phlogiston operator surface over explicit authority ports.

The browser surface owns neither PDS nor community authority.  It authenticates
an already-enrolled operator, validates browser intent, then delegates exactly
one typed operation to either the official PDS XRPC boundary or communityd.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Protocol


MAX_FORM_BYTES = 32 * 1024
SESSION_MAX_AGE = 8 * 60 * 60
CONFIRM_MAX_AGE = 10 * 60


@dataclass(frozen=True, slots=True)
class OperatorSession:
    did: str
    csrf: str


@dataclass(frozen=True, slots=True)
class EffectResult:
    authority: str
    operation: str
    disposition: str
    reference: str | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    content_type: str
    body: bytes
    headers: tuple[tuple[str, str], ...] = ()


class PdsAdministration(Protocol):
    def create_invite(self, *, use_count: int, for_account: str | None) -> EffectResult: ...
    def create_account(self, *, handle: str, email: str, password: str, invite_code: str) -> EffectResult: ...
    def account_info(self, did: str) -> Mapping[str, object]: ...
    def search_accounts(self, email: str | None = None) -> tuple[Mapping[str, object], ...]: ...


class CommunityAdministration(Protocol):
    def membership(self, *, operation_id: str, operator_did: str, subject_did: str, action: str, reason: str | None) -> EffectResult: ...
    def admit(self, *, operation_id: str, operator_did: str, uri: str, cid: str) -> EffectResult: ...
    def remove(self, *, operation_id: str, operator_did: str, uri: str, cid: str, reason: str) -> EffectResult: ...


class CommunityProjection(Protocol):
    def health(self) -> Mapping[str, object]: ...
    def moderation_queue(self) -> Mapping[str, object]: ...
    def members(self) -> Mapping[str, object]: ...
    def discussions(self) -> Mapping[str, object]: ...


class SessionCodec:
    """Small versioned HMAC envelope for an already-authenticated operator."""

    def __init__(self, key: bytes, *, clock=time.time) -> None:
        if len(key) < 32:
            raise ValueError("session key must contain at least 32 bytes")
        self._key = key
        self._clock = clock

    def issue(self, did: str, csrf: str | None = None) -> str:
        payload = {"v": 1, "did": _did(did), "csrf": csrf or secrets.token_urlsafe(24), "iat": int(self._clock())}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        tag = hmac.new(self._key, b"phlogiston/operator-session/v1\x00" + raw, hashlib.sha256).digest()
        return _b64(raw + tag)

    def parse(self, token: str) -> OperatorSession:
        try:
            packed = _unb64(token)
            raw, supplied = packed[:-32], packed[-32:]
            expected = hmac.new(self._key, b"phlogiston/operator-session/v1\x00" + raw, hashlib.sha256).digest()
            if not hmac.compare_digest(supplied, expected):
                raise ValueError
            value = json.loads(raw)
            if set(value) != {"v", "did", "csrf", "iat"} or value["v"] != 1:
                raise ValueError
            age = int(self._clock()) - int(value["iat"])
            if age < -30 or age > SESSION_MAX_AGE:
                raise ValueError
            return OperatorSession(_did(value["did"]), _text(value["csrf"], 200, "csrf"))
        except Exception as exc:
            raise PermissionError("operator session is invalid or expired") from exc

    def confirmation(self, session: OperatorSession, action: Mapping[str, str]) -> str:
        payload = {"v": 1, "did": session.did, "iat": int(self._clock()), "action": dict(sorted(action.items()))}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        tag = hmac.new(self._key, b"phlogiston/operator-confirm/v1\x00" + raw, hashlib.sha256).digest()
        return _b64(raw + tag)

    def verify_confirmation(self, session: OperatorSession, token: str, action: Mapping[str, str]) -> None:
        try:
            packed = _unb64(token)
            raw, supplied = packed[:-32], packed[-32:]
            expected = hmac.new(self._key, b"phlogiston/operator-confirm/v1\x00" + raw, hashlib.sha256).digest()
            value = json.loads(raw)
            valid = hmac.compare_digest(supplied, expected)
            valid &= value == {"v": 1, "did": session.did, "iat": value.get("iat"), "action": dict(sorted(action.items()))}
            age = int(self._clock()) - int(value["iat"])
            valid &= -30 <= age <= CONFIRM_MAX_AGE
            if not valid:
                raise ValueError
        except Exception as exc:
            raise PermissionError("confirmation is invalid or expired") from exc


class XrpcPdsAdminClient:
    """Calls official PDS XRPCs; secrets stay in the server-side transport."""

    def __init__(self, origin: str, admin_password: str, *, opener=urllib.request.urlopen) -> None:
        parsed = urllib.parse.urlsplit(origin)
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("PDS origin must use HTTPS outside loopback")
        self.origin = origin.rstrip("/")
        self._authorization = "Basic " + base64.b64encode(f"admin:{admin_password}".encode()).decode()
        self._open = opener

    def create_invite(self, *, use_count: int, for_account: str | None) -> EffectResult:
        if use_count < 1 or use_count > 100:
            raise ValueError("invite use count must be between 1 and 100")
        body: dict[str, object] = {"useCount": use_count}
        if for_account:
            body["forAccount"] = _did(for_account)
        result = self._request("POST", "com.atproto.server.createInviteCode", body=body)
        return EffectResult("pds", "create_invite", "created", detail=_text(result.get("code"), 500, "invite code"))

    def create_account(self, *, handle: str, email: str, password: str, invite_code: str) -> EffectResult:
        body = {"handle": _text(handle, 253, "handle"), "email": _text(email, 320, "email"), "password": _text(password, 1024, "password"), "inviteCode": _text(invite_code, 500, "invite code")}
        result = self._request("POST", "com.atproto.server.createAccount", body=body, admin=False)
        # Access and refresh JWTs are deliberately discarded before crossing the adapter.
        return EffectResult("pds", "create_account", "created", reference=_did(result.get("did")), detail=_text(result.get("handle"), 253, "handle"))

    def account_info(self, did: str) -> Mapping[str, object]:
        return self._request("GET", "com.atproto.admin.getAccountInfo", query={"did": _did(did)})

    def search_accounts(self, email: str | None = None) -> tuple[Mapping[str, object], ...]:
        result = self._request("GET", "com.atproto.admin.searchAccounts", query={"email": email} if email else {})
        accounts = result.get("accounts")
        if not isinstance(accounts, list) or not all(isinstance(item, dict) for item in accounts):
            raise RuntimeError("PDS returned an invalid account list")
        return tuple(accounts)

    def _request(self, method: str, nsid: str, *, body: Mapping[str, object] | None = None, query: Mapping[str, str] | None = None, admin: bool = True) -> Mapping[str, object]:
        encoded_query = urllib.parse.urlencode(query or {})
        url = f"{self.origin}/xrpc/{nsid}" + (f"?{encoded_query}" if encoded_query else "")
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if admin:
            headers["Authorization"] = self._authorization
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with self._open(request, timeout=10) as response:
                raw = response.read(256 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"PDS refused {nsid} with HTTP {exc.code}") from exc
        if len(raw) > 256 * 1024:
            raise RuntimeError("PDS response exceeds limit")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise RuntimeError("PDS returned a non-object response")
        return value


class OperatorApp:
    """Framework-neutral request handler used by the HTTP entry point and tests."""

    def __init__(self, *, sessions: SessionCodec, operator_dids: frozenset[str], pds: PdsAdministration, community: CommunityAdministration, projection: CommunityProjection) -> None:
        self.sessions = sessions
        self.operator_dids = frozenset(_did(value) for value in operator_dids)
        self.pds = pds
        self.community = community
        self.projection = projection

    def handle(self, method: str, path: str, *, cookie: str = "", body: bytes = b"") -> Response:
        try:
            if method == "GET" and path == "/community/":
                return self._community_page()
            session = self._session(cookie)
            if method == "GET" and path == "/admin/":
                return self._dashboard(session)
            if method == "POST":
                form = _form(body)
                if form.pop("csrf", None) != session.csrf:
                    raise PermissionError("form token did not match")
                return self._post(session, path, form)
            return _page(404, "Not found", "That operator route does not exist.")
        except PermissionError as exc:
            return _page(403, "Operator access refused", str(exc))
        except (ValueError, RuntimeError) as exc:
            return _page(400, "Operation refused", str(exc))

    def _community_page(self) -> Response:
        document = self.projection.discussions()
        discussions = document.get("discussions")
        if not isinstance(discussions, list):
            raise RuntimeError("community projection omitted discussions")
        items = []
        for item in discussions:
            if not isinstance(item, dict):
                raise RuntimeError("community projection returned an invalid discussion")
            status = _e(item.get("status", "unknown"))
            post = item.get("post") if isinstance(item.get("post"), dict) else {}
            author = _e(item.get("authorDid", "unknown author"))
            text = _e(post.get("text", "[content unavailable]"))
            items.append(f"<li><article><h2>{author}</h2><p>{text}</p><p>Community state: <strong>{status}</strong></p></article></li>")
        snapshot = document.get("snapshot") if isinstance(document.get("snapshot"), dict) else {}
        body = f'<p class=lede>Author-owned posts admitted into this community view.</p><ol>{"".join(items) or "<li>No admitted discussions are currently projected.</li>"}</ol><p>Projection generation: <code>{_e(snapshot.get("generation", "unknown"))}</code></p>'
        return _page(200, "Phlogiston community", body, raw=True)

    def _session(self, cookie: str) -> OperatorSession:
        values = {}
        for item in cookie.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                values[key] = value
        session = self.sessions.parse(values.get("phlogiston_operator", ""))
        if session.did not in self.operator_dids:
            raise PermissionError("operator is not enrolled")
        return session

    def _dashboard(self, session: OperatorSession) -> Response:
        health = self.projection.health()
        queue = self.projection.moderation_queue()
        members = self.projection.members()
        content = f"""
<p class=lede>Routine custody and community operations. Reading this page grants no authority.</p>
<section class=pds><h2>PDS custody administration</h2><p>Official PDS account and invite APIs. This authority does not admit or remove community content.</p>
<form method=post action=/admin/pds/search><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Account email filter (optional) <input name=email type=email></label><button>Search accounts</button></form>
<form method=post action=/admin/pds/inspect><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Account DID <input name=did required></label><button>Inspect account</button></form>
<form method=post action=/admin/pds/invites><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Uses <input name=use_count value=1 inputmode=numeric></label><label>Bind to DID (optional) <input name=for_account></label><button>Create invite</button></form>
<form method=post action=/admin/pds/accounts><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Handle <input name=handle required></label><label>Email <input name=email type=email required></label><label>Temporary password <input name=password type=password required></label><label>Invite code <input name=invite_code required></label><button>Create account</button></form></section>
<section class=community><h2>Community authority</h2><p>Membership and content decisions are written only by communityd. They do not alter PDS account custody.</p>
<form method=post action=/admin/community/membership><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Subject DID <input name=subject_did required></label><label>Action <select name=action><option value=add>Add member</option><option value=remove>Remove member</option></select></label><label>Reason <input name=reason></label><button>Review membership effect</button></form>
<form method=post action=/admin/community/admit><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Submission AT URI <input name=uri required></label><label>Submission CID <input name=cid required></label><button>Admit content</button></form>
<form method=post action=/admin/community/remove><input type=hidden name=csrf value="{_e(session.csrf)}"><label>Admission AT URI <input name=uri required></label><label>Admission CID <input name=cid required></label><label>Reason <input name=reason required></label><button>Review removal</button></form></section>
<section><h2>Projection and reconciliation</h2><dl><dt>Status</dt><dd>{_e(str(health.get('status', 'unknown')))}</dd><dt>Projection</dt><dd>{_e(str(health.get('projectionStatus', 'unknown')))}</dd><dt>Freshness</dt><dd>{_e(', '.join(map(str, health.get('reasonCodes', []))) or 'no reported degradation')}</dd><dt>Pending admissions</dt><dd>{len(queue.get('submissions', []))}</dd><dt>Membership records</dt><dd>{len(members.get('members', []))}</dd></dl></section>"""
        return _page(200, "Phlogiston operator", content, raw=True)

    def _post(self, session: OperatorSession, path: str, form: dict[str, str]) -> Response:
        if path == "/admin/pds/search":
            return _account_results(self.pds.search_accounts(form.get("email") or None))
        if path == "/admin/pds/inspect":
            return _account_results((self.pds.account_info(_did(form.get("did"))),))
        if path == "/admin/pds/invites":
            result = self.pds.create_invite(use_count=int(form.get("use_count", "0")), for_account=form.get("for_account") or None)
            return _effect(result)
        if path == "/admin/pds/accounts":
            result = self.pds.create_account(handle=form.get("handle", ""), email=form.get("email", ""), password=form.get("password", ""), invite_code=form.get("invite_code", ""))
            return _effect(result)
        if path in {"/admin/community/membership", "/admin/community/remove"}:
            return self._destructive(session, path, form)
        if path == "/admin/community/admit":
            result = self.community.admit(operation_id=_operation_id(session.did, path, form), operator_did=session.did, uri=_text(form.get("uri"), 2048, "URI"), cid=_text(form.get("cid"), 256, "CID"))
            return _effect(result)
        if path == "/admin/confirm":
            return self._confirmed(session, form)
        return _page(404, "Not found", "That operator action does not exist.")

    def _destructive(self, session: OperatorSession, path: str, form: dict[str, str]) -> Response:
        action = {"path": path, **{key: value for key, value in form.items() if key != "confirm"}}
        token = self.sessions.confirmation(session, action)
        fields = "".join(f'<input type=hidden name="{_e(k)}" value="{_e(v)}">' for k, v in action.items())
        return _page(200, "Confirm authoritative effect", f'<p>This will request a <strong>{_e(path)}</strong> effect from communityd. It does not change the subject PDS account.</p><form method="post" action="/admin/confirm"><input type="hidden" name="csrf" value="{_e(session.csrf)}"><input type="hidden" name="confirmation" value="{_e(token)}">{fields}<label><input type="checkbox" name="confirm" value="yes" required> I understand this changes authoritative community state.</label><button>Confirm effect</button></form>', raw=True)

    def _confirmed(self, session: OperatorSession, form: dict[str, str]) -> Response:
        if form.pop("confirm", None) != "yes":
            raise PermissionError("explicit confirmation was not supplied")
        token = form.pop("confirmation", "")
        path = form.get("path", "")
        action = dict(form)
        self.sessions.verify_confirmation(session, token, action)
        if path == "/admin/community/membership":
            result = self.community.membership(operation_id=_operation_id(session.did, path, action), operator_did=session.did, subject_did=_did(action.get("subject_did")), action=action.get("action", ""), reason=action.get("reason") or None)
        elif path == "/admin/community/remove":
            result = self.community.remove(operation_id=_operation_id(session.did, path, action), operator_did=session.did, uri=_text(action.get("uri"), 2048, "URI"), cid=_text(action.get("cid"), 256, "CID"), reason=_text(action.get("reason"), 2000, "reason"))
        else:
            raise ValueError("confirmed operation is unsupported")
        return _effect(result)


def _operation_id(did: str, path: str, fields: Mapping[str, str]) -> str:
    intent = json.dumps({"did": did, "path": path, "fields": dict(sorted(fields.items()))}, sort_keys=True, separators=(",", ":"))
    return "phlogiston:" + hashlib.sha256(intent.encode()).hexdigest()


def _form(body: bytes) -> dict[str, str]:
    if len(body) > MAX_FORM_BYTES:
        raise ValueError("form exceeds limit")
    parsed = urllib.parse.parse_qs(body.decode(), keep_blank_values=True, strict_parsing=True)
    if any(len(values) != 1 for values in parsed.values()):
        raise ValueError("duplicate form fields are not allowed")
    return {key: values[0] for key, values in parsed.items()}


def _did(value: object) -> str:
    text = _text(value, 2048, "DID")
    if not text.startswith("did:") or any(char.isspace() for char in text):
        raise ValueError("DID is invalid")
    return text


def _text(value: object, limit: int, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > limit or "\x00" in value:
        raise ValueError(f"{name} is invalid")
    return value


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _page(status: int, title: str, content: str, *, raw: bool = False) -> Response:
    body = content if raw else f"<p>{_e(content)}</p>"
    css = "body{font:16px system-ui;max-width:70rem;margin:auto;padding:2rem;background:#f6f2e8;color:#182026}section{padding:1rem;margin:1rem 0;border:2px solid #52606d}.pds{border-color:#276749}.community{border-color:#9c4221}label{display:block;margin:.7rem 0}input,select,button{font:inherit;padding:.45rem}button{cursor:pointer}dt{font-weight:700}dd{margin-bottom:.5rem}a:focus,button:focus,input:focus,select:focus{outline:3px solid #2563eb;outline-offset:2px}"
    document = f'<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>{_e(title)}</title><style>{css}</style><main><h1>{_e(title)}</h1>{body}</main></html>'
    return Response(status, "text/html; charset=utf-8", document.encode(), (("Cache-Control", "no-store"), ("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"), ("Referrer-Policy", "no-referrer")))


def _effect(result: EffectResult) -> Response:
    content = f"<p><strong>Authority:</strong> {_e(result.authority)}</p><p><strong>Operation:</strong> {_e(result.operation)}</p><p><strong>Authoritative disposition:</strong> {_e(result.disposition)}</p>"
    if result.reference:
        content += f"<p><strong>Reference:</strong> <code>{_e(result.reference)}</code></p>"
    if result.detail:
        content += f"<p><strong>Result detail:</strong> <code>{_e(result.detail)}</code></p>"
    content += '<p><a href="/admin/">Return to operator surface</a></p>'
    return _page(200, "Authoritative effect result", content, raw=True)


def _account_results(accounts: tuple[Mapping[str, object], ...]) -> Response:
    if len(accounts) > 100:
        raise RuntimeError("PDS account result exceeds display limit")
    rows = []
    for account in accounts:
        # The operator view deliberately allowlists fields instead of rendering
        # an arbitrary admin response (which may gain sensitive fields later).
        rows.append(
            "<tr>"
            f"<td><code>{_e(account.get('did', 'unknown'))}</code></td>"
            f"<td>{_e(account.get('handle', 'unknown'))}</td>"
            f"<td>{_e(account.get('email', 'unavailable'))}</td>"
            f"<td>{_e(account.get('status', 'unknown'))}</td>"
            "</tr>"
        )
    content = (
        "<p>This is PDS custody state, not community membership.</p>"
        "<table><thead><tr><th>DID</th><th>Handle</th><th>Email</th><th>Status</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        '<p><a href="/admin/">Return to operator surface</a></p>'
    )
    return _page(200, "PDS account results", content, raw=True)
