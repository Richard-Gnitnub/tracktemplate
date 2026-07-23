"""Qualified FreeCAD persistence for canonical transition state."""

import hashlib

import FreeCAD as App

from tracktemplate.application.transition_state import (
    TRANSITION_STATE_SCHEMA_ID,
    TransitionState,
    TransitionStateError,
    transition_state_from_json,
    transition_state_to_json,
)


FREECAD_TRANSITION_OBJECT_TYPE = "App::FeaturePython"
FREECAD_PROPERTY_GROUP = "Track Template"
FREECAD_RECORD_TYPE_PROPERTY = "TrackTemplateRecordType"
FREECAD_STATE_JSON_PROPERTY = "TrackTemplateStateJSON"
FREECAD_TRANSITION_RECORD_TYPE = TRANSITION_STATE_SCHEMA_ID
FREECAD_CUSTOM_PROPERTIES = (
    FREECAD_RECORD_TYPE_PROPERTY,
    FREECAD_STATE_JSON_PROPERTY,
)

__all__ = (
    "FREECAD_TRANSITION_OBJECT_TYPE",
    "FREECAD_PROPERTY_GROUP",
    "FREECAD_RECORD_TYPE_PROPERTY",
    "FREECAD_STATE_JSON_PROPERTY",
    "FREECAD_TRANSITION_RECORD_TYPE",
    "FREECAD_CUSTOM_PROPERTIES",
    "FreeCADTransitionStore",
    "TransitionDocumentError",
    "find_transition_object",
    "read_transition_object",
)


class TransitionDocumentError(RuntimeError):
    """Structured failure at the FreeCAD canonical-state boundary."""

    def __init__(
        self,
        code,
        message,
        object_name="",
        source_code="",
        recoverable=True,
        document_mutation=False,
    ):
        self.code = str(code)
        self.detail = str(message)
        self.object_name = str(object_name)
        self.source_code = str(source_code)
        self.recoverable = bool(recoverable)
        self.document_mutation = bool(document_mutation)
        location = " on {!r}".format(self.object_name) if self.object_name else ""
        super().__init__("{}{}: {}".format(self.code, location, self.detail))

    def diagnostic(self):
        """Return a JSON-compatible, adapter-neutral diagnostic."""
        return {
            "code": self.code,
            "message": self.detail,
            "object_name": self.object_name,
            "source_code": self.source_code,
            "recoverable": self.recoverable,
            "document_mutation": self.document_mutation,
        }


def _object_name(obj):
    try:
        return str(getattr(obj, "Name", ""))
    except Exception:
        return ""


def _object_properties(obj):
    try:
        return tuple(obj.PropertiesList)
    except Exception as error:
        raise TransitionDocumentError(
            "invalid-object-reference",
            "a live FreeCAD document object is required",
            _object_name(obj),
        ) from error


def _require_live_object(obj):
    try:
        document = obj.Document
        registered = App.getDocument(str(document.Name))
        present = any(item is obj for item in document.Objects)
    except Exception as error:
        raise TransitionDocumentError(
            "invalid-object-reference",
            "a live FreeCAD document object is required",
            _object_name(obj),
        ) from error
    if registered is not document or not present:
        raise TransitionDocumentError(
            "invalid-object-reference",
            "the object is not present in its registered live document",
            _object_name(obj),
        )
    return document


def _require_open_document(document):
    try:
        name = str(document.Name)
        registered = App.getDocument(name)
    except Exception as error:
        raise TransitionDocumentError(
            "invalid-document",
            "a live FreeCAD document is required",
        ) from error
    if registered is not document:
        raise TransitionDocumentError(
            "invalid-document",
            "the supplied document is not the registered live document",
        )
    return document


def _require_object_document(document, obj):
    owning_document = _require_live_object(obj)
    if owning_document is not document:
        raise TransitionDocumentError(
            "object-document-mismatch",
            "the transition object does not belong to the supplied document",
            _object_name(obj),
        )


def _property_text(obj, property_name):
    if property_name not in _object_properties(obj):
        raise TransitionDocumentError(
            "invalid-record-envelope",
            "required property {!r} is missing".format(property_name),
            _object_name(obj),
        )
    try:
        return str(getattr(obj, property_name))
    except Exception as error:
        raise TransitionDocumentError(
            "invalid-record-envelope",
            "required property {!r} cannot be read".format(property_name),
            _object_name(obj),
        ) from error


def _is_transition_candidate(obj):
    properties = set(_object_properties(obj))
    if FREECAD_RECORD_TYPE_PROPERTY not in properties:
        if FREECAD_STATE_JSON_PROPERTY in properties:
            raise TransitionDocumentError(
                "invalid-record-envelope",
                "canonical state exists without a record type",
                _object_name(obj),
            )
        return False
    record_type = _property_text(obj, FREECAD_RECORD_TYPE_PROPERTY)
    if record_type != FREECAD_TRANSITION_RECORD_TYPE:
        return False
    return True


def read_transition_object(obj):
    """Read one owned object without mutating it or trusting its label/name."""
    _require_live_object(obj)
    if not _is_transition_candidate(obj):
        raise TransitionDocumentError(
            "not-transition-record",
            "the object is not a canonical transition record",
            _object_name(obj),
        )
    try:
        type_id = str(obj.TypeId)
    except Exception as error:
        raise TransitionDocumentError(
            "invalid-object-reference",
            "a live FreeCAD document object is required",
            _object_name(obj),
        ) from error
    if type_id != FREECAD_TRANSITION_OBJECT_TYPE:
        raise TransitionDocumentError(
            "unsupported-object-type",
            "expected {}, observed {}".format(
                FREECAD_TRANSITION_OBJECT_TYPE,
                type_id,
            ),
            _object_name(obj),
        )
    payload = _property_text(obj, FREECAD_STATE_JSON_PROPERTY)
    try:
        return transition_state_from_json(payload)
    except TransitionStateError as error:
        raise TransitionDocumentError(
            "invalid-canonical-state",
            str(error),
            _object_name(obj),
            source_code=error.code,
        ) from error


def find_transition_object(document, transition_id):
    """Return the unique object for a stable identity, or ``None``."""
    document = _require_open_document(document)
    if not isinstance(transition_id, str) or not transition_id.strip():
        raise TransitionDocumentError(
            "invalid-stable-identity",
            "transition_id must be a non-empty stable string",
        )
    matches = []
    for obj in sorted(document.Objects, key=lambda item: str(item.Name)):
        if not _is_transition_candidate(obj):
            continue
        state = read_transition_object(obj)
        if state.intent.transition_id == transition_id:
            matches.append(obj)
    if len(matches) > 1:
        raise TransitionDocumentError(
            "duplicate-stable-identity",
            "{} canonical objects use transition identity {!r}".format(
                len(matches),
                transition_id,
            ),
        )
    return matches[0] if matches else None


def _validated_profile_id(qualification):
    if not isinstance(qualification, dict):
        raise TransitionDocumentError(
            "runtime-not-qualified",
            "bootstrap qualification evidence is required before writing",
        )
    evaluation = qualification.get("compatibility_evaluation") or {}
    runtime = qualification.get("runtime") or {}
    freecad = runtime.get("freecad") or {}
    profile_id = evaluation.get("matched_profile_id")
    if (
        evaluation.get("status") != "qualified"
        or not isinstance(profile_id, str)
        or not profile_id
        or freecad.get("available") is not True
    ):
        raise TransitionDocumentError(
            "runtime-not-qualified",
            "bootstrap evidence does not describe a qualified FreeCAD runtime",
        )
    try:
        recorded_version = tuple(int(value) for value in freecad["version_info"])
        live_version = tuple(int(value) for value in App.Version()[:3])
    except (KeyError, TypeError, ValueError) as error:
        raise TransitionDocumentError(
            "runtime-not-qualified",
            "bootstrap evidence has no usable FreeCAD version",
        ) from error
    if recorded_version != live_version:
        raise TransitionDocumentError(
            "runtime-evidence-mismatch",
            "qualified evidence is for {}, but the live host is {}".format(
                recorded_version,
                live_version,
            ),
        )
    return profile_id


def _require_undo(document):
    try:
        enabled = int(document.UndoMode) == 1
    except Exception:
        enabled = False
    if not enabled:
        raise TransitionDocumentError(
            "undo-disabled",
            "FreeCAD document UndoMode must be enabled before a write",
        )


def _transition_object_name(transition_id):
    digest = hashlib.sha256(transition_id.encode("utf-8")).hexdigest()[:16]
    return "TrackTemplateTransition_" + digest


def _add_string_property(obj, name, description):
    if name in _object_properties(obj):
        raise TransitionDocumentError(
            "property-collision",
            "new transition object already has property {!r}".format(name),
            _object_name(obj),
        )
    obj.addProperty(
        "App::PropertyString",
        name,
        FREECAD_PROPERTY_GROUP,
        description,
    )


def _write_transition_payload(obj, payload):
    setattr(obj, FREECAD_STATE_JSON_PROPERTY, payload)


def _initialise_transition_object(obj, payload):
    _add_string_property(
        obj,
        FREECAD_RECORD_TYPE_PROPERTY,
        "Adapter record type; canonical schema and version remain in the payload.",
    )
    _add_string_property(
        obj,
        FREECAD_STATE_JSON_PROPERTY,
        "Versioned canonical transition intent and accepted analytical result.",
    )
    setattr(obj, FREECAD_RECORD_TYPE_PROPERTY, FREECAD_TRANSITION_RECORD_TYPE)
    _write_transition_payload(obj, payload)
    obj.Label = "Track Template transition"
    for property_name in FREECAD_CUSTOM_PROPERTIES:
        obj.setEditorMode(property_name, 1)


def _abort_transaction(document, original_error):
    try:
        document.abortTransaction()
    except Exception as rollback_error:
        raise TransitionDocumentError(
            "transaction-rollback-failed",
            "FreeCAD could not abort the failed canonical-state transaction: {}".format(
                rollback_error
            ),
            recoverable=False,
            document_mutation=True,
        ) from original_error


def _raise_transaction_error(error, object_name=""):
    if isinstance(error, TransitionDocumentError):
        raise error
    raise TransitionDocumentError(
        "transaction-failed",
        str(error),
        object_name,
    ) from error


class FreeCADTransitionStore:
    """Qualified writer for one compact canonical transition object."""

    def __init__(self, qualification):
        self.qualified_profile_id = _validated_profile_id(qualification)

    def create(self, document, state):
        """Create one logical object as one atomic FreeCAD command."""
        document = _require_open_document(document)
        _require_undo(document)
        if not isinstance(state, TransitionState):
            raise TypeError("state must be a TransitionState")
        try:
            payload = transition_state_to_json(state)
        except TransitionStateError as error:
            raise TransitionDocumentError(
                "invalid-write-state",
                str(error),
                source_code=error.code,
            ) from error
        identity = state.intent.transition_id
        if find_transition_object(document, identity) is not None:
            raise TransitionDocumentError(
                "duplicate-stable-identity",
                "transition identity {!r} already exists".format(identity),
            )

        transaction_open = False
        obj = None
        try:
            document.openTransaction("Create Track Template transition " + identity)
            transaction_open = True
            obj = document.addObject(
                FREECAD_TRANSITION_OBJECT_TYPE,
                _transition_object_name(identity),
            )
            _initialise_transition_object(obj, payload)
            if transition_state_to_json(read_transition_object(obj)) != payload:
                raise TransitionDocumentError(
                    "write-verification-failed",
                    "the new object did not retain the requested canonical state",
                    _object_name(obj),
                )
            document.commitTransaction()
            transaction_open = False
            return obj
        except Exception as error:
            failed_object_name = _object_name(obj)
            if transaction_open:
                _abort_transaction(document, error)
            _raise_transaction_error(error, failed_object_name)

    def create_many(self, document, states):
        """Create a non-empty transition set as one atomic FreeCAD command."""
        document = _require_open_document(document)
        _require_undo(document)
        try:
            states = tuple(states)
        except TypeError as error:
            raise TypeError("states must be an iterable of TransitionState values") from error
        if not states:
            raise TransitionDocumentError(
                "empty-create-batch",
                "an atomic transition batch must contain at least one state",
            )

        prepared = []
        identities = set()
        for state in states:
            if not isinstance(state, TransitionState):
                raise TypeError("every batch item must be a TransitionState")
            try:
                payload = transition_state_to_json(state)
            except TransitionStateError as error:
                raise TransitionDocumentError(
                    "invalid-write-state",
                    str(error),
                    source_code=error.code,
                ) from error
            identity = state.intent.transition_id
            if identity in identities:
                raise TransitionDocumentError(
                    "duplicate-batch-stable-identity",
                    "transition identity {!r} occurs more than once in the batch".format(
                        identity
                    ),
                )
            identities.add(identity)
            prepared.append((identity, payload))

        for identity, _payload in prepared:
            if find_transition_object(document, identity) is not None:
                raise TransitionDocumentError(
                    "duplicate-stable-identity",
                    "transition identity {!r} already exists".format(identity),
                )

        transaction_open = False
        objects = []
        try:
            document.openTransaction("Create Track Template transition batch")
            transaction_open = True
            for identity, payload in prepared:
                obj = document.addObject(
                    FREECAD_TRANSITION_OBJECT_TYPE,
                    _transition_object_name(identity),
                )
                objects.append(obj)
                _initialise_transition_object(obj, payload)
            for obj, (_identity, payload) in zip(objects, prepared):
                if transition_state_to_json(read_transition_object(obj)) != payload:
                    raise TransitionDocumentError(
                        "write-verification-failed",
                        "a batch object did not retain its requested canonical state",
                        _object_name(obj),
                    )
            document.commitTransaction()
            transaction_open = False
            return tuple(objects)
        except Exception as error:
            failed_object_name = _object_name(objects[-1]) if objects else ""
            if transaction_open:
                _abort_transaction(document, error)
            _raise_transaction_error(error, failed_object_name)

    def update(self, document, obj, state):
        """Replace canonical state atomically, or make no history for a no-op."""
        document = _require_open_document(document)
        _require_undo(document)
        _require_object_document(document, obj)
        if not isinstance(state, TransitionState):
            raise TypeError("state must be a TransitionState")
        current = read_transition_object(obj)
        identity = current.intent.transition_id
        if state.intent.transition_id != identity:
            raise TransitionDocumentError(
                "stable-identity-mismatch",
                "updates cannot replace transition identity {!r} with {!r}".format(
                    identity,
                    state.intent.transition_id,
                ),
                _object_name(obj),
            )
        resolved = find_transition_object(document, identity)
        if resolved is not obj:
            raise TransitionDocumentError(
                "identity-resolution-mismatch",
                "stable identity did not resolve to the supplied object",
                _object_name(obj),
            )
        try:
            payload = transition_state_to_json(state)
        except TransitionStateError as error:
            raise TransitionDocumentError(
                "invalid-write-state",
                str(error),
                _object_name(obj),
                source_code=error.code,
            ) from error
        current_payload = _property_text(obj, FREECAD_STATE_JSON_PROPERTY)
        if current_payload == payload:
            return obj

        transaction_open = False
        try:
            document.openTransaction("Update Track Template transition " + identity)
            transaction_open = True
            _write_transition_payload(obj, payload)
            if transition_state_to_json(read_transition_object(obj)) != payload:
                raise TransitionDocumentError(
                    "write-verification-failed",
                    "the object did not retain the requested canonical state",
                    _object_name(obj),
                )
            document.commitTransaction()
            transaction_open = False
            return obj
        except Exception as error:
            failed_object_name = _object_name(obj)
            if transaction_open:
                _abort_transaction(document, error)
            _raise_transaction_error(error, failed_object_name)
