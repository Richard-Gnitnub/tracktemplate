"""Development-only post-open attachment for canonical transition previews."""

from tracktemplate.application.transition_derived import TransitionDerivedCache
from tracktemplate.application.transition_state import (
    TransitionState,
    TransitionStateError,
)
from tracktemplate.presentation.transition_coin import TransitionCoinStyle
from tracktemplate.presentation.transition_coin_viewprovider import (
    TransitionCoinViewProviderFixture,
)
from tracktemplate.presentation.transition_preview import (
    TransitionPreviewSpecification,
    regenerate_transition_preview,
)


TRANSITION_COIN_DOCUMENT_ATTACHMENT_FIXTURE_ID = (
    "tracktemplate.transition-coin-document-attachment.fixture.v1"
)

__all__ = (
    "TRANSITION_COIN_DOCUMENT_ATTACHMENT_FIXTURE_ID",
    "TransitionCoinDocumentAttachmentFixture",
)


def _attachment_error(code, path, message):
    return TransitionStateError(code, path, message)


def _object_name(obj):
    try:
        return str(getattr(obj, "Name", ""))
    except Exception:
        return ""


def _require_callbacks(record_loader, state_reader, source_property_name):
    if (
        not callable(record_loader)
        or not callable(state_reader)
        or not isinstance(source_property_name, str)
        or not source_property_name
    ):
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.callbacks",
            "record_loader, state_reader and a property name are required",
        )


def _require_presentation_contract(specification, style):
    if not isinstance(specification, TransitionPreviewSpecification):
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.specification",
            "expected TransitionPreviewSpecification",
        )
    if not isinstance(style, TransitionCoinStyle):
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.style",
            "expected TransitionCoinStyle",
        )


def _document_objects(document):
    try:
        return tuple(document.Objects)
    except Exception as error:
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.document",
            "expected a document with an Objects collection",
        ) from error


def _require_document_member(document, obj):
    try:
        owning_document = obj.Document
        view_object = obj.ViewObject
    except Exception as error:
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.records",
            "each record requires a document object and ViewObject",
        ) from error
    if owning_document is not document or not any(
        candidate is obj for candidate in _document_objects(document)
    ):
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.records",
            "record {!r} is not present in the supplied document".format(
                _object_name(obj)
            ),
        )
    return view_object


def _require_transition_state(state, path):
    if not isinstance(state, TransitionState):
        raise _attachment_error(
            "invalid-coin-document-attachment",
            path,
            "expected canonical TransitionState",
        )
    return state


def _require_default_proxy(view_object, obj):
    try:
        proxy = view_object.Proxy
    except Exception as error:
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.records",
            "ViewObject.Proxy cannot be read for {!r}".format(
                _object_name(obj)
            ),
        ) from error
    if proxy is not None and type(proxy) is not int:
        raise _attachment_error(
            "invalid-coin-document-attachment",
            "$.coin.document_attachment.records",
            "record {!r} already has a non-default ViewProvider".format(
                _object_name(obj)
            ),
        )
    return proxy


class _AttachmentEntry:
    def __init__(self, obj, view_object, original_proxy, cache, proxy):
        self.obj = obj
        self.view_object = view_object
        self.original_proxy = original_proxy
        self.cache = cache
        self.proxy = proxy


def _is_original_proxy(proxy, original_proxy):
    return (
        proxy is original_proxy
        or (
            type(proxy) is int
            and type(original_proxy) is int
            and proxy == original_proxy
        )
    )


def _cleanup_resources(
    obj,
    view_object,
    proxy,
    original_proxy,
    cache,
):
    errors = []
    label = _object_name(obj) or "<pending attachment>"
    if not _is_original_proxy(proxy, original_proxy):
        dispose = getattr(proxy, "dispose", None)
        if callable(dispose):
            try:
                dispose()
            except Exception as error:
                errors.append(
                    "ViewProvider cleanup failed for {!r}: {}".format(
                        label,
                        error,
                    )
                )
    try:
        cache.discard()
    except Exception as error:
        errors.append(
            "preview-cache cleanup failed for {!r}: {}".format(
                label,
                error,
            )
        )
    try:
        current_proxy = view_object.Proxy
    except Exception as error:
        errors.append(
            "ViewProvider inspection failed for {!r}: {}".format(
                label,
                error,
            )
        )
    else:
        if current_proxy is proxy:
            try:
                view_object.Proxy = original_proxy
            except Exception as error:
                errors.append(
                    "ViewProvider restoration failed for {!r}: {}".format(
                        label,
                        error,
                    )
                )
        elif not _is_original_proxy(current_proxy, original_proxy):
            errors.append(
                "ViewProvider changed while attachment {!r} was active".format(
                    label
                )
            )
    return tuple(errors)


def _dispose_entry(entry):
    return _cleanup_resources(
        entry.obj,
        entry.view_object,
        entry.proxy,
        entry.original_proxy,
        entry.cache,
    )


def _dispose_candidate(view_object, original_proxy, cache):
    try:
        candidate = view_object.Proxy
    except Exception as error:
        cleanup_errors = []
        try:
            cache.discard()
        except Exception as cache_error:
            cleanup_errors.append(
                "cache cleanup failed: {}".format(cache_error)
            )
        try:
            view_object.Proxy = original_proxy
        except Exception as proxy_error:
            cleanup_errors.append(
                "ViewProvider restoration failed: {}".format(proxy_error)
            )
        detail = "failed ViewProvider cannot be read: {}".format(error)
        if cleanup_errors:
            detail += "; cleanup also failed: {}".format(
                "; ".join(cleanup_errors)
            )
        return (detail,)
    return _cleanup_resources(
        None,
        view_object,
        candidate,
        original_proxy,
        cache,
    )


class TransitionCoinDocumentAttachmentFixture:
    """Explicitly attach disposable previews to an existing document."""

    def __init__(
        self,
        document,
        *,
        record_loader,
        state_reader,
        source_property_name,
        specification,
        style,
        coin_module,
    ):
        _require_callbacks(
            record_loader,
            state_reader,
            source_property_name,
        )
        _require_presentation_contract(specification, style)
        self._document = document
        self._state_reader = state_reader
        self._source_property_name = source_property_name
        self._specification = specification
        self._style = style
        self._coin_module = coin_module
        self._entries = {}
        self._transition_ids = ()
        self._active = False

        records = self._load_records(record_loader)
        self._transition_ids = tuple(
            state.intent.transition_id for _obj, state in records
        )
        try:
            for obj, loaded_state in records:
                self._attach_record(obj, loaded_state)
        except Exception as error:
            cleanup_errors = self._dispose_entries()
            detail = str(error)
            if cleanup_errors:
                detail += "; cleanup also failed: {}".format(
                    "; ".join(cleanup_errors)
                )
            raise _attachment_error(
                "coin-document-attachment-failed",
                "$.coin.document_attachment",
                detail,
            ) from error
        self._active = True

    def _load_records(self, record_loader):
        try:
            loaded = tuple(record_loader(self._document))
        except Exception as error:
            raise _attachment_error(
                "coin-document-attachment-failed",
                "$.coin.document_attachment.records",
                str(error),
            ) from error

        records = []
        identities = set()
        objects = set()
        for index, record in enumerate(loaded):
            try:
                obj, state = record
            except (TypeError, ValueError) as error:
                raise _attachment_error(
                    "invalid-coin-document-attachment",
                    "$.coin.document_attachment.records[{}]".format(index),
                    "expected one (document_object, state) pair",
                ) from error
            state = _require_transition_state(
                state,
                "$.coin.document_attachment.records[{}].state".format(
                    index
                ),
            )
            _require_document_member(
                self._document,
                obj,
            )
            object_identity = id(obj)
            if object_identity in objects:
                raise _attachment_error(
                    "invalid-coin-document-attachment",
                    "$.coin.document_attachment.records",
                    "record {!r} occurs more than once".format(
                        _object_name(obj)
                    ),
                )
            objects.add(object_identity)
            identity = state.intent.transition_id
            if identity in identities:
                raise _attachment_error(
                    "invalid-coin-document-attachment",
                    "$.coin.document_attachment.records",
                    "transition identity {!r} occurs more than once".format(
                        identity
                    ),
                )
            identities.add(identity)
            records.append((obj, state))
        return tuple(
            sorted(
                records,
                key=lambda record: record[1].intent.transition_id,
            )
        )

    def _read_current_state(self, obj, expected_identity):
        try:
            state = self._state_reader(obj)
        except Exception as error:
            raise _attachment_error(
                "coin-document-attachment-refresh-failed",
                "$.coin.document_attachment.state",
                str(error),
            ) from error
        state = _require_transition_state(
            state,
            "$.coin.document_attachment.state",
        )
        if state.intent.transition_id != expected_identity:
            raise _attachment_error(
                "coin-document-attachment-refresh-failed",
                "$.coin.document_attachment.state.transition_id",
                "record {!r} no longer has transition identity {!r}".format(
                    _object_name(obj),
                    expected_identity,
                ),
            )
        return state

    def _attach_record(self, obj, loaded_state):
        identity = loaded_state.intent.transition_id
        view_object = _require_document_member(
            self._document,
            obj,
        )
        current_state = self._read_current_state(obj, identity)
        if current_state != loaded_state:
            raise _attachment_error(
                "coin-document-attachment-refresh-failed",
                "$.coin.document_attachment.state",
                "canonical state changed while the attachment was prepared",
            )
        original_proxy = _require_default_proxy(view_object, obj)
        cache = TransitionDerivedCache()

        def artifact_for_state(state):
            return regenerate_transition_preview(
                cache,
                state,
                self._specification,
            )

        try:
            if original_proxy is not None:
                view_object.Proxy = None
            artifact = artifact_for_state(current_state)
            proxy = TransitionCoinViewProviderFixture(
                view_object,
                artifact,
                self._style,
                self._coin_module,
                state_reader=self._state_reader,
                artifact_for_state=artifact_for_state,
                source_property_name=self._source_property_name,
            )
        except Exception as error:
            cleanup_errors = _dispose_candidate(
                view_object,
                original_proxy,
                cache,
            )
            if cleanup_errors:
                raise _attachment_error(
                    "coin-document-attachment-failed",
                    "$.coin.document_attachment.cleanup",
                    "{}; cleanup also failed: {}".format(
                        error,
                        "; ".join(cleanup_errors),
                    ),
                ) from error
            raise

        self._entries[identity] = _AttachmentEntry(
            obj,
            view_object,
            original_proxy,
            cache,
            proxy,
        )

    @property
    def attached(self):
        """Return whether the complete document attachment is active."""
        return self._active

    @property
    def attachment_count(self):
        """Return the number of records in the prepared attachment set."""
        return len(self._transition_ids)

    @property
    def transition_ids(self):
        """Return the deterministic stable-identity order."""
        return self._transition_ids

    def _require_active(self):
        if not self._active:
            raise _attachment_error(
                "discarded-coin-document-attachment",
                "$.coin.document_attachment",
                "the document attachment fixture is not active",
            )

    def _entry(self, transition_id):
        self._require_active()
        try:
            return self._entries[transition_id]
        except (KeyError, TypeError):
            raise _attachment_error(
                "unknown-coin-document-transition",
                "$.coin.document_attachment.transition_id",
                "the transition does not belong to this attachment",
            ) from None

    def proxy_for_transition(self, transition_id):
        """Return one attached development ViewProvider by stable identity."""
        return self._entry(transition_id).proxy

    def cache_for_transition(self, transition_id):
        """Return one disposable preview cache by stable identity."""
        return self._entry(transition_id).cache

    def refresh_transition(self, transition_id):
        """Refresh one attached preview from its current canonical state."""
        entry = self._entry(transition_id)
        state = self._read_current_state(entry.obj, transition_id)
        try:
            return entry.proxy.refresh_for_state(state)
        except Exception as error:
            raise _attachment_error(
                "coin-document-attachment-refresh-failed",
                "$.coin.document_attachment.refresh",
                str(error),
            ) from error

    def _dispose_entries(self):
        errors = []
        for identity in reversed(self._transition_ids):
            entry = self._entries.get(identity)
            if entry is not None:
                errors.extend(_dispose_entry(entry))
        return tuple(errors)

    def dispose(self):
        """Dispose the complete batch and restore every original proxy."""
        if not self._entries and not self._active:
            return ()
        self._active = False
        cleanup_errors = self._dispose_entries()
        if cleanup_errors:
            raise _attachment_error(
                "coin-document-attachment-dispose-failed",
                "$.coin.document_attachment.cleanup",
                "; ".join(cleanup_errors),
            )
        self._entries.clear()
        return self._transition_ids
