"""Explicit Templot 556b REA B/C source mathematics for transient geometry.

Templot source: Martin Wynne and OpenTemplot contributors, GPL-3.0-or-later.
Retained input provenance and output restrictions remain in force. This
module preserves the distinct legacy C10 calculation in domain.turnout;
it does not reinterpret legacy documents or qualify physical chair fit.
"""

from dataclasses import dataclass
import math


__all__ = ()

SOURCE_CONTEXT = "templot-556b-rea-bh-regular-auto-fit-square-on"
_SOURCE_MINFP = 1.0e-12  # control_room.pas:479; source arithmetic, not fit.
_SOURCE_MAX_RADIUS = 99995000.0  # control_room.pas:486; source sentinel.
_SOURCE_ARCHIVE_SHA256 = (
    "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
)


# Prototype inches and RAM ratios, switch_select.pas:1749-1858.
def _switch_data(switch_size):
    """Return fresh source values without shared mutable module state."""
    return {
        "B": {
            "planing": 88.0, "heel": 257.0, "radius": 7356.0,
            "planing_ratio": 32.0, "switch_rail": 270.0, "stock_rail": 360.0,
            "timber_intervals": (
                3.5, 28.0, 28.0, 28.0, 28.0, 28.0, 28.0,
                28.5, 28.5, 28.5, 26.0, 24.0,
            ),
        },
        "C": {
            "planing": 110.0, "heel": 329.0, "radius": 11520.0,
            "planing_ratio": 40.0, "switch_rail": 342.0, "stock_rail": 432.0,
            "timber_intervals": (
                3.5, 28.5, 28.5, 28.5, 30.0, 30.0, 30.0,
                30.0, 30.0, 30.0, 30.0, 30.0, 26.0, 24.0,
            ),
        },
    }[switch_size]


class ReaTurnoutError(ValueError):
    """A source request is invalid or needs a separately qualified branch."""

    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__("{}: {}".format(code, detail))


@dataclass(frozen=True)
class ReaTurnoutSpecification:
    """Opt into one fixed-profile, square-on source calculation.

    The continuous crossing ratio is dimensionless RAM. Construction has
    narrower source-qualified branches than Templot's numeric input domain.
    """

    switch_size: str
    crossing_ratio: float
    schema_version: int = 1
    source_context: str = SOURCE_CONTEXT

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ReaTurnoutError(
                "unsupported-source-version",
                "Only source version 1 is supported.",
            )
        if (type(self.switch_size) is not str
                or self.switch_size not in ("B", "C")):
            raise ReaTurnoutError(
                "invalid-switch", "The source switch size must be B or C.",
            )
        if type(self.crossing_ratio) not in (int, float):
            raise ReaTurnoutError(
                "invalid-crossing-ratio",
                "A finite numeric RAM ratio >= 0.5 is required.",
            )
        try:
            ratio = float(self.crossing_ratio)
        except OverflowError as error:
            raise ReaTurnoutError(
                "invalid-crossing-ratio",
                "The RAM ratio cannot be represented as a finite number.",
            ) from error
        if not math.isfinite(ratio) or ratio < 0.5:
            raise ReaTurnoutError(
                "invalid-crossing-ratio",
                "A finite numeric RAM ratio >= 0.5 is required.",
            )
        if (type(self.source_context) is not str
                or self.source_context != SOURCE_CONTEXT):
            raise ReaTurnoutError(
                "unsupported-source-context",
                "Only the named square-on context is supported.",
            )

    def to_record(self):
        """Return deterministic intent, separate from derived values."""
        return {
            "schema_version": self.schema_version,
            "switch_size": self.switch_size,
            "crossing_ratio": float(self.crossing_ratio),
            "source_context": self.source_context,
            "source_archive_sha256": _SOURCE_ARCHIVE_SHA256,
            "calculation_revision": 1,
            "track_gauge_mm": 16.5,
            "flangeway_mm": 1.0,
            "model_scale": 76.2,
        }


def _require_specification(spec):
    if type(spec) is not ReaTurnoutSpecification:
        raise ReaTurnoutError(
            "invalid-source-specification",
            "An explicit ReaTurnoutSpecification is required.",
        )
    spec.__post_init__()


def _source_context_flags():
    return {
        "xing_type_i": 0, "entry_straight_code": 0,
        "half_diamond": False, "plain_track": False, "gaunt": False,
        "retpar_i": 0, "timbers_equalized": False,
        "square_on_angled": False, "equalizing_fixed": False,
        "force_eq": False, "randangle": 0, "ccd_end_adjustments": 0,
        "ftimbspmax_inches": 30,
    }


def _crossing_counts(ratio):
    # math_unit.pas:3598-3623. Below 1:4 and improvised 20.125+ are refused.
    if ratio < 6.875:
        return 3, 5
    if ratio < 10.125:
        return 3, 6
    if ratio < 15.125:
        return 4, 7
    return 5, 8


def rea_turnout_dimensions(spec):
    """Return transient square-on REA B/C dimensions in model millimetres.

    This explicit source path does not replace legacy C10 arithmetic.
    It admits positive, nonstraight, nonimprovised regular crossings only.
    The inherited module extension is a product envelope, not source exit
    sleeper qualification. No physical-fit or production claim is made.
    """
    _require_specification(spec)
    k3n = float(spec.crossing_ratio)
    if k3n < 4.0:
        raise ReaTurnoutError(
            "unsupported-prototype-region",
            "Templot does not qualify normal prototype timbering below 1:4.",
        )
    if k3n >= 20.125:
        raise ReaTurnoutError(
            "unsupported-improvised-crossing",
            "The improvised vee-length branch is not construction-qualified.",
        )
    switch = _switch_data(spec.switch_size)
    gauge = 16.5
    flange = 1.0
    scale_ratio = 76.2
    inch = 25.4 / scale_ratio
    planing = switch["planing"] * inch
    heel_lead = switch["heel"] * inch
    switch_radius = switch["radius"] * inch
    switch_front = 65.0 * inch
    switch_rail_length = switch["switch_rail"] * inch
    stock_rail_length = switch["stock_rail"] * inch
    k1 = math.atan(1.0 / switch["planing_ratio"])
    k3 = math.atan(1.0 / k3n)
    planing_x = planing * math.cos(k1)
    argument = ((heel_lead - planing_x) / switch_radius) + math.sin(k1)
    if abs(argument) > 1.0:
        raise ValueError(
            "The source switch data cannot be resolved at the fixed scale."
        )
    k2 = math.asin(argument)
    heel_offset = (
        (planing_x / switch["planing_ratio"])
        + switch_radius * math.cos(k1)
        - switch_radius * math.cos(k2)
    )

    # Templot regular-crossing minimum entry straight: 2 flangeways at N times.
    entry_straight = 2.0 * flange * k3n
    offset_at_curve_end = gauge - (entry_straight / k3n)
    denominator = math.cos(k2) - math.cos(k3)
    if abs(k2 - k3) < _SOURCE_MINFP:
        raise ReaTurnoutError(
            "unsupported-straight-closure",
            "The source straight closure needs a separate path.",
        )
    # The denominator sentinel is distinct from the straight-angle flag.
    # Source math_unit.pas:3373-3412 can cap it to the switch radius.
    if abs(denominator) < _SOURCE_MINFP:
        turnout_radius = _SOURCE_MAX_RADIUS + 0.5 * gauge
    else:
        turnout_radius = (offset_at_curve_end - heel_offset) / denominator
    if turnout_radius <= 0.0:
        raise ReaTurnoutError(
            "unsupported-negative-closure",
            "The source negative closure is not construction-qualified.",
        )
    auto_fit_cap = turnout_radius > switch_radius + _SOURCE_MINFP
    if auto_fit_cap:
        turnout_radius = switch_radius
        offset_at_curve_end = heel_offset + turnout_radius * denominator
        entry_straight = (gauge - offset_at_curve_end) * k3n
        if entry_straight < 2.0 * flange * k3n:
            raise ReaTurnoutError(
                "invalid-auto-fit-entry",
                "The source auto-fit entry is shorter than its minimum.",
            )
    turnout_curve_length = turnout_radius * (math.sin(k3) - math.sin(k2))
    if turnout_curve_length <= 0.0:
        raise ReaTurnoutError(
            "unsupported-negative-closure",
            "A nonpositive source closure span is not construction-qualified.",
        )
    switch_curve_end_x = heel_lead + turnout_curve_length
    fine_point_x = switch_curve_end_x + entry_straight
    turnout_origin_x = heel_lead - turnout_radius * math.sin(k2)
    turnout_origin_y = heel_offset + turnout_radius * math.cos(k2)

    # Templot5 REA/BH regular-crossing defaults. Values expressed in model mm.
    rail_head_width = 2.75 * inch
    blunt_nose_width = 0.75 * inch
    blunt_nose_x = fine_point_x + (0.5 * blunt_nose_width) / math.sin(0.5 * k3)
    blunt_nose_splice_x = blunt_nose_x - blunt_nose_width * math.sin(0.5 * k3)
    blunt_nose_outer_x = fine_point_x + rail_head_width / math.tan(0.5 * k3)
    a_timber_x = blunt_nose_x + 4.0 * inch

    flare_length = 36.0 * inch
    flare_end_gap = flange + 1.75 * inch
    flare_difference = max(0.0, flare_end_gap - flange)
    if flare_length <= flare_difference:
        raise ValueError(
            "The crossing flare length is too short for the requested "
            "flangeway end gap."
        )
    flare_angle = math.asin(flare_difference / flare_length)
    rail_bend_width = rail_head_width / math.cos(0.5 * flare_angle)

    wing_reach = (48.0 if k3n < 10.01 else 78.0) * inch
    wing_end_main_x = a_timber_x + wing_reach
    wing_flare_main_x = wing_end_main_x - flare_length
    wing_flare_main_outer_x = wing_flare_main_x - rail_head_width * math.tan(
        0.5 * flare_angle
    )
    wing_end_main_outer_x = wing_end_main_x - rail_head_width * math.sin(
        flare_angle
    )

    check_working_length = (
        78.0 if k3n <= 5.99 else 108.0 if k3n < 12.01 else 138.0
    ) * inch
    check_extension_length = (48.0 if k3n < 10.01 else 78.0) * inch
    check_total_length = check_working_length + check_extension_length
    check_main_end_x = a_timber_x + check_extension_length
    check_main_flare_out_x = check_main_end_x - flare_length
    check_main_start_x = check_main_end_x - check_total_length
    check_main_flare_in_x = check_main_start_x + flare_length
    check_main_outer_start_x = check_main_start_x + rail_head_width * math.sin(
        flare_angle
    )
    check_main_outer_flare_in_x = (
        check_main_flare_in_x + rail_head_width * math.tan(0.5 * flare_angle)
    )
    check_main_outer_flare_out_x = (
        check_main_flare_out_x - rail_head_width * math.tan(0.5 * flare_angle)
    )
    check_main_outer_end_x = check_main_end_x - rail_head_width * math.sin(
        flare_angle
    )

    # Virtual knuckles and the normal Templot knuckle radius.
    wing_turnout_x = fine_point_x - flange * k3n
    wing_turnout_outer_x = wing_turnout_x + rail_head_width * math.tan(
        0.5 * k3
    )
    wing_main_x = fine_point_x - flange / math.sin(k3)
    wing_main_outer_x = wing_main_x - rail_head_width * math.tan(0.5 * k3)
    scale_mm_per_foot = 304.8 / scale_ratio
    knuckle_radius = k3n * scale_mm_per_foot
    knuckle_tangent_x = abs(knuckle_radius * math.tan(0.5 * k3))
    knuckle_maximum_x = abs(fine_point_x - wing_turnout_x - inch)
    if knuckle_tangent_x > knuckle_maximum_x:
        knuckle_tangent_x = knuckle_maximum_x
        knuckle_radius = knuckle_tangent_x / math.tan(0.5 * k3)
    knuckle_crossing_x = knuckle_tangent_x * math.cos(k3)
    wing_bend_offset = knuckle_tangent_x * math.sin(k3)
    wing_turnout_plus_x = wing_turnout_x + knuckle_tangent_x
    wing_turnout_minus_x = wing_turnout_x - knuckle_crossing_x
    wing_turnout_outer_plus_x = wing_turnout_plus_x
    wing_turnout_outer_minus_x = (
        wing_turnout_minus_x + rail_head_width * math.sin(k3)
    )
    wing_main_plus_x = wing_main_x + knuckle_crossing_x
    wing_main_minus_x = wing_main_x - knuckle_tangent_x
    wing_main_outer_plus_x = wing_main_plus_x - rail_head_width * math.sin(k3)
    wing_main_outer_minus_x = wing_main_minus_x

    # Turnout-side wing rail follows the running rail before its flare.
    wing_fine_point_x = fine_point_x - flange * math.sin(k3)
    wing_to_flare_length = (
        (a_timber_x - fine_point_x) + wing_reach - flare_length
    )
    wing_flare_turnout_base_x = fine_point_x + wing_to_flare_length * math.cos(
        k3
    )
    wing_flare_turnout_x = wing_fine_point_x + wing_to_flare_length * math.cos(
        k3
    )
    wing_flare_turnout_outer_x = (
        wing_flare_turnout_x
        - rail_bend_width * math.sin(k3 + 0.5 * flare_angle)
    )
    # Regular crossing: the source flare length is projected along its
    # unflared rail, unlike the preserved legacy C10 approximation.
    wing_end_turnout_x = wing_flare_turnout_x + (
        flare_length / math.cos(flare_angle)
    ) * math.cos(k3 + flare_angle)
    wing_end_turnout_outer_x = wing_end_turnout_x - rail_head_width * math.sin(
        k3 + flare_angle
    )

    # Square-on regular-crossing check rail is centred on the A timber.
    check_turnout_fine_point_x = fine_point_x - (gauge - flange) * math.sin(k3)
    check_turnout_mid_offset = (
        a_timber_x - check_turnout_fine_point_x
    ) / math.cos(k3)
    check_turnout_length_after_fp = (
        check_turnout_mid_offset + check_extension_length - flare_length
    )
    check_turnout_length_before_fp = (
        check_total_length
        - check_turnout_length_after_fp
        - flare_length
        - flare_length
    )
    angled_entry_length = entry_straight / max(math.cos(k3), 1.0e-12)
    curved_stock_radius = turnout_radius - gauge
    check_turnout_radius = curved_stock_radius + flange
    check_turnout_flare_radius = curved_stock_radius + flare_end_gap
    if check_turnout_length_before_fp < angled_entry_length:
        check_turnout_working_mode = "straight crossing leg"
        check_flare_in_angle = k3
        check_start_angle = k3
        check_turnout_flare_in_x = (
            check_turnout_fine_point_x
            - check_turnout_length_before_fp * math.cos(k3)
        )
        check_turnout_start_x = check_turnout_flare_in_x - (
            flare_length / math.cos(flare_angle)
        ) * math.cos(k3 + flare_angle)
    else:
        if check_turnout_radius <= 0.0 or check_turnout_flare_radius <= 0.0:
            raise ValueError(
                "The selected gauge and flangeway produce an invalid "
                "turnout-side check-rail radius."
            )
        check_curve_angle = (
            check_turnout_length_before_fp - angled_entry_length
        ) / check_turnout_radius
        check_flare_curve_angle = flare_length / check_turnout_radius
        if (check_curve_angle >= k3
                or check_curve_angle + check_flare_curve_angle >= k3):
            raise ReaTurnoutError(
                "unsupported-check-rail-approximation",
                "The source check-rail approximation needs qualification.",
            )
        check_flare_in_angle = k3 - check_curve_angle
        check_start_angle = check_flare_in_angle - check_flare_curve_angle
        check_turnout_flare_in_x = (
            turnout_origin_x
            + check_turnout_radius * math.sin(k3 - check_curve_angle)
        )
        check_turnout_start_x = (
            turnout_origin_x
            + check_turnout_flare_radius
            * math.sin(k3 - check_curve_angle - check_flare_curve_angle)
        )
        check_turnout_working_mode = "turnout curve and crossing leg"
    check_turnout_flare_out_x = (
        check_turnout_fine_point_x
        + check_turnout_length_after_fp * math.cos(k3)
    )
    check_turnout_end_x = check_turnout_flare_out_x + (
        flare_length / math.cos(flare_angle)
    ) * math.cos(k3 - flare_angle)
    # Bent-flare outer anchors: math_unit.pas:4438-4467,4505-4510.
    check_turnout_outer_start_x = check_turnout_start_x + (
        rail_head_width * math.sin(check_start_angle + flare_angle)
    )
    check_turnout_outer_flare_in_x = check_turnout_flare_in_x + (
        rail_bend_width * math.sin(check_flare_in_angle + 0.5 * flare_angle)
    )
    check_turnout_outer_flare_out_x = check_turnout_flare_out_x + (
        rail_bend_width * math.sin(k3 - 0.5 * flare_angle)
    )
    check_turnout_outer_end_x = check_turnout_end_x + (
        rail_head_width * math.sin(k3 - flare_angle)
    )

    # REA/BH vee-joint position used by the established module extent.
    wing_front_count, vee_timber_count = _crossing_counts(k3n)
    vee_joint_length = (
        4.0 + 12.5 + (vee_timber_count - 1.0) * 30.0
    ) * inch
    vee_joint_x = blunt_nose_x + vee_joint_length
    exit_extension = 60.0 * inch
    module_start_x = -switch_front
    module_end_x = vee_joint_x + exit_extension

    switch_origin_x = heel_lead - switch_radius * math.sin(k2)
    switch_origin_y = heel_offset + switch_radius * math.cos(k2)
    turnout_origin_x = heel_lead - turnout_radius * math.sin(k2)
    turnout_origin_y = heel_offset + turnout_radius * math.cos(k2)

    return {
        "size": "REA {}{:g} regular".format(spec.switch_size, k3n),
        "gauge": gauge,
        "flangeway": flange,
        "model_scale": scale_ratio,
        "inch": inch,
        "planing": planing,
        "planing_x": planing_x,
        "heel_lead": heel_lead,
        "heel_offset": heel_offset,
        "switch_radius": switch_radius,
        "switch_front": switch_front,
        "switch_rail_length": switch_rail_length,
        "stock_rail_length": stock_rail_length,
        "k1": k1,
        "k2": k2,
        "k3": k3,
        "crossing_n": k3n,
        "entry_straight": entry_straight,
        "curve_end_offset": offset_at_curve_end,
        "turnout_radius": turnout_radius,
        "turnout_curve_length": turnout_curve_length,
        "switch_curve_end_x": switch_curve_end_x,
        "fine_point_x": fine_point_x,
        "rail_head_width": rail_head_width,
        "blunt_nose_width": blunt_nose_width,
        "blunt_nose_x": blunt_nose_x,
        "blunt_nose_splice_x": blunt_nose_splice_x,
        "blunt_nose_outer_x": blunt_nose_outer_x,
        "a_timber_x": a_timber_x,
        "flare_length": flare_length,
        "flare_end_gap": flare_end_gap,
        "flare_angle": flare_angle,
        "rail_bend_width": rail_bend_width,
        "wing_reach": wing_reach,
        "wing_end_main_x": wing_end_main_x,
        "wing_flare_main_x": wing_flare_main_x,
        "wing_flare_main_outer_x": wing_flare_main_outer_x,
        "wing_end_main_outer_x": wing_end_main_outer_x,
        "check_working_length": check_working_length,
        "check_extension_length": check_extension_length,
        "check_total_length": check_total_length,
        "check_main_end_x": check_main_end_x,
        "check_main_flare_out_x": check_main_flare_out_x,
        "check_main_start_x": check_main_start_x,
        "check_main_flare_in_x": check_main_flare_in_x,
        "check_main_outer_start_x": check_main_outer_start_x,
        "check_main_outer_flare_in_x": check_main_outer_flare_in_x,
        "check_main_outer_flare_out_x": check_main_outer_flare_out_x,
        "check_main_outer_end_x": check_main_outer_end_x,
        "wing_turnout_x": wing_turnout_x,
        "wing_turnout_outer_x": wing_turnout_outer_x,
        "wing_main_x": wing_main_x,
        "wing_main_outer_x": wing_main_outer_x,
        "knuckle_radius": knuckle_radius,
        "wing_bend_offset": wing_bend_offset,
        "wing_turnout_plus_x": wing_turnout_plus_x,
        "wing_turnout_minus_x": wing_turnout_minus_x,
        "wing_turnout_outer_plus_x": wing_turnout_outer_plus_x,
        "wing_turnout_outer_minus_x": wing_turnout_outer_minus_x,
        "wing_main_plus_x": wing_main_plus_x,
        "wing_main_minus_x": wing_main_minus_x,
        "wing_main_outer_plus_x": wing_main_outer_plus_x,
        "wing_main_outer_minus_x": wing_main_outer_minus_x,
        "wing_fine_point_x": wing_fine_point_x,
        "wing_to_flare_length": wing_to_flare_length,
        "wing_flare_turnout_base_x": wing_flare_turnout_base_x,
        "wing_flare_turnout_x": wing_flare_turnout_x,
        "wing_flare_turnout_outer_x": wing_flare_turnout_outer_x,
        "wing_end_turnout_x": wing_end_turnout_x,
        "wing_end_turnout_outer_x": wing_end_turnout_outer_x,
        "check_turnout_fine_point_x": check_turnout_fine_point_x,
        "check_turnout_length_after_fp": check_turnout_length_after_fp,
        "check_turnout_length_before_fp": check_turnout_length_before_fp,
        "check_turnout_working_mode": check_turnout_working_mode,
        "curved_stock_radius": curved_stock_radius,
        "check_turnout_radius": check_turnout_radius,
        "check_turnout_flare_radius": check_turnout_flare_radius,
        "check_turnout_flare_in_x": check_turnout_flare_in_x,
        "check_turnout_start_x": check_turnout_start_x,
        "check_turnout_flare_out_x": check_turnout_flare_out_x,
        "check_turnout_end_x": check_turnout_end_x,
        "check_turnout_outer_start_x": check_turnout_outer_start_x,
        "check_turnout_outer_flare_in_x": check_turnout_outer_flare_in_x,
        "check_turnout_outer_flare_out_x": check_turnout_outer_flare_out_x,
        "check_turnout_outer_end_x": check_turnout_outer_end_x,
        "vee_joint_x": vee_joint_x,
        "module_start_x": module_start_x,
        "module_end_x": module_end_x,
        "switch_origin_x": switch_origin_x,
        "switch_origin_y": switch_origin_y,
        "turnout_origin_x": turnout_origin_x,
        "turnout_origin_y": turnout_origin_y,
        "source_specification": spec.to_record(),
        "source_context_flags": _source_context_flags(),
        "source_status": "transient-unqualified",
        "auto_fit_cap": auto_fit_cap,
        "wing_front_count": wing_front_count,
        "vee_timber_count": vee_timber_count,
        "wing_chair_span": 3 if k3n > 10.0 else 2,
        "crossing_seat": "ABSEAT" if k3n < 10.01 else "BCSEAT",
        "source_gaps": [
            "Exit sleeper stations and the rail-length profile are not yet "
            "qualified; no R1/R2 source stations are supplied.",
            "The 60-inch module extension is an inherited product envelope, "
            "not source-derived exit sleeper evidence.",
            "Chair placement and native/GUI construction remain unqualified "
            "for this explicit source specification.",
        ],
    }


def rea_turnout_timber_stations(spec):
    """Return source square-on timber stations; omit unqualified exit bays.

    Coordinates and widths are model millimetres. Source suffixes remain
    empty where Templot provides no letter; numeric X identities stay unique.
    """
    dimensions = rea_turnout_dimensions(spec)
    inch = dimensions["inch"]
    records = []

    def add(identifier, section, station, width, suffix=""):
        records.append({
            "identifier": identifier,
            "section": section,
            "x": station,
            "width": width,
            "crossing_suffix": suffix,
            "angle_radians": 0.0,
        })

    # B and C source front-joint spacings, switch_select.pas:1765,1820.
    # Both switches have front_timbered=True: math_unit.pas:23140 uses
    # the 12-inch timber width, not the legacy 10-inch sleeper width.
    add("J2", "switch front", -52.5 * inch, 12.0 * inch)
    add("J1", "switch front", -24.5 * inch, 12.0 * inch)
    intervals = _switch_data(spec.switch_size)["timber_intervals"]
    station = 0.0
    for index, spacing in enumerate(intervals):
        station += spacing * inch
        last = index == len(intervals) - 1
        add("T1" if last else "S{}".format(index + 1),
            "closure" if last else "switch", station, 12.0 * inch)

    # math_unit.pas:22841-22895; force_eq/equalizing_fixed are both false.
    wing_count = dimensions["wing_front_count"]
    first_crossing = dimensions["a_timber_x"] - wing_count * 30.0 * inch
    closure_length = first_crossing - 25.0 * inch - station
    if closure_length <= 0.0:
        raise ReaTurnoutError(
            "unsupported-closure-timbering",
            "The source closure timber region is not positive.",
        )
    quotient = closure_length / (30.0 * inch)
    count = math.trunc(quotient)
    if quotient - count > _SOURCE_MINFP:
        count += 1
    count = max(1, count)
    for index in range(1, count + 1):
        add("T{}".format(index + 1), "closure",
            station + index * closure_length / count, 12.0 * inch)

    # math_unit.pas:23560-23570 supplies only these seven suffix letters.
    suffixes = {1: "Z", 2: "Y", 3: "X", 4: "A", 5: "B", 6: "C", 7: "D"}
    for index in range(wing_count + dimensions["vee_timber_count"]):
        number = index + 1
        suffix = suffixes.get(number + 3 - wing_count, "")
        identifier = "X{}".format(number)
        if suffix:
            identifier += "-" + suffix
        add(identifier,
            "crossing wing front" if index < wing_count else "crossing vee",
            first_crossing + index * 30.0 * inch, 12.0 * inch, suffix)
    for sequence, record in enumerate(records, 1):
        record["sequence"] = sequence
    return records


def rea_turnout_source_rail_point(
    dimensions, actual_x, rail_kind, outer=False,
):
    """Return a source wing/check ordinate at an actual local x, in mm.

    Templot docrossing dispatches these rails to turnoutst_wing/check,
    whose cuflare offset is linear in actual x. This is not a normal-offset
    circle or a straight chord through the independently selected anchors.
    The input dimensions must come from the explicit source calculation.
    """
    if dimensions.get("source_status") != "transient-unqualified":
        raise ReaTurnoutError(
            "invalid-source-dimensions", "Source dimensions are required.",
        )
    if rail_kind not in ("wing", "check") or type(outer) is not bool:
        raise ReaTurnoutError(
            "invalid-source-rail", "Select a wing/check rail and face.",
        )
    x = float(actual_x)
    if not math.isfinite(x):
        raise ReaTurnoutError("invalid-source-station", "x must be finite.")
    gauge = dimensions["gauge"]
    width = dimensions["rail_head_width"] if outer else 0.0
    k3 = dimensions["k3"]
    flare_prefix = "outer_" if outer else ""
    if rail_kind == "wing":
        start_key = "wing_flare_turnout_{}x".format(flare_prefix)
        end_key = "wing_end_turnout_{}x".format(flare_prefix)
        start = dimensions[start_key]
        end = dimensions[end_key]
        fraction = (x - start) / (end - start) if x >= start else 0.0
        # aq2offset on the admitted regular crossing leg, source 9198.
        if x < dimensions["switch_curve_end_x"]:
            raise ReaTurnoutError(
                "unsupported-wing-running-branch",
                "The wing path precedes the qualified crossing leg.",
            )
        running_y = dimensions["curve_end_offset"] + (
            x - dimensions["switch_curve_end_x"]
        ) * math.tan(k3)
        heading = k3
        side = 1.0
    else:
        prefix = "check_turnout_" + flare_prefix
        start = dimensions[prefix + "start_x"]
        flare_in = dimensions[prefix + "flare_in_x"]
        flare_out = dimensions[prefix + "flare_out_x"]
        end = dimensions[prefix + "end_x"]
        fine_point_x = dimensions["check_turnout_fine_point_x"] + (
            width * math.sin(k3)
        )
        if x < fine_point_x:
            fraction = (
                (flare_in - x) / (flare_in - start)
                if x <= flare_in else 0.0
            )
        else:
            fraction = (
                (x - flare_out) / (end - flare_out)
                if x >= flare_out else 0.0
            )
        # aq3offset: the actual-x stock face, not a check-radius circle.
        curve_end_x = dimensions["switch_curve_end_x"] - gauge * math.sin(k3)
        if x < curve_end_x:
            heel_x = dimensions["heel_lead"] - gauge * math.sin(
                dimensions["k2"]
            )
            if x < heel_x:
                raise ReaTurnoutError(
                    "unsupported-check-running-branch",
                    "The check path precedes the qualified closure curve.",
                )
            radius = dimensions["curved_stock_radius"]
            dx = x - dimensions["turnout_origin_x"]
            radicand = radius * radius - dx * dx
            if radicand <= 0.0:
                raise ReaTurnoutError(
                    "invalid-source-stock-radius",
                    "The stock circle is invalid.",
                )
            running_y = dimensions["turnout_origin_y"] - math.sqrt(radicand)
            heading = math.asin(dx / radius)
        else:
            running_y = dimensions["curve_end_offset"] + gauge * math.cos(k3)
            running_y += (x - curve_end_x) * math.tan(k3)
            heading = k3
        side = -1.0
    # math_unit.pas:9517-9553,9193-9214,9258-9284. Source y has its
    # origin on the main gauge face; the product local frame is mid-gauge.
    flare_offset = (
        fraction * dimensions["flare_length"]
        * math.sin(dimensions["flare_angle"])
    )
    y = running_y + side * (
        dimensions["flangeway"] + width + flare_offset
    ) / math.cos(heading)
    return x, y - 0.5 * gauge
