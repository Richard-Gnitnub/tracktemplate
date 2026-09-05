---
name: tracktemplate-python-writing
description: Write, refactor or review TrackTemplate Python and FCMacro code using PEP 8 as the style baseline while preserving railway behaviour, FreeCAD compatibility, frozen legacy evidence, public APIs, stored identifiers and narrow diffs. Use whenever creating or materially editing Python or macro source.
---

# TrackTemplate Python writing

## Standard and precedence

Use [PEP 8](https://peps.python.org/pep-0008/) as the baseline for new and
materially edited Python. Use
[PEP 257](https://peps.python.org/pep-0257/) for public docstrings.

Apply standards in this order:

1. the current explicit user decision;
2. `AGENTS.md` and the applicable canonical project documents;
3. railway correctness, recoverability and qualified FreeCAD/Python
   compatibility;
4. established local style where changing it would create risk or obscure the
   functional diff; and
5. PEP 8 and PEP 257.

Do not change behaviour, a public interface, persisted name or compatibility
identifier merely to improve style.

## Layout and naming

- Indent with four spaces and never mix tabs and spaces.
- Limit code to 79 characters and comments or docstrings to 72 characters.
  Exceed those limits only when wrapping would reduce clarity or alter a
  load-bearing string, identifier, URL or external interface.
- Wrap with implicit continuation inside parentheses, brackets or braces.
  Avoid backslash continuation where implicit continuation is possible.
- Put top-level classes and functions between two blank lines and methods
  between one blank line.
- Import one module per line. Group standard-library, qualified third-party or
  host, and local imports with blank lines between the groups.
- Avoid wildcard imports unless an accepted compatibility or re-export boundary
  requires one.
- Use `snake_case` for functions and variables, `CapWords` for classes and
  exception types, and `UPPER_CASE` for constants.
- Give units and coordinate meaning explicit names such as `radius_mm` and
  `total_angle_rad`. Follow `reference/TERMINOLOGY.md` for railway language.
- Preserve frozen, public, persisted and compatibility identifiers even when
  they do not follow current naming conventions.

## Functions, types and interfaces

- Keep each function cohesive and make side effects, document mutation and
  external calls visible at the interface.
- Prefer clear control flow over clever compression, compound statements or
  dense expressions.
- Add type annotations where they clarify a stable domain or application
  contract and remain compatible with the qualified runtime.
- Do not force static-looking annotations onto dynamic FreeCAD, Qt, Coin or
  legacy boundaries when they would misrepresent runtime behaviour.
- Keep public APIs deliberate. Use a leading underscore for genuinely internal
  names, but do not rename an existing public or stored name without accepted
  migration authority.
- Use named constants for shared tolerances, units, schema versions and other
  values with project meaning. Do not conceal a one-off obvious value behind a
  speculative constant.

## Comments, docstrings and failures

- Give public modules, classes, functions and methods concise docstrings that
  state their observable contract, important side effects, failures and units.
- Write comments for non-obvious railway reasoning, compatibility constraints,
  recovery requirements or evidence boundaries. Do not narrate visible syntax.
- Keep comments accurate when code changes; remove stale explanation in the
  same bounded change.
- Catch the narrowest useful exception. Preserve the original cause with
  `raise ... from error` when translating a failure across a boundary.
- Do not use a bare `except`, silently swallow a failure or replace a structured
  diagnostic with a generic success path.

## TrackTemplate boundaries

- Do not style-clean the immutable B14 oracle or accepted B15 behavioural
  reference. Treat their existing formatting as frozen evidence unless an
  explicitly accepted factual correction requires a change.
- Apply this guide to the B16 composition root, modular `tracktemplate` package,
  project tools and tests within the exact requested scope.
- Keep FCMacro code valid for its qualified FreeCAD-bundled Python and host
  imports. Do not add a third-party runtime dependency for formatting or style.
- Preserve UTF-8, exact property names, schema fields, stable identities,
  deterministic ordering, diagnostics, transactions and rollback behaviour.
- Separate mechanical formatting from extraction, refactoring, optimisation and
  behaviour change. Never reformat unrelated files to make a functional diff
  look uniform.

## Writing and verification flow

1. Read the affected code, its callers, tests and owning canonical document.
2. Identify frozen identifiers, host constraints and observable behaviour
   before editing.
3. Write the smallest coherent PEP 8-aligned change consistent with nearby
   accepted code.
4. Parse every changed `.py` and `.FCMacro` file and run the nearest relevant
   tests selected through `$tracktemplate-change-validation`.
5. Inspect the complete diff for accidental formatting spread, renamed
   interfaces, altered strings and behavioural drift.

Before source review, examine the complete assembled submission with the
content from all agents. Connect the relevant checks to that candidate
version. Report the exact changed files, preserved behaviour, test results,
and unresolved facts.

When a test assertion changes, preserve each technical safeguard. If the
changed assertion could accept an incorrect result, use a negative case.
These responsibilities are part of writing. They add no approval stage.

If the repository later adopts a formatter or linter configuration, treat that
configuration as the executable local style contract. Do not run a write-mode
formatter across unrelated, legacy or frozen files without explicit scope and
review.
