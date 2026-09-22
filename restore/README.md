# Restore preparation

Restore accepts only an exact two-member regular-file archive, writes into a
new run-owned child below an existing canonical target root, and verifies the
input snapshot, renderer source, receipt schema, member list, and member hashes.
It rejects missing, extra, symlink, duplicate-destination, and tampered inputs.
It is not PDS recovery and does not establish recovery of any live identity or
social data.
