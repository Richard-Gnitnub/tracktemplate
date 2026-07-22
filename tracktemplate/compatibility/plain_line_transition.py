"""Read-only B14/B15 assessment for spacing-matched plain-line transitions.

The assessment proves whether one accepted legacy snapshot contains enough
unambiguous persisted input to construct the already accepted canonical
transition records.  It neither advertises nor performs migration and it
never grants document or production-output write authority.
"""

from dataclasses import dataclass
import json
import math
import re

from tracktemplate.application.transition_state import (
    TransitionState,
    analyse_transition_state,
    transition_state_to_json,
)
from tracktemplate.compatibility import legacy_document
from tracktemplate.domain.alignment import clothoid_entry_displacement
from tracktemplate.domain.transition import TransitionIntent


ASSESSMENT_SCHEMA_ID = (
    "tracktemplate.legacy-plain-line-transition-assessment"
)
ASSESSMENT_SCHEMA_VERSION = 1
FAMILY_ID = "plain-line-spacing-matched-transition-intent"
SUPPORTED_ALIGNMENT_MODE = "Euler - match spacings"
STATUS_CANONICAL_INPUTS_SUFFICIENT = "canonical-inputs-sufficient"
STATUS_INSPECTION_ONLY = "inspection-only"
STATUS_BLOCKED = "blocked-corrupt-or-ambiguous"
IDENTITY_BASIS = (
    "template-set-id+persisted-track-configuration-ordinal+transition-end"
)
_SETTINGS_ROLE = "Settings"
_PROPERTY_TYPES = (
    ("GeneratedBy", "App::PropertyString"),
    ("GeneratedRole", "App::PropertyString"),
    ("TemplateSetID", "App::PropertyString"),
    ("GeneratorVersion", "App::PropertyString"),
    ("TransitionLength", "App::PropertyLength"),
    ("CurveRadius", "App::PropertyLength"),
    ("TotalTurnAngle", "App::PropertyAngle"),
    ("ParallelTrackCount", "App::PropertyInteger"),
    ("TrackConfigurationJSON", "App::PropertyString"),
)
_TRACK_FIELDS = (
    "alignment_mode",
    "create_template",
    "curve_spacing",
    "entry_transition_length",
    "exit_transition_length",
    "finish_spacing",
    "name",
    "show_centreline",
    "side",
    "start_spacing",
    "width",
)

__all__ = (
    "ASSESSMENT_SCHEMA_ID",
    "ASSESSMENT_SCHEMA_VERSION",
    "FAMILY_ID",
    "IDENTITY_BASIS",
    "STATUS_CANONICAL_INPUTS_SUFFICIENT",
    "STATUS_INSPECTION_ONLY",
    "STATUS_BLOCKED",
    "SUPPORTED_ALIGNMENT_MODE",
    "PlainLineTransitionAssessment",
    "PlainLineTransitionCandidate",
    "PlainLineTransitionFinding",
    "assess_plain_line_transitions",
    "plain_line_transition_assessment_to_json",
)


@dataclass(frozen=True)
class PlainLineTransitionFinding:
    """One deterministic reason why the bounded family remains read-only."""

    level: str
    code: str
    object_name: str
    property_path: str
    message: str

    def to_record(self):
        return {
            "level": self.level,
            "code": self.code,
            "object_name": self.object_name,
            "property_path": self.property_path,
            "message": self.message,
        }


@dataclass(frozen=True)
class PlainLineTransitionCandidate:
    """One replay-verified canonical state derived without document mutation."""

    source_object_name: str
    template_set_id: str
    track_number: int
    end_name: str
    stored_transition_length_mm: float
    state: TransitionState

    def to_record(self):
        return {
            "canonical_state": json.loads(transition_state_to_json(self.state)),
            "end_name": self.end_name,
            "identity_basis": IDENTITY_BASIS,
            "source_object_name": self.source_object_name,
            "stored_transition_length_mm": self.stored_transition_length_mm,
            "template_set_id": self.template_set_id,
            "track_number": self.track_number,
        }


@dataclass(frozen=True)
class PlainLineTransitionAssessment:
    """Non-authorising result for the selected legacy calculation family."""

    status: str
    outer_inspection: legacy_document.LegacyDocumentInspection
    candidates: tuple
    findings: tuple

    @property
    def canonical_inputs_sufficient(self):
        return self.status == STATUS_CANONICAL_INPUTS_SUFFICIENT

    @property
    def write_authorized(self):
        return False

    @property
    def migration_authorized(self):
        return False

    @property
    def production_output_authorized(self):
        return False

    def to_record(self):
        return {
            "canonical_inputs_sufficient": self.canonical_inputs_sufficient,
            "candidates": [item.to_record() for item in self.candidates],
            "family_id": FAMILY_ID,
            "findings": [item.to_record() for item in self.findings],
            "migration_authorized": False,
            "outer_inspection": self.outer_inspection.to_record(),
            "production_output_authorized": False,
            "schema_id": ASSESSMENT_SCHEMA_ID,
            "schema_version": ASSESSMENT_SCHEMA_VERSION,
            "status": self.status,
            "write_authorized": False,
        }


class _AssessmentIssue(ValueError):
    def __init__(self, level, code, property_path, message):
        self.level = str(level)
        self.code = str(code)
        self.property_path = str(property_path)
        self.detail = str(message)
        super().__init__("{}: {}".format(self.code, self.detail))


def plain_line_transition_assessment_to_json(assessment):
    """Serialise one assessment deterministically for review evidence."""
    if not isinstance(assessment, PlainLineTransitionAssessment):
        raise TypeError("assessment must be a PlainLineTransitionAssessment")
    return json.dumps(
        assessment.to_record(),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _finding(level, code, object_name="", property_path="", message=""):
    return PlainLineTransitionFinding(
        str(level),
        str(code),
        str(object_name),
        str(property_path),
        str(message),
    )


def _finding_key(item):
    return (
        item.object_name,
        item.property_path,
        item.level,
        item.code,
        item.message,
    )


def _object_name(obj):
    try:
        return str(obj.Name)
    except Exception:
        return ""


def _properties(obj):
    try:
        names = tuple(obj.PropertiesList)
    except Exception as error:
        raise _AssessmentIssue(
            "blocking",
            "unreadable-settings-object",
            "PropertiesList",
            "the settings property list cannot be read",
        ) from error
    if any(not isinstance(name, str) for name in names):
        raise _AssessmentIssue(
            "blocking",
            "unreadable-settings-object",
            "PropertiesList",
            "the settings property list contains a non-text name",
        )
    return names


def _property_type(obj, property_name):
    try:
        property_type = obj.getTypeIdOfProperty(property_name)
    except Exception as error:
        raise _AssessmentIssue(
            "inspection",
            "missing-property-type-evidence",
            property_name,
            "the required FreeCAD property type cannot be established",
        ) from error
    if not isinstance(property_type, str) or not property_type:
        raise _AssessmentIssue(
            "inspection",
            "missing-property-type-evidence",
            property_name,
            "the required FreeCAD property type cannot be established",
        )
    return property_type


def _required_value(obj, properties, property_name, expected_type):
    if property_name not in properties:
        raise _AssessmentIssue(
            "inspection",
            "missing-required-property",
            property_name,
            "the selected family requires this persisted property",
        )
    observed_type = _property_type(obj, property_name)
    if observed_type != expected_type:
        raise _AssessmentIssue(
            "blocking",
            "invalid-property-type",
            property_name,
            "expected {!r}, observed {!r}".format(expected_type, observed_type),
        )
    try:
        return getattr(obj, property_name)
    except Exception as error:
        raise _AssessmentIssue(
            "blocking",
            "unreadable-required-property",
            property_name,
            "the selected family property cannot be read",
        ) from error


def _finite_number(value, property_path):
    raw_value = getattr(value, "Value", value)
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        raise _AssessmentIssue(
            "blocking",
            "invalid-number",
            property_path,
            "expected a finite number",
        )
    try:
        result = float(raw_value)
    except (OverflowError, TypeError, ValueError) as error:
        raise _AssessmentIssue(
            "blocking",
            "invalid-number",
            property_path,
            "expected a finite number",
        ) from error
    if not math.isfinite(result):
        raise _AssessmentIssue(
            "blocking",
            "invalid-number",
            property_path,
            "expected a finite number",
        )
    return result


def _integer(value, property_path):
    if isinstance(value, bool) or not isinstance(value, int):
        raise _AssessmentIssue(
            "blocking",
            "invalid-integer",
            property_path,
            "expected an integer",
        )
    return int(value)


def _text(value, property_path, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise _AssessmentIssue(
            "blocking",
            "invalid-text",
            property_path,
            "expected {}text".format("" if allow_empty else "non-empty "),
        )
    return value


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key {!r}".format(key))
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError("non-standard JSON number {!r}".format(value))


def _track_configurations(raw_payload):
    if not isinstance(raw_payload, str):
        raise _AssessmentIssue(
            "blocking",
            "invalid-track-configuration-property",
            "TrackConfigurationJSON",
            "the persisted track configuration must be JSON text",
        )
    try:
        payload = json.loads(
            raw_payload,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (TypeError, ValueError, RecursionError) as error:
        raise _AssessmentIssue(
            "blocking",
            "malformed-track-configuration",
            "TrackConfigurationJSON",
            str(error),
        ) from error
    if not isinstance(payload, list):
        raise _AssessmentIssue(
            "blocking",
            "invalid-track-configuration-root",
            "TrackConfigurationJSON",
            "expected an ordered array of secondary-track records",
        )
    return payload


def _normalise_track_config(record, index):
    path = "TrackConfigurationJSON[{}]".format(index)
    if not isinstance(record, dict):
        raise _AssessmentIssue(
            "blocking",
            "invalid-track-configuration-record",
            path,
            "expected an object",
        )
    observed = set(record)
    expected = set(_TRACK_FIELDS)
    if observed != expected:
        missing = sorted(expected - observed)
        unexpected = sorted(observed - expected)
        level = "blocking" if unexpected else "inspection"
        raise _AssessmentIssue(
            level,
            "unrecognised-track-configuration-fields",
            path,
            "missing {!r}; unexpected {!r}".format(missing, unexpected),
        )
    name = _text(record["name"], path + ".name", allow_empty=True)
    side = _text(record["side"], path + ".side")
    if side not in ("Inside", "Outside"):
        raise _AssessmentIssue(
            "blocking",
            "invalid-track-side",
            path + ".side",
            "expected 'Inside' or 'Outside'",
        )
    mode = _text(record["alignment_mode"], path + ".alignment_mode")
    for field_name in ("create_template", "show_centreline"):
        if not isinstance(record[field_name], bool):
            raise _AssessmentIssue(
                "blocking",
                "invalid-boolean",
                path + "." + field_name,
                "expected a JSON boolean",
            )
    values = {}
    for field_name in (
        "start_spacing",
        "curve_spacing",
        "finish_spacing",
        "entry_transition_length",
        "exit_transition_length",
        "width",
    ):
        values[field_name] = _finite_number(
            record[field_name],
            path + "." + field_name,
        )
    if min(
        values["start_spacing"],
        values["curve_spacing"],
        values["finish_spacing"],
        values["width"],
    ) <= 0.0:
        raise _AssessmentIssue(
            "blocking",
            "invalid-positive-track-input",
            path,
            "spacing and width values must be greater than zero",
        )
    if min(
        values["entry_transition_length"],
        values["exit_transition_length"],
    ) < 0.0:
        raise _AssessmentIssue(
            "blocking",
            "invalid-transition-length",
            path,
            "stored transition lengths cannot be negative",
        )
    return {
        "alignment_mode": mode,
        "curve_spacing": values["curve_spacing"],
        "entry_transition_length": values["entry_transition_length"],
        "exit_transition_length": values["exit_transition_length"],
        "finish_spacing": values["finish_spacing"],
        "name": name,
        "side": side,
        "start_spacing": values["start_spacing"],
        "width": values["width"],
    }


def _stable_transition_id(template_set_id, track_number, end_name):
    return "{}/curve-track/{}/transition/{}".format(
        template_set_id,
        track_number,
        end_name.lower(),
    )


def _settings_candidates(obj, generator_id):
    object_name = _object_name(obj)
    properties = _properties(obj)
    values = {}
    for property_name, expected_type in _PROPERTY_TYPES:
        values[property_name] = _required_value(
            obj,
            properties,
            property_name,
            expected_type,
        )
    if values["GeneratedBy"] != generator_id or values["GeneratedRole"] != _SETTINGS_ROLE:
        raise _AssessmentIssue(
            "blocking",
            "settings-identity-changed-during-assessment",
            "GeneratedBy/GeneratedRole",
            "the object no longer matches the inspected settings identity",
        )
    template_set_id = _text(values["TemplateSetID"], "TemplateSetID")
    if (
        re.fullmatch(r"SET-[0-9]{3,}", template_set_id) is None
        or int(template_set_id[4:]) <= 0
    ):
        raise _AssessmentIssue(
            "inspection",
            "unsupported-template-set-identity",
            "TemplateSetID",
            "the selected family requires a generated SET-nnn identity",
        )
    _text(values["GeneratorVersion"], "GeneratorVersion")
    main_transition = _finite_number(values["TransitionLength"], "TransitionLength")
    main_radius = _finite_number(values["CurveRadius"], "CurveRadius")
    total_angle_degrees = _finite_number(values["TotalTurnAngle"], "TotalTurnAngle")
    parallel_track_count = _integer(
        values["ParallelTrackCount"],
        "ParallelTrackCount",
    )
    if main_transition < 0.0 or main_radius <= 0.0 or abs(total_angle_degrees) <= 1.0e-9:
        raise _AssessmentIssue(
            "blocking",
            "invalid-main-alignment-input",
            "TransitionLength/CurveRadius/TotalTurnAngle",
            "the stored main transition, radius and angle cannot regenerate the alignment",
        )
    records = _track_configurations(values["TrackConfigurationJSON"])
    if parallel_track_count != len(records):
        raise _AssessmentIssue(
            "blocking",
            "parallel-track-count-mismatch",
            "ParallelTrackCount/TrackConfigurationJSON",
            "stored count {} does not match {} records".format(
                parallel_track_count,
                len(records),
            ),
        )
    if not records:
        raise _AssessmentIssue(
            "inspection",
            "no-secondary-transition-family",
            "TrackConfigurationJSON",
            "the selected solver family has no secondary track in this set",
        )

    normalised = [
        _normalise_track_config(record, index)
        for index, record in enumerate(records)
    ]
    unsupported = [
        (index, record["alignment_mode"])
        for index, record in enumerate(normalised)
        if record["alignment_mode"] != SUPPORTED_ALIGNMENT_MODE
    ]
    if unsupported:
        raise _AssessmentIssue(
            "inspection",
            "unsupported-alignment-mode",
            "TrackConfigurationJSON",
            "only {!r} is in this bounded family; observed {!r}".format(
                SUPPORTED_ALIGNMENT_MODE,
                unsupported,
            ),
        )

    total_angle_rad = math.radians(abs(total_angle_degrees))
    if total_angle_rad - (main_transition / main_radius) < -1.0e-9:
        raise _AssessmentIssue(
            "blocking",
            "invalid-main-alignment-input",
            "TransitionLength/CurveRadius/TotalTurnAngle",
            "the two stored main transitions consume more than the total turn angle",
        )
    _x_end, main_y_end, main_entry_angle = clothoid_entry_displacement(
        main_transition,
        main_radius,
    )
    circle_centre_y = main_y_end + (main_radius * math.cos(main_entry_angle))
    candidates = []
    for index, record in enumerate(normalised):
        track_number = index + 2
        side_factor = 1.0 if record["side"] == "Inside" else -1.0
        radius = (
            main_radius - record["curve_spacing"]
            if record["side"] == "Inside"
            else main_radius + record["curve_spacing"]
        )
        if radius <= record["width"] / 2.0:
            raise _AssessmentIssue(
                "blocking",
                "invalid-effective-radius",
                "TrackConfigurationJSON[{}]".format(index),
                "the effective radius cannot regenerate this track width",
            )
        end_inputs = (
            (
                "Entry",
                record["start_spacing"],
                record["entry_transition_length"],
            ),
            (
                "Exit",
                record["finish_spacing"],
                record["exit_transition_length"],
            ),
        )
        for end_name, spacing, stored_length in end_inputs:
            intent = TransitionIntent(
                transition_id=_stable_transition_id(
                    template_set_id,
                    track_number,
                    end_name,
                ),
                circle_centre_y_mm=circle_centre_y,
                radius_mm=radius,
                target_signed_offset_mm=side_factor * spacing,
                total_angle_rad=total_angle_rad,
                track_name=record["name"],
                end_name=end_name,
            )
            try:
                state = analyse_transition_state(TransitionState(intent=intent))
            except (TypeError, ValueError) as error:
                raise _AssessmentIssue(
                    "blocking",
                    "transition-replay-failed",
                    "TrackConfigurationJSON[{}].{}_transition_length".format(
                        index,
                        end_name.lower(),
                    ),
                    str(error),
                ) from error
            replayed_length = state.analysis.transition_length_mm
            if replayed_length != stored_length:
                raise _AssessmentIssue(
                    "blocking",
                    "stored-transition-result-mismatch",
                    "TrackConfigurationJSON[{}].{}_transition_length".format(
                        index,
                        end_name.lower(),
                    ),
                    "stored {!r}, replayed {!r}".format(
                        stored_length,
                        replayed_length,
                    ),
                )
            candidates.append(
                PlainLineTransitionCandidate(
                    source_object_name=object_name,
                    template_set_id=template_set_id,
                    track_number=track_number,
                    end_name=end_name,
                    stored_transition_length_mm=stored_length,
                    state=state,
                )
            )
    return template_set_id, tuple(candidates)


def assess_plain_line_transitions(document, compatibility_contract):
    """Assess the bounded family without mutating or authorising the document."""
    outer = legacy_document.inspect_legacy_document(
        document,
        compatibility_contract,
    )
    findings = []
    candidates = []
    if outer.status == legacy_document.STATUS_BLOCKED:
        findings.append(
            _finding(
                "blocking",
                "outer-ingress-blocked",
                message="the accepted outer detector found corrupt or conflicting evidence",
            )
        )
    elif outer.version_window_status != "accepted":
        findings.append(
            _finding(
                "inspection",
                "outer-version-window-not-accepted",
                message="the document is outside the owner-accepted B14/B15 read window",
            )
        )
    else:
        try:
            objects = tuple(document.Objects)
        except Exception as error:
            raise legacy_document.LegacyInspectionError(
                "invalid-document",
                "a readable Objects collection is required",
            ) from error
        settings = []
        for obj in sorted(objects, key=_object_name):
            try:
                properties = tuple(obj.PropertiesList)
                generated_by = (
                    getattr(obj, "GeneratedBy")
                    if "GeneratedBy" in properties
                    else None
                )
                generated_role = (
                    getattr(obj, "GeneratedRole")
                    if "GeneratedRole" in properties
                    else None
                )
            except Exception as error:
                raise legacy_document.LegacyInspectionError(
                    "unreadable-document-object",
                    "cannot re-read the inspected object {!r}".format(
                        _object_name(obj)
                    ),
                ) from error
            if generated_by == outer.generator_id and generated_role == _SETTINGS_ROLE:
                settings.append(obj)
        if not settings:
            findings.append(
                _finding(
                    "inspection",
                    "no-plain-line-settings-object",
                    message="no owned Settings object exposes this bounded family",
                )
            )
        set_claims = {}
        for obj in settings:
            properties = tuple(obj.PropertiesList)
            set_id = (
                getattr(obj, "TemplateSetID")
                if "TemplateSetID" in properties
                else None
            )
            if isinstance(set_id, str) and set_id:
                set_claims.setdefault(set_id, []).append(_object_name(obj))
        duplicate_names = set()
        for set_id in sorted(set_claims):
            names = tuple(sorted(set_claims[set_id]))
            if len(names) <= 1:
                continue
            duplicate_names.update(names)
            findings.append(
                _finding(
                    "blocking",
                    "ambiguous-template-set-settings",
                    names[0],
                    "TemplateSetID",
                    "more than one Settings object claims {!r}: {!r}".format(
                        set_id,
                        names,
                    ),
                )
            )
        for obj in settings:
            object_name = _object_name(obj)
            if object_name in duplicate_names:
                continue
            try:
                _template_set_id, object_candidates = _settings_candidates(
                    obj,
                    outer.generator_id,
                )
            except _AssessmentIssue as error:
                findings.append(
                    _finding(
                        error.level,
                        error.code,
                        object_name,
                        error.property_path,
                        error.detail,
                    )
                )
                continue
            candidates.extend(object_candidates)

    blocking = any(item.level == "blocking" for item in findings)
    if blocking:
        status = STATUS_BLOCKED
    elif findings or not candidates:
        status = STATUS_INSPECTION_ONLY
    else:
        status = STATUS_CANONICAL_INPUTS_SUFFICIENT
    candidates = (
        tuple(
            sorted(
                candidates,
                key=lambda item: (
                    item.template_set_id,
                    item.track_number,
                    0 if item.end_name == "Entry" else 1,
                ),
            )
        )
        if status == STATUS_CANONICAL_INPUTS_SUFFICIENT
        else ()
    )
    return PlainLineTransitionAssessment(
        status=status,
        outer_inspection=outer,
        candidates=candidates,
        findings=tuple(sorted(findings, key=_finding_key)),
    )
