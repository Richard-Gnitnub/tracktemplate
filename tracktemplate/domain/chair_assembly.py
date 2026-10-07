"""Compose the five proven research components in their shared chair frame.

This finite identity placement keeps the key central. It applies no
random key displacement, skew, scale or manufacturing compensation.
The result preserves separate boundaries, including reference overlaps;
its volume sum is not the material volume of a Boolean union.
"""

from dataclasses import dataclass

from tracktemplate.domain.chair_base import ChairBaseGeometry
from tracktemplate.domain.chair_inner_jaw import ChairInnerJawGeometry
from tracktemplate.domain.chair_key import ChairKeyGeometry
from tracktemplate.domain.chair_outer_jaw import ChairOuterJawGeometry
from tracktemplate.domain.chair_seat import ChairSeatGeometry


CHAIR_ASSEMBLY_ROLES = (
    "base-plinth", "rail-seat", "key", "outer-jaw", "inner-jaw",
)
_GEOMETRY_TYPES = (
    ChairBaseGeometry, ChairSeatGeometry, ChairKeyGeometry,
    ChairOuterJawGeometry, ChairInnerJawGeometry,
)
_SHARED_PARAMETERS = (
    "chair_half_width_mm", "outer_corner_radius_mm", "edge_thickness_mm",
    "plinth_thickness_mm", "seat_thickness_mm", "rail_head_width_mm",
    "rail_foot_width_mm", "rail_web_width_mm", "rail_depth_mm",
    "outer_jaw_face_mm",
)
_COMMON_LANDMARKS = (
    "base-origin", "rail-seat-centre", "rail-top-centre",
    "gauge-face-at-seat",
)


@dataclass(frozen=True)
class ChairAssemblyGeometry:
    """Named analytical components in full-size mm, without host state."""

    components: tuple
    bounds_mm: tuple
    component_volume_sum_mm3: object
    landmarks: tuple


def assemble_chair_components(components):
    """Check shared inputs and compose exactly five central components.

    Equal purpose text alone does not establish shared meaning. The two
    jaws have separate depths and fillet radii with some equal names.
    Only the explicit shared quantities and outer-jaw references below
    must agree. These checks are mathematical consistency constraints,
    not physical rail-fit or prototype acceptance criteria.
    """
    if not isinstance(components, tuple) or len(components) != 5:
        raise ValueError("assembly requires exactly five named components")
    for item, role, expected in zip(
        components, CHAIR_ASSEMBLY_ROLES, _GEOMETRY_TYPES,
    ):
        if (not isinstance(item, tuple) or len(item) != 2
                or item[0] != role or not isinstance(item[1], expected)):
            raise ValueError("assembly component role, order or type differs")
    geometries = tuple(item[1] for item in components)
    for name in _SHARED_PARAMETERS:
        values = [getattr(g.parameters, name) for g in geometries
                  if hasattr(g.parameters, name)]
        if any(value != values[0] for value in values[1:]):
            raise ValueError("assembly shared input differs: " + name)

    outer, inner = geometries[3].parameters, geometries[4].parameters
    for stage in ("top", "mid"):
        if getattr(inner, "outer_" + stage + "_height_mm") != getattr(
            outer, stage + "_height_mm",
        ):
            raise ValueError("inner jaw references a different outer height")
    for stage in ("top", "mid", "seat", "plinth"):
        width = (getattr(outer, stage + "_half_rib_space_mm")
                 + getattr(outer, stage + "_rib_width_mm"))
        if getattr(inner, "outer_" + stage + "_half_width_mm") != width:
            raise ValueError("inner jaw references a different outer width")

    landmarks = dict(geometries[0].landmarks)
    for geometry in geometries[1:]:
        other = dict(geometry.landmarks)
        if any(other.get(name) != landmarks[name]
               for name in _COMMON_LANDMARKS):
            raise ValueError("assembly landmark frame differs")
    bounds = tuple(
        (min if index < 3 else max)(g.bounds_mm[index] for g in geometries)
        for index in range(6)
    )
    return ChairAssemblyGeometry(
        components=components, bounds_mm=bounds,
        component_volume_sum_mm3=sum(g.volume_mm3 for g in geometries),
        landmarks=tuple((name, landmarks[name]) for name in _COMMON_LANDMARKS),
    )
