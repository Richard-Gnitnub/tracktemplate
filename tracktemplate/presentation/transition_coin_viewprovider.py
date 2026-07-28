"""Development-only ViewProvider fixture for one transition Coin scene."""

from contextlib import contextmanager

from tracktemplate.application.transition_state import TransitionStateError
from tracktemplate.presentation.transition_coin import (
    TransitionCoinStyle,
    build_transition_coin_binding,
)


TRANSITION_COIN_VIEWPROVIDER_FIXTURE_ID = (
    "tracktemplate.transition-coin-viewprovider.fixture.v1"
)
TRANSITION_COIN_VIEW_ELEMENT = "TransitionPreviewCentreline"
TRANSITION_COIN_VIEW_MODE = "Transition Preview"

__all__ = (
    "TRANSITION_COIN_VIEW_ELEMENT",
    "TRANSITION_COIN_VIEW_MODE",
    "TRANSITION_COIN_VIEWPROVIDER_FIXTURE_ID",
    "TransitionCoinViewProviderFixture",
)


def _view_error(code, path, message):
    return TransitionStateError(code, path, message)


def _require_view_object(view_object):
    root = getattr(view_object, "RootNode", None)
    switch = getattr(view_object, "SwitchNode", None)
    add_display_mode = getattr(view_object, "addDisplayMode", None)
    if (
        root is None
        or switch is None
        or not callable(add_display_mode)
        or not callable(getattr(switch, "findChild", None))
        or not callable(getattr(switch, "getChild", None))
    ):
        raise _view_error(
            "invalid-coin-viewprovider",
            "$.coin.view_object",
            "expected a FreeCAD ViewObject with display-mode nodes",
        )
    return root, switch, add_display_mode


def _build_selection_root(coin_module):
    so_type = getattr(coin_module, "SoType", None)
    from_name = getattr(so_type, "fromName", None)
    if not callable(from_name):
        raise _view_error(
            "invalid-coin-viewprovider",
            "$.coin.module.SoType",
            "expected SoType.fromName for FreeCAD selection",
        )
    try:
        selection_type = from_name("SoFCSelection")
        create_instance = getattr(selection_type, "createInstance", None)
        if not callable(create_instance):
            raise TypeError("SoFCSelection type has no constructor")
        selection_root = create_instance()
    except Exception as error:
        raise _view_error(
            "invalid-coin-viewprovider",
            "$.coin.module.SoFCSelection",
            str(error),
        ) from error
    if selection_root is None or any(
        not callable(getattr(selection_root, name, None))
        for name in ("addChild", "removeAllChildren", "replaceChild")
    ):
        raise _view_error(
            "invalid-coin-viewprovider",
            "$.coin.module.SoFCSelection",
            "expected a mutable SoFCSelection node",
        )
    return selection_root


def _cleanup_view_nodes(selection_root, binding):
    errors = []
    if selection_root is not None:
        try:
            selection_root.removeAllChildren()
        except Exception as error:
            errors.append(
                "selection-root cleanup failed: {}".format(error)
            )
    if binding is not None:
        try:
            binding.discard()
        except Exception as error:
            errors.append("Coin binding cleanup failed: {}".format(error))
    return tuple(errors)


def _refresh_contract(
    state_reader,
    artifact_for_state,
    source_property_name,
):
    values = (
        state_reader,
        artifact_for_state,
        source_property_name,
    )
    if all(value is None for value in values):
        return None, None, None
    if (
        not callable(state_reader)
        or not callable(artifact_for_state)
        or not isinstance(source_property_name, str)
        or not source_property_name
    ):
        raise _view_error(
            "invalid-coin-viewprovider-refresh",
            "$.coin.refresh",
            "state_reader, artifact_for_state and a property name "
            "must be supplied together",
        )
    return state_reader, artifact_for_state, source_property_name


class TransitionCoinViewProviderFixture:
    """Attach one removable Coin preview to a development-only ViewObject."""

    def __init__(
        self,
        view_object,
        artifact,
        style,
        coin_module,
        state_reader=None,
        artifact_for_state=None,
        source_property_name=None,
    ):
        if not isinstance(style, TransitionCoinStyle):
            raise _view_error(
                "invalid-coin-viewprovider",
                "$.coin.style",
                "expected TransitionCoinStyle",
            )
        (
            state_reader,
            artifact_for_state,
            source_property_name,
        ) = _refresh_contract(
            state_reader,
            artifact_for_state,
            source_property_name,
        )
        self._artifact = artifact
        self._style = style
        self._coin_module = coin_module
        self._state_reader = state_reader
        self._artifact_for_state = artifact_for_state
        self._source_property_name = source_property_name
        self._document_update_deferrals = 0
        self._view_object = None
        self._view_root = None
        self._switch_node = None
        self._selection_root = None
        self._binding = None
        self._retired_bindings = []
        self._discarded = False
        self._cleanup_pending = False

        try:
            view_object.Proxy = self
        except Exception:
            raise
        if not self.attached:
            self._discarded = True
            raise _view_error(
                "coin-viewprovider-attach-failed",
                "$.coin.view_object.Proxy",
                "the qualified host did not call attach",
            )

    @property
    def attached(self):
        """Return whether the fixture currently owns a live view graph."""
        return (
            not self._discarded
            and self._view_object is not None
            and self._selection_root is not None
            and self._binding is not None
        )

    @property
    def selection_root(self):
        """Return the selectable root while the fixture is attached."""
        if not self.attached:
            raise _view_error(
                "discarded-coin-viewprovider",
                "$.coin.viewprovider",
                "the ViewProvider fixture is not attached",
            )
        return self._selection_root

    @property
    def display_mode(self):
        """Return the one development-only display-mode name."""
        self._require_attached()
        return TRANSITION_COIN_VIEW_MODE

    @property
    def element_name(self):
        """Return the stable FreeCAD subelement name for this v1 scene."""
        self._selection()
        return TRANSITION_COIN_VIEW_ELEMENT

    @property
    def source_signature(self):
        """Return the attached renderer-neutral source signature."""
        self._require_attached()
        return self._binding.source_signature

    @property
    def style_signature(self):
        """Return the attached renderer-style signature."""
        self._require_attached()
        return self._binding.style_signature

    def _require_attached(self):
        if not self.attached:
            raise _view_error(
                "discarded-coin-viewprovider",
                "$.coin.viewprovider",
                "the ViewProvider fixture is not attached",
            )

    def _selection(self):
        self._require_attached()
        selections = self._binding.selections
        if len(selections) != 1:
            raise _view_error(
                "invalid-coin-viewprovider",
                "$.coin.selection",
                "the v1 ViewProvider requires one selectable element",
            )
        return selections[0]

    def attach(self, view_object):
        """Build and attach the selectable scene when FreeCAD wires the proxy."""
        if self.attached:
            if view_object is self._view_object:
                return
            raise _view_error(
                "coin-viewprovider-attach-failed",
                "$.coin.view_object",
                "the fixture is already attached to another ViewObject",
            )
        if self._discarded:
            raise _view_error(
                "discarded-coin-viewprovider",
                "$.coin.viewprovider",
                "a discarded ViewProvider fixture cannot be reattached",
            )

        binding = None
        selection_root = None
        view_root = None
        switch_node = None
        try:
            binding = build_transition_coin_binding(
                self._artifact,
                self._style,
                self._coin_module,
            )
            selection_root = _build_selection_root(self._coin_module)
            selection_root.addChild(binding.root)
            (
                view_root,
                switch_node,
                add_display_mode,
            ) = _require_view_object(view_object)
            add_display_mode(
                selection_root,
                TRANSITION_COIN_VIEW_MODE,
            )
        except Exception as error:
            cleanup_errors = _cleanup_view_nodes(
                selection_root,
                binding,
            )
            self._view_object = view_object
            self._view_root = view_root
            self._switch_node = switch_node
            self._selection_root = selection_root
            self._binding = binding
            self._discarded = True
            self._cleanup_pending = bool(cleanup_errors)
            detail = str(error)
            if cleanup_errors:
                detail += "; cleanup also failed: {}".format(
                    "; ".join(cleanup_errors)
                )
            raise _view_error(
                "coin-viewprovider-attach-failed",
                "$.coin.view_object.RootNode",
                detail,
            ) from error

        self._view_object = view_object
        self._view_root = view_root
        self._switch_node = switch_node
        self._selection_root = selection_root
        self._binding = binding

    def selection_for_element(self, element_name):
        """Resolve a FreeCAD subelement name to stable preview identities."""
        selection = self._selection()
        if element_name != TRANSITION_COIN_VIEW_ELEMENT:
            raise _view_error(
                "unknown-coin-view-element",
                "$.coin.selection.element_name",
                "the element does not belong to this ViewProvider",
            )
        return selection

    def getDetailPath(self, subname, path, append):
        """Map a stable subelement name to the selectable Coin path."""
        self.selection_for_element(subname)
        if append:
            try:
                path.append(self._view_root)
                path.append(self._switch_node)
                mode_index = int(
                    self._switch_node.whichChild.getValue()
                )
                if (
                    mode_index < 0
                    or int(
                        self._switch_node.findChild(
                            self._selection_root
                        )
                    )
                    != mode_index
                ):
                    raise ValueError(
                        "the transition display mode is not active"
                    )
                path.append(self._selection_root)
            except Exception as error:
                raise _view_error(
                    "coin-view-selection-path-failed",
                    "$.coin.selection.path",
                    str(error),
                ) from error
        return True

    def getElementPicked(self, picked_point):
        """Map a picked selectable root back to its stable subelement name."""
        self._require_attached()
        try:
            path = picked_point.getPath()
            index = int(path.findNode(self._selection_root))
        except Exception as error:
            raise _view_error(
                "coin-view-selection-path-failed",
                "$.coin.selection.pick",
                str(error),
            ) from error
        if index < 0:
            raise _view_error(
                "unknown-coin-view-pick",
                "$.coin.selection.pick",
                "the picked path does not contain this ViewProvider",
            )
        return self.element_name

    def getDisplayModes(self, view_object):
        """Return the one Coin-only development display mode."""
        return [TRANSITION_COIN_VIEW_MODE]

    def getDefaultDisplayMode(self):
        """Return the default Coin-only development display mode."""
        return TRANSITION_COIN_VIEW_MODE

    def setDisplayMode(self, mode):
        """Accept only the registered development display mode."""
        if mode != TRANSITION_COIN_VIEW_MODE:
            raise _view_error(
                "unknown-coin-view-mode",
                "$.coin.display_mode",
                "the display mode does not belong to this ViewProvider",
            )
        return mode

    def _discard_retired_bindings(self):
        errors = []
        retained = []
        for binding in self._retired_bindings:
            try:
                binding.discard()
            except Exception as error:
                retained.append(binding)
                errors.append(str(error))
        self._retired_bindings = retained
        return tuple(errors)

    def refresh_for_state(self, state):
        """Replace the derived scene atomically for one canonical state."""
        self._require_attached()
        if self._artifact_for_state is None:
            raise _view_error(
                "coin-viewprovider-refresh-unavailable",
                "$.coin.refresh",
                "this fixture has no canonical-state refresh contract",
            )

        retired_errors = self._discard_retired_bindings()
        if retired_errors:
            self._cleanup_pending = True
            raise _view_error(
                "coin-viewprovider-refresh-failed",
                "$.coin.refresh.cleanup",
                "; ".join(retired_errors),
            )
        self._cleanup_pending = False

        candidate = None
        try:
            artifact = self._artifact_for_state(state)
            candidate = build_transition_coin_binding(
                artifact,
                self._style,
                self._coin_module,
            )
            if (
                candidate.source_signature
                == self._binding.source_signature
                and candidate.style_signature
                == self._binding.style_signature
            ):
                candidate.discard()
                return False
            self._selection_root.replaceChild(
                self._binding.root,
                candidate.root,
            )
        except Exception as error:
            cleanup_errors = []
            if candidate is not None:
                try:
                    candidate.discard()
                except Exception as cleanup_error:
                    cleanup_errors.append(str(cleanup_error))
            detail = str(error)
            if cleanup_errors:
                detail += "; candidate cleanup also failed: {}".format(
                    "; ".join(cleanup_errors)
                )
            raise _view_error(
                "coin-viewprovider-refresh-failed",
                "$.coin.refresh",
                detail,
            ) from error

        previous = self._binding
        self._artifact = artifact
        self._binding = candidate
        try:
            previous.discard()
        except Exception as error:
            self._retired_bindings.append(previous)
            self._cleanup_pending = True
            raise _view_error(
                "coin-viewprovider-refresh-failed",
                "$.coin.refresh.cleanup",
                str(error),
            ) from error
        self._cleanup_pending = False
        return True

    @contextmanager
    def defer_document_updates(self):
        """Defer callback refresh while an adapter owns an atomic write."""
        self._require_attached()
        self._document_update_deferrals += 1
        try:
            yield
        finally:
            self._document_update_deferrals -= 1

    def updateData(self, obj, property_name):
        """Refresh after canonical property changes, including Undo/Redo."""
        if (
            self._source_property_name is None
            or property_name != self._source_property_name
            or self._document_update_deferrals
            or not self.attached
        ):
            return None
        try:
            state = self._state_reader(obj)
        except Exception as error:
            raise _view_error(
                "coin-viewprovider-refresh-failed",
                "$.coin.refresh.state",
                str(error),
            ) from error
        return self.refresh_for_state(state)

    def dispose(self):
        """Clear selectable contents fail-closed, with deterministic retry."""
        if self._discarded and not self._cleanup_pending:
            return False
        self._discarded = True
        cleanup_errors = _cleanup_view_nodes(
            self._selection_root,
            self._binding,
        )
        cleanup_errors += self._discard_retired_bindings()
        if cleanup_errors:
            self._cleanup_pending = True
            raise _view_error(
                "coin-viewprovider-dispose-failed",
                "$.coin.view_object.RootNode",
                "; ".join(cleanup_errors),
            )
        self._cleanup_pending = False
        self._view_object = None
        self._view_root = None
        self._switch_node = None
        self._selection_root = None
        self._binding = None
        self._retired_bindings = []
        return True

    def dumps(self):
        """Persist no transient Coin or preview state."""
        return None

    def loads(self, state):
        """Accept no transient proxy state from FreeCAD."""
        return None
