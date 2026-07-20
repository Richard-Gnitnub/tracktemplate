# Contributing to TrackTemplateMacro

Contributions are welcome when their authorship, source and permitted project
use are explicit. These controls are prospective; they do not invent
attestations for historical commits or convert unresolved legacy material into
accepted production data.

## Developer Certificate of Origin

Every commit offered for inclusion must carry a Developer Certificate of
Origin 1.1 sign-off. The project uses the standard, unmodified
[DCO 1.1](https://developercertificate.org/). Add the sign-off with
`git commit --signoff`, or include this line in the commit message:

```text
Signed-off-by: Your Name <your.email@example.com>
```

The sign-off certifies the contribution under DCO 1.1. In particular, it
records that the contributor has the right to submit the contribution under
the licence identified for it, and that the contribution and sign-off form a
public record. A sign-off is an authorship/authority record, not a legal opinion
or a guarantee that no third-party rights exist.

Code is contributed under `GPL-3.0-or-later` unless the affected file states an
accepted compatible alternative. Do not remove or obscure existing upstream
notices.

## Data and evidence declaration

A contribution containing measurements, dimensions, tables, profiles, chair
definitions, scans, CAD, drawings, photographs, fixtures or other evidence
must also state, in its manifest or contribution description, that:

1. the contributor created or lawfully measured the submitted material, or has
   identified the third-party source and has authority under its recorded terms
   to contribute it for the declared uses;
2. the contribution does not silently copy an upstream table, proprietary CAD
   model, protected drawing or opaque generated output;
3. every source locator, file hash, unit, scale, classification, licence and
   permission statement supplied is accurate to the contributor's knowledge;
4. any adaptation, attribution, redistribution, commercial-production or
   publication condition is disclosed; and
5. if a package is offered under CC0-1.0 or another data licence, the
   contributor has authority to make that dedication or grant for the material
   they contributed.

Legitimately licensed or public-domain third-party evidence is not prohibited;
it must be identified rather than presented as the contributor's own work.
Material with `NOASSERTION`, non-commercial, reference-only, conflicting or
unclear terms may be useful local evidence, but it cannot silently enter a
`project-cleared` production path.

## Package and output manifests

Every reusable chair-definition package and every output proposed for
`project-cleared` status must have a dependency/project-status manifest that
passes:

```bash
.venv/bin/python tools/validate_dependency_manifest.py \
  --require-project-cleared path/to/dependency-manifest.json
```

The schema and status rules are maintained in
[reference/LICENSING_BOUNDARIES.md](reference/LICENSING_BOUNDARIES.md). A valid
manifest may deliberately remain `unknown`, `restricted` or `reference-only`;
only the explicit `--require-project-cleared` gate qualifies the internal
project status. The manifest records adaptation, output, redistribution,
commercial-use and publication permission separately; do not infer one from
another.

Raw scans, CAD files, standards and reference media need not be committed. If
their terms do not permit redistribution, keep them local and record their
identity, hash, acquisition basis and permitted role without adding the file to
Git.

## Review expectations

- Keep changes small and distinguish mechanical movement, cleanup,
  optimisation and behaviour changes.
- Add proportionate tests under
  [reference/TESTING_POLICY.md](reference/TESTING_POLICY.md).
- Preserve railway geometry, stable identities, persistence and production
  behaviour unless an accepted requirement explicitly changes them.
- Disclose known copyright, database, design-right, patent, trade-mark,
  contractual or confidentiality concerns. The project manifest review records
  unresolved questions rather than guessing them away.
