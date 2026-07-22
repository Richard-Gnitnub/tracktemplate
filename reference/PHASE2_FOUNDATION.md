# Phase 2 Modular Foundation Evidence

Status: **complete and accepted by the project owner on 2026-07-22. Phase 3 is
current; no Phase 3 calculation movement has started.**

## Bounded result

The accepted Phase 2 package/loading foundation now exists. No transition
calculation has moved, no B14/B15 caller is routed, and neither immutable macro
changed. `tracktemplate/domain/alignment.py` is only the selected Phase 3
destination; its public export set is empty.

The small `TrackTemplate.FCMacro` composition root locates the adjacent
authoritative package from its own file path, verifies that exact package was
loaded, reads the accepted runtime contract, and stops before composition when
the host is unqualified. On the qualified host it reports a JSON-compatible
B16 foundation result and performs no FreeCAD document mutation.

## Authoritative boundaries

| Concept | Authoritative implementation and narrow interface | Dependency direction | Evidence and retirement gate |
| --- | --- | --- | --- |
| Development checkpoint | `tracktemplate.DEVELOPMENT_CHECKPOINT`, re-exported by `tracktemplate.api` | Façade to package root | Standalone and FreeCAD foundation validators; public versioning remains Phase 10/11 work |
| Runtime observation and qualification | `tracktemplate.bootstrap.runtime_record`, `evaluate_runtime` and `require_qualified_runtime` | Standard library plus optional host inspection inside call boundaries; never imported by domain | The existing probe is now a thin CLI over one authoritative runtime implementation; the exact matrix remains owned by the Phase 1 compatibility contract and Phase 10 requalification |
| Selected domain destination | `tracktemplate.domain.alignment`, with no supported exports in Phase 2 | Standard library/domain inward only | Structural and isolated-import guards; Phase 3 owns mechanical calculation movement and exact parity |
| Migration façade | `tracktemplate.api`, currently exporting only the checkpoint identity | Façade may point inward to domain/package contracts | Phase 3 adds the three selected functions together; Phase 10 retires migration-only compatibility surfaces not retained by the Workbench |
| Development composition root | `TrackTemplate.FCMacro.run_macro` | Launcher to façade/bootstrap | FreeCAD loading and zero-document-mutation smoke; Phase 10 reduces or retires the compatibility launcher |
| Structural enforcement | `tools/modular_structure.py` | Development-only AST inspection; no runtime dependency | Deterministic module/export/import report, cycle, layer, forbidden-domain-import and warning gates; retain through release qualification |
| Legacy/new evidence comparison | `tools/semantic_compare.py.compare_structures` | Development-only standard library | Exact types, structured values, ordering, stable identities, diagnostics and output metadata are directly tested; retire only after Phase 11 no longer needs a legacy comparison path |

The record/type choice for this foundation is deliberately narrow:
JSON-compatible dictionaries, lists and scalar values cross the bootstrap and
comparison evidence boundaries. It does not choose the Phase 4 canonical
persistence schema or introduce a third-party runtime dependency.

## Loading route

1. Keep `TrackTemplate.FCMacro`, `tracktemplate/` and `reference/contracts/`
   under the same development checkout root.
2. Launch `TrackTemplate.FCMacro` from that location in FreeCAD.
3. The launcher prepends its own root, rejects a differently resolved
   `tracktemplate` package, and consumes
   `reference/contracts/phase1-compatibility.json`.
4. An absent, invalid or unqualified contract/runtime emits a structured
   blocked result and raises before any composition or document mutation.
5. The exact qualified FreeCAD 1.1.1 Flatpak profile loads the package and
   emits `TRACKTEMPLATE_B16_FOUNDATION=...`; it does not start a workflow.

This is a development loading route, not the Phase 10 Addon installation or
catalogue design.

## Deterministic controls

Run:

```bash
.venv/bin/python tools/modular_structure.py
.venv/bin/python tests/validate_phase2_foundation.py
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase2_foundation.py
```

The structure report is generated rather than committed as a duplicated
snapshot. Its validator requires exactly the five package modules justified by
this foundation, an acyclic permitted import graph, no platform/third-party
domain import, no import-time patch/service warning, and the small launcher
boundary. A disposable synthetic package proves the analyser itself detects a
cycle, prohibited reverse edge and forbidden FreeCAD domain import; mutating
only a generated report is not treated as sufficient detector evidence.

## Validation evidence

Observed on 2026-07-22 from the repository root:

| Check | Result |
| --- | --- |
| Parse B14, B15 and `TrackTemplate.FCMacro` | Passed |
| Every `tests/validate_*.py` check | 29/29 passed |
| Isolated standalone domain/API import with FreeCAD, Part, Qt and pivy blocked | Passed; no forbidden import attempted |
| Standalone B16 launch | Expected fail-closed result: `blocked-before-composition`, `not-freecad-runtime`, no document mutation |
| Deterministic modular-structure report | Five justified modules, two permitted internal edges, no cycle, prohibited edge, forbidden domain import or warning |
| Qualified FreeCAD runtime probe | `linux-x86_64-flatpak-freecad-1.1.1` matched exactly |
| B15 FreeCAD 1.1 headless smoke | `B15 FreeCAD 1.1 headless smoke test passed` |
| B16 FreeCAD foundation smoke | `foundation-loaded-not-routed`; `Phase 2 FreeCAD foundation smoke test passed`; document state unchanged |

The immutable source fingerprints remain:

- B14: `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`
- B15: `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`

No real-GUI workflow run is claimed: this phase adds no user-visible editing,
selection, persistence or export behaviour. Real-GUI evidence remains at its
named later gates.

## Maintainability and P1-X10 review

- Runtime probing and launcher qualification share one implementation; the CLI
  no longer maintains a second evaluator.
- The package contains only root, façade, bootstrap and the selected domain
  destination. No speculative application, adapter, presentation, UI,
  compatibility or chair tree was created.
- Detailed Phase 1 compatibility and transition facts remain in their owning
  contracts and are linked here rather than copied into another manifest.
- Generated structure output is not committed, preventing a stale duplicate;
  the tool and executable assertions are retained because each closes a named
  Phase 2 dependency/cycle/import gap.
- The façade, launcher and legacy/new comparison path have explicit later
  owners and retirement gates. None is treated as permanent merely because it
  passes today.

This satisfies the Phase 2 P1-X10 maintainability/reuse review.

## Owner acceptance

The project owner explicitly accepted this bounded Phase 2 foundation and its
recorded exit evidence on 2026-07-22:

> ok, accepted

That acceptance closes Phase 2 and makes Phase 3 current. It authorises only
the parity-controlled transition-length vertical slice described by the
accepted transition contract. It does not itself move a calculation or caller,
retire a legacy path, configure an independent backup, or waive any migration,
GUI, performance, provenance, chair, rights, terminology, persistence, export
or later release gate.
