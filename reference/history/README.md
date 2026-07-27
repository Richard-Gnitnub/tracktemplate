# Frozen Evidence History

Historical inventories, foundations, closeouts, dated audits and benchmark
reports are immutable evidence, not live project documentation. Their accepted
locations and hashes are recorded in
[frozen-records.json](frozen-records.json).

The records remain at their existing paths for now. This avoids rewriting
accepted files, breaking their internal links or changing hashes merely to
match a preferred directory layout. A future physical archive migration must be
a separate accepted change that updates links and the manifest deliberately.

Routine work must not align historical prose with the current implementation.
Validation checks only that frozen records:

- still exist;
- retain their accepted hashes and status;
- keep required internal links resolvable; and
- are changed only to correct a demonstrated factual error or an explicitly
  accepted scope change.

New phase closeouts will use `reference/history/phase-closeouts/`. Dated audits,
benchmarks and retired contracts can move under their corresponding history
categories during a later controlled migration. Live records always remain at
[reference/current/](../current/).
