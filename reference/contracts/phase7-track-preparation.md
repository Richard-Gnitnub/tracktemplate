# Phase 7 Track Alignment Preparation API

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

## Authority and purpose

[D-P7-001](../current/PHASE_EVIDENCE.md#phase-7-opening-panel) keeps
Phase 7 open for Core alignment, station, and multiple-track migration.
[D-GOV-004](../PROJECT_PLAN.md#owner-decisions) supplies the accepted route for
bounded Level 2 work. The project owner's 2026-09-20
`$tracktemplate-chief-of-staff` instruction authorises this result. The
instruction is to continue Phase 7 and advance its exits. These API instructions
specify preparation of one secondary track alignment. They accept no Phase 7 exit.

The B14 and B15 definitions are equal. The product moves
`signed_side_factor`, `effective_constant_radius`, and
`prepare_track_alignment` to `tracktemplate.domain.alignment`.
`tracktemplate.api` supplies the same three names. The task does not change B14 or B15.

## Helper functions

`signed_side_factor(side)` returns `1.0` when `side` is `Inside`. It returns
`-1.0` for all other values.

`effective_constant_radius(main_radius, curve_spacing, side)` subtracts
`curve_spacing` from `main_radius` when `side` is `Inside`. It adds
`curve_spacing` for all other values. Length values use mm.

The two functions change no input. They use no FreeCAD or Qt function. They
read no document and keep no result for another operation.

## Track alignment preparation

`prepare_track_alignment` has these five inputs in this sequence:

1. `config`
2. `circle_centre`
3. `main_radius`
4. `total_angle`
5. `main_alignment`.

All five inputs are necessary. The [JSON data](phase7-track-preparation.json)
define `frame` as `canonical-local-XY-left-turn`. Lengths and XY values use mm.
`total_angle` and `headings` use rad. The `geometry_tolerance` value is `1.0e-8`.

The function accepts these exact values for `alignment_mode`:

- `Euler - match spacings`
- `Euler - use lengths`
- `Platform widening`.

The function first validates `start_spacing`, `curve_spacing`,
`finish_spacing`, and `width`. Each value must be more than zero. It then
calculates the constant radius. That radius must be more than half the track
width.

For `Euler - match spacings`, the function uses `solve_transition_length`
for the entry before the exit. It then uses `build_concentric_core`.

For `Euler - use lengths`, the function calculates the entry offset before
the exit offset. These offsets have signs. The function validates the side of
the entry straight before the side of the exit straight. It then uses
`build_concentric_core`.

For `Platform widening`, the function validates `entry_transition_length`
before `exit_transition_length`. It calculates the main-track line offsets.
It uses `solve_platform_shape_parameter` for the entry before the exit.
It then uses `build_platform_core` and validates `minimum_radius`.

The function uses the modular functions in the JSON data. It changes no
operation in those functions. It changes no point, result, tolerance,
diagnostic, or sequence.

## Results, changes, and identities

After all functions and validation steps give their necessary results,
`prepare_track_alignment` changes four items in `config` in this sequence:

1. `entry_transition_length`
2. `exit_transition_length`
3. `start_spacing`
4. `finish_spacing`.

It keeps the identity of `config` and each unrelated item. It does not change
`main_alignment`.

The function keeps the result from `build_concentric_core` or
`build_platform_core`, with the same item sequence. It then adds these items
in this sequence:

1. `name`
2. `side`
3. `alignment_mode`
4. `start_spacing`
5. `curve_spacing`
6. `finish_spacing`
7. `width`
8. `create_template`
9. `show_centreline`.

Each operation without an error returns a new result, a new `points` list,
and a new `headings` list. Each point is a new pair of X and Y numbers.
The result from `tracktemplate.domain.alignment` contains no FreeCAD object.
The function changes no FreeCAD document and keeps no result for another
operation.

For the bounded inputs, an error before the four `config` changes keeps
`config` and `main_alignment` as they were. The tests compare the complete
result, its item sequence, input identities, and state after an error with B14
and B15.

## Diagnostics

The function preserves these B14/B15 diagnostics and their sequence:

- `All spacing and width values for '{}' must be greater than zero.`
- `The constant radius for '{}' is {:.3f} mm, which is too small for its {:.3f} mm template width.`
- `The manual entry Euler easement for '{}' places its entry straight on the wrong side of the main track. Change the entry length or select Platform widening.`
- `The manual exit Euler easement for '{}' places its exit straight on the wrong side of the main track. Change the exit length or select Platform widening.`
- `Platform widening for '{}' needs a positive Entry transition length.`
- `Platform widening for '{}' needs a positive Exit transition length.`
- `The platform widening for '{}' produces a peak minimum radius of {:.3f} mm, which is too small for its {:.3f} mm template width. Increase the platform transition length or reduce the spacing change.`
- `Unknown alignment mode '{}' for '{}'.`

The API instructions for each selected function own its other diagnostics.

## B16 caller and recovery

The `run_macro` caller uses the name `prepare_track_alignment`. The product
sets that name to a `_PrepareTrackAlignmentAdapter` object in
`tracktemplate.compatibility.transition_workflow`. The adapter uses
`tracktemplate.api.prepare_track_alignment` one time. It changes only the new
`points` list to contain `App.Vector(float(x), float(y), 0.0)` values in the
same sequence. It keeps all other result items and input identities.

The product selects 18 functions together and validates 39 caller identities.
The `run_macro` caller uses the selected `prepare_track_alignment` adapter
and the selected `signed_side_factor` function. The preparation function uses
the seven selected dependencies in the JSON data.

After a selection error, the product puts all previous values back. It removes
a new value when that name had no previous value. The product rejects a mixed
set of selected values before workflow launch.

The routing record uses schema `11` and the identity
`tracktemplate:phase7:track-preparation:1`. The task changes no earlier API
instructions or their JSON data. It changes no B14, B15,
`TrackTemplate.FCMacro`, or `load_b15_workflow_host` source.

## Scope and limits

The bounded proof uses the B14/B15 number inputs and the inputs from the
qualified host profile. It makes no claim about the error sequence for all
possible Python number or point objects. It also makes no such claim for an
error from a different `vector_factory`.

The task does not change persistence, physical-platform, sectioning,
validation, output, or export behaviour. It does not remove a legacy path.
The Core migration owner keeps the compatibility adapter until its caller has
an accepted replacement and all removal conditions are complete.

The task accepts no Phase 7 exit, product performance result, output status,
or release state. D-P6-008 and all conditions to compare results and remove
legacy paths stay in full.
