"""Refuse unqualified legacy operations on stored B/C research dependencies.

    The source decoder and record identifiers belong to application state.
    This module reads host links without importing a FreeCAD adapter and
    never registers source intent in a legacy C10 catalogue.
"""

from tracktemplate.application.rea_turnout_state import (
    REA_HOSTS_PROPERTY,
    REA_INTENT_JSON_PROPERTY,
    REA_RECORD_TYPE_PROPERTY,
    REA_TRACKWORK_SCHEMA_ID,
    rea_trackwork_intent_from_json,
)


class ReaTrackworkAdmissionError(ValueError):
    """Source research dependencies cannot enter this legacy operation."""


def _present(obj, name):
    return (name in getattr(obj, "PropertiesList", ())
            or hasattr(obj, name))


def _source_intent(document, obj):
    try:
        marker = getattr(obj, REA_RECORD_TYPE_PROPERTY)
        payload = getattr(obj, REA_INTENT_JSON_PROPERTY)
        links = getattr(obj, REA_HOSTS_PROPERTY)
    except (AttributeError, RuntimeError, TypeError) as error:
        raise ReaTrackworkAdmissionError(
            "An incomplete REA source record prevents legacy admission."
        ) from error
    if marker != REA_TRACKWORK_SCHEMA_ID:
        raise ReaTrackworkAdmissionError(
            "An unknown REA source record prevents legacy admission."
        )
    if any(_present(obj, name) for name in ("TurnoutID", "CrossoverID")):
        raise ReaTrackworkAdmissionError(
            "A REA source object has conflicting legacy identity metadata."
        )
    try:
        intent = rea_trackwork_intent_from_json(payload)
    except ValueError as error:
        raise ReaTrackworkAdmissionError(
            "An invalid REA source intent prevents legacy admission."
        ) from error
    if (getattr(obj, "Document", None) is not document
            or getattr(obj, "TypeId", None) != "App::FeaturePython"
            or document.getObject(obj.Name) is not obj):
        raise ReaTrackworkAdmissionError(
            "The REA source object does not match its document."
        )
    if type(links) not in (list, tuple) or len(links) != len(intent.host_names):
        raise ReaTrackworkAdmissionError(
            "The REA source host links are incomplete."
        )
    for host, name in zip(links, intent.host_names):
        if (getattr(host, "Name", None) != name
                or getattr(host, "Document", None) is not document
                or document.getObject(name) is not host
                or not any(item is host for item in document.Objects)
                or getattr(host, "TemplateSetID", None)
                != intent.template_set_id):
            raise ReaTrackworkAdmissionError(
                "The REA source host identity or ordered link is invalid."
            )
    return intent


def source_records(document):
    """Read every source marker strictly; retain malformed records on refusal."""
    records, identities = [], set()
    for obj in getattr(document, "Objects", ()):
        if not any(_present(obj, name) for name in (
            REA_RECORD_TYPE_PROPERTY, REA_INTENT_JSON_PROPERTY,
            REA_HOSTS_PROPERTY,
        )):
            continue
        intent = _source_intent(document, obj)
        if intent.entity_id in identities:
            raise ReaTrackworkAdmissionError(
                "Duplicate REA source logical identities prevent admission."
            )
        identities.add(intent.entity_id)
        records.append((obj, intent))
    return tuple(sorted(records, key=lambda item: item[1].entity_id))


def refuse_rea_operation(
    document, *, set_id=None, host_names=(), entity_id=None,
):
    """Refuse any matching dependency; absent selectors mean the document.

    A malformed marker refuses even an apparently unrelated selector:
    its scope cannot safely be inferred. Valid unrelated source entities
    and legacy-only documents are unchanged.
    """
    records = source_records(document)
    if not records:
        return
    if (type(host_names) not in (tuple, list)
            or any(type(name) is not str or not name for name in host_names)
            or (set_id is not None and (type(set_id) is not str or not set_id))
            or (entity_id is not None
                and (type(entity_id) is not str or not entity_id))):
        raise ReaTrackworkAdmissionError(
            "Legacy admission needs explicit dependency selectors."
        )
    for _obj, intent in records:
        if (not (set_id or host_names or entity_id)
                or set_id == intent.template_set_id
                or entity_id == intent.entity_id
                or any(name in intent.host_names for name in host_names)):
            raise ReaTrackworkAdmissionError(
                "REA source research dependency {} requires its explicit "
                "source operation; legacy admission is not qualified."
                .format(intent.entity_id)
            )


def refuse_rea_entity_operation(module, document, entity_kind, entity_id):
    """Protect host integration before transaction or inherited mutation."""
    if not source_records(document):
        return
    identifier = str(entity_id or "").strip()
    refuse_rea_operation(document, entity_id=identifier or None)
    reader = getattr(module, entity_kind + "_config_by_id")
    config = reader(document, identifier)
    if config is None:
        return
    host_fields = (("host_object",) if entity_kind == "turnout"
                   else ("host_a_object", "host_b_object"))
    names = tuple(config[field] for field in host_fields if config.get(field))
    refuse_rea_operation(
        document, set_id=config.get("template_set_id"),
        host_names=names, entity_id=identifier or None,
    )
