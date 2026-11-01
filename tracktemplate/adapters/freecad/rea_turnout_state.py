"""Transactional storage of one explicit REA research TO or XO intent."""

from contextlib import nullcontext
import hashlib
import re

from tracktemplate.application.rea_turnout_state import (
    REA_HOSTS_PROPERTY,
    REA_INTENT_JSON_PROPERTY,
    REA_RECORD_TYPE_PROPERTY,
    REA_TRACKWORK_SCHEMA_ID,
    ReaTrackworkStateError,
    rea_trackwork_intent_from_json,
    rea_trackwork_intent_to_json,
    replace_rea_trackwork_intent,
)


_PROPERTY_TYPES = (
    (REA_RECORD_TYPE_PROPERTY, "App::PropertyString"),
    (REA_INTENT_JSON_PROPERTY, "App::PropertyString"),
    (REA_HOSTS_PROPERTY, "App::PropertyLinkList"),
)


class ReaTrackworkDocumentError(RuntimeError):
    """Recoverable refusal or an explicit failure of transaction recovery."""

    def __init__(self, code, detail, *, source_code="", recoverable=True,
                 document_mutation=False):
        self.code, self.detail = code, str(detail)
        self.source_code = source_code
        self.recoverable = recoverable
        self.document_mutation = document_mutation
        super().__init__("{}: {}".format(code, detail))

    def diagnostic(self):
        return {"code": self.code, "message": self.detail,
                "source_code": self.source_code,
                "recoverable": self.recoverable,
                "document_mutation": self.document_mutation}


def _app():
    import FreeCAD
    return FreeCAD


def _document(document):
    if _app().getDocument(str(document.Name)) is not document:
        raise ReaTrackworkDocumentError("invalid-document",
                                       "A registered live document is required.")
    return document


def _member(document, obj):
    if (obj.Document is not document
            or not any(item is obj for item in document.Objects)):
        raise ReaTrackworkDocumentError("object-document-mismatch",
                                       "The object is not in this document.")


def _hosts(document, intent, hosts):
    hosts = tuple(hosts)
    if tuple(host.Name for host in hosts) != intent.host_names:
        raise ReaTrackworkDocumentError("host-reference-mismatch",
                                       "Ordered hosts differ from intent.")
    for host in hosts:
        _member(document, host)
        if getattr(host, "TemplateSetID", None) != intent.template_set_id:
            raise ReaTrackworkDocumentError("host-template-set-mismatch",
                                           "Host template set differs.")
    return hosts


def _payload(intent):
    try:
        return rea_trackwork_intent_to_json(intent)
    except ReaTrackworkStateError as error:
        raise ReaTrackworkDocumentError("invalid-canonical-intent", str(error),
                                       source_code=error.code) from error


def _dependencies(document, hosts, dependencies):
    dependencies = tuple(hosts if dependencies is None else dependencies)
    for dependency in dependencies:
        _member(document, dependency)
    if any(not any(host is item for item in dependencies) for host in hosts):
        raise ReaTrackworkDocumentError("missing-display-dependency",
                                       "Every host must be observed.")
    return dependencies


def _candidate(obj):
    properties = obj.PropertiesList
    if not any(name in properties for name, _type_id in _PROPERTY_TYPES):
        return False
    if (REA_RECORD_TYPE_PROPERTY not in properties
            or getattr(obj, REA_RECORD_TYPE_PROPERTY)
            != REA_TRACKWORK_SCHEMA_ID):
        raise ReaTrackworkDocumentError("invalid-record-envelope",
                                       "Missing or unknown REA record type.")
    return True


def read_rea_trackwork_object(obj):
    """Read strict intent and ordered host links without altering the object."""
    document = _document(obj.Document)
    _member(document, obj)
    if not _candidate(obj):
        raise ReaTrackworkDocumentError("not-rea-record",
                                       "Expected a REA research record.")
    if obj.TypeId != "App::FeaturePython":
        raise ReaTrackworkDocumentError("unsupported-object-type",
                                       "Expected App::FeaturePython.")
    for name, type_id in _PROPERTY_TYPES:
        if (name not in obj.PropertiesList
                or obj.getTypeIdOfProperty(name) != type_id):
            raise ReaTrackworkDocumentError("invalid-record-envelope",
                                           "Missing or mistyped " + name)
    try:
        intent = rea_trackwork_intent_from_json(
            getattr(obj, REA_INTENT_JSON_PROPERTY),
        )
    except ReaTrackworkStateError as error:
        raise ReaTrackworkDocumentError("invalid-canonical-intent", str(error),
                                       source_code=error.code) from error
    _hosts(document, intent, getattr(obj, REA_HOSTS_PROPERTY))
    return intent


def read_rea_trackwork_objects(document):
    """Read owned records in logical identity order; reject duplicate IDs."""
    document = _document(document)
    records, identities = [], set()
    for obj in document.Objects:
        if not _candidate(obj):
            continue
        intent = read_rea_trackwork_object(obj)
        if intent.entity_id in identities:
            raise ReaTrackworkDocumentError("duplicate-stable-identity",
                                           "Duplicate REA logical identity.")
        identities.add(intent.entity_id)
        records.append((obj, intent))
    return tuple(sorted(records, key=lambda record: record[1].entity_id))


def find_rea_trackwork_object(document, entity_id):
    """Find the unique owned object by canonical identity, never its label."""
    return next((obj for obj, intent in read_rea_trackwork_objects(document)
                 if intent.entity_id == entity_id), None)


def _label(intent):
    spec = intent.source_specification
    return "REA {} 1:{:g} {} (research)".format(
        spec.switch_size, spec.crossing_ratio, intent.entity_kind,
    )


def _current(signature, current_signature):
    if (not isinstance(signature, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", signature) is None
            or not callable(current_signature)):
        raise ReaTrackworkDocumentError("invalid-prepared-state",
                                       "A signed prepared scene is required.")
    if current_signature() != signature:
        raise ReaTrackworkDocumentError("stale-prepared-state",
                                       "Source, hosts or occupancy changed.")


def _scene(intent, scene):
    if getattr(scene, "entity_id", None) != intent.entity_id:
        raise ReaTrackworkDocumentError("invalid-prepared-scene",
                                       "Scene and intent identities differ.")


def _qualified(qualification):
    evaluation = qualification.get("compatibility_evaluation", {})
    freecad = qualification.get("runtime", {}).get("freecad", {})
    profile = evaluation.get("matched_profile_id")
    if (evaluation.get("status") != "qualified" or not profile
            or freecad.get("available") is not True
            or tuple(freecad.get("version_info", ()))
            != tuple(int(value) for value in _app().Version()[:3])):
        raise ReaTrackworkDocumentError("runtime-not-qualified",
                                       "Matching bootstrap evidence is required.")
    return profile


class FreeCADReaTrackworkStore:
    """Write intent and its disposable display as one research operation."""

    def __init__(self, qualification, *, view_factory=None):
        self.qualified_profile_id = _qualified(qualification)
        self._view_factory = view_factory
        self._views = {}

    def view_for(self, obj):
        """Return this store's currently attached disposable view, if any."""
        entry = self._views.get(id(obj))
        return entry[1] if entry is not None and entry[0] is obj else None

    def _attach(self, obj, scene, signature):
        if self._view_factory is not None:
            view = self._view_factory(obj, scene, signature)
        elif _app().GuiUp:
            raise ReaTrackworkDocumentError(
                "view-factory-required",
                "The GUI composition must supply its research view factory.",
            )
        else:
            return None
        if view is None:
            return None
        self._views[id(obj)] = (obj, view)
        return view

    def invalidate_view(self, obj, diagnostic):
        """Clear a faulty or stale view without rewriting canonical state."""
        view = self.view_for(obj)
        if view is not None:
            view.invalidate(diagnostic)

    def check_view(self, obj, current_signature):
        """Clear a stale view; callers supply source-aware host currentness."""
        view = self.view_for(obj)
        if view is None:
            return False
        try:
            read_rea_trackwork_object(obj)
            _current(view.signature, current_signature)
        except Exception as error:
            view.invalidate(str(error))
            return False
        return True

    def detach_view(self, obj):
        """Dispose only this store's derived view, keeping canonical intent."""
        view = self.view_for(obj)
        if view is not None:
            view.dispose()
            del self._views[id(obj)]

    def rebuild(self, obj, scene, signature, *, current_signature,
                dependencies=None):
        """Rebuild a validated current view after open, without undo history."""
        try:
            intent = read_rea_trackwork_object(obj)
            dependencies = _dependencies(
                obj.Document, getattr(obj, REA_HOSTS_PROPERTY), dependencies,
            )
            _scene(intent, scene)
            _current(signature, current_signature)
            view = self.view_for(obj)
            if view is None:
                view = self._attach(obj, scene, signature)
            else:
                view.replace(scene, signature)
            if view is not None:
                view.observe_dependencies(obj, dependencies)
            _current(signature, current_signature)
        except Exception as error:
            self.invalidate_view(obj, str(error))
            raise
        return obj

    def create(self, document, intent, scene, signature, *, hosts,
               current_signature, dependencies=None):
        """Create one logical object and its view in one transaction."""
        return self._write(document, None, intent, scene, signature,
                           hosts, current_signature, dependencies)

    def update(self, document, obj, intent, scene, signature, *, hosts,
               current_signature, dependencies=None):
        """Edit atomically; unchanged canonical bytes create no history."""
        return self._write(document, obj, intent, scene, signature,
                           hosts, current_signature, dependencies)

    def _write(self, document, obj, intent, scene, signature, hosts,
               current_signature, dependencies):
        document = _document(document)
        if int(document.UndoMode) != 1:
            raise ReaTrackworkDocumentError("undo-disabled",
                                           "Enable document Undo before writing.")
        payload = _payload(intent)
        _scene(intent, scene)
        hosts = _hosts(document, intent, hosts)
        dependencies = _dependencies(document, hosts, dependencies)
        existing = find_rea_trackwork_object(document, intent.entity_id)
        previous = None
        if obj is None and existing is not None:
            raise ReaTrackworkDocumentError("duplicate-stable-identity",
                                           "This logical identity already exists.")
        if obj is not None:
            _member(document, obj)
            previous = read_rea_trackwork_object(obj)
            try:
                replace_rea_trackwork_intent(previous, intent)
            except ReaTrackworkStateError as error:
                raise ReaTrackworkDocumentError("invalid-replacement", str(error),
                                               source_code=error.code) from error
            if existing is not obj:
                raise ReaTrackworkDocumentError("identity-resolution-mismatch",
                                               "Logical identity is not unique.")
        _current(signature, current_signature)
        view = self.view_for(obj) if obj is not None else None
        old_payload = getattr(obj, REA_INTENT_JSON_PROPERTY) if obj else None
        if payload == old_payload:
            if (view is None or view.signature != signature
                    or view.scene != scene):
                return self.rebuild(obj, scene, signature,
                                    current_signature=current_signature,
                                    dependencies=dependencies)
            view.observe_dependencies(obj, dependencies)
            return obj
        snapshot = view.snapshot() if view is not None else None
        old_label = obj.Label if obj is not None else None
        old_hosts = tuple(getattr(obj, REA_HOSTS_PROPERTY)) if obj else None
        defer = getattr(view, "defer_document_updates", nullcontext)
        created = obj is None
        opened = False
        with defer():
            try:
                document.openTransaction("{} REA research {}".format(
                    "Create" if created else "Edit", intent.entity_id,
                ))
                opened = True
                if created:
                    name = "ReaTrackwork_" + hashlib.sha256(
                        intent.entity_id.encode("utf-8"),
                    ).hexdigest()[:16]
                    obj = document.addObject("App::FeaturePython", name)
                    for name, type_id in _PROPERTY_TYPES:
                        if name in obj.PropertiesList:
                            raise ReaTrackworkDocumentError("property-collision",
                                                           name)
                        obj.addProperty(type_id, name, "Track Template",
                                        "Explicit REA research intent.")
                        obj.setEditorMode(name, 1)
                    setattr(obj, REA_RECORD_TYPE_PROPERTY, REA_TRACKWORK_SCHEMA_ID)
                setattr(obj, REA_INTENT_JSON_PROPERTY, payload)
                setattr(obj, REA_HOSTS_PROPERTY, list(hosts))
                if created or obj.Label == _label(previous):
                    obj.Label = _label(intent)
                if _payload(read_rea_trackwork_object(obj)) != payload:
                    raise ReaTrackworkDocumentError("write-verification-failed",
                                                   "Canonical readback differs.")
                if view is None:
                    view = self._attach(obj, scene, signature)
                else:
                    view.replace(scene, signature)
                if view is not None:
                    view.observe_dependencies(obj, dependencies)
                _current(signature, current_signature)
                document.commitTransaction()
                opened = False
                return obj
            except Exception as error:
                try:
                    if created:
                        try:
                            self.detach_view(obj)
                        finally:
                            if opened:
                                document.abortTransaction()
                        if any(item is obj for item in document.Objects):
                            raise RuntimeError("Created object survived abort.")
                    else:
                        if opened:
                            document.abortTransaction()
                        if (getattr(obj, REA_INTENT_JSON_PROPERTY) != old_payload
                                or tuple(getattr(obj, REA_HOSTS_PROPERTY))
                                != old_hosts or obj.Label != old_label):
                            raise RuntimeError("Canonical rollback differs.")
                        if snapshot is not None:
                            view.restore(snapshot)
                        elif view is not None:
                            self.detach_view(obj)
                except Exception as recovery_error:
                    try:
                        self.invalidate_view(obj, str(recovery_error))
                    except Exception as invalidation_error:
                        recovery_error = RuntimeError(
                            "{}; view invalidation failed: {}".format(
                                recovery_error, invalidation_error,
                            )
                        )
                    raise ReaTrackworkDocumentError(
                        "transaction-recovery-failed", str(recovery_error),
                        recoverable=False, document_mutation=True,
                    ) from error
                if isinstance(error, ReaTrackworkDocumentError):
                    raise
                raise ReaTrackworkDocumentError("transaction-failed",
                                               str(error)) from error
