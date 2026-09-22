"""One isolated, real-PDS Phlogiston/community lifecycle qualification."""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import threading
import time
import urllib.parse
import urllib.error
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from community_model import EventBatch, IncomingDelivery, RecordRef
from communitywatch import ObserverStore, ProjectionQuery
from communitywatch.syncclient import PdsClient, UrllibHttpGetter
from communitywatch.repoproof import extract_pds_endpoint, extract_verification_key
from communitywatch.verifying import VerifiedSubjectResolver, VerifyingEventSource
from communitywatch_web.app import WebApp
from communitywatch_web.server import make_server
from phlogiston_appview.community import HttpCommunityProjectionClient, UnixCommunityAuthorityClient
from phlogiston_appview.operator import OperatorApp, SessionCodec, XrpcPdsAdminClient


def xrpc(origin: str, nsid: str, *, body=None, query=None, token=None, admin=None):
    url = origin + "/xrpc/" + nsid
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    headers = {"accept": "application/json"}
    if data is not None:
        headers["content-type"] = "application/json"
    if token:
        headers["authorization"] = "Bearer " + token
    if admin:
        headers["authorization"] = "Basic " + base64.b64encode(("admin:" + admin).encode()).decode()
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", "replace")
        raise RuntimeError(f"synthetic XRPC {nsid} refused with HTTP {exc.code}: {detail}") from exc


def create_account(origin: str, handle: str, password: str):
    return xrpc(origin, "com.atproto.server.createAccount", body={"handle": handle, "email": handle + "@example.test", "password": password})


class Resolver:
    def __init__(self, documents, origins):
        self.documents, self.origins = documents, origins

    def resolve(self, did):
        value = json.loads(json.dumps(self.documents[did]))
        for service in value.get("service", []):
            if service.get("type") == "AtprotoPersonalDataServer":
                service["serviceEndpoint"] = self.origins[did]
        return value


class DidDirectory:
    """Loopback-only DID directory exposing exact synthetic documents."""

    def __init__(self, documents):
        encoded = {
            did: json.dumps(document, separators=(",", ":")).encode()
            for did, document in documents.items()
        }

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802 - stdlib HTTP API
                did = urllib.parse.unquote(self.path.lstrip("/"))
                body = encoded.get(did)
                if body is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("content-type", "application/did+json")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format, *_args):
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def start(self):
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


class One:
    def __init__(self, item):
        self.item = item

    def read(self, _cursor):
        return EventBatch(items=(self.item,), next_cursor=self.item.cursor)


def claims(origin, repo, collections, start):
    rev = xrpc(origin, "com.atproto.sync.getLatestCommit", query={"did": repo})["rev"]
    result = []
    sequence = start
    for collection in collections:
        page = xrpc(origin, "com.atproto.repo.listRecords", query={"repo": repo, "collection": collection, "limit": "100"})
        for entry in page.get("records", []):
            sequence += 1
            result.append(IncomingDelivery(
                source="isolated-pds",
                cursor=str(sequence),
                source_event_time=None,
                received_at=datetime.now(UTC),
                raw_envelope={
                    "repo": repo,
                    "rev": rev,
                    "operation": "create",
                    "collection": collection,
                    "rkey": entry["uri"].rsplit("/", 1)[1],
                    "cid": entry["cid"],
                },
                trust_mode="verify_repo",
                verification_outcome="unverified",
                verification_method="isolated-current-state",
                verifier_version="1",
            ))
    return result, sequence


def create_record(origin, session, collection, record):
    return xrpc(origin, "com.atproto.repo.createRecord", body={"repo": session["did"], "collection": collection, "record": record}, token=session["accessJwt"])


def operator_post(app, cookie, path, csrf, fields):
    body = urllib.parse.urlencode({"csrf": csrf, **fields}).encode()
    response = app.handle("POST", path, cookie=cookie, body=body)
    if response.status != 200:
        raise RuntimeError(f"Phlogiston operator route {path} refused with {response.status}")
    return response


def confirm_effect(app, cookie, csrf, review, fields):
    marker = 'name="confirmation" value="'
    text = review.body.decode()
    if marker not in text:
        raise RuntimeError("Phlogiston did not render an explicit confirmation")
    token = text.split(marker, 1)[1].split('"', 1)[0]
    return operator_post(
        app,
        cookie,
        "/admin/confirm",
        csrf,
        {"confirmation": token, "confirm": "yes", **fields},
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pds-origin", required=True)
    parser.add_argument("--participant-pds-origin", required=True)
    parser.add_argument("--plc-origin", required=True)
    parser.add_argument("--pds-image", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    args.root.mkdir(mode=0o700)

    community_password = "synthetic-community-password"
    community = create_account(args.pds_origin, "phlogcommunity.test", community_password)
    operator = create_account(args.pds_origin, "phlogoperator.test", "synthetic-operator-password")
    pds = XrpcPdsAdminClient(args.pds_origin, "synthetic-community-admin-password")
    participant_pds = XrpcPdsAdminClient(
        args.participant_pds_origin, "synthetic-participant-admin-password"
    )
    invite = pds.create_invite(use_count=1, for_account=None)
    participant_invite = participant_pds.create_invite(use_count=1, for_account=None)
    participant = participant_pds.create_account(
        handle="phlogparticipant.test",
        email="participant@example.test",
        password="synthetic-participant-password",
        invite_code=participant_invite.detail or "",
    )
    participant_session = xrpc(args.participant_pds_origin, "com.atproto.server.createSession", body={"identifier": "phlogparticipant.test", "password": "synthetic-participant-password"})
    post_ref = create_record(args.participant_pds_origin, participant_session, "app.bsky.feed.post", {
        "$type": "app.bsky.feed.post",
        "text": "A real isolated Phlogiston community post.",
        "createdAt": "2026-09-22T12:00:00Z",
    })
    submission = create_record(args.participant_pds_origin, participant_session, "zone.neutral.community.submit", {
        "$type": "zone.neutral.community.submit",
        "community": community["did"],
        "subject": {"uri": post_ref["uri"], "cid": post_ref["cid"]},
        "createdAt": "2026-09-22T12:00:01Z",
    })

    documents = {}
    origins = {
        community["did"]: args.pds_origin,
        operator["did"]: args.pds_origin,
        participant.reference: args.participant_pds_origin,
    }
    for did, pds_origin in origins.items():
        described = xrpc(pds_origin, "com.atproto.repo.describeRepo", query={"repo": did})
        document = described.get("didDoc")
        if not isinstance(document, dict) or document.get("id") != did:
            raise RuntimeError("PDS describeRepo omitted the synthetic DID document")
        for service in document.get("service", []):
            if service.get("type") == "AtprotoPersonalDataServer":
                service["serviceEndpoint"] = pds_origin
        documents[did] = document
    did_directory = DidDirectory(documents)
    did_directory.start()

    credential = args.root / "community-credential.json"
    credential.write_text(json.dumps({"identifier": "phlogcommunity.test", "app_password": community_password}))
    credential.chmod(0o600)
    socket_path = args.root / "communityd.sock"
    journal = args.root / "authority.sqlite3"
    config = args.root / "communityd.toml"
    config.write_text(
        f'community_did = "{community["did"]}"\n'
        f'administrator_did = "{operator["did"]}"\n'
        f'community_pds_url = "{args.pds_origin}"\n'
        f'allowed_uid = {os.geteuid()}\n'
        'reader_adapter = "pds"\n'
        'ledger_adapter = "pds"\n'
        'writer_adapter = "pds"\n'
        'credential_provider = "env_file"\n'
        'credential_ref = "env:PHLOG_SMOKE_CREDENTIAL"\n'
        'request_timeout_ms = 5000\n'
        'max_retries = 0\n'
        f'operation_journal_path = "{journal}"\n'
        f'authority_socket_path = "{socket_path}"\n'
        f'web_peer_uid = {os.geteuid()}\n'
        f'policy_peer_uid = {os.geteuid() + 1}\n'
        f'plc_directory_url = "{did_directory.origin}"\n'
        'allow_loopback_public_endpoints = true\n'
    )
    environment = dict(os.environ, PHLOG_SMOKE_CREDENTIAL=str(credential))
    daemon = subprocess.Popen(
        [
            os.environ.get("PYTHON", "python3"),
            "-c",
            "from communityd.serve_cli import main; raise SystemExit(main())",
            "--config",
            str(config),
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(100):
            if socket_path.exists():
                break
            if daemon.poll() is not None:
                raise RuntimeError("communityd failed: " + (daemon.stderr.read() if daemon.stderr else ""))
            time.sleep(0.05)
        else:
            raise RuntimeError("communityd socket did not appear")

        authority = UnixCommunityAuthorityClient(str(socket_path))
        codec = SessionCodec(b"s" * 32, clock=lambda: 1000)
        cookie = f"phlogiston_operator={codec.issue(operator['did'], 'smoke-csrf')}"
        write_app = OperatorApp(
            sessions=codec,
            operator_dids=frozenset({operator["did"]}),
            pds=pds,
            community=authority,
            projection=None,  # type: ignore[arg-type] - write routes never consult projection
        )
        membership_fields = {
            "path": "/admin/community/membership",
            "subject_did": participant.reference or "",
            "action": "add",
            "reason": "isolated qualification",
        }
        review = operator_post(
            write_app,
            cookie,
            membership_fields["path"],
            "smoke-csrf",
            {key: value for key, value in membership_fields.items() if key != "path"},
        )
        confirm_effect(write_app, cookie, "smoke-csrf", review, membership_fields)
        operator_post(
            write_app,
            cookie,
            "/admin/community/admit",
            "smoke-csrf",
            {"uri": submission["uri"], "cid": submission["cid"]},
        )

        for did, document in documents.items():
            try:
                extract_verification_key(document)
                extract_pds_endpoint(
                    Resolver({did: document}, {did: origins[did]}).resolve(did)
                )
            except Exception as exc:
                raise RuntimeError(
                    "synthetic DID document is not proof-usable: "
                    + json.dumps({
                        "did": did,
                        "keys": sorted(document),
                        "verificationTypes": [item.get("type") for item in document.get("verificationMethod", []) if isinstance(item, dict)],
                        "verificationFields": [sorted(item) for item in document.get("verificationMethod", []) if isinstance(item, dict)],
                        "verificationIds": [item.get("id") for item in document.get("verificationMethod", []) if isinstance(item, dict)],
                        "serviceTypes": [item.get("type") for item in document.get("service", []) if isinstance(item, dict)],
                        "error": type(exc).__name__,
                    }, sort_keys=True)
                ) from exc
        resolver = Resolver(documents, origins)
        getter = UrllibHttpGetter(timeout_seconds=10)
        verifier_args = {"did_resolver": resolver, "pds_client": PdsClient(getter)}
        store = ObserverStore(args.root / "observer.sqlite3", community_did=community["did"], administrator_did=operator["did"])
        participant_claims, cursor = claims(
            args.participant_pds_origin,
            participant.reference,
            ("zone.neutral.community.submit",),
            0,
        )
        community_claims, cursor = claims(args.pds_origin, community["did"], (
            "zone.neutral.community.memberAction",
            "zone.neutral.community.admission",
            "zone.neutral.community.replyPolicy",
        ), cursor)
        admission_event_key = None
        admission_reference = None
        admission_cid = None
        verdicts = []
        for claim in participant_claims + community_claims:
            for verified in VerifyingEventSource(One(claim), **verifier_args).verify_delivery(claim):
                ingested = store.ingest(verified)
                envelope = verified.raw_envelope
                verdicts.append({
                    "collection": envelope.get("collection") if isinstance(envelope, Mapping) else None,
                    "rev": envelope.get("rev") if isinstance(envelope, Mapping) else None,
                    "outcome": verified.verification_outcome,
                    "method": verified.verification_method,
                    "hasEvidence": verified.evidence_hash is not None,
                })
                if isinstance(envelope, Mapping) and envelope.get("collection") == "zone.neutral.community.admission" and verified.verification_outcome == "verified":
                    admission_event_key = ingested.key
                    admission_reference = (
                        f"at://{community['did']}/zone.neutral.community.admission/"
                        f"{envelope['rkey']}"
                    )
                    admission_cid = envelope.get("cid")
        subject = RecordRef(uri=post_ref["uri"], cid=post_ref["cid"])
        if admission_event_key is None:
            raise RuntimeError("verified admission event was not produced: " + json.dumps(verdicts, sort_keys=True))
        store.record_subject_observation(
            VerifiedSubjectResolver(**verifier_args).resolve_exact(subject),
            triggering_event_variant_key=admission_event_key,
        )

        query = ProjectionQuery(store, slug="isolated")
        web = WebApp(query, community_did=community["did"], slug="isolated", stale_threshold_seconds=0)
        server = make_server(web, host="127.0.0.1", port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_address[1]}"
            projection = HttpCommunityProjectionClient(origin, community["did"])
            app = OperatorApp(
                sessions=codec,
                operator_dids=frozenset({operator["did"]}),
                pds=pds,
                community=authority,
                projection=projection,
            )
            before = app.handle("GET", "/community/").body.decode()
            if "real isolated Phlogiston community post" not in before:
                raise RuntimeError("Phlogiston did not render admitted post")
            if not isinstance(admission_reference, str) or not isinstance(admission_cid, str):
                raise RuntimeError("verified admission omitted its exact reference")
            removal_fields = {
                "path": "/admin/community/remove",
                "uri": admission_reference,
                "cid": admission_cid,
                "reason": "isolated removal",
            }
            review = operator_post(
                app,
                cookie,
                removal_fields["path"],
                "smoke-csrf",
                {key: value for key, value in removal_fields.items() if key != "path"},
            )
            confirm_effect(app, cookie, "smoke-csrf", review, removal_fields)
            removal_claims, cursor = claims(args.pds_origin, community["did"], ("zone.neutral.community.modAction",), cursor)
            removal_reference = None
            for claim in removal_claims:
                for verified in VerifyingEventSource(One(claim), **verifier_args).verify_delivery(claim):
                    store.ingest(verified)
                    envelope = verified.raw_envelope
                    if isinstance(envelope, Mapping):
                        removal_reference = (
                            f"at://{community['did']}/zone.neutral.community.modAction/"
                            f"{envelope['rkey']}"
                        )
            after = app.handle("GET", "/community/").body.decode()
            if "real isolated Phlogiston community post" in after:
                raise RuntimeError("removed post remained visible")
            receipt = {
                "schema": "phlogiston.community-slice.v1",
                "result": "passed",
                "pdsImage": args.pds_image,
                "pdsCount": 2,
                "multiPds": origins[community["did"]] != origins[participant.reference],
                "phlogistonCommit": os.environ.get("PHLOGISTON_SOURCE_COMMIT"),
                "communityCommit": os.environ.get("COMMUNITY_SOURCE_COMMIT"),
                "communityDid": community["did"],
                "participantDid": participant.reference,
                "membership": projection.members(),
                "admission": admission_reference,
                "removal": removal_reference,
                "renderedBeforeRemoval": True,
                "hiddenAfterRemoval": True,
                "observerHealth": projection.health(),
                "externalNetwork": False,
            }
            args.receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    finally:
        daemon.terminate()
        try:
            daemon.wait(timeout=5)
        except subprocess.TimeoutExpired:
            daemon.kill()
            daemon.wait()
        did_directory.close()


if __name__ == "__main__":
    main()
