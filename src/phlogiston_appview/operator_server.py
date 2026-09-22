"""Minimal HTTP entry point for the authenticated operator surface."""

from __future__ import annotations

import argparse
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .community import HttpCommunityProjectionClient, UnixCommunityAuthorityClient
from .operator import OperatorApp, SessionCodec, XrpcPdsAdminClient


def _secret(path: str, name: str) -> bytes:
    target = Path(path)
    mode = target.stat().st_mode & 0o777
    if mode & 0o077:
        raise RuntimeError(f"{name} file permissions are too broad")
    value = target.read_bytes().strip()
    if len(value) < 32:
        raise RuntimeError(f"{name} is too short")
    return value


def build_app() -> OperatorApp:
    session_key = _secret(os.environ["PHLOGISTON_SESSION_KEY_FILE"], "session key")
    admin_password = _secret(os.environ["PHLOGISTON_PDS_ADMIN_PASSWORD_FILE"], "PDS admin password").decode()
    operators = frozenset(value.strip() for value in os.environ["PHLOGISTON_OPERATOR_DIDS"].split(",") if value.strip())
    return OperatorApp(
        sessions=SessionCodec(session_key),
        operator_dids=operators,
        pds=XrpcPdsAdminClient(os.environ["PHLOGISTON_PDS_ORIGIN"], admin_password),
        community=UnixCommunityAuthorityClient(os.environ["PHLOGISTON_COMMUNITYD_SOCKET"]),
        projection=HttpCommunityProjectionClient(
            os.environ["PHLOGISTON_COMMUNITYWATCH_ORIGIN"],
            os.environ["PHLOGISTON_COMMUNITY_DID"],
        ),
    )


def serve(app: OperatorApp, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        server_version = "PhlogistonOperator/0.1"

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch(b"")

        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length < 0 or length > 32 * 1024:
                self.send_error(413)
                return
            self._dispatch(self.rfile.read(length))

        def _dispatch(self, body: bytes) -> None:
            response = app.handle(
                self.command,
                self.path,
                cookie=self.headers.get("Cookie", ""),
                body=body,
            )
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            for key, value in response.headers:
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(response.body)

        def log_message(self, format: str, *args: object) -> None:
            # Deliberately omit query/body/cookie data. The operator surface has
            # no query routes; status code and peer address are sufficient.
            print(f"operator-http peer={self.client_address[0]} status={args[1] if len(args) > 1 else 'unknown'}")

    ThreadingHTTPServer((host, port), Handler).serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    issue = sub.add_parser("issue-session")
    issue.add_argument("--did", required=True)
    run = sub.add_parser("serve")
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8091)
    args = parser.parse_args()
    app = build_app()
    if args.command == "issue-session":
        if args.did not in app.operator_dids:
            raise SystemExit("DID is not an enrolled operator")
        print(app.sessions.issue(args.did))
        return
    serve(app, args.host, args.port)


if __name__ == "__main__":
    main()

