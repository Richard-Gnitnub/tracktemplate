"""Independent Templot 556b single-rail insertion oracle, model mm.

Source-informed calculations, copyright Martin Wynne and OpenTemplot
contributors, GPL-3.0-or-later. See NOTICE.md and reference/PROVENANCE.md.
Private source/model inputs remain reference-only; no physical-fit,
production, rights or final global/random fixing-angle parity is claimed.

No product or FreeCAD imports. Frozen Pascal parsing and independently
derived decimal closure circles reuse the earlier test oracles. This is
an explicit independence limit. Selection and insertion marks are derived
here; retained shapes are consumed unchanged, never reconstructed.
"""

import cmath
from decimal import localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from check_end_source_oracle import _decimal, _source_geometry
from paired_switch_source_oracle import (
    _assignment,
    expected_world_frame,
    source_parameters,
    world_point,
)

SOURCE_CONTEXT_SHA256 = (
    "925462e8e080f7d1b7f08c2eb6680ccd832b36d6cc3e6730ca155dbb41f03e71"
)
MODEL_INPUTS = (
    (
        "S1",
        "existing-02/models/S1.FCStd",
        "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb",
    ),
    (
        "L1",
        "existing-02/models/L1.FCStd",
        "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042",
    ),
    (
        "S1J",
        "basic-04/S1J/S1J.FCStd",
        "fd5cb5ffa9fa2004ef2930ab9280b4e906175b9233364448d07d8ef63c212c4b",
    ),
)
NORMALISATION_INPUTS = (
    (
        "final_adapter/family_assembly.py",
        "8cf4b88c8533b68f5b1954d68be49a7f118a326d8939f1c0bba37d816d7b376e",
    ),
    (
        "final_adapter/fixing_adapter.py",
        "767c4b82ee7e94a3b09238623893b1a14b13c6ed9ea3d07a68c99eeab63e0e98",
    ),
    (
        "existing-02/models/build-receipt.json",
        "b3a5d11827ade1c961219efd50488aaf46fa14ca449059fd22f371e1e71b9a65",
    ),
    (
        "basic-04/result.json",
        "a28d5d2d73eec3f6a52f90d1a1415da8a40351783e98908b9cc002214ca20ae5",
    ),
)
REFERENCES = {
    "dimensions": "chairs_unit.pas:920-965",
    "selection": "math_unit.pas:29551-29665,29750-29831",
    "joint": "math_unit.pas:3598-3609,37587-37603",
    "check_bounds": "math_unit.pas:3470-3487,4140-4176,4359-4381,4480-4518",
    "rails": "math_unit.pas:17766-17927",
    "midpoint": "math_unit.pas:31377-31479,31685-31736",
    "fixed_insertions": "math_unit.pas:28271-28314,28364-28409,28517-28559",
    "hand": "dxf_unit.pas:11902-11905,11998-12001,12064-12067",
    "fixings": "math_unit.pas:24152-24237;dxf_unit.pas:2534-2542,8543-8571",
}
SOURCE_PARAMETERS = {
    "scale_mm_per_inch": 1 / 3,
    "gauge_mm": 16.5,
    "flangeway_mm": 1.0,
    "rail_head_width_mm": 0.9,
    "crossing_ratio": 10,
    "switch": {
        "planing": 110,
        "heel_lead_inches": 329,
        "planing_angle": 40,
        "switch_radius_inchormax": 11520,
    },
}
NOMINAL_STATIONS = (
    ("S13", 118.33333333333333),
    ("T1", 126.33333333333333),
    ("T2", 135.76150516183702),
    ("T14", 248.8995671038812),
    ("X6-C", 307.23290043721454),
    ("X7-D", 317.23290043721454),
    ("X8-E", 327.23290043721454),
    ("X9-F", 337.23290043721454),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_rail_pose(parameters, station_mm, rail_code):
    """Direct decimal circle/tangent evaluation of rails 1/2/3/4.

    The domain starts at the closure heel. The binary64 join belongs to
    the straight branch. Rail 2 uses the closure radius; rail 4 uses its
    parallel stock radius. Neither travel nor host curvature changes it.
    """
    if type(rail_code) is not int or rail_code not in (1, 2, 3, 4):
        raise ValueError("Unsupported source rail")
    station = _decimal(station_mm)
    geometry = _source_geometry(parameters)
    heel = (
        float(parameters["switch"]["heel_lead_inches"])
        * parameters["scale_mm_per_inch"]
    )
    if float(station) < heel:
        raise ValueError("Station precedes the bounded closure span")
    if rail_code in (1, 3):
        return {
            "source_rail_code": rail_code,
            "source_branch": "main_straight",
            "y_mm": 0.0 if rail_code == 1 else parameters["gauge_mm"],
            "k_rad": 0.0,
        }
    with localcontext() as context:
        context.prec = 60
        ratio = geometry["crossing_ratio"]
        norm = (ratio * ratio + 1).sqrt()
        radius = geometry[
            "closure_radius_mm" if rail_code == 2 else "stock_radius_mm"
        ]
        join = geometry["centre_x_mm"] + radius / norm
        if float(station) < float(join):
            dx = station - geometry["centre_x_mm"]
            if abs(dx) >= radius:
                raise ValueError("Source circle has no point")
            leg = (radius * radius - dx * dx).sqrt()
            y = geometry["centre_y_mm"] - leg
            angle = math.atan2(float(dx), float(leg))
            branch = "radcurve"
        else:
            y = (
                geometry["centre_y_mm"]
                - radius * ratio / norm
                + (station - join) / ratio
            )
            angle = math.atan2(1, float(ratio))
            branch = "turnoutst_main"
    return {
        "source_rail_code": rail_code,
        "source_branch": branch,
        "y_mm": float(y),
        "k_rad": angle,
    }


def dimensions(family):
    """Exact source inches converted once; no retained bbox inference."""
    if family not in ("S1", "L1", "S1J"):
        raise ValueError("Unsupported fixed single-rail family")
    inner, outer = (
        (Fraction(7, 6), Fraction(7, 3))
        if family == "L1"
        else (Fraction(7, 4), Fraction(37, 12))
    )
    inner_x = Fraction(5, 4) if family == "L1" else Fraction(2, 3)
    centres = [
        (-inner_x, inner - Fraction(7, 12)),
        (inner_x, inner - Fraction(7, 12)),
    ]
    outer_x = (-inner_x, inner_x) if family == "L1" else (Fraction(),)
    centres += [(x, -outer + Fraction(7, 12)) for x in outer_x]
    return {
        "inner_mm": float(inner),
        "outer_mm": float(outer),
        "midpoint_mm": float((outer - inner) / 2),
        "fixing_centres_mm": tuple((float(x), float(y)) for x, y in centres),
    }


def a_timber(parameters):
    geometry = _source_geometry(parameters)
    angle = math.atan2(1, parameters["crossing_ratio"])
    return (
        float(geometry["fine_point_mm"]) + 0.125 / math.sin(angle / 2) + 4 / 3
    )


def joint_window(parameters):
    """REA default exit joint, including strict source inequality limits."""
    centre = a_timber(parameters) + (12.5 + 5 * 30) / 3
    return centre - 13.5 / 3, centre + 13.5 / 3


def check_bounds(parameters):
    """The retained 52-inch C10 check construction, independently evaluated."""
    angle = math.atan2(1, parameters["crossing_ratio"])
    fine = float(_source_geometry(parameters)["fine_point_mm"])
    a = a_timber(parameters)
    main = (a - 36 + 4 / 3, a + 16 - 4 / 3)
    fp = fine - 15.5 * math.sin(angle)
    after = (a - fp) / math.cos(angle) + 4
    before = 28 - after
    flare = math.asin((19 / 12 - 1) / 12)
    turnout = (
        fp
        - before * math.cos(angle)
        - 12 / math.cos(flare) * math.cos(angle + flare)
        + 4 / 3,
        fp
        + after * math.cos(angle)
        + 12 / math.cos(flare) * math.cos(angle - flare)
        - 4 / 3,
    )
    return {1: main, 4: turnout}


def selected_family(parameters, timber, station, rail):
    """Evaluate only the authorised 17 local contexts; no other mappings."""
    if timber in ("S13", "T1", "T2") and rail in (2, 4):
        gap = source_rail_pose(parameters, station - 4 / 3, 4)["y_mm"] - 16.5
        if not 10.75 / 3 < gap < 15 / 3:
            raise ValueError("Heel source selection is outside L1 interval")
        return "L1" if rail == 2 or gap < 13.25 / 3 else "S1"
    if timber == "T14" and rail == 2:
        gap = 16.5 - source_rail_pose(parameters, station + 4 / 3, 2)["y_mm"]
        if not 9.25 / 3 < gap < 11 / 3:
            raise ValueError("Closure source selection changed")
        return "L1"
    if timber in ("X6-C", "X7-D", "X8-E", "X9-F") and rail in (1, 4):
        lower, upper = check_bounds(parameters)[rail]
        if lower <= station <= upper:
            raise ValueError("A check-chair context is required")
        low, high = joint_window(parameters)
        return "S1J" if low < station < high else "S1"
    if timber == "X9-F" and rail in (2, 3):
        gap = source_rail_pose(parameters, station - 4 / 3, 2)["y_mm"] - 16.5
        if not 14.5 / 3 < gap < 16.75 / 3:
            raise ValueError("Vee source selection changed")
        return "L1"
    raise ValueError("Position is outside the bounded source selection")


def matrix(angle, origin):
    c, s = math.cos(angle), math.sin(angle)
    return (
        (c, -s, 0.0, origin[0]),
        (s, c, 0.0, origin[1]),
        (0.0, 0.0, 1.0, origin[2]),
        (0.0, 0.0, 0.0, 1.0),
    )


def local_frames(family, rail, angle, gauge_y):
    """Transform source insertion marks, then cancel native normalisation.

    Fixed jaw/seat/key names retain chair_k at the nominal station.
    aq(midpoint) custom-jaw updates do not affect those fixed names.
    Each fixing keeps its original source index and zero local head angle.
    Returned matrices use the retained mounting plane Z=0.
    """
    dims = dimensions(family)
    if rail not in (1, 2, 3, 4):
        raise ValueError("Unsupported source rail")
    if not all(
        type(x) in (int, float) and math.isfinite(x) for x in (angle, gauge_y)
    ):
        raise ValueError("Source pose must be finite")
    delta = (
        {1: 0, 2: -1, 3: 0, 4: 1}[rail] * dims["midpoint_mm"] * math.sin(angle)
    )
    # Two nominal marks establish the handed insertion axis independently.
    turn = cmath.rect(1, angle)
    marks = [
        (complex(delta + x, 0) * turn + complex(0, gauge_y)).conjugate()
        for x in (-1, 1)
    ]
    anchor = sum(marks) / 2
    direction = (marks[1] - marks[0]) / 2
    if rail in (3, 4):
        direction = -direction
    origin = anchor + complex(0, 0.45) * direction
    body = matrix(cmath.phase(direction), (origin.real, origin.imag, 0))
    fixings = []
    for cx, cy in dims["fixing_centres_mm"]:
        source_y = -cy if rail in (3, 4) else cy
        target = (
            complex(cx + delta, source_y) * turn + complex(0, gauge_y)
        ).conjugate()
        # N(source centre)=(-cx,-cy-.45), R(pi)N=(cx,cy+.45).
        fixings.append(
            matrix(math.pi, (target.real - cx, target.imag - cy - 0.45, 0))
        )
    return {
        "body": body,
        "fixings": tuple(fixings),
        "source_anchor_mm": (anchor.real, anchor.imag),
        "midpoint_delta_mm": delta,
    }


def _position_rail(position):
    timber, name = (
        position["prototype_timber_identifier"],
        position["rail_name"],
    )
    if name == "main-side stock rail":
        return 1
    if name == "turnout-side stock rail":
        return 4
    if (
        timber in ("S13", "T1", "T2", "T14")
        and name == "curved switch and closure rail"
    ):
        return 2
    if timber == "X9-F" and name == "vee point rail":
        return 3
    if timber == "X9-F" and name == "vee splice rail":
        return 2
    raise ValueError("Not one of the scoped source rails")


def station_from_position(position):
    """Use nominal source station, including identified B4 extensions only."""
    source = position["source_configuration"]["timber"]
    timber = position["prototype_timber_identifier"]
    if timber not in dict(NOMINAL_STATIONS):
        raise ValueError("No qualified source station")
    if "local_x" in source:
        return float(source["local_x"])
    if timber not in ("X6-C", "X7-D", "X8-E", "X9-F"):
        raise ValueError("Unqualified extended source timber")
    owner = {"XO-001-A001": "A", "XO-001-B001": "B"}.get(
        position["parent_turnout_identity"]
    )
    if (
        source.get("extended_source_timber_identity")
        != f"XO-001:{owner}:{timber}"
    ):
        raise ValueError("Extended source identity differs")
    return float(source["path_station"])


def _parts(model, family):
    with zipfile.ZipFile(model) as archive:
        document = ET.fromstring(archive.read("Document.xml"))
    parts = {}
    for obj in document.findall("./ObjectData/Object"):
        name = obj.attrib["name"]
        label = obj.find("./Properties/Property[@name='Label']/String")
        if label is None:
            continue
        label = label.attrib["value"]
        if not label.startswith(family + " / "):
            continue
        semantic = label.split(" / ", 1)[1]
        part = {"native_object": name, "kind": "body"}
        if name.startswith("SourceFixing"):
            part.update(
                kind="fixing", source_fixing_index=int(semantic.split("-")[1])
            )
        parts[semantic] = part
    expected = {"S1": 17, "L1": 23, "S1J": 18}[family]
    if len(parts) != expected:
        raise ValueError("Retained native part inventory differs")
    return {
        name: part for name, part in parts.items() if name != "display-rail"
    }


def load(source_directory, inventory_directory, source_context_path):
    """Bind frozen private inputs and derive 17 contexts covering 34 IDs."""
    source, inventory, context_path = map(
        Path, (source_directory, inventory_directory, source_context_path)
    )
    if sha(context_path) != SOURCE_CONTEXT_SHA256:
        raise ValueError("Fixed XO-001 source context changed")
    parameters = source_parameters(
        source,
        scale_mm_per_inch=1 / 3,
        gauge_mm=16.5,
        flangeway_mm=1,
        rail_head_width_mm=0.9,
        crossing_ratio=10,
    )
    chairs = (source / "chairs_unit.pas").read_text(encoding="latin-1")
    chairs = chairs.split("implementation", 1)[1].split(
        "procedure init_3d_rea", 1
    )[0]
    chairs = re.sub(r"\{.*?\}", "", chairs, flags=re.DOTALL)
    for family in ("S1", "L1", "S1J"):
        dims = dimensions(family)
        for suffix, field in (("inlong", "inner_mm"), ("outlong", "outer_mm")):
            assert (
                float(_assignment(chairs, family + "_chair_" + suffix) / 3)
                == dims[field]
            )
        inset = _assignment(chairs, family + "_bolts_from_end") / 3
        centres = []
        source_inner = _assignment(chairs, family + "_chair_inlong") / 3
        source_outer = _assignment(chairs, family + "_chair_outlong") / 3
        for side, height in (
            ("in", float(source_inner - inset)),
            ("out", float(-source_outer + inset)),
        ):
            for number in (1, 2):
                centre = (
                    float(
                        _assignment(chairs, f"{family}_{side}bolt_{number}x")
                        / 3
                    ),
                    height,
                )
                if centre not in centres:
                    centres.append(centre)
        assert tuple(centres) == dims["fixing_centres_mm"]
    bindings = {
        str(source / name): digest
        for name, digest in parameters["source_hashes"].items()
    }
    bindings[str(context_path)] = SOURCE_CONTEXT_SHA256
    for relative, digest in NORMALISATION_INPUTS:
        path = inventory / relative
        if sha(path) != digest:
            raise ValueError("Retained normalization evidence changed")
        bindings[str(path)] = digest
    for filename in (
        "paired_switch_source_oracle.py",
        "check_end_source_oracle.py",
    ):
        path = Path(__file__).with_name(filename)
        bindings[str(path)] = sha(path)
    models, parts = {}, {}
    for family, relative, digest in MODEL_INPUTS:
        model = inventory / relative
        if sha(model) != digest:
            raise ValueError("Retained native model changed: " + family)
        bindings[str(model)] = digest
        models[family] = str(model)
        parts[family] = _parts(model, family)
    positions = json.loads(context_path.read_text())["analysis"]["positions"]
    contexts = {}
    for position in positions:
        timber = position["prototype_timber_identifier"]
        if timber not in dict(NOMINAL_STATIONS):
            continue
        try:
            rail = _position_rail(position)
            station = station_from_position(position)
            family = selected_family(parameters, timber, station, rail)
        except ValueError:
            continue
        assert station == dict(NOMINAL_STATIONS)[timber]
        pose = source_rail_pose(parameters, station, rail)
        identity = f"{timber}:rail-{rail}"
        current = contexts.setdefault(
            identity,
            dict(
                timber=timber,
                family=family,
                station_mm=station,
                source_rail_code=rail,
                source_angle_rad=pose["k_rad"],
                source_gauge_y_mm=pose["y_mm"],
                source_branch=pose["source_branch"],
                source_position_ids=[],
            ),
        )
        current["source_position_ids"].append(
            position["stable_chair_position_identity"]
        )
    assert len(contexts) == 17
    assert all(
        len(item["source_position_ids"]) == 2 for item in contexts.values()
    )
    assert (
        sum(len(parts[item["family"]]) * 2 for item in contexts.values())
        == 674
    )
    return {
        "bindings": bindings,
        "references": dict(REFERENCES),
        "parameters": parameters,
        "contexts": contexts,
        "parts_by_family": parts,
        "models": models,
    }


def native_to_target(data, context_id, part_id):
    """Return one proper native-to-source matrix at mounting Z=0."""
    context = data["contexts"][context_id]
    frames = local_frames(
        context["family"],
        context["source_rail_code"],
        context["source_angle_rad"],
        context["source_gauge_y_mm"],
    )
    part = data["parts_by_family"][context["family"]][part_id]
    if part["kind"] == "fixing":
        return frames["fixings"][part["source_fixing_index"] - 1]
    return frames["body"]
