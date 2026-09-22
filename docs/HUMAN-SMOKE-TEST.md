# First human-use smoke test

Status: prepared; every effect still requires the authority named in the
synthetic activation packet.

1. In a private browser window, open `https://phlogiston.app/`. Confirm the
   page says authentication does not create membership and exposes no admin or
   mutation control.
2. Enter the one designated controlled account handle and complete its normal
   PDS OAuth flow. Verify the callback hostname and requested `atproto` scope.
3. On `/me`, confirm the stable DID and an authenticated eight-hour
   Phlogiston session. Before any community operation, membership must be
   `absent`, not active.
4. A separately authenticated community operator performs the intent-bound
   membership operation outside the user browser. Refresh `/me`; verify the
   projected active state and authority reference.
5. Visit `/community/`. Exercise only the already-qualified ordinary content
   lifecycle from the activation packet and verify admitted content renders in
   plain application language.
6. After separately authorized removal, refresh the public page and confirm
   the removed item stays hidden after observer restart/reconciliation.
7. Sign out. Confirm the local cookie expires but membership authority does
   not change. Sign back in and verify the same DID and existing authority
   standing.
8. Disconnect ATProto access. Confirm local use is refused on the next `/me`
   request and raw infrastructure errors, credentials, paths and tokens never
   appear.

The current application is intentionally small. It supports login, identity /
membership explanation and public community rendering. It does not expose the
qualified operator surface, general posting UI, account creation, PDS admin,
or production community mutations. Those absences are not disguised as user
features.
