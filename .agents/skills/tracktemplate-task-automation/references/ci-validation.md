# TrackTemplate CI validation automation

Read this reference only for CI, clean-checkout or complete standalone-matrix
automation. `reference/VALIDATION.md` remains the command and evidence owner.

## Evidence profiles

| Profile | May prove | Must not claim |
| --- | --- | --- |
| Clean-checkout CI | Tracked source parsing, deterministic standalone contracts, dependency direction, frozen tracked hashes, links and current-record consistency | Presence or hash of ignored local evidence, backup/restore state, FreeCAD/GUI behaviour, branch authority or release acceptance |
| Local workstation | The same tracked matrix plus explicitly selected ignored-asset and checkpoint checks | Remote GitHub execution, independent backup completion, GUI or production-output acceptance |
| Qualified host/GUI | The specifically selected FreeCAD, GUI or output boundary | Unrelated standalone, remote-CI, release or owner-decision status |

Keep the profiles explicit. A clean checkout should test that a requested
missing local asset fails closed; it should not pretend the ignored asset is
present. The workstation profile may require the real asset and accepted hash.

## Repair loop

1. Resolve the exact repository, commit, workflow run, job and failing step.
2. Preserve the raw command, profile, output and first relevant failure.
3. Classify the failure under `reference/TESTING_POLICY.md` before editing.
4. Reproduce it with the matching profile or a disposable clean checkout.
5. Repair only the classified product, test, fixture, harness or environment
   boundary.
6. Rerun the original proof, then the complete affected profile. The standalone
   runner must execute every validator and report all failures.
7. Review the complete diff and keep commit/push/re-run authority explicit.
8. After an authorised push, inspect the run for the exact commit SHA. Preserve
   logs and repeat the classification loop if it fails.

## CI gotchas

- A local green matrix does not prove that GitHub Actions ran.
- An ignored archive or backup destination cannot appear in a normal checkout.
- A successful workflow is technical evidence, not branch protection, release
  authority or product acceptance.
- Stopping at the first failed validator hides later failures and creates
  unnecessary diagnostic cycles.
- Generic GitHub skills may retrieve runs and logs; TrackTemplate validation
  policy still owns failure classification and evidence meaning.
