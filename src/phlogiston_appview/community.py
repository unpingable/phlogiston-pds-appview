"""Adapters to communityd authority and communitywatch projection."""

from __future__ import annotations

import json
import socket
import urllib.parse
import urllib.request
from collections.abc import Mapping

from .operator import EffectResult


class UnixCommunityAuthorityClient:
    def __init__(self, socket_path: str, *, timeout: float = 10.0) -> None:
        self.socket_path = socket_path
        self.timeout = timeout

    def membership(self, *, operation_id: str, operator_did: str, subject_did: str, action: str, reason: str | None) -> EffectResult:
        if action not in {"add", "remove"}:
            raise ValueError("membership action must be add or remove")
        result = self._request({"operationId": operation_id, "action": f"member_{action}", "authenticatedDid": operator_did, "subjectDid": subject_did, "reason": reason})
        return _effect("membership_" + action, result)

    def admit(self, *, operation_id: str, operator_did: str, uri: str, cid: str) -> EffectResult:
        result = self._request({"operationId": operation_id, "action": "root_admit", "authenticatedDid": operator_did, "target": {"uri": uri, "cid": cid}})
        return _effect("admit", result)

    def remove(self, *, operation_id: str, operator_did: str, uri: str, cid: str, reason: str) -> EffectResult:
        result = self._request({"operationId": operation_id, "action": "root_remove", "authenticatedDid": operator_did, "target": {"uri": uri, "cid": cid}, "reason": reason})
        return _effect("remove", result)

    def _request(self, value: Mapping[str, object]) -> Mapping[str, object]:
        encoded = json.dumps(value, separators=(",", ":")).encode() + b"\n"
        if len(encoded) > 64 * 1024:
            raise ValueError("community authority request exceeds limit")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(self.timeout)
            connection.connect(self.socket_path)
            connection.sendall(encoded)
            chunks = bytearray()
            while b"\n" not in chunks and len(chunks) <= 64 * 1024:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                chunks.extend(chunk)
        if b"\n" not in chunks or len(chunks) > 64 * 1024:
            raise RuntimeError("communityd returned an invalid frame")
        response = json.loads(bytes(chunks).split(b"\n", 1)[0])
        if not isinstance(response, dict) or not response.get("ok"):
            code = response.get("error", "authority_unavailable") if isinstance(response, dict) else "authority_unavailable"
            raise RuntimeError(f"communityd refused the operation ({code})")
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("communityd omitted the authoritative result")
        return result


class HttpCommunityProjectionClient:
    def __init__(self, origin: str, community_did: str, *, opener=urllib.request.urlopen) -> None:
        self.origin = origin.rstrip("/")
        self.community_did = community_did
        self._open = opener

    def health(self) -> Mapping[str, object]:
        return self._get("/health")

    def moderation_queue(self) -> Mapping[str, object]:
        return self._get(f"/api/v0/communities/{urllib.parse.quote(self.community_did, safe='')}/moderation-queue")

    def members(self) -> Mapping[str, object]:
        return self._get(f"/api/v0/communities/{urllib.parse.quote(self.community_did, safe='')}/members")

    def discussions(self) -> Mapping[str, object]:
        return self._get(f"/api/v0/communities/{urllib.parse.quote(self.community_did, safe='')}/discussions")

    def _get(self, path: str) -> Mapping[str, object]:
        request = urllib.request.Request(self.origin + path, headers={"Accept": "application/json"})
        with self._open(request, timeout=10) as response:
            raw = response.read(256 * 1024 + 1)
        if len(raw) > 256 * 1024:
            raise RuntimeError("community projection response exceeds limit")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise RuntimeError("community projection returned a non-object")
        return value


def _effect(operation: str, result: Mapping[str, object]) -> EffectResult:
    record = result.get("record") or result.get("admission") or result.get("membership")
    reference = None
    if isinstance(record, dict) and isinstance(record.get("uri"), str):
        reference = record["uri"]
    disposition = str(result.get("operation", "committed"))
    return EffectResult("community", operation, disposition, reference=reference)
