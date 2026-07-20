# Reference Source Provenance and Licensing Decision Record

Status: **COMPLETE — source, licence, attribution, and redistribution policy
accepted by the project owner on 2026-07-19.**

This record captures what can be established from the repository and the local
reference material. It is a project-control record, not legal advice or a legal
conclusion about derivative-work status.

## Local reference snapshot

The following archive is present locally and deliberately ignored by Git:

| Item | Recorded value |
| --- | --- |
| Path | `reference/t5_files_556b_06_feb_2025.zip` |
| Size | 2,350,856 bytes |
| SHA-256 | `2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3` |
| Archive root | `T556B_ZIPPED_FOR_UPLOAD/` |
| Contents | 156 entries; 13,862,960 uncompressed bytes |
| Snapshot indication | filenames and timestamps identify Templot5 revision 556b material prepared on or before 2025-02-06 |
| Acquisition source | [Templot5 SourceForge files](https://sourceforge.net/projects/opentemplot/files/) |
| Direct download page | [SourceForge download](https://sourceforge.net/projects/opentemplot/files/t5_files_556b_06_feb_2025.zip/download) |
| SourceForge publication | 2025-02-06; identified there as the open-source development files released under GNU GPLv3 |
| Repository status | ignored and untracked by project-owner decision; use the upstream download instead of redistributing the ZIP here |

The acquisition chain is now confirmed. SourceForge lists the exact filename,
date, approximate size, purpose, copyright notice, and GPLv3 release statement.
Those facts agree with the local archive's name, contents, notices, and exact
byte record above. The archive README identifies the material as Templot5, the
open-source version of Templot by Martin Wynne.

A public [Mat Harris Templot5 GitHub
mirror](https://github.com/mattharris/Templot5) preserves a historical Git
snapshot and identifies it as GPL-3.0. It is useful corroborating evidence, but
SourceForge is the provenance source for the exact local ZIP.

## Upstream notices found in the snapshot

The reviewed Pascal headers, including `chairs_unit.pas` and `dxf_unit.pas`,
state:

- copyright 2024 Martin Wynne and OpenTemplot contributors; and
- GNU General Public License version 3, or any later version.

The archive also contains the corresponding GPL licence text. Preserve those
notices when retaining, reviewing, adapting, or redistributing the source.

## Relationship to TrackTemplateMacro

The B14/B15 macro is not documented as a clean-room implementation. Its own
source explicitly cites Templot5 revision 556b files and named routines,
including `switch_select.pas`, `math_unit.pas`, `shove_timber.pas`,
`chairs_unit.pas`, `chairs_unit_x.pas`, and `dxf_unit.pas`. It also describes
rules, tables, profiles, and chair geometry as Templot-derived,
Templot-cross-checked, or source-dimensional.

The accepted project classification is therefore:

> TrackTemplateMacro is source-informed and contains data, dimensions, rules,
> and calculations explicitly based on or cross-checked against Templot5
> source material. Whether any particular passage constitutes a translation or
> derivative work has not been legally determined.

Mathematical concepts, railway methods, functionality, and factual dimensions
are distinguished from copyrightable source expression. The project-wide GPL
choice is a conservative compatibility decision; it does not assert that those
underlying ideas are copyrightable or that every macro line derives from
Templot. Do not replace the source-informed classification with “clean-room” or
“independently implemented” unless a traceable authorship review supports it.

## Chair procedural source-audit record

On 2026-07-20 a read-only architecture audit examined the chair-related paths
in the exact local Templot5 revision 556b archive, principally
`chairs_unit.pas`, `chairs_unit_x.pas`, `dxf_unit.pas` and
`custom_3d_unit.pas`. The audit records that the upstream program separates
full-size 2D/3D chair data from procedural constituent builders, reuses named
jaw/seat/key blocks at calculated transforms, emits derived DXF 3D faces and
triangulates them for STL. Its `.sk4` loading path covers rail, dimensional and
manufacturing settings; this audit found no generic arbitrary-chair mesh to
procedural-definition importer in the reviewed snapshot.

TrackTemplateMacro's B15 body already cites selected `init_2d_rea`,
`init_3d_rea` and rail-section dimensions, but its supported S1/S1J exact body
is a bounded five-box approximation and omits additional constituents. The
accepted successor architecture will therefore remain explicitly
Templot-source-informed: it will implement a full-size, parameterised,
constituent chair definition and may use FreeCAD/OpenCASCADE B-reps rather than
transcribing the upstream DXF face writer. Output and method equivalence must be
supported by recorded geometric evidence; different implementation technology
does not justify relabelling the work clean-room.

This documentation change records the source/data-flow findings and intended
boundary. It does not copy or translate Pascal implementation into production
code and does not alter either macro.

## External chair-evidence provenance

Each reusable chair-definition package derived from a scan, CAD model,
drawing, physical measurement or combination must record, as applicable:

- creator/supplier and acquisition date;
- prototype designation and the evidence supporting that designation;
- original filename, format, byte hash, declared units, scale and coordinate
  frame;
- ownership, licence, permitted use and redistribution status;
- calibration references and direct measurements;
- which values are measured, source-derived, fitted, inferred or unresolved;
  and
- the definition version, fitting/validation result and explicit acceptance.

Do not assume that an accessible forum attachment, downloadable model or scan
may be redistributed. Source evidence may remain local and untracked while a
rights-compatible derived definition records its hashes and provenance. The
first pilot's working description is an S1 chair; its precise REA/company
designation must be confirmed from evidence before the published package is
named.

## Accepted repository licensing state

- TrackTemplateMacro is licensed under **GPL-3.0-or-later**. The complete GPLv3
  text is in the repository-root [`LICENSE`](../LICENSE) file.
- [`NOTICE.md`](../NOTICE.md) applies the project licence, preserves the Templot5 source-basis
  attribution, and gives particular thanks to Martin Wynne and Steve Cornford.
- The local ZIP remains ignored and is not part of the Git checkpoint.
- Templot5 source may be consulted or adapted only with its notices and the
  project provenance maintained; mathematical ideas and expressive source must
  not be conflated in future records.

## Phase 0 decision

On 2026-07-19 the project owner approved:

1. GPL-3.0-or-later for TrackTemplateMacro;
2. the source-basis attribution in `NOTICE.md` and particular thanks to Martin
   Wynne and Steve Cornford;
3. SourceForge as the acquisition source for the exact ZIP;
4. keeping the ZIP ignored and untracked while linking to the upstream copy;
   and
5. retaining its exact checksum as reproducibility evidence.

This decision aligns the project licence with the notices found in the source
material while leaving the mathematics/copyright distinction explicit. It is a
project-control decision, not legal advice or a court finding.
