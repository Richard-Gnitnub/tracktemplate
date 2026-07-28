"""Disposable Coin scene binding for the bounded transition preview."""

from dataclasses import dataclass, field
import math

from tracktemplate.application.transition_derived import (
    TransitionDerivedArtifact,
    transition_derived_contract_signature,
)
from tracktemplate.application.transition_state import TransitionStateError
from tracktemplate.presentation.transition_preview import (
    TransitionPreviewScene,
)


TRANSITION_COIN_CONTRACT_ID = (
    "tracktemplate.transition-coin.centreline.v1"
)

__all__ = (
    "TRANSITION_COIN_CONTRACT_ID",
    "TransitionCoinBinding",
    "TransitionCoinSelection",
    "TransitionCoinStyle",
    "build_transition_coin_binding",
)


def _coin_error(code, path, message):
    return TransitionStateError(code, path, message)


def _finite_coin_float(path, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _coin_error(
            "invalid-coin-style",
            path,
            "expected a finite number",
        )
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise _coin_error(
            "invalid-coin-style",
            path,
            "expected a finite number",
        ) from error
    if not math.isfinite(result):
        raise _coin_error(
            "invalid-coin-style",
            path,
            "expected a finite number",
        )
    return result


@dataclass(frozen=True)
class TransitionCoinStyle:
    """Complete renderer-owned style inputs for one Coin centreline."""

    line_color_rgb: tuple[float, float, float]
    line_width: float

    def __post_init__(self):
        color = self.line_color_rgb
        if not isinstance(color, tuple) or len(color) != 3:
            raise _coin_error(
                "invalid-coin-style",
                "$.coin.line_color_rgb",
                "expected an RGB tuple with three values",
            )
        converted = tuple(
            _finite_coin_float(
                "$.coin.line_color_rgb[{}]".format(index),
                value,
            )
            for index, value in enumerate(color)
        )
        if any(value < 0.0 or value > 1.0 for value in converted):
            raise _coin_error(
                "invalid-coin-style",
                "$.coin.line_color_rgb",
                "RGB values must be between zero and one",
            )
        line_width = _finite_coin_float(
            "$.coin.line_width",
            self.line_width,
        )
        if line_width <= 0.0:
            raise _coin_error(
                "invalid-coin-style",
                "$.coin.line_width",
                "line width must be positive",
            )
        object.__setattr__(self, "line_color_rgb", converted)
        object.__setattr__(self, "line_width", line_width)

    def contract_signature(self):
        """Sign every renderer-owned style input deterministically."""
        return transition_derived_contract_signature(
            TRANSITION_COIN_CONTRACT_ID,
            {
                "line_color_rgb": list(self.line_color_rgb),
                "line_width": self.line_width,
            },
        )


@dataclass(frozen=True)
class TransitionCoinSelection:
    """Map one derived Coin node back to stable preview/domain identities."""

    layer_id: str
    visual_id: str
    domain_id: str
    node: object = field(compare=False, repr=False)


class TransitionCoinBinding:
    """Own one disposable Coin root and its stable selection mapping."""

    def __init__(
        self,
        root,
        source_signature,
        style_signature,
        selections,
    ):
        self.root = root
        self.source_signature = source_signature
        self.style_signature = style_signature
        self._selections = tuple(selections)
        self._selection_by_node = {
            _coin_node_key(selection.node): selection
            for selection in self._selections
        }
        self._discarded = False
        self._cleanup_pending = False

    @property
    def selections(self):
        """Return the current stable selection records."""
        return self._selections

    def selection_for_node(self, node):
        """Resolve a Coin node by identity without trusting labels or order."""
        if self._discarded:
            raise _coin_error(
                "discarded-coin-binding",
                "$.coin.selection",
                "the Coin binding has been discarded",
            )
        node_key = _coin_node_key(node)
        selection = self._selection_by_node.get(node_key)
        if (
            selection is None
            or _coin_node_key(selection.node) != node_key
        ):
            raise _coin_error(
                "unknown-coin-selection",
                "$.coin.selection",
                "the Coin node does not belong to this binding",
            )
        return selection

    def discard(self):
        """Remove derived Coin children and identities idempotently."""
        if self._discarded and not self._cleanup_pending:
            return False
        self._discarded = True
        self._selection_by_node.clear()
        self._selections = ()
        self._cleanup_pending = True
        try:
            self.root.removeAllChildren()
        except Exception as error:
            raise _coin_error(
                "coin-scene-discard-failed",
                "$.coin.root",
                str(error),
            ) from error
        self._cleanup_pending = False
        return True


def _coin_node_key(node):
    node_id = getattr(node, "getNodeId", None)
    if callable(node_id):
        try:
            return ("coin-node-id", int(node_id()))
        except Exception as error:
            raise _coin_error(
                "coin-node-identity-failed",
                "$.coin.selection",
                "could not read Coin node identity: {}".format(error),
            ) from error
    return ("python-id", id(node))


def _require_coin_module(coin_module):
    required = (
        "SoSeparator",
        "SoBaseColor",
        "SoDrawStyle",
        "SoCoordinate3",
        "SoLineSet",
    )
    missing = tuple(
        name
        for name in required
        if not callable(getattr(coin_module, name, None))
    )
    if missing:
        raise _coin_error(
            "invalid-coin-module",
            "$.coin.module",
            "missing Coin constructors: {}".format(", ".join(missing)),
        )
    return coin_module


def _require_preview_artifact(artifact):
    if (
        not isinstance(artifact, TransitionDerivedArtifact)
        or artifact.stage != "preview"
        or not isinstance(artifact.payload, TransitionPreviewScene)
    ):
        raise _coin_error(
            "invalid-coin-source",
            "$.coin.source",
            "expected a renderer-neutral transition preview artifact",
        )
    return artifact


def build_transition_coin_binding(artifact, style, coin_module):
    """Build one unpersisted Coin binding without touching a document."""
    artifact = _require_preview_artifact(artifact)
    if not isinstance(style, TransitionCoinStyle):
        raise _coin_error(
            "invalid-coin-style",
            "$.coin.style",
            "expected TransitionCoinStyle",
        )
    coin_module = _require_coin_module(coin_module)

    root = None
    try:
        root = coin_module.SoSeparator()
        selections = []
        for polyline in artifact.payload.polylines:
            layer = coin_module.SoSeparator()
            color = coin_module.SoBaseColor()
            color.rgb.setValue(*style.line_color_rgb)
            draw_style = coin_module.SoDrawStyle()
            draw_style.lineWidth.setValue(style.line_width)
            coordinates = coin_module.SoCoordinate3()
            points = [
                (point.x_mm, point.y_mm, 0.0)
                for point in polyline.points
            ]
            coordinates.point.setValues(0, len(points), points)
            line_set = coin_module.SoLineSet()
            line_set.numVertices.setValue(len(points))
            for node in (color, draw_style, coordinates, line_set):
                layer.addChild(node)
            root.addChild(layer)
            selections.append(
                TransitionCoinSelection(
                    layer_id=polyline.layer_id,
                    visual_id=polyline.visual_id,
                    domain_id=polyline.domain_id,
                    node=line_set,
                )
            )
        return TransitionCoinBinding(
            root=root,
            source_signature=artifact.source_signature,
            style_signature=style.contract_signature(),
            selections=selections,
        )
    except Exception as error:
        cleanup_error = None
        if root is not None:
            try:
                root.removeAllChildren()
            except Exception as secondary_error:
                cleanup_error = secondary_error
        detail = str(error)
        if cleanup_error is not None:
            detail += "; Coin cleanup also failed: {}".format(cleanup_error)
        raise _coin_error(
            "coin-scene-build-failed",
            "$.coin.root",
            detail,
        ) from error
