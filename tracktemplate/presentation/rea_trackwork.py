"""Disposable batched lines for explicit REA research trackwork."""

from contextlib import contextmanager
from dataclasses import dataclass
import math
import re

from tracktemplate.application.rea_turnout_state import (
    REA_HOSTS_PROPERTY,
    REA_INTENT_JSON_PROPERTY,
    REA_RECORD_TYPE_PROPERTY,
)

REA_TRACKWORK_VIEW_MODE = "REA research"
REA_TRACKWORK_VIEW_ELEMENT = "ReaTrackwork"
_ROOT_NAME = "TrackTemplateReaResearchViewV1"


def _signature(value):
    if not isinstance(value, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", value,
    ) is None:
        raise ValueError("A prepared SHA-256 source signature is required.")
    return value


@dataclass(frozen=True)
class ReaTrackworkLine:
    """One identified world-space polyline in millimetres."""

    visual_id: str
    layer_id: str
    points: tuple

    def __post_init__(self):
        if not isinstance(self.visual_id, str) or not self.visual_id:
            raise ValueError("A stable visual identity is required.")
        if self.layer_id not in ("rails", "timbers"):
            raise ValueError("Expected a rail or timber display layer.")
        if not isinstance(self.points, tuple) or len(self.points) < 2:
            raise ValueError("A polyline requires at least two points.")
        for point in self.points:
            if not isinstance(point, tuple) or len(point) != 3:
                raise ValueError("World points require three millimetre values.")
            try:
                valid = all(
                    type(value) in (int, float) and math.isfinite(value)
                    for value in point
                )
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError("World coordinates must be finite numbers.")


@dataclass(frozen=True)
class ReaTrackworkScene:
    """Ordered derived lines belonging to one stable logical entity."""

    entity_id: str
    lines: tuple

    def __post_init__(self):
        if not isinstance(self.entity_id, str) or not self.entity_id:
            raise ValueError("A stable logical entity identity is required.")
        if not isinstance(self.lines, tuple) or not self.lines:
            raise ValueError("A research scene needs ordered display lines.")
        if any(not isinstance(line, ReaTrackworkLine) for line in self.lines):
            raise ValueError("Expected validated research display lines.")
        ids = tuple(line.visual_id for line in self.lines)
        if len(set(ids)) != len(ids):
            raise ValueError("Visual identities must be unique in the scene.")


@dataclass(frozen=True)
class _Binding:
    root: object
    coordinates: object
    line_set: object


@dataclass(frozen=True)
class _Snapshot:
    scene: object
    signature: str
    binding: object
    diagnostic: str
    visibility: bool
    dependencies: tuple
    observed_object: object
    observer_app: object


def _binding(scene, coin):
    root = coin.SoSeparator()
    color = coin.SoBaseColor()
    color.rgb.setValue(0.18, 0.18, 0.18)
    style = coin.SoDrawStyle()
    style.lineWidth.setValue(1.5)
    coordinates = coin.SoCoordinate3()
    points = tuple(point for line in scene.lines for point in line.points)
    coordinates.point.setValues(0, len(points), points)
    lines = coin.SoLineSet()
    counts = tuple(len(line.points) for line in scene.lines)
    lines.numVertices.setValues(0, len(counts), counts)
    for child in (color, style, coordinates, lines):
        root.addChild(child)
    return _Binding(root, coordinates, lines)


def read_rea_trackwork_view(obj):
    """Resolve an owned view without replacing an existing visible scene."""
    view = getattr(obj, "ViewObject", None)
    if view is None or view.Proxy is None or type(view.Proxy) is int:
        return None
    proxy = view.Proxy
    if not isinstance(proxy, ReaTrackworkViewProvider):
        raise ValueError("A foreign ViewProvider cannot be adopted.")
    if proxy._view is not None and proxy._view is not view:
        raise ValueError("The ViewProvider belongs to a different object.")
    if proxy._view is None:
        proxy.attach(view)
    return proxy


def attach_rea_trackwork_view(obj, scene, signature):
    """Create or rebuild the injected GUI view; headless objects have none."""
    view = obj.ViewObject
    if view is None:
        return None
    proxy = view.Proxy
    if isinstance(proxy, ReaTrackworkViewProvider):
        proxy.attach(view)
        proxy.replace(scene, signature)
        return proxy
    return ReaTrackworkViewProvider(obj, scene, signature)


class ReaTrackworkViewProvider:
    """Keep Coin state disposable; restoration waits for explicit rebuild."""

    def __init__(self, obj, scene, signature, *, coin_module=None):
        self._empty()
        self._coin = coin_module
        view = obj.ViewObject
        original = view.Proxy
        if original is not None and type(original) is not int:
            raise ValueError("A foreign ViewProvider cannot be replaced.")
        self._original_proxy = original
        try:
            view.Proxy = self
            self.attach(view)
            self.replace(scene, signature)
        except Exception:
            if self.selection_root is not None:
                self.selection_root.removeAllChildren()
            view.Proxy = original
            raise

    def _empty(self):
        self.scene = None
        self.signature = ""
        self.diagnostic = "Research display requires explicit rebuild."
        self.selection_root = None
        self._view = None
        self._coin = None
        self._binding = None
        self._deferred = 0
        self._original_proxy = None
        self._dependencies = ()
        self._observed_object = None
        self._observed_document = None
        self._observer_app = None

    def attach(self, view_object):
        """Attach an empty owned mode; never calculate railway geometry."""
        if not hasattr(self, "_view"):
            self._empty()
        if self._view is view_object and self.selection_root is not None:
            return
        if self._coin is None:
            from pivy import coin
            self._coin = coin
        switch = view_object.SwitchNode
        owned = tuple(
            switch.getChild(index)
            for index in range(switch.getNumChildren())
            if str(switch.getChild(index).getName()) == _ROOT_NAME
        )
        if len(owned) > 1:
            raise ValueError("Duplicate REA research display modes.")
        if owned:
            root = owned[0]
            root.removeAllChildren()
        else:
            root = self._coin.SoType.fromName("SoFCSelection").createInstance()
            if root is None:
                raise ValueError("FreeCAD selection node is unavailable.")
            root.setName(_ROOT_NAME)
            view_object.addDisplayMode(root, REA_TRACKWORK_VIEW_MODE)
        self._view = view_object
        self.selection_root = root
        view_object.DisplayMode = REA_TRACKWORK_VIEW_MODE
        switch.whichChild.setValue(switch.findChild(root))

    def snapshot(self):
        """Retain the exact derived binding and visibility for rollback."""
        return _Snapshot(self.scene, self.signature, self._binding,
                         self.diagnostic, bool(self._view.Visibility),
                         self._dependencies, self._observed_object,
                         self._observer_app)

    def replace(self, scene, signature):
        """Build before swapping the visible scene, with no document write."""
        if not isinstance(scene, ReaTrackworkScene):
            raise TypeError("Expected ReaTrackworkScene.")
        signature = _signature(signature)
        candidate = _binding(scene, self._coin)
        if self._binding is None:
            self.selection_root.addChild(candidate.root)
        else:
            self.selection_root.replaceChild(self._binding.root,
                                             candidate.root)
        self.scene, self.signature = scene, signature
        self._binding = candidate
        self.diagnostic = ""

    def restore(self, snapshot):
        """Restore previously retained nodes without recalculation."""
        self.selection_root.removeAllChildren()
        if snapshot.binding is not None:
            self.selection_root.addChild(snapshot.binding.root)
        self.scene, self.signature = snapshot.scene, snapshot.signature
        self._binding = snapshot.binding
        self.diagnostic = snapshot.diagnostic
        self._view.Visibility = snapshot.visibility
        if snapshot.observer_app is not None:
            self.observe_dependencies(
                snapshot.observed_object, snapshot.dependencies,
                app_module=snapshot.observer_app,
            )
        elif not self._stop_observing():
            raise RuntimeError(self.diagnostic)

    def observe_dependencies(self, obj, dependencies, *, app_module=None):
        """Watch only declared source objects; never calculate in callbacks."""
        dependencies = tuple(dependencies)
        if any(item.Document is not obj.Document for item in dependencies):
            raise ValueError("Display dependencies must share one document.")
        if app_module is None:
            import FreeCAD
            app_module = FreeCAD
        if self._observer_app is not None and self._observer_app is not app_module:
            if not self._stop_observing():
                raise RuntimeError(self.diagnostic)
        if self._observer_app is None:
            self._observer_app = app_module
            try:
                app_module.addDocumentObserver(self)
            except Exception as error:
                try:
                    self.invalidate("Observer registration failed: " + str(error))
                finally:
                    self._stop_observing()
                raise
        self._observed_object = obj
        self._observed_document = obj.Document
        self._dependencies = dependencies

    def _stop_observing(self):
        self._dependencies = ()
        self._observed_object = self._observed_document = None
        if self._observer_app is not None:
            try:
                self._observer_app.removeDocumentObserver(self)
            except Exception as error:
                self.diagnostic = "Observer cleanup failed: {}".format(error)
                return False
            self._observer_app = None
        return True

    def slotChangedObject(self, obj, property_name):
        """Invalidate a changed dependency, including changes during Undo."""
        if any(obj is item for item in self._dependencies):
            self.invalidate("Host or settings changed; rebuild the display.")

    def slotDeletedObject(self, obj):
        """Invalidate deleted dependencies and release deleted own objects."""
        if obj is self._observed_object:
            self.onDelete(self._view, ())
        elif any(obj is item for item in self._dependencies):
            self.invalidate("A display dependency was deleted.")

    def slotDeletedDocument(self, document):
        """Release this observer when its own document closes."""
        if document is self._observed_document:
            self.onDelete(self._view, ())

    def onDelete(self, view_object, subelements):
        """Permit deletion and retain any uncertain cleanup diagnostic."""
        try:
            self.invalidate("Research display removed.")
        except Exception as error:
            self.diagnostic = "Display cleanup failed: {}".format(error)
        self._stop_observing()
        return True

    def invalidate(self, diagnostic):
        """Clear stale or faulty geometry while preserving canonical data."""
        self.selection_root.removeAllChildren()
        self.scene = self._binding = None
        self.signature = ""
        self.diagnostic = str(diagnostic)

    @contextmanager
    def defer_document_updates(self):
        """Let the transactional writer replace canonical and view state."""
        self._deferred += 1
        try:
            yield
        finally:
            self._deferred -= 1

    def updateData(self, obj, property_name):
        """Clear changes outside the writer, including Undo and Redo."""
        if self._deferred or self.selection_root is None:
            return
        if property_name in (REA_INTENT_JSON_PROPERTY, REA_HOSTS_PROPERTY,
                             REA_RECORD_TYPE_PROPERTY):
            self.invalidate("Canonical state changed; rebuild the display.")

    def selection_for_element(self, name):
        """Resolve the selected logical entity independently of labels."""
        if name != REA_TRACKWORK_VIEW_ELEMENT or self.scene is None:
            raise ValueError("No current REA research selection exists.")
        return self.scene.entity_id

    def getElementPicked(self, picked_point):
        """Return the stable logical subelement only for this visible root."""
        if (self.scene is not None and picked_point.getPath().findNode(
                self.selection_root) >= 0):
            return REA_TRACKWORK_VIEW_ELEMENT
        return None

    def getDetailPath(self, subname, path, append):
        """Build a selectable path for the stable logical entity."""
        self.selection_for_element(subname)
        if append:
            switch = self._view.SwitchNode
            if switch.whichChild.getValue() != switch.findChild(
                self.selection_root,
            ):
                raise ValueError("The REA research display is not active.")
            path.append(self._view.RootNode)
            path.append(switch)
            path.append(self.selection_root)
        return True

    def getDisplayModes(self, view_object):
        return [REA_TRACKWORK_VIEW_MODE]

    def getDefaultDisplayMode(self):
        return REA_TRACKWORK_VIEW_MODE

    def setDisplayMode(self, mode):
        if mode != REA_TRACKWORK_VIEW_MODE:
            self.invalidate("Unknown display mode; rebuild the display.")
            raise ValueError("Unknown REA research display mode.")
        return mode

    def dispose(self):
        """Clear the owned view and restore its original default proxy."""
        self.invalidate("Research display detached.")
        if not self._stop_observing():
            raise RuntimeError(self.diagnostic)
        if self._view.Proxy is self:
            self._view.Proxy = self._original_proxy

    def dumps(self):
        """Persist no sampled geometry, callbacks, signatures or Coin nodes."""
        return None

    def loads(self, state):
        """Initialize restored proxies empty, without trusting saved caches."""
        self._empty()
