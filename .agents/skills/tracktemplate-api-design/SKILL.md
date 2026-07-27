---
name: tracktemplate-api-design
description: Design, integrate or review narrow, versioned TrackTemplate contracts across Python APIs, application commands, FreeCAD integration, persistence, chair packages, exporters and optional network interfaces. Use before adding or changing a public boundary, schema, command, stored property, adapter or compatibility contract, or an accepted third-party API, OAuth, webhook or GraphQL integration.
---

# TrackTemplate API design

## Outcome

Define the smallest explicit contract that lets its real consumers perform an
accepted workflow while preserving railway semantics, compatibility,
recoverability and dependency direction.

## Contract surfaces

Apply this workflow to:

- the small public façade exposed by `tracktemplate.api`;
- domain and application commands, results and structured failures;
- FreeCAD commands, document objects, properties and ViewProvider boundaries;
- persistence, migration and chair-definition schemas;
- exact-geometry and exporter requests, results and manifests;
- optional third-party clients, HTTP or GraphQL APIs, OAuth flows and webhook
  boundaries only when accepted scope requires them.

Do not turn every internal function into a supported API or add a network
service merely to follow generic API guidance.

## Preparation

1. Read `reference/PROJECT_PLAN.md`, `reference/ARCHITECTURE.md` and
   `reference/MODULARISATION_PLAN.md`.
2. Read the affected compatibility, schema, persistence, export, terminology,
   provenance and licensing contracts.
3. Identify every current and planned consumer, the authoritative
   implementation and the dependency direction.
4. Inspect qualified Python, FreeCAD, Qt/PySide and package constraints.
5. Use `$tracktemplate-freecad-addon-research` before relying on current
   FreeCAD command, document-object, property or ViewProvider practice.
6. If a network API, authentication flow or event integration is in accepted
   scope, read
   [`references/network-integrations.md`](references/network-integrations.md)
   before designing or implementing it.

## Contract definition

Specify:

1. **Owner and consumers:** concept owner, supported callers and non-goals.
2. **Operations:** accepted use cases, lifecycle and state transitions.
3. **Inputs:** names, types, required/optional state, units, coordinate frames,
   tolerances, identities, ordering and validation.
4. **Outputs:** structure, determinism, identities, ordering, signatures and
   provenance or rights metadata.
5. **Failures:** invalid, unsupported, conflicting and partial states; stable
   error structure; diagnostics and recovery.
6. **Side effects:** document mutation, transactions, recompute, files,
   staging, external actions and idempotency.
7. **Compatibility:** public/stored identifiers, versions, support window,
   deprecation, migration and rollback.
8. **Performance:** cost boundary, deferred work, cache signature and
   invalidation.
9. **Evidence:** contract, unit, integration, FreeCAD, GUI, persistence,
   migration, export and performance tests that can disprove correctness.

Resolve these before choosing syntax or framework.

## TrackTemplate design rules

- Keep `tracktemplate.api` small; consumers must not import arbitrary internals.
- Pass serialisable domain/application records across core boundaries. Do not
  expose `Part.Shape`, meshes, GUI objects or opaque evidence bodies as
  canonical domain state.
- Make units, frames, tolerances, identities, ordering and production intent
  explicit.
- Return structured results and failures; adapters translate them into FreeCAD
  state or operator messages.
- Keep one authoritative operation behind a cohesive interface. Record every
  temporary façade or duplicate with an owner and retirement gate.
- Preserve atomic command, transaction, Undo/Redo, rollback and
  validate-before-mutation behaviour.
- Version stored and interchange schemas. Reject unknown, future, corrupt or
  insufficiently parametric input before mutation.
- Treat an additive field, changed default, reordered result, new exception or
  timing shift as a compatibility question, not automatically as a safe
  change.
- Add no speculative generic repository, service locator, CRUD layer or
  transport-neutral abstraction without a demonstrated shared invariant.

## Select applicable external standards

Use a standard only when it matches the accepted surface and qualified
toolchain:

- For Python and FCMacro APIs, use `$tracktemplate-python-writing`.
- For JSON interchange, state the chosen schema version/dialect and validate
  round-trip, invalid input and deterministic serialisation. Consult the
  [JSON Schema specification](https://json-schema.org/specification) when JSON
  Schema is selected.
- For an accepted HTTP API, derive method, status, conditional request,
  caching and content semantics from
  [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html). Describe it with a
  qualified version of the
  [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) when that
  improves interoperability.
- Do not require REST, CRUD, HATEOAS, pagination, rate-limit headers or
  version-in-URL patterns when the actual contract does not need them.
- For accepted OAuth, webhook or GraphQL work, use the standards and
  provider-specific verification rules selected in the network-integration
  reference. Do not infer provider behaviour from a generic example.

Verify current standards from primary sources when designing the concrete
surface; do not assume the examples embedded in this skill remain current.

## Change workflow

1. Inventory the current contract and its consumers.
2. Write the proposed contract and compatibility matrix before implementation.
3. Separate mechanical extraction, cleanup, behaviour change and migration.
4. Add direct contract evidence, including invalid and rollback cases.
5. Implement Python through `$tracktemplate-python-writing` and the applicable
   adapter boundary.
6. Compare legacy/new results and exercise the highest observable integration
   boundary.
7. Update only the canonical API/schema owner and current phase evidence.
8. Run `$tracktemplate-change-validation` and
   `$tracktemplate-quality-review`.

## Report

Report the contract surface, owner and consumers, operations, schemas,
invariants, compatibility/migration decision, errors and side effects,
standards selected, evidence run, unsupported consumers and remaining
project-owner decisions.
