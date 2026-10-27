"""Independent source oracle for fixed XO-001 crossing and exit coverage.

Templot 556b source-informed calculations, copyright Martin Wynne and
OpenTemplot contributors, GPL-3.0-or-later. See NOTICE.md and provenance.
No product, catalogue recipe or FreeCAD imports. Reuses the accepted
independent decimal rail-circle oracle and its frozen C10 inputs; this
is an explicit independence limit. Source model coordinates are mm,
angles radians, right hand, square source frame, zero key offset.
No physical-fit, random fixing-angle, rights or production qualification.
"""

import math

from single_rail_source_oracle import (
    SOURCE_PARAMETERS,
    _source_geometry,
    a_timber,
    joint_window,
    source_rail_pose,
)

REFERENCES = {
    "selection": "math_unit.pas:29750-30048",
    "second_station": "math_unit.pas:24245-24277",
    "wing_ends": "math_unit.pas:4287-4344,26648-26691",
    "marks": "math_unit.pas:30704-30879",
    "components": "math_unit.pas:30893-31350",
    "requests": "dxf_unit.pas:7126-7578",
    "insertion": "math_unit.pas:28214-28560;dxf_unit.pas:11880-12078",
    "base": "math_unit.pas:30502-30680",
}
TIMBERS = ("X1-Z", "X2-Y", "X3-X", "X4-A", "X5-B", "X6-C", "X7-D", "X8-E")
EXPECTED_FAMILIES = ("ZY", "ZY", "XA", "AA", "BB", "CD", "DD", "EF")


def _inputs():
    geometry = _source_geometry(SOURCE_PARAMETERS)
    angle = math.atan2(1, 10)
    fine = float(geometry["fine_point_mm"])
    return {
        "scale": 1 / 3,
        "gauge": 16.5,
        "angle": angle,
        "half": angle / 2,
        "fine": fine,
        "a": a_timber(SOURCE_PARAMETERS),
        "wing3": fine - 1 / math.sin(angle),
        "wing2": fine - 1 / math.tan(angle),
        "flare": math.asin((19 / 12 - 1) / 12),
    }


def second_station(station):
    """Evaluate source first-crossed step with reverse half-step."""
    p = _inputs()
    direction = 1 if station < p["fine"] else -1
    for index in range(1, 1000001):
        delta = index / 600
        target = station + direction * delta
        y = source_rail_pose(SOURCE_PARAMETERS, target, 2)["y_mm"]
        gap = abs(p["gauge"] - y)
        if gap == 0 or math.atan(delta / gap) > p["half"]:
            return station + direction * (delta - 1 / 1200)
    raise ValueError("Source second-station search did not terminate")


def _wings(station, second, p):
    starts = (
        p["a"] + 4,
        p["wing3"] + (p["a"] - p["wing2"] + 4) * math.cos(p["angle"]),
    )
    ends = (
        p["a"] + 16 - 4 / 3,
        starts[1]
        + 12 / math.cos(p["flare"]) * math.cos(p["angle"] + p["flare"])
        - 4 / 3,
    )
    result = []
    for x, start, end in zip((station, second), starts, ends):
        kind = 2 if x <= start else 3 if x <= end else 0
        result.append(
            {
                "kind": kind,
                "add_mm": (x - start) * math.tan(p["flare"])
                if kind == 3
                else 0,
                "angle_rad": p["flare"] if kind == 3 else 0,
            }
        )
    return result


def source_decision(timber):
    """Source predicates determine family; canonical labels are unused."""
    if timber not in TIMBERS:
        raise ValueError("Unsupported crossing timber")
    p = _inputs()
    station = p["a"] + (TIMBERS.index(timber) - 3) * 10
    second = second_station(station)
    rail = source_rail_pose(SOURCE_PARAMETERS, second, 2)
    separation = abs(16.5 - rail["y_mm"]) / math.cos(p["half"])
    wings = _wings(station, second, p)
    space = (
        source_rail_pose(SOURCE_PARAMETERS, station - 4 / 3, 2)["y_mm"] - 16.5
    )
    if station > p["fine"] and space >= 4:
        if space >= 29 / 6:
            raise ValueError("Source requires single-rail chairs")
        family, code = "EF", 28
    elif station < p["wing3"] - 40 * math.tan(p["half"]) + 0.5:
        family, code = "ZY", 21
    elif (
        station
        < p["wing3"] + 40 * math.tan(p["half"]) * math.cos(p["angle"]) - 0.5
    ):
        family, code = "XN", 22
    elif station < p["a"] - 4:
        family, code = "XA", 23
    elif station < p["a"] + 5:
        family, code = "AA", 24
    elif wings[0]["kind"] == wings[1]["kind"] == 2:
        family, code = "AB", 25
    elif wings[0]["kind"] or wings[1]["kind"]:
        family, code = "BB", 26
    else:
        family, code = ("CD" if separation < 2.5 else "DD"), 27
    return {
        "context_id": "RH-" + timber,
        "timber": timber,
        "family": family,
        "chair_code": code,
        "station_mm": station,
        "second_station_mm": second,
        "rail_separation_mm": separation,
        "source_rail_2_branch": rail["source_branch"],
        "source_rail_2_angle_rad": rail["k_rad"],
        "source_rail_2_gauge_y_mm": rail["y_mm"],
        "source_rail_3_branch": "main_straight",
        "wing_ends": wings,
    }


def crossing_context(timber):
    """Return independently calculated RH source requests and placements.

    Base scalars and fixing centres are checked independently. Complete
    source base faces remain the native proof's separate obligation.
    """
    p = _inputs()
    result = source_decision(timber)
    family, code = result["family"], result["chair_code"]
    x, x2 = result["station_mm"], result["second_station_mm"]
    k, h = p["angle"], p["half"]
    y2, tangent = (
        result["source_rail_2_gauge_y_mm"],
        result["source_rail_2_angle_rad"],
    )
    q = 16.5 - y2
    curvi = y2 - 16.5 - (x - p["fine"]) * math.tan(k)
    delta = tangent - k
    curvi_offset = curvi * math.cos(tangent)
    ms, ts = result["wing_ends"]
    ma, ta = ms["add_mm"], ts["add_mm"]
    mk, tk = ms["angle_rad"], ts["angle_rad"]
    u = (x - p["wing3"]) * math.sin(h) * 2 + curvi_offset
    v = (
        (x - p["wing3"]) * math.sin(h) * 2 / math.cos(k)
        + ta / math.cos(tk + k)
        + curvi_offset
    ) * math.cos(h)
    # Each mark is centre X/Y and endpoint tangent in the pre-hand frame.
    marks = {
        "main": (0, 0, 0),
        "second": (q * math.sin(h), -q, tangent),
        "point": (math.sin(h), 0, 0),
        "wing3": (-u * math.tan(h + delta), u, k + delta),
        "wing2": (math.tan(h), -1, 0),
        "flare3": (
            -v * math.tan(h + tk + delta) + 0.9 * math.sin(tk + h),
            v,
            k + tk + delta,
        ),
        "flare2": (math.tan(h), -1 - ma, -mk - delta),
    }
    marks["splice"] = (marks["second"][0] + math.sin(h), -q, tangent)
    marks["outer3"] = (marks["flare3"][0] + 1 / 9, v, k + tk + delta)
    marks["outer2"] = (math.tan(h) + 1 / 30, -1 - ma, -mk - delta)
    marks["splice_flare"] = (
        marks["splice"][0] + math.tan(k + tk) / 3,
        -q,
        tangent,
    )
    components = []

    def emit(block, rail, mark, builder, **arguments):
        cx, cy, slope = marks[mark]
        endpoints = [
            [cx - 4 / 3, -16.5 - cy + 4 / 3 * math.tan(slope)],
            [cx + 4 / 3, -16.5 - cy - 4 / 3 * math.tan(slope)],
        ]
        angle = math.atan2(
            endpoints[1][1] - endpoints[0][1],
            endpoints[1][0] - endpoints[0][0],
        )
        angle += math.pi + (math.pi if rail == 3 else 0)
        request = {
            "builder": builder,
            "scale_mm_per_foot": 4.0,
            "flangeway_mm": 1.0,
            "profile": "code75-a",
            "loose": False,
        }
        if builder == "inner":
            request.update(
                ef=False,
                cc=False,
                sc=True,
                l1=False,
                swap=False,
                shear_rad=0,
                crop_mm=0,
                flare_mm=0,
                half_widen_mm=0,
                jaw_name=block,
            )
        elif builder == "outer-sc":
            request.update(
                shear_rad=0,
                crop_mm=0,
                flare_mm=0,
                cc_swap=False,
                jaw_name=block,
            )
        request.update(arguments)
        components.append(
            {
                "source_block": block,
                "rail_code": rail,
                "request": request,
                "source_endpoints_mm": endpoints,
                "insertion": {
                    "x_mm": cx,
                    "y_mm": -16.5 - cy,
                    "z_mm": 0,
                    "rotation_rad": angle,
                },
            }
        )

    def seat(block, rail, mark, flag):
        emit(block, rail, mark, "seat", seat_name=block, **{flag: True})

    def key(rail, mark):
        emit("KEY", rail, mark, "key", cc=False)

    sep = result["rail_separation_mm"]
    outlong, inlong = 37 / 12, 7 / 4
    if family == "ZY":
        inlong = outlong + sep
        for prefix, rail, mark, shear in (
            ("W", 3, "main", -h),
            ("V", 2, "second", h),
        ):
            emit(prefix + "A", rail, mark, "outer-sc", shear_rad=shear)
            emit(
                prefix + "H",
                rail,
                mark,
                "inner",
                shear_rad=shear,
                crop_mm=sep / 2,
            )
            seat("ZYSEAT", rail, mark, "zy")
            key(rail, mark)
    elif family in ("XA", "AA", "BB"):
        base_second = (
            p["fine"] - (p["fine"] - x) * math.cos(k)
            if code in (23, 24)
            else x2
        )
        base_y = source_rail_pose(SOURCE_PARAMETERS, base_second, 2)["y_mm"]
        inlong = (
            outlong
            + (16.5 - base_y) / math.cos(h)
            + (base_second - p["wing2"]) * math.tan(h) * 2
        )
        outlong += (x - p["wing3"]) * math.tan(h) * 2
        if family == "XA":
            crop = (x - p["wing3"]) * math.sin(k) + (p["fine"] - x) * math.sin(
                h
            )
            for prefix, rail, mark, shear in (
                ("W", 3, "wing3", h),
                ("V", 2, "wing2", -h),
            ):
                emit(prefix + "C", rail, mark, "outer-sc", shear_rad=shear)
                emit(
                    prefix + "J",
                    rail,
                    mark,
                    "inner",
                    shear_rad=shear,
                    crop_mm=crop,
                )
                seat("XASEAT", rail, mark, "xa")
                key(rail, mark)
        elif family == "AA":
            for prefix, rail, mark, point, shear in (
                ("W", 3, "wing3", "point", h),
                ("V", 2, "wing2", "splice", -h),
            ):
                emit(prefix + "D", rail, mark, "outer-sc", shear_rad=shear)
                emit(
                    prefix + "K",
                    rail,
                    mark,
                    "inner",
                    crop_mm=0.5 + (1 / 12 + curvi_offset if rail == 3 else 0),
                    half_widen_mm=5 / 12,
                )
                emit(
                    prefix + "P",
                    rail,
                    point,
                    "inner",
                    crop_mm=0.5 + (1 / 12 if rail == 2 else 0),
                    half_widen_mm=5 / 12 if rail == 3 else -5 / 12,
                )
                seat("AASEAT", rail, mark, "aa")
                key(rail, mark)
        else:
            inlong += ma + 1 / 12
            outlong += ta / math.cos(k) + 1 / 12
            emit("WF", 3, "outer3", "outer-sc", shear_rad=h + tk)
            emit(
                "WM",
                3,
                "outer3",
                "inner",
                crop_mm=0.5 + ta + curvi_offset,
                half_widen_mm=1 / 12,
            )
            emit(
                "WR",
                3,
                "point",
                "inner",
                crop_mm=0.5 + ma,
                half_widen_mm=1 / 12,
            )
            seat("ABSEAT", 3, "flare3", "aa")
            key(3, "flare3")
            emit("VF", 2, "outer2", "outer-sc", shear_rad=-h - mk)
            emit(
                "VM",
                2,
                "flare2",
                "inner",
                crop_mm=0.5 + ma,
                half_widen_mm=1 / 12,
            )
            emit(
                "VR",
                2,
                "splice_flare",
                "inner",
                crop_mm=0.5 + ta,
                half_widen_mm=1 / 12,
            )
            seat("ABSEAT", 2, "flare2", "aa")
            key(2, "flare2")
    elif family in ("CD", "DD", "EF"):
        outlong = inlong + sep
        for prefix, rail, mark, shear in (
            ("W", 3, "main", -h),
            ("V", 2, "second", h),
        ):
            emit(
                prefix + ("Z" if family == "EF" else "G"),
                rail,
                mark,
                "inner",
                ef=True,
                sc=False,
                shear_rad=shear,
            )
            if family == "DD":
                emit(
                    prefix + "N",
                    rail,
                    mark,
                    "outer-p",
                    dd_name=prefix + "N",
                    dx_stretch_mm=sep / 2 - 0.9 + 1 / 12,
                )
                seat("DDSEAT", rail, mark, "zy")
                seat("DXSEAT", rail, mark, "zy")
            else:
                seat("ZYSEAT", rail, mark, "zy")
                if family == "EF":
                    emit(
                        prefix + "O",
                        rail,
                        mark,
                        "outer-sc",
                        shear_rad=shear,
                        crop_mm=-(x - p["fine"]) * math.sin(h),
                    )
                    key(rail, mark)
    else:
        raise ValueError("Unqualified crossing family")
    bolts = []
    for bx, by in (
        (-2 / 3, -inlong + 7 / 12),
        (2 / 3, -inlong + 7 / 12),
        (-2 / 3, outlong - 7 / 12),
        (2 / 3, outlong - 7 / 12),
    ):
        bolts.append(
            [
                bx * math.cos(h) - by * math.sin(h),
                -16.5 - bx * math.sin(h) - by * math.cos(h),
            ]
        )
    result.update(
        components=components,
        base={
            "outlong_mm": outlong,
            "inlong_mm": inlong,
            "source_twist_rad": -h,
            "bolt_centres_source_mm": bolts,
            "source_plinth_inches": 0.875 if code == 27 else 1.125,
            "source_mark_code": 494 if code == 27 else 484,
        },
    )
    return result


def exit_family(timber, rail):
    """Follow continued X timber sequence, not literal R return track."""
    if timber not in ("R1", "R2") or rail not in (2, 3):
        raise ValueError("Unsupported exit context")
    station = (
        a_timber(SOURCE_PARAMETERS) + 175 / 3 + (10 if timber == "R2" else 0)
    )
    low, high = joint_window(SOURCE_PARAMETERS)
    family = "S1J" if low < station < high else "S1"
    gap = (
        source_rail_pose(SOURCE_PARAMETERS, station - 4 / 3, 2)["y_mm"] - 16.5
    )
    if gap < 29 / 6:
        raise ValueError("Paired crossing family required")
    if gap < 19 / 3 and (rail == 2 or gap < 67 / 12):
        family = "L1"
    return family, station


def source_to_native(point):
    """Existing retained normalization, source Z0 is rail top."""
    return (-point[0], -point[1] - 0.45, point[2] + 149 / 60)


def native_to_target(_data=None, _context_id=None, _part_id=None):
    """Inverse normalization; every qualified RH component already posed."""
    return (
        (-1.0, 0.0, 0.0, 0.0),
        (0.0, -1.0, 0.0, -0.45),
        (0.0, 0.0, 1.0, -149 / 60),
        (0.0, 0.0, 0.0, 1.0),
    )
