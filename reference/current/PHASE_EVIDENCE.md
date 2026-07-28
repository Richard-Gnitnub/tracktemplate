# Phase 5 Lightweight Editing Prototype and Renderer Decision Evidence

Status: **Not started — awaiting an explicit project-owner opening decision.**
Phase 4 closed with all six revised exits accepted on 2026-07-28; its frozen
record is [PHASE4_CLOSEOUT.md](../history/phase-closeouts/PHASE4_CLOSEOUT.md).

This fixed live path is prepared for the next phase. It records no Phase 5
implementation evidence and authorises no product work.

## Opening boundary

Phase 5 owns the visible lightweight editing decision: renderer and style
selection, deterministic visual-to-domain selection mapping, GUI parameter
editing and Undo/Redo behaviour, save/reopen behaviour, invalidation, resource
evidence and project-owner acceptance of the editing behaviour and limitations.

The starting exit state is 0/4:

| Exit condition | Starting disposition |
| --- | --- |
| One renderer accepted using correctness, editing, FreeCAD integration, maintainability and measured resource evidence | Pending — phase not opened |
| Small logical object/layer count with deterministic selection-to-domain mapping | Pending — phase not opened |
| Normal edits avoid dense exact `Part` geometry | Pending — phase not opened |
| Project owner accepts editing behaviour and documented limitations | Pending — phase not opened |

Phase 6 retains complete exact-validation/export signatures and invalidation,
transient exact geometry, cleanup, output equivalence, rollback and end-to-end
performance. Phase 5 does not authorise those duties, operator migration,
production output, chair clearance or release work.

## Current controls

All residual risks continue in [risks.json](risks.json) without a treatment or
control-effectiveness change. [gate-decisions.json](gate-decisions.json) is
clean for the unopened phase. Phase 5 requires a separate Level 3 opening
decision before implementation or evidence may be added here.
