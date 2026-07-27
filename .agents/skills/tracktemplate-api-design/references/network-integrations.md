# Network integration guidance

Read this reference only when accepted TrackTemplate scope includes a
third-party network client, HTTP or GraphQL endpoint, OAuth flow or webhook.
It does not authorise a network service, external account, credential, runtime
dependency, background worker or live external mutation.

## Establish the boundary

Before implementation:

1. identify the provider, exact documentation or machine-readable contract,
   reviewed version/date and required operations;
2. define the data owner, trust boundary, credential owner, minimum privileges,
   privacy/provenance classification and offline behaviour;
3. choose request/response, polling, webhook or GraphQL from demonstrated
   consumer and provider behaviour;
4. define timeouts, rate limits, pagination, ordering, consistency, delivery
   guarantees, deprecation signals and observable failure states; and
5. decide which project adapter owns translation into TrackTemplate records and
   structured failures.

Keep provider payloads and transport objects outside the domain model. Do not
let an SDK become the public TrackTemplate contract.

## Third-party clients

- Set explicit connect and response deadlines derived from the workflow; bound
  total attempts and total elapsed time.
- Retry only failures proven transient and operations proven safe to repeat.
  Honour `Retry-After` where applicable. Use an idempotency key or
  provider-supported reconciliation for a mutating request whose outcome may
  be ambiguous.
- Treat authentication, validation and most other client errors as structured
  non-retryable failures unless provider documentation says otherwise.
- Model pagination and truncation explicitly. Preserve stable provider
  identities and deterministic local ordering.
- Record version negotiation and deprecation/sunset behaviour. Do not assume
  URL versioning or a provider SDK prevents breaking changes.
- Redact secrets and sensitive data from diagnostics, fixtures and telemetry.
  Do not log complete request or response bodies by default.
- Add a circuit breaker, cache, polling loop or background queue only when its
  state, recovery and operational ownership are accepted and tested.
- Prefer the qualified standard library or an already accepted dependency.
  A convenient SDK or resilience package is still a new dependency requiring
  project approval and compatibility evidence.

## OAuth and credentials

Use provider metadata and current primary standards rather than copying a
generic flow. Start with
[RFC 9700, OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html)
and the specifications it identifies for the selected deployment.

- Select a flow from the actual client type and user presence. Do not use the
  resource-owner-password grant; avoid the implicit grant.
- Use authorization code with PKCE where applicable, exact redirect matching,
  transaction-bound CSRF protection and issuer validation.
- Request the minimum scope and audience. Distinguish OAuth authorization from
  user authentication; use OpenID Connect only when identity is required.
- Keep client secrets and tokens out of source, URLs, logs, exported documents
  and ordinary FreeCAD properties. Use an approved operating-system or
  deployment secret store.
- Define expiry, refresh, rotation, revocation, concurrent-refresh and
  re-authentication behaviour. Never loop indefinitely on `invalid_grant`.
- Treat browser launch, callback listeners, device-code polling and credential
  persistence as explicit UI, network and security boundaries.

## Webhooks and event delivery

- Follow the provider's current signing specification. Verify the exact raw
  bytes before parsing, use constant-time comparison where applicable and
  define timestamp, replay-window and secret-rotation handling.
- Authenticate before accepting an event. Validate size, content type, schema,
  event type, identity and tenancy before invoking TrackTemplate behaviour.
- Persist or transactionally accept the event before acknowledging success
  when loss would matter. Keep acknowledgement within the provider's deadline
  and move longer work behind an accepted recoverable queue.
- Deduplicate by a stable delivery/event identity and make side effects
  idempotent. Do not assume ordered or exactly-once delivery.
- Define retry, poison-event, dead-letter, replay and operator-diagnostic
  behaviour without silently adding infrastructure.
- Subscribe only to required events. Treat unknown event versions/types
  according to the provider contract and fail closed before mutation.

Use [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) only when the
protocol selects HTTP Message Signatures; many providers use a distinct
signature scheme. Use [CloudEvents](https://cloudevents.io/) only when the
producer and consumer deliberately select it.

## GraphQL

Select GraphQL only when its query model serves a real consumer. Consult the
current [GraphQL specification](https://spec.graphql.org/) and the chosen
server/client documentation.

- Model domain concepts, nullability, input and payload types deliberately.
- Bound list size and use stable cursor pagination where required.
- Define partial-data/error handling; an HTTP success does not prove the
  GraphQL operation succeeded completely.
- Prevent N+1 work at the resolver/data boundary and bound query depth,
  complexity or other resource cost.
- Apply authentication and authorisation at the appropriate operation and
  field boundaries.
- Evolve schemas additively only after checking semantic compatibility;
  deprecate with a consumer migration and retirement decision.
- Treat subscriptions as reconnectable event streams with an explicit
  resynchronisation path.

Do not add federation, subscriptions, DataLoader or Relay conventions merely
because they are common GraphQL patterns.

## Evidence and documentation

Test the lowest deterministic contract and the highest observable boundary:

- valid, invalid, unknown-version and malformed responses;
- timeouts, unavailable service, rate limiting and exhausted retries;
- pagination, duplicate or reordered events and ambiguous mutation outcomes;
- OAuth state/issuer mismatch, expiry, refresh rotation and refresh races;
- webhook invalid signatures, replay, deduplication and failure recovery; and
- GraphQL partial data, resolver errors and bounded resource use.

Use local fakes or sanitised contract fixtures for repeatability. Recorded
traffic must contain no secrets or unapproved personal/proprietary data and
must retain its provenance. Live-provider tests require explicit credentials,
external-action authority and safe disposable targets.

Keep one canonical machine-readable or written contract. Derive examples and
consumer documentation from it where practical, state version and
compatibility expectations, and never publish real credentials or payloads.
