"""Reproduce this source-served candidate from its exact public Git commit."""
import gzip
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tarfile

REVISION = "860fcae4b9a97ee47982c487e7d9bc6659fefe39"
PREFIX = "apps/community-live/"


def package(repository: str) -> tuple[bytes, dict[str, str]]:
    names = subprocess.check_output(
        ["git", "-C", repository, "ls-tree", "-r", "--name-only", REVISION, PREFIX]
    ).decode().splitlines()
    output = io.BytesIO()
    files = {}
    with tarfile.open(fileobj=output, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for path in sorted(names):
            content = subprocess.check_output(["git", "-C", repository, "show", f"{REVISION}:{path}"])
            name = path.removeprefix(PREFIX)
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            entry.mode = 0o644
            entry.mtime = 0
            archive.addfile(entry, io.BytesIO(content))
            files[name] = hashlib.sha256(content).hexdigest()
    return gzip.compress(output.getvalue(), mtime=0), files


if __name__ == "__main__":
    repository, destination = sys.argv[1:]
    body, files = package(repository)
    path = pathlib.Path(destination)
    if path.exists() and path.read_bytes() != body:
        raise SystemExit("refusing to replace different candidate bytes")
    path.write_bytes(body)
    print(json.dumps({"source_revision": REVISION, "archive_sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "files": files}, indent=2))
