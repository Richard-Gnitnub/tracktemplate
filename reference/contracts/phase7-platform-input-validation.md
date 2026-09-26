# Phase 7 Platform Input Validation API

Status: **Level 2 instructions for one bounded Phase 7 product route.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps Phase 7
open for Core alignment, station and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) permits one bounded Level 2
continuation. The project owner's 2026-09-26 continuation selects this
result. These instructions give no Phase 7 exit acceptance.

The B14 and B15 definitions of `validate_platform_inputs` are equal. The
project keeps those definitions unchanged. The calculation now uses
`tracktemplate.domain.alignment` through `tracktemplate.api`. The
[JSON data](phase7-platform-input-validation.json) give its exact source,
values, diagnostics and product route.

## Input and result

`validate_platform_inputs(config, all_alignments)` takes a configuration
record and an ordered list of track-alignment records. It returns `None` for
a valid input. It also returns `None` when `config["enabled"]` is false. In
that case, it reads no other input field. It does not change an input or a
FreeCAD document, and it keeps no result for another call.

The function checks a nonblank name and a nonempty alignment list. It then
checks the Track A index. For `Between two tracks`, it checks the Track B
index and requires a different track. It checks positive edge clearances and
length. For `Outside one track`, it also checks positive width. For a `3D
platform solid`, it checks positive height. When `vertical_end_ramps` is true,
that height must be greater than the 1.0 mm template surface plus the
`1.0e-8` mm geometry tolerance.

A `Tapered` entry or exit needs a positive end length. `Edges only (2D)`
needs `create_edges` to be true.

When `check_clearance` is true, the function checks each selected track in
order. Its minimum is the greater of `required_clearance` and half of the
track width when that track has `create_template` true. The comparison adds
`1.0e-9` mm to the selected edge clearance. The function keeps the B14/B15
sequence of reads, checks and errors. This includes the behaviour for an
arrangement value other than the two named values. The [JSON data](phase7-platform-input-validation.json)
keep the exact diagnostic strings.

## B16 caller and recovery

The B16 `calculate_platform_boundaries` caller invokes the selected function
after its enabled check and before platform-boundary geometry. Selection binds
the Core function directly to the inherited host name. No adapter or native
vector is necessary for this input check. The host stays the owner of the
FreeCAD workflow and document changes.

The product selects twenty functions together and validates 39 caller
identities. It checks that the selected function has the Core domain closure
and the same seven constant values as the inherited host. It also checks the
`calculate_platform_boundaries` call. The routing record uses schema `13`
and identity `tracktemplate:phase7:platform-input-validation:1`. After a
setup error, selection puts each previous host value back. It removes a
selected name only when the host did not have that name before selection.

## Scope and limits

This result moves one platform-input check to Core. It does not change the
B14 or B15 source, the host configuration, stored state, production geometry
or export. It does not remove the legacy path. The selected B16 workflow
keeps its existing product status and conditions.

The [evidence record](../benchmarks/2026-09-26-phase7-platform-input-validation-regression.md)
identifies the bounded comparison and its limits. The proof does not cover
all possible custom Python containers or later platform geometry and output.
D-P6-008 and all other comparison and legacy-retirement conditions stay in
full. No Phase 7 exit, performance result, output status or release state is
accepted.
