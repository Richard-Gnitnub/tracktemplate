"""Project the finite research assembly into its 4 mm/ft comparison frame.

The canonical full-size geometry stays unchanged. This separate derived
boundary applies the exact length factor 5/381 about the same origin and
axes. It preserves names, incidence, ordering and separate components;
it applies no manufacturing compensation or Boolean fusion.
"""

from dataclasses import dataclass
from fractions import Fraction

from tracktemplate.domain.chair_assembly import ChairAssemblyGeometry


@dataclass(frozen=True)
class ChairModelComponentGeometry:
    """One model-mm component boundary, without full-size parameters."""

    vertices: tuple
    faces: tuple
    bounds_mm: tuple
    volume_mm3: object
    landmarks: tuple


@dataclass(frozen=True)
class ChairModelAssemblyGeometry:
    """Five derived boundaries in model mm, with their component volume sum."""

    components: tuple
    bounds_mm: tuple
    component_volume_sum_mm3: object
    landmarks: tuple


def _project_landmarks(landmarks, factor):
    return tuple(
        (name, tuple(coordinate * factor for coordinate in point))
        for name, point in landmarks
    )


def project_chair_assembly_to_model(full_size_geometry, scale_denominator):
    """Derive only the frozen 4 mm/ft boundary using exact arithmetic.

    The caller supplies a validated full-size assembly and the explicit
    Fraction(381, 5) denominator. Coordinates and lengths scale by 5/381;
    volumes scale by its cube. Exact algebraic coordinates retain their
    existing representation. No full-size parameter record is copied or
    relabelled as a model parameter record.
    """
    if not isinstance(full_size_geometry, ChairAssemblyGeometry):
        raise TypeError("full_size_geometry must be a ChairAssemblyGeometry")
    if not isinstance(scale_denominator, Fraction):
        raise TypeError("scale_denominator must be an exact Fraction")
    if scale_denominator != Fraction(381, 5):
        raise ValueError("only the explicit 4 mm/ft comparison is supported")
    factor = 1 / scale_denominator
    volume_factor = factor ** 3
    components = tuple(
        (role, ChairModelComponentGeometry(
            vertices=tuple(
                (name, x * factor, y * factor, z * factor)
                for name, x, y, z in geometry.vertices
            ),
            faces=geometry.faces,
            bounds_mm=tuple(value * factor for value in geometry.bounds_mm),
            volume_mm3=geometry.volume_mm3 * volume_factor,
            landmarks=_project_landmarks(geometry.landmarks, factor),
        ))
        for role, geometry in full_size_geometry.components
    )
    return ChairModelAssemblyGeometry(
        components=components,
        bounds_mm=tuple(value * factor
                        for value in full_size_geometry.bounds_mm),
        component_volume_sum_mm3=(
            full_size_geometry.component_volume_sum_mm3 * volume_factor
        ),
        landmarks=_project_landmarks(full_size_geometry.landmarks, factor),
    )
