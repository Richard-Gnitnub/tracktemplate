# First S1 Chair Pilot Plan

Status: **Accepted Phase 1 control; production definition and pilot remain
blocked.**

This document defines the minimum neutral package, evidence, rights and
acceptance plan for the first S1 chair. It is a project-control plan, not a
chair definition, an assertion that the working description “S1” is a precise
prototype designation, or legal clearance.

The governing boundaries are [ARCHITECTURE.md](ARCHITECTURE.md) and
[LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md). The local Templot
comparison remains controlled by the
[frozen 556b oracle](oracles/templot5-556b-s1-oracle.json).

The plan deliberately contains no production dimensions, copied Templot value
collection, generated chair body or positive rights decision. The current
[dependency manifest](manifests/s1-chair-pilot.dependency-manifest.json)
therefore remains `unknown` with package licence `NOASSERTION`, and the
[first-S1/core lineage register](lineage/phase1-s1-core-lineage.json) remains
blocked.

## Accepted direction

The project owner accepted these architectural and scope decisions on
2026-07-20:

- the authoritative interchange is a neutral, versioned TrackTemplateMacro
  `ChairDefinition`, not a Templot file or retained FreeCAD shape;
- one full-size procedural constituent generator serves native definitions and
  the operator-assisted assimilation path;
- source scans, CAD bodies, drawings and measurements are evidence, not normal
  runtime geometry;
- Templot5 revision 556b may be a local comparison oracle but is not canonical
  production data;
- the RC includes validated external chair packages and one assisted S1 pilot,
  while arbitrary automatic conversion remains post-RC research; and
- the intended first-S1 uses are public redistribution, commercial production,
  publication and physical production, subject to the actual package passing
  every provenance, permission, non-copyright-rights and manifest gate.

## Neutral package requirements

The future schema must describe the following logical records. This list does
not prescribe a ZIP layout or create the Phase 4/9 implementation early.

1. Package identity: stable package and definition identifiers, package
   version, schema version, precise prototype designation and human-readable
   description.
2. Prototype quantities: full-size values separated from model scale,
   rail-fit policy and manufacturing compensation.
3. Frames and datums: an explicit right-handed chair-local frame, base mounting
   plane, longitudinal centre plane, rail-section centre plane, rail-seat plane,
   gauge-face datum and key/loose-component directions where applicable.
4. Rail interfaces: independently evidenced rail section, seat relationship,
   gauge/field orientation, contact and clearance intent.
5. Constituents: stable named base/plinth, seat, inner and outer jaws, ribs,
   fillets, key and any applicable fastening, loose-jaw or plug-interface
   records. Optional parts must be explicitly absent rather than silently
   defaulted.
6. Procedural relationships: profiles, sections, radii, slopes, symmetry,
   placements and assembly constraints rather than an opaque final mesh.
7. Manufacturing variants: model scale, material/printer compensation,
   clearances and export settings kept outside prototype geometry.
8. Field/component provenance: classification, source locator and hash,
   measured/factual/fitted/derived/inferred/unresolved state, uncertainty,
   assumptions, derivation inputs, rights and acceptance.
9. Validation state: required dimensions, interfaces, topology, residuals,
   findings, reviewer and explicit acceptance.
10. Dependency linkage: the exact package dependency manifest and its content
    signature, without embedding local-only source evidence.

### Accepted quantity representation

- Serialised output-affecting numbers use exact decimal strings, never JSON
  binary-floating-point literals as the sole source value.
- Every sourced quantity retains its original decimal value and unit. Lengths
  also carry or deterministically derive a full-size millimetre value using the
  exact declared conversion; angles and dimensionless values declare their own
  canonical units.
- Project derivations identify their input field identities and rule/version.
  An adapter may convert validated canonical values to FreeCAD floats only at
  the exact-geometry boundary and under the accepted tolerance policy.
- No value is admitted merely because it matches Templot. Unknown or inferred
  values remain explicit findings and cannot receive an invented default.

### Accepted chair-local frame

Use a right-handed full-size Cartesian frame with:

- `+X` longitudinally along the nominal rail direction;
- `+Y` from the gauge side towards the field side;
- `+Z` upwards from the base mounting plane; and
- the origin at the intersection of the longitudinal chair centre plane, the
  rail-section centre plane and the base mounting plane.

The rail-seat plane, gauge-face datum and component-local frames are named
datums related to that origin by explicit transforms. A placed chair may be
reflected or transformed only by an application-level placement record; the
prototype package itself does not silently infer track hand or key direction.

## Version and failure contract

The future package loader must:

- distinguish schema version, package version and definition identity;
- parse into memory and validate the complete package before creating geometry,
  changing a FreeCAD document or writing an export;
- reject missing required fields, duplicate identities, malformed decimal
  values, non-finite derived values, inconsistent units/frames, unresolved
  output-affecting fields and dependency-manifest disagreement;
- reject unsupported future schema versions and unknown v1 core fields with a
  recoverable diagnostic—never partially load them through a legacy fallback;
- use deterministic UTF-8 canonical serialisation and content signatures so a
  load/serialise/load round trip is stable;
- keep source scans, CAD files, drawings, Templot artifacts and fitting tools
  outside the runtime dependency set after an accepted definition is created;
  and
- leave the document and filesystem unchanged after any failed package load,
  validation, exact generation or export attempt.

Phase 4 owns the reusable loader, schema-version window and copied-document
failure fixtures. Phase 9 owns the S1 constituent schema completion, package
values, exact generation, assisted pilot and production/output qualification.

## Minimum evidence bundle

Before the working name “S1 chair” becomes a published package designation,
the evidence bundle must provide:

- a precise prototype/company/standard designation and evidence supporting
  that name;
- creator or supplier, acquisition date, exact locator, file format and
  lowercase SHA-256 for every source artifact;
- authority for access, measurement/fitting, adaptation, production output,
  redistribution, commercial use and publication as applicable;
- calibrated full-size dimensions with units, uncertainty and measurement
  method, plus evidence for nominal, hidden and worn-sensitive geometry that a
  surface scan alone cannot establish;
- an independently evidenced rail section and its chair-fit relationship;
- operator-declared component boundaries and placement/fit landmarks;
- complete field/component classifications, contributor or supplier authority,
  package-licence basis and all four non-copyright-rights reviews; and
- a local comparison record that keeps any Templot media/reference data
  non-output-affecting and untracked.

A rights-compatible drawing/standard plus project measurements may satisfy the
bundle without a scan. A scan or CAD body may assist fitting, but cannot alone
prove prototype identity, hidden geometry, nominal dimensions or rail fit.

## Comparison and fit metrics

Phase 1 fixes the metric families, not unsupported numerical limits. Phase 9
must set tolerances from the selected evidence, its uncertainty, the rail-fit
requirement and the intended manufacturing process before fitting is accepted:

- source calibration and unit residuals;
- required prototype dimension and section/profile residuals;
- component landmark, datum and assembly-transform residuals;
- surface maximum and distribution statistics over declared comparable areas;
- base/seat/gauge-face/key and other rail-interface constraints;
- constituent presence, stable identities, topology, solidity and interference;
- assembled bounds, orientation and supported placement;
- rail fit and declared clearance/contact results;
- deterministic definition, STEP/STL and retained-component summaries; and
- separate prototype-versus-manufacturing signatures and change-back tests.

Mesh hash, face order, visual similarity or a low aggregate surface residual is
never sufficient by itself.

## Decision register

| ID | Topic | State | Phase 1 disposition | Acceptance or evidence still needed |
| --- | --- | --- | --- | --- |
| S1-01 | Canonical interchange | accepted-direction | One neutral `ChairDefinition` feeds native, assimilated, exact and export paths | Phase 4/9 implementation evidence |
| S1-02 | RC capability boundary | accepted-direction | Validated external packages plus one assisted S1 pilot; arbitrary automatic conversion excluded | Preserve scope through RC |
| S1-03 | Intended uses | accepted-direction | Public redistribution, commercial production, publication and physical production are the declared targets | Actual package must pass each declared-use permission and manifest gate |
| S1-04 | Quantity representation | accepted-direction | Preserve original decimal/unit and deterministic canonical values; convert to float only at adapters | Phase 4 round-trip tests |
| S1-05 | Canonical units and frame | accepted-direction | Full-size millimetres for length plus the declared right-handed chair-local frame and named datums | Phase 4 schema tests and Phase 9 geometry proof |
| S1-06 | Version and failure behaviour | accepted-direction | Validate completely before mutation; reject missing, corrupt, ambiguous or unsupported state without fallback | Phase 4 loader and rollback fixtures |
| S1-07 | Precise prototype designation | owner-decision-required | Keep “S1 chair” as a working description; do not publish “LMS”, “REA” or another attribution by assumption | Rights-compatible primary evidence and explicit owner confirmation |
| S1-08 | Primary evidence bundle | owner-decision-required | Prefer documented nominal evidence plus calibrated project measurements; scan/CAD is optional supporting evidence | Select exact sources, hashes, authority, calibration and uncertainty |
| S1-09 | Rail interface | owner-decision-required | Do not promote the Templot Code 75 profile into canonical data | Select and evidence the exact supported rail section and fit policy |
| S1-10 | Constituents and landmarks | owner-decision-required | Require named constituent boundaries and rail/base/key datums; unresolved parts remain findings | Evidence-led component and landmark review |
| S1-11 | Package licence | owner-decision-required | Target CC0-1.0 only if the project controls the complete package rights; otherwise select compatible explicit terms | Evidence authority, contribution record and project-owner licence decision |
| S1-12 | Non-copyright rights | blocked-evidence | Registered design, unregistered design, patent and trade-mark reviews remain `not-performed` | Recorded GB-scope reviews and escalation of any uncertain finding |
| S1-13 | Metrics and tolerances | owner-decision-required | Use the fixed metric families above; do not invent numeric thresholds before evidence selection | Evidence uncertainty, rail fit and manufacturing needs plus explicit acceptance |
| S1-14 | Templot 556b comparison | blocked-evidence | Local `reference-only`, non-output-affecting comparison under the frozen capture contract | Exact 556b executable/acquisition evidence, S1 fixture/artifacts and geometric review |
| S1-15 | Assimilation residual policy | owner-decision-required | Report per-metric residuals, inferred/unresolved values and operator decisions; no aggregate score may auto-accept | Selected evidence, numeric thresholds and explicit operator-acceptance procedure |

## Phase 1 acceptance boundary

The project owner explicitly accepted this plan on 2026-07-22 in these terms:

> I accept S1_PILOT_PLAN.md as the blocked Phase 1 control, including S1-04
> through S1-06, the intended uses and conditional CC0 target. S1-07 through
> S1-15 remain blocked pending their stated evidence and decisions.

That owner acceptance means only that:

1. S1-04 through S1-06 are accepted as the schema/loader direction;
2. the existing intended uses and conditional CC0 target are confirmed;
3. S1-07 through S1-15 remain explicit blockers until their named evidence and
   decisions exist; and
4. no S1 production definition, project-cleared package or permission from a
   third party is being claimed.

The Phase 1 first-S1 evidence/rights **plan** gate is therefore evidenced while
the package itself remains blocked for Phase 9. Editing this document or the
manifest cannot substitute for the recorded owner acceptance.

## Reproduction

Run the plan, manifest, lineage and premature-clearance checks with:

```bash
.venv/bin/python tests/validate_phase1_s1_pilot_plan.py
```

The strict manifest command must continue to fail until real evidence and all
reviews support a positive decision:

```bash
.venv/bin/python tools/validate_dependency_manifest.py \
  --require-project-cleared \
  reference/manifests/s1-chair-pilot.dependency-manifest.json
```
