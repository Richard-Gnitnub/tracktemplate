# TrackTemplate

TrackTemplate is an in-development FreeCAD system for parametric model-railway
track templates: plain line, turnouts, crossovers, timbering, chairs,
persistence, display and production export.

Phase 5 is complete. Phase 6 is not started, unopened and unauthorised. The
project is not yet a production-ready Addon and does not claim project-cleared
production output.

## Repository orientation

- [Current project status](reference/PROJECT_PLAN.md)
- [Current unopened Phase 6 holding record](reference/current/PHASE_EVIDENCE.md)
- [Architecture](reference/ARCHITECTURE.md)
- [Engineering policy](reference/ENGINEERING_POLICY.md)
- [Validation strategy](reference/VALIDATION.md)
- [Licensing boundaries](reference/LICENSING_BOUNDARIES.md)
- [Provenance](reference/PROVENANCE.md)
- [Contributor and agent workflows](reference/AGENT_WORKFLOWS.md)

`AdvancedTurnout.FCMacro` is the immutable B14 legacy comparison oracle. The
long B15 macro is the accepted behavioural reference. `TrackTemplate.FCMacro`
and the modular `tracktemplate` package are the B16 development checkpoint.

## Development checks

The tracked CI workflow parses Python and macro sources and runs every
standalone validator in `tests/validate_*.py`. That matrix includes contract,
dependency-direction, frozen-hash, Markdown-link and project-progress controls.

FreeCAD host, real-GUI, persistence, exact-output and performance checks remain
separate evidence layers selected from [VALIDATION.md](reference/VALIDATION.md);
a green standalone CI run does not imply those checks passed.

Installation and operator guidance will be added with the beta Addon packaging
work. Until then, this README is a repository map rather than a release guide.
