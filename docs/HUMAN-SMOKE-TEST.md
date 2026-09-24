# First human-use smoke test

Status: prepared; every effect still requires the authority named in the
synthetic activation packet.

1. In a private browser window, open `https://phlogiston.app/`. Confirm the
   page says it is the account and status page, not the place to post; that
   signing in only confirms the account and taking part happens at the
   community site; that a "Go to the community" link precedes the sign-in form
   when `PHLOGISTON_COMMUNITY_URL` is configured (and is absent otherwise); and
   that it exposes no admin or mutation control.
2. Enter the one designated controlled account handle and complete its normal
   PDS OAuth flow. Verify the callback hostname and requested `atproto` scope.
3. On `/me`, confirm the stable DID and an authenticated eight-hour
   Phlogiston session. Before any community operation, no "Community standing"
   row appears and the page does not mention membership; the "Technical
   details" disclosure shows the community projection as `fresh
   (no_authority_record)`.
4. A separately authenticated community operator performs the intent-bound
   membership operation outside the user browser. Refresh `/me`; verify the
   projected active state and authority reference.
5. Visit `/community/`. Confirm it says it is a read-only mirror and that
   posting happens at the community site, with a link to the community home
   when configured. Exercise only the already-qualified ordinary content
   lifecycle from the activation packet and verify each admitted post shows its
   text first, the author DID on a secondary line, and "In the community"
   rather than a raw status token; the projection generation appears only
   under "Technical details".
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
