"""Explicit B/C research intent and signatures, without document effects.

The caller supplies complete host and occupancy snapshot signatures.
Their syntax and binding are checked here; a digest alone cannot prove
that its caller captured every canonical input. Geometry admission and
source gaps remain owned by the existing source preparation operation.
"""

from dataclasses import dataclass
import hashlib
import json
import math

from tracktemplate.domain.rea_turnout import ReaTurnoutError
from tracktemplate.domain.rea_turnout import ReaTurnoutSpecification


REA_TRACKWORK_SCHEMA_ID = "tracktemplate.rea-trackwork-intent"
REA_TRACKWORK_SCHEMA_VERSION = 1
REA_RECORD_TYPE_PROPERTY = "TrackTemplateReaRecordType"
REA_INTENT_JSON_PROPERTY = "TrackTemplateReaIntentJSON"
REA_HOSTS_PROPERTY = "TrackTemplateReaHosts"
_FACING = "Facing in host travel direction"
_TRAILING = "Trailing against host travel direction"
_SIGNATURE_PREFIX = "sha256:"
_HEXADECIMAL = "0123456789abcdef"
__all__ = ()


class ReaTrackworkStateError(ValueError):
    """Structured refusal that leaves canonical and document state intact."""

    def __init__(self, code, path, detail):
        self.code = code
        self.path = path
        self.detail = detail
        super().__init__("{} at {}: {}".format(code, path, detail))

    def diagnostic(self):
        """Return the non-mutating failure for the application adapter."""
        return {
            "code": self.code, "path": self.path, "message": self.detail,
            "recoverable": True, "document_mutation": False,
        }


def _number(value, path):
    if type(value) not in (int, float):
        raise ReaTrackworkStateError(
            "invalid-number", path, "A finite JSON number is required.",
        )
    try:
        result = float(value)
    except OverflowError as error:
        raise ReaTrackworkStateError(
            "invalid-number", path, "The number is not representable.",
        ) from error
    if not math.isfinite(result):
        raise ReaTrackworkStateError(
            "invalid-number", path, "A finite JSON number is required.",
        )
    return 0.0 if result == 0.0 else result


def _identity(value, path):
    if type(value) is not str or not value or value.strip() != value:
        raise ReaTrackworkStateError(
            "invalid-identity", path,
            "An explicit non-empty identity without outer spaces is required.",
        )


def _object(value, fields, path):
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ReaTrackworkStateError(
            "invalid-object", path, "A JSON object is required.",
        )
    if set(value) != set(fields):
        raise ReaTrackworkStateError(
            "invalid-fields", path,
            "Missing {!r}; unexpected {!r}.".format(
                sorted(set(fields) - set(value)),
                sorted(set(value) - set(fields)),
            ),
        )
    return value


def _source_from_record(value):
    path = "$.intent.source_specification"
    record = _object(value, (
        "schema_version", "switch_size", "crossing_ratio", "source_context",
        "source_archive_sha256", "calculation_revision", "track_gauge_mm",
        "flangeway_mm", "model_scale",
    ), path)
    try:
        specification = ReaTurnoutSpecification(
            switch_size=record["switch_size"],
            crossing_ratio=record["crossing_ratio"],
            schema_version=record["schema_version"],
            source_context=record["source_context"],
        )
    except ReaTurnoutError as error:
        raise ReaTrackworkStateError(
            "invalid-source-specification", path, str(error),
        ) from error
    expected = specification.to_record()
    for field in ("source_archive_sha256", "calculation_revision"):
        observed = record[field]
        if (type(observed) is not type(expected[field])
                or observed != expected[field]):
            raise ReaTrackworkStateError(
                "unsupported-source-contract", path + "." + field,
                "The retained source identity and revision are required.",
            )
    for field in ("track_gauge_mm", "flangeway_mm", "model_scale"):
        if _number(record[field], path + "." + field) != expected[field]:
            raise ReaTrackworkStateError(
                "unsupported-source-profile", path + "." + field,
                "The qualified source model profile is required.",
            )
    return specification


@dataclass(frozen=True)
class ReaTrackworkIntent:
    """One logical TO/XO request; host names are ordered object locators.

    Chainage and minimum radius are millimetres. The source specification
    supplies the dimensionless RAM ratio and the fixed model profile.
    Host membership and geometry must also pass preparation before commit.
    """

    entity_id: str
    entity_kind: str
    template_set_id: str
    host_names: tuple
    source_specification: ReaTurnoutSpecification
    reference_chainage_mm: float
    handing: str
    orientation: str | None = None
    arrangement: str | None = None
    minimum_radius_mm: float | None = None

    def __post_init__(self):
        for field in ("entity_id", "template_set_id"):
            _identity(getattr(self, field), "$.intent." + field)
        if (type(self.entity_kind) is not str
                or self.entity_kind not in ("turnout", "crossover")):
            raise ReaTrackworkStateError(
                "invalid-entity-kind", "$.intent.entity_kind",
                "Only turnout and crossover source intent is supported.",
            )
        count = 1 if self.entity_kind == "turnout" else 2
        if type(self.host_names) is not tuple or len(self.host_names) != count:
            raise ReaTrackworkStateError(
                "invalid-hosts", "$.intent.host_names",
                "An ordered tuple of {} host references is required.".format(
                    count,
                ),
            )
        for index, name in enumerate(self.host_names):
            _identity(name, "$.intent.host_names[{}]".format(index))
        if len(set(self.host_names)) != count:
            raise ReaTrackworkStateError(
                "invalid-hosts", "$.intent.host_names",
                "Crossover host references must be distinct.",
            )
        source = self.source_specification
        if type(source) is not ReaTurnoutSpecification:
            raise ReaTrackworkStateError(
                "invalid-source-specification", "$.intent.source_specification",
                "An explicit source specification is required.",
            )
        _source_from_record(source.to_record())
        chainage = _number(
            self.reference_chainage_mm, "$.intent.reference_chainage_mm",
        )
        if chainage < 0:
            raise ReaTrackworkStateError(
                "invalid-chainage", "$.intent.reference_chainage_mm",
                "Host chainage must be non-negative.",
            )
        object.__setattr__(self, "reference_chainage_mm", chainage)
        self._validate_placement()

    def _validate_placement(self):
        hands = ("Left-hand", "Right-hand")
        if self.entity_kind == "turnout":
            valid = (
                self.handing in hands
                and self.orientation in (_FACING, _TRAILING)
                and self.arrangement is None
                and self.minimum_radius_mm is None
            )
        else:
            valid = (
                self.handing in hands + ("Automatic handing",)
                and self.orientation is None
                and self.arrangement in (
                    "Facing crossover", "Trailing crossover",
                )
            )
            radius = _number(
                self.minimum_radius_mm, "$.intent.minimum_radius_mm",
            )
            # Existing CROSSOVER_MINIMUM_ALLOWED_RADIUS; not a fit limit.
            valid = valid and radius >= 50.0
            object.__setattr__(self, "minimum_radius_mm", radius)
        if not valid:
            raise ReaTrackworkStateError(
                "invalid-placement", "$.intent",
                "Explicit supported handing, direction and radius are required.",
            )


def _require_intent(intent):
    if type(intent) is not ReaTrackworkIntent:
        raise ReaTrackworkStateError(
            "invalid-intent", "$.intent", "A source intent is required.",
        )
    intent.__post_init__()


def _record(intent):
    _require_intent(intent)
    return {
        "schema": REA_TRACKWORK_SCHEMA_ID,
        "schema_version": REA_TRACKWORK_SCHEMA_VERSION,
        "intent": {
            "entity_id": intent.entity_id,
            "entity_kind": intent.entity_kind,
            "template_set_id": intent.template_set_id,
            "host_names": list(intent.host_names),
            "source_specification": intent.source_specification.to_record(),
            "reference_chainage_mm": intent.reference_chainage_mm,
            "handing": intent.handing,
            "orientation": intent.orientation,
            "arrangement": intent.arrangement,
            "minimum_radius_mm": intent.minimum_radius_mm,
        },
    }


def _canonical_json(value):
    return json.dumps(value, allow_nan=False, ensure_ascii=True,
                      sort_keys=True, separators=(",", ":"))


def rea_trackwork_intent_to_json(intent):
    """Encode complete source intent; no geometry or document mutation."""
    return _canonical_json(_record(intent))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReaTrackworkStateError(
                "duplicate-field", "$", "Duplicate field {!r}.".format(key),
            )
        result[key] = value
    return result


def _reject_constant(value):
    raise ReaTrackworkStateError(
        "invalid-number", "$", "Non-finite JSON constant {!r}.".format(value),
    )


def rea_trackwork_intent_from_json(text):
    """Decode only this explicit source schema; never fall back to C10."""
    if type(text) is not str:
        raise ReaTrackworkStateError(
            "invalid-json", "$", "Canonical intent must be JSON text.",
        )
    try:
        value = json.loads(text, object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
    except ReaTrackworkStateError:
        raise
    except (ValueError, RecursionError) as error:
        raise ReaTrackworkStateError(
            "invalid-json", "$", str(error),
        ) from error
    record = _object(value, ("schema", "schema_version", "intent"), "$")
    if record["schema"] != REA_TRACKWORK_SCHEMA_ID:
        raise ReaTrackworkStateError(
            "unsupported-schema", "$.schema",
            "The explicit REA trackwork intent schema is required.",
        )
    if (type(record["schema_version"]) is not int
            or record["schema_version"] != REA_TRACKWORK_SCHEMA_VERSION):
        raise ReaTrackworkStateError(
            "unsupported-schema-version", "$.schema_version",
            "Only source intent version 1 is supported.",
        )
    intent = _object(record["intent"], (
        "entity_id", "entity_kind", "template_set_id", "host_names",
        "source_specification", "reference_chainage_mm", "handing",
        "orientation", "arrangement", "minimum_radius_mm",
    ), "$.intent")
    if type(intent["host_names"]) is not list:
        raise ReaTrackworkStateError(
            "invalid-hosts", "$.intent.host_names",
            "Ordered host references must be a JSON array.",
        )
    values = dict(intent)
    values["host_names"] = tuple(intent["host_names"])
    values["source_specification"] = _source_from_record(
        intent["source_specification"],
    )
    return ReaTrackworkIntent(**values)


def replace_rea_trackwork_intent(current, replacement):
    """Validate a logical replacement; preserve identity and no-op state."""
    _require_intent(current)
    _require_intent(replacement)
    for field in ("entity_id", "entity_kind", "template_set_id"):
        if getattr(current, field) != getattr(replacement, field):
            raise ReaTrackworkStateError(
                "conflicting-identity", "$.intent." + field,
                "An edit must preserve logical kind, identity and template set.",
            )
    return current if current == replacement else replacement


def _signature(record):
    return _SIGNATURE_PREFIX + hashlib.sha256(
        _canonical_json(record).encode("utf-8"),
    ).hexdigest()


def rea_trackwork_intent_signature(intent):
    """Bind all canonical intent, including source/profile provenance."""
    return _signature(_record(intent))


def _require_signature(value, path):
    if (type(value) is not str
            or not value.startswith(_SIGNATURE_PREFIX)
            or len(value) != len(_SIGNATURE_PREFIX) + 64
            or any(c not in _HEXADECIMAL
                   for c in value[len(_SIGNATURE_PREFIX):])):
        raise ReaTrackworkStateError(
            "invalid-signature", path,
            "Expected sha256: and 64 lowercase hexadecimal characters.",
        )


def rea_trackwork_geometry_signature(intent, *, host_state, occupancy):
    """Bind derived geometry to intent and caller-owned complete snapshots.

    Each ordered host record contains object_name, template_set_id and
    state_signature. The latter and occupancy are complete snapshot SHA256
    signatures supplied by the application coordinator. Object names alone
    do not establish canonical railway identity or currentness.
    """
    record = _record(intent)
    if (type(host_state) not in (list, tuple)
            or len(host_state) != len(intent.host_names)):
        raise ReaTrackworkStateError(
            "invalid-host-state", "$.host_state",
            "Complete ordered host snapshot signatures are required.",
        )
    records = []
    for index, (name, value) in enumerate(zip(intent.host_names, host_state)):
        path = "$.host_state[{}]".format(index)
        host = _object(value, (
            "object_name", "template_set_id", "state_signature",
        ), path)
        if (host["object_name"] != name
                or host["template_set_id"] != intent.template_set_id):
            raise ReaTrackworkStateError(
                "conflicting-host-state", path,
                "Host snapshot order and identity must match the intent.",
            )
        _require_signature(host["state_signature"], path + ".state_signature")
        records.append(dict(host))
    _require_signature(occupancy, "$.occupancy")
    return _signature({
        "signature_format": "tracktemplate.rea-trackwork-geometry:1",
        "intent": record, "host_state": records, "occupancy": occupancy,
    })
