# API for station values and points

Status: **Level 2 API instructions for the bounded Phase 7 scope.**

The [machine record](phase7-station-mapping.json) keeps the exact values and caller routes.
The [current evidence](../current/PHASE_EVIDENCE.md) owns the task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Station data

`tracktemplate.api.alignment_station_data(alignment)` uses the function in `tracktemplate.domain.alignment`.
It calculates station values along the supplied points in travel sequence.
The first station is `0.0` mm. Each subsequent station adds the distance from the previous point in the XY plane.

Point coordinates, station values and extension lengths use millimetres. Values for track direction use radians.
The `global-document-XY` definition stays unchanged. The API does not translate points or change travel direction.

In ordinary use, `alignment` is a Python `dict` with `points` and `headings`.
Each point supplies its X value through `[0]` and its Y value through `[1]`.
An ordinary caller supplies XY pairs. The API uses no FreeCAD value or function.

The API copies `points` to a new Python `list`, then copies `headings` to another new Python `list`.
The items in these lists keep their initial identities and sequence.
The lists must have equal counts and contain at least two points.
Otherwise, the function raises this inherited diagnostic before it reads point coordinates:

```text
A selected track alignment is incomplete.
```

The result is a new Python `dict` with these named items in this sequence:

```text
alignment
points
headings
stations
total
core_start
core_end
```

The result's `alignment` is the exact input object. `points` and `headings` are the new lists.
`stations` is a new list of calculated station values. `total` is its last value.
Consecutive points at the same position give equal station values.

The optional `entry_extension` and `exit_extension` values each use `0.0` when absent.
Each value is separately limited to the interval from `0.0` to `total` with the inherited operations.
`core_start` is the limited entry value. `core_end` is `max(core_start, total - exit_extension)`.
The API keeps the initial sequence of point reads, calculations, extension reads and errors.
It adds no input checks or automatic corrections.

## A point at a station

`tracktemplate.api.interpolate_alignment_station(data, station)` uses the function in `tracktemplate.domain.alignment`.
`data` supplies `total`, `stations`, `points` and `headings`. Other items in the station data are unnecessary for this call.
The points supply the same XY pairs.

The function first uses `float(station)` and limits the result to the interval from `0.0` to `total`.
The inherited `bisect.bisect_right` operation selects the later part between points at equal station values.
The difference between the two selected station values supplies `span`.
When `span` is at or below `1.0e-8` mm, `fraction` is `0.0`.
Otherwise, `fraction` is the distance from the first selected station divided by `span`.

The API keeps the initial operation sequence for coordinates and track direction. It adds no change of angle range.

The result is an `AlignmentStationInterpolation` object with these named items:

```text
point
heading_a
heading_b
fraction
```

`point` is the calculated XY pair. The other items keep the two selected input values for track direction and `fraction`.
These items cannot change after the result is created.
Reading `heading` calculates `heading_a + ((heading_b - heading_a) * fraction)` in radians.
The API does not calculate that value before the caller reads the property. It keeps no result of this property for subsequent use.

This sequence lets the host create its point before it calculates the final track direction.
The result is temporary calculation data. It is not a persistence schema or canonical railway state.

## B16 callers and recovery

The product sets the inherited names to `_AlignmentStationDataAdapter` and `_AlignmentStationInterpolationAdapter` objects in `tracktemplate.compatibility.transition_workflow`.
These compatibility objects use the exact selected API functions.
Private temporary objects supply point coordinate reads to the API in the initial sequence.
They keep host values outside the domain calculation and do not keep calculated point values for subsequent calls.

The first compatibility object returns the same seven named items as the inherited host function.
Its `alignment` is the original host record. Its new `points` list contains the original host point objects.
The new `headings` list contains the original items. The temporary objects do not occur in this host result.

The second compatibility object reads only the two selected points for each call.
It does not copy the complete point list for each station request.
It evaluates both XY coordinates, then creates `App.Vector(float(x), float(y), 0.0)`, then reads `heading`.
Thus, each successful call returns the inherited pair of one new `App.Vector` and the value for track direction.
Point creation occurs before the final angle calculation, including when that calculation gives an error.

The host's copied point list keeps references to the original point objects.
A change to one of those objects stays visible through that reference.
The inherited requirement to calculate new station data after source changes stays unchanged.
This API does not make old station data valid after a source change.

The product selects ten functions together and validates 38 actual caller routes.
The station pair has 15 and 30 caller functions, respectively, with 34 different callers in total.
The checks include `CrossoverManagerPanel.use_picked_crossover_position` and the nested `point_at_station` function in `_project_centreline_to_reference_normal`.

A selection error puts all ten previous values back before the workflow can start.
It removes a new value when there was no previous value.
The checks validate the exact compatibility types, selected functions and the host's actual `App.Vector` function.
The routing record uses schema `7` and contract ID `tracktemplate:phase7:station-mapping:1`.
The frozen B14/B15 sources, earlier contracts and tools to compare results stay unchanged.

## Scope and limits

The [regression record](../benchmarks/2026-09-12-phase7-station-mapping-regression.md) owns the proof, measured costs and limitations.
The supported scope includes generated alignment records, ordinary invalid inputs and the controlled error combinations in that proof.
The API keeps the inherited numerical operations, diagnostics, repeated points and sequence of errors.
The proof compares exception types, messages and operation sequence. It does not compare the complete error output.
It does not cover every possible Python object or a failure from insufficient memory.

The Core migration owner keeps the temporary compatibility objects until their callers have replacements.
Those replacements need the necessary checks to compare results, recovery, measured resource evidence and owner acceptance.
The wider platform, turnout, crossover, timber and chair callers keep their inherited interface.
This task does not migrate or accept those complete families.

The task changes no transaction, persistence, output contract or condition to remove a legacy path.
It accepts no Phase 7 exit, product performance result, output or release.
Phase 7 stays Open at 0/4. D-P6-008 and all conditions to compare results and remove legacy paths stay in full.
