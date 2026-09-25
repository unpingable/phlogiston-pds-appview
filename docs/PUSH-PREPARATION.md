# Push preparation — phlogiston `main`

Status: **prepared action, not executed.** No push has been made. The push
is independent of every host action in
[Q2-ACTIVATION-RUNBOOK.md](Q2-ACTIVATION-RUNBOOK.md): the host runs the
phlogiston release from an immutable, hash-verified archive, never from the
remote.

## The action

| Field | Value |
| --- | --- |
| Remote | `origin` (`git remote get-url origin` from the worktree) |
| Branch | `main` |
| Expected old remote tip | `cbc6f88deb4a0d2610009f5a2bb29fe5ae0ad0f2` (`origin/main` as fetched 2026-09-25) |
| New tip | the tip of `main` at push time: the commit that carries this document and `PHASE-2-FREEZE.md` (its parent is `35e6545`); confirm with `git rev-parse main` and compare with the tranche closeout at the workspace root |
| Commit count `origin/main..main` | 38 at the freeze base `6670e17`; 42 at this lane's tip `campaign/phase2-freeze` before its merge; 45 at the frozen tip |
| Worktree holding `main` | `/data/git/atproto-nutrition/.worktrees/phlogiston-community-integration-20260922` |

Preconditions, checked immediately before the push:

```sh
cd /data/git/atproto-nutrition/.worktrees/phlogiston-community-integration-20260922
git status --porcelain            # empty (web/node_modules is ignored; a symlink there must not be added)
git fetch origin
git rev-parse origin/main          # must print cbc6f88deb4a0d2610009f5a2bb29fe5ae0ad0f2
git merge-base --is-ancestor origin/main main && echo fast-forward
git rev-parse main                 # must equal the tip named in the tranche closeout
PYTHONPATH=src python3 -m pytest -q
( cd web && ./node_modules/.bin/tsc --noEmit && node --import tsx --test src/*.test.ts )
```

The exact command, from that worktree:

```sh
git push origin main
```

Read-back, immediately after:

```sh
git fetch origin
git rev-parse origin/main          # must equal the pushed tip
git log --oneline origin/main -3
git status -sb                     # "## main...origin/main" with no ahead/behind
```

## If the push is rejected

A rejection means `origin/main` moved past `cbc6f88` since the freeze. Do
not resolve it here. `git push --force-with-lease` and `--force` are **not
allowed**: they would discard whatever was pushed elsewhere. Instead:

1. `git fetch origin && git log --oneline main..origin/main` to see what
   arrived;
2. report the new remote tip and that listing to the owner and stop;
3. the owner decides whether to rebase or merge; this document is then
   redone with the new expected old tip.

There is no rollback for a completed push other than pushing a further
commit; nothing in the branch is expected to need one.

## Secrets and garbage scan

Run 2026-09-25 over `origin/main..HEAD` at this lane's tip (42 commits):

```sh
git log -p origin/main..main | grep -n -i -E 'password|secret|token|BEGIN (RSA|EC|OPENSSH) PRIVATE|jwt'
```

218 matching lines; 188 in the 38 pre-existing commits, 30 in this lane's
four. Zero private-key blocks, zero JWT-shaped literals, zero populated
credential values. Every hit falls into one of the classes below; files are
listed with their hit counts.

| Class | Files (hits) | What the hits are |
| --- | --- | --- |
| Code identifiers (no values) | `src/phlogiston_appview/operator.py` (21), `web/src/storage.ts` (16), `web/src/server.ts` (12), `web/src/oauth.ts` (6), `src/phlogiston_appview/operator_server.py` (4), `deploy/production/preflight.py` (3), `web/src/config.ts` (2), `qualification/production/oauth-continuity.ts` (6), `qualification/production/lib.sh` (1) | names such as `token`, `SecretJsonFileStore`, `secret_custody_receipt`, `admin_password` parameters, `parsed.password` URL checks, `grant_types: refresh_token`, `dpop_bound_access_tokens`; comments stating that tokens are discarded or never printed |
| Test fixtures (synthetic, isolated) | `tests/test_operator.py` (16), `web/src/server.test.ts` (12), `web/src/storage.test.ts` (9), `web/src/oauth.test.ts` (1), `tests/test_production_deploy.py` (3), `tests/test_production_verification.py` (3), `qualification/community_slice.py` (17), `qualification/run-community-slice.sh` (6) | `phlogiston_session=${issued.token}` runtime-random cookies; literal strings `SECRET-A`, `SECRET-R`, `admin-secret`, `must-not-render`; the isolated-PDS harness's `synthetic-*-password` and `PDS_JWT_SECRET=synthetic-*-jwt-not-production` values for throwaway containers on a private Docker network |
| Placeholders | `deploy/production/phlogiston-pds.env.example` (3: `PDS_JWT_SECRET`, `PDS_DPOP_SECRET`, `PDS_ADMIN_PASSWORD` all `=SET_OWNER_ONLY_AT_ACTIVATION`), `deploy/production/secret-custody.json.example` (4), `deploy/production/deployment.json.example` (1), `deploy/production/communityd.toml.example` (2: `credential_ref = "env:..."`) | `SET_*` sentinels that `preflight.py` refuses; schema names; a credential *reference*, not a credential |
| Documentation prose | `docs/SECRET-CUSTODY.md` (17), `docs/ACTIVATION-READINESS.md` (10), `docs/PRE-Q2-ACTIVATION-READINESS.md` (6), `docs/OPERATOR-SURFACE.md` (5), `docs/DEPLOYABLE-ARTIFACT-QUALIFICATION.md` (3), `docs/OAUTH-SESSION-ENROLLMENT.md` (3), `docs/HUMAN-SMOKE-TEST.md` (2), `docs/PRODUCTION-READINESS-QUALIFICATION.md` (1), `docs/INTEGRATED-RECOVERY.md` (1), `docs/COMMUNITY-INTEGRATION.md` (1), `docs/PRODUCTION-VERIFICATION.md` (5), `docs/Q2-ACTIVATION-RUNBOOK.md` (2), `docs/PHASE-2-PARTICIPANT-PACKET.md` (1), `deploy/production/Caddyfile.fragment` (1, a comment) | custody maps and readiness text that *say* no secret is present, describe where secrets live on the host, or tell the operator not to enter one |
| Credential hand-off code (no values) | `qualification/production/verify-indexing-lag.sh` (10), `qualification/production/verify-oauth-continuity.sh` (1) | reads an app password from a 0600 file named by `PHLOGISTON_VERIFY_APP_PASSWORD_FILE`, passes the access token through the environment, `unset`s it, never records it |

Garbage check over the same range: no `.env`, `*.pem`, `*.key`,
`*.sqlite3`, receipt or log files are added (`git diff --stat
origin/main..HEAD` lists only source, docs, deploy templates, tests, and the
qualification evidence JSON already reviewed in earlier tranches);
`web/node_modules` is a local symlink, untracked and never added.

Verdict: nothing in `origin/main..HEAD` is a secret or key. Rerun the
scan once more on the final `main` tip before pushing; this document's own
commit adds the classification words above and nothing else.
