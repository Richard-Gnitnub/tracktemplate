# Academy to TrackTemplate authority mapping

This map routes external findings to the project document that can accept,
reject or qualify them. The Academy is research evidence, not a project
authority.

| Academy subject | TrackTemplate owner | Ontology boundary |
| --- | --- | --- |
| Addon type and Workbench product form | `reference/ARCHITECTURE.md` | `tt:Adapter`, `tt:WorkflowOperation` |
| Namespaced source layout and dependency direction | `reference/MODULARISATION_PLAN.md` | Product implementation; not canonical railway state |
| Commands, workbench registration and UI wiring | `reference/ARCHITECTURE.md` | `tt:WorkflowOperation`, presentation boundary |
| Custom document objects and ViewProviders | `reference/ARCHITECTURE.md` | `tt:PersistentRecord`, `tt:PersistenceAdapter`, `tt:PresentationAdapter` |
| Package metadata and distribution | `reference/ARCHITECTURE.md`; live timing in `reference/PROJECT_PLAN.md` | Versioned Addon artifact, outside canonical railway state |
| Dependencies and vendoring | `AGENTS.md`; `reference/MODULARISATION_PLAN.md`; licensing where applicable | Adapter/runtime dependency, never implicit canonical data |
| Code and asset licensing | `reference/LICENSING_BOUNDARIES.md`; `reference/PROVENANCE.md` | `tt:DependencyManifest`, `tt:ProvenanceRecord`, `tt:ProjectStatus` |
| Local development and testing | `reference/VALIDATION.md`; `reference/TESTING_POLICY.md` | Evidence for the affected adapter/workflow boundary |
| FreeCAD compatibility | `reference/ARCHITECTURE.md`; qualified profile contract; live gate in `reference/PROJECT_PLAN.md` | `tt:CompatibilityAdapter`, `tt:PersistentRecord` |
| Data/schema migration | `reference/ARCHITECTURE.md`; `reference/TESTING_POLICY.md` | `tt:VersionedRecord`, `tt:CompatibilityAdapter` |
| Addon Index qualities and publication | `reference/PROJECT_PLAN.md`; licensing/provenance owners | Release evidence, not ontology maturity status |
| Recovery or destructive installation steps | `reference/RECOVERY_AND_BACKUP.md` | Repository/system safety boundary |

## Reconciliation rules

- An Academy recommendation may inform an implementation proposal; only the
  canonical owner can make it a TrackTemplate requirement.
- A supported FreeCAD legacy layout does not override the accepted modular
  package direction.
- A runnable demo does not prove qualified FreeCAD, GUI, persistence, recovery,
  export or performance behaviour.
- General dependency guidance does not authorize a new TrackTemplate runtime
  dependency.
- General licensing guidance does not reclassify existing TrackTemplate source,
  chair data, evidence or generated output.
- Addon Index acceptance criteria do not close a TrackTemplate phase or release
  gate.
- Use `reference/ONTOLOGY.md` to name stable product concepts, and
  `reference/PROJECT_PLAN.md` only for live status.
