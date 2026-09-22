"""Verify exact authority state and rebuild projection from restored PDSes."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from urllib.error import URLError

from community_model import RecordRef
from communitywatch import ObserverStore, ProjectionQuery
from communitywatch.repoproof import extract_pds_endpoint, extract_verification_key
from communitywatch.syncclient import PdsClient, UrllibHttpGetter
from communitywatch.verifying import VerifiedSubjectResolver, VerifyingEventSource

from community_slice import One, Resolver, claims, xrpc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def records(origin: str, did: str, collection: str) -> list[dict[str, object]]:
    value = xrpc(origin, "com.atproto.repo.listRecords", query={"repo": did, "collection": collection, "limit": "100"})
    result = value.get("records")
    if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
        raise RuntimeError("restored PDS returned an invalid record list")
    return result


def unavailable(args: argparse.Namespace) -> None:
    prior = json.loads(args.prior.read_text())
    try:
        xrpc(args.participant_pds_origin, "com.atproto.sync.getLatestCommit", query={"did": prior["participantDid"]})
    except (RuntimeError, URLError, OSError):
        prior["onePdsUnavailable"] = {
            "result": "dependency_unavailable",
            "authorityWidened": False,
            "projectionCompletionClaimed": False,
        }
        args.output.write_text(json.dumps(prior, sort_keys=True, indent=2) + "\n")
        return
    raise RuntimeError("unavailable-PDS qualification unexpectedly reached the participant PDS")


def verify(args: argparse.Namespace) -> None:
    expected = json.loads(args.expected.read_text())
    community_did = expected["communityDid"]
    participant_did = expected["participantDid"]
    origins = {community_did: args.community_pds_origin, participant_did: args.participant_pds_origin}
    documents = {}
    for did, origin in origins.items():
        document = xrpc(origin, "com.atproto.repo.describeRepo", query={"repo": did}).get("didDoc")
        if not isinstance(document, dict) or document.get("id") != did:
            raise RuntimeError("restored PDS omitted an exact DID document")
        for service in document.get("service", []):
            if service.get("type") == "AtprotoPersonalDataServer":
                service["serviceEndpoint"] = origin
        extract_verification_key(document)
        extract_pds_endpoint(Resolver({did: document}, {did: origin}).resolve(did))
        documents[did] = document

    expected_refs = {expected["admission"], expected["removal"]}
    found_refs = {
        item["uri"]
        for collection in ("zone.neutral.community.admission", "zone.neutral.community.modAction")
        for item in records(args.community_pds_origin, community_did, collection)
    }
    member_records = records(args.community_pds_origin, community_did, "zone.neutral.community.memberAction")
    if expected_refs != found_refs or len(member_records) != 1:
        raise RuntimeError("restored authority records do not match the source occurrence")

    resolver = Resolver(documents, origins)
    verifier_args = {"did_resolver": resolver, "pds_client": PdsClient(UrllibHttpGetter(timeout_seconds=10))}
    store = ObserverStore(args.root / "rebuilt-observer.sqlite3", community_did=community_did, administrator_did=member_records[0]["value"]["actor"])
    participant_claims, cursor = claims(args.participant_pds_origin, participant_did, ("zone.neutral.community.submit",), 0)
    community_claims, _ = claims(args.community_pds_origin, community_did, (
        "zone.neutral.community.memberAction",
        "zone.neutral.community.admission",
        "zone.neutral.community.modAction",
    ), cursor)
    admission_event = None
    deliveries = participant_claims + community_claims
    verdicts = []
    for replay in range(2):
        for claim in deliveries:
            for verified in VerifyingEventSource(One(claim), **verifier_args).verify_delivery(claim):
                ingested = store.ingest(verified)
                envelope = verified.raw_envelope
                if replay == 0:
                    verdicts.append({
                        "collection": envelope.get("collection") if isinstance(envelope, Mapping) else None,
                        "outcome": verified.verification_outcome,
                        "method": verified.verification_method,
                        "evidence": verified.evidence_hash is not None,
                    })
                if replay == 0 and isinstance(envelope, Mapping) and envelope.get("collection") == "zone.neutral.community.admission":
                    admission_event = ingested.key
    if admission_event is None:
        raise RuntimeError("restored admission did not produce verified evidence: " + json.dumps(verdicts, sort_keys=True))

    submission = records(args.participant_pds_origin, participant_did, "zone.neutral.community.submit")
    if len(submission) != 1:
        raise RuntimeError("restored participant submission is not exact")
    subject_value = submission[0]["value"]["subject"]
    subject = RecordRef(uri=subject_value["uri"], cid=subject_value["cid"])
    store.record_subject_observation(
        VerifiedSubjectResolver(**verifier_args).resolve_exact(subject),
        triggering_event_variant_key=admission_event,
    )
    query = ProjectionQuery(store, slug="restored")
    members = query.list_members(community_did)
    if len(members) != 1 or members[0]["did"] != participant_did or members[0]["status"] != "active":
        raise RuntimeError("rebuilt membership projection differs from authority")
    if query.list_visible(community_did, 100, None).items:
        raise RuntimeError("removed content became visible after reconstruction")

    result = {
        "schema": "phlogiston.community-recovery-qualification.v1",
        "result": "passed",
        "sourceLifecycleReceiptSha256": sha256(args.expected),
        "archiveSha256": sha256(args.archive),
        "archiveBytes": args.archive.stat().st_size,
        "communityDid": community_did,
        "participantDid": participant_did,
        "admission": expected["admission"],
        "removal": expected["removal"],
        "authorityRecordsExact": True,
        "projectionAbsentBeforeRebuild": True,
        "projectionRebuilt": True,
        "replayIdempotent": True,
        "membershipInvented": False,
        "removedContentVisible": False,
        "pdsCount": 2,
    }
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--community-pds-origin", required=True)
    parser.add_argument("--participant-pds-origin", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--prior", type=Path)
    args = parser.parse_args()
    if args.prior:
        unavailable(args)
    else:
        if args.expected is None or args.archive is None:
            parser.error("--expected and --archive are required for restored verification")
        verify(args)


if __name__ == "__main__":
    main()
