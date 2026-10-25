"""Independent source oracle for the private CCL/CCR check-end proof.

Source-informed Templot5 revision 556b calculations, copyright Martin
Wynne and OpenTemplot contributors, GPL-3.0-or-later. See NOTICE.md and
reference/PROVENANCE.md. Private inputs grant no fit or production rights.

No product-placement or FreeCAD imports are used. The accepted central
oracle supplies elementary transforms, finite face identity and source-only
host interpolation; its paired helper supplies frozen Pascal parameters.
This reuse is an explicit independence limit. Rail branches are derived
from direct decimal circle and tangent constraints. End selection, handed
jaw arguments and check-seat placement are derived here. Distances are model
mm; angles are radians. Geometry is read from caller-supplied private paths.
The source frame is square-on with fixed end flare, unmodified flangeways,
zero key offset and deterministic zero-angle heads. Neither random export
parity nor final Templot pad/global fixing-angle parity is claimed.
"""

from decimal import Decimal
from decimal import localcontext
from fractions import Fraction
from functools import lru_cache
import hashlib
import importlib.util
import math
from pathlib import Path
import sys

CENTRAL_ORACLE_SHA256 = (
    "1fad60666dfc8bce7af85e70a9cea78690c43cd2c46e35ba8712e0724a69dc65"
)
SOURCE_CONTEXT_SHA256 = (
    "925462e8e080f7d1b7f08c2eb6680ccd832b36d6cc3e6730ca155dbb41f03e71"
)
INVENTORY_HASHES = {
    "context-native-02/result.json": "794e14a1a395cb63a22692d2f2ab7cf5e19bf103274faf4f0f8679ae719a8237",
    "turnout_context/assembly-recipes.json": "e484b241fb8edc435b12a162f5eec99ba6c3a3f36100d47fb624fd07956e90a9",
    "turnout_context/requests.json": "879726329cd59126abd80e7aaf37dcfc4503115193ddbcb9c943ae23360128c2",
    "context-native-02/CCL/CCL.FCStd": "692a8cfbe6845fd9fce4e8b471f1ec37d5388366c6451f9bff2d65601dbccb3d",
    "context-native-02/CCR/CCR.FCStd": "d594dfb2f387c2b2a0360863ea8dcc30cd2057ed06095f8eb1e49a9421282fa7",
    "context-native-02/components/515fe85189c68fd841eb.normalisation.json": "a2f0636651eac7acdc94c8fa4185e818dc615084e4f20c7ff2897df73fee7d08",
    "context-native-02/components/04f5464f083c8ca02d0a.normalisation.json": "fa1bf68ac8f13242b9a14a44a774aada0098ad098a3a095ad976c593b0e4e239",
    "context-native-02/components/423e88aa43f52473c8e3.normalisation.json": "540ae60b49f6fa890d517bdd8e12da411e304ee92e9101622728095448e8b789",
    "context-native-02/components/fe618a6c4da5480c984a.normalisation.json": "b57a4def2b7b678b4adcc9ad37b365b637d8fda83d7a35477add7da05d6a5b0f",
    "context-native-02/components/b18739f93ed1801e2019.normalisation.json": "3431156aba2da515a6ea7b230aa5f2779e64aeb5cd7e84683732e1e0a7452a5a",
    "context-native-02/components/9ee0ac01860bf58a0d18.normalisation.json": "81d73d3b1a284a4aa6a73cf55372365c9393d1b425d55d37f41dfffe13bd6c6d",
    "context-native-02/components/5e9ae18f2c8aa15e4bab.normalisation.json": "60d8a385470ddedf02ee8fad41713d9a9f12ff6d18e58b5fcfd68f37537e120a",
    "context-native-02/components/7f86841a7011e33b9885.normalisation.json": "1b2246b1997293fc8a64098c90d9b10a152587730cd93d37afd947303653bc82",
    "context-native-02/components/622d0ca1b4fcce98f29c.normalisation.json": "9b0107a3d9349489704b2ed0d86f19e320803a0d4784e4b71d9cd1e3c45c0b63",
    "context-native-02/components/8701acf7d79f5cbf724f.normalisation.json": "4cb1f21eda21da5727be7ff8233f35c2293360e93fe577778aabbb61a8389d70",
    "fixing_candidate/prepared-01.json": "d977520baca779d8bb165a2e9e6bd764e2d1c74dc99d5c797230c4ca83e9d778",
    "source_generator/bolt.faces.json": "a6cd7fda8decb63fe707291a7f0c41b535b77cbab94ef38052414edec0eb5115",
}
REFERENCES = {
    "rail_geometry": "math_unit.pas:3039-3059,3357-3428,3840-3855,4735,9035-9171,17766-17799,17865-17927",
    "rail_4_pose": "math_unit.pas:31602-31620",
    "selection": "math_unit.pas:3470-3487,4140-4176,4359-4381,4439,4480-4518,26696-26832",
    "selection_state": "math_unit.pas:22665-22669,22723-22821",
    "handed_family": "heave_chairs.pas:1363-1400",
    "base": "math_unit.pas:30144-30181,30225-30270,31622-31647,31690-31736",
    "main_check_insertions": "math_unit.pas:30333-30370,30434-30473",
    "turnout_check_insertions": "math_unit.pas:31790-31824,31892-31931",
    "jaw_arguments": "math_unit.pas:28116-28132; dxf_unit.pas:7046-7126",
    "block_name_limit": "dxf_unit.pas:3667-4524,4525-5148; WG/VG condition4285",
    "insertions": "dxf_unit.pas:11880-11910,11980-12010,12048-12078",
    "fixings": "dxf_unit.pas:2534-2542,8543-8571",
}


def _decimal(value):
    if (isinstance(value, bool)
            or not isinstance(value, (int, float, Fraction))
            or not math.isfinite(value)):
        raise ValueError("Source parameters must be finite numbers")
    if isinstance(value, Fraction):
        return Decimal(value.numerator) / Decimal(value.denominator)
    return Decimal(str(value))


def _source_geometry(parameters):
    """Solve source circle/tangent constraints, without product helpers.

    Sixty decimal digits keep arithmetic error below binary64 conversion
    error for this frozen C+10 source case. The source parameter reader is
    reused; its circle construction and branch selector are not reused.
    These calculations qualify source placement, not physical fit.
    """
    with localcontext() as context:
        context.prec = 60
        switch = parameters["switch"]
        scale = _decimal(parameters["scale_mm_per_inch"])
        gauge = _decimal(parameters["gauge_mm"])
        flangeway = _decimal(parameters["flangeway_mm"])
        planing = _decimal(switch["planing_angle"])
        crossing = _decimal(parameters["crossing_ratio"])
        planing_length = _decimal(switch["planing"]) * scale
        heel_x = _decimal(switch["heel_lead_inches"]) * scale
        switch_radius = _decimal(switch["switch_radius_inchormax"]) * scale
        if min(scale, gauge, flangeway, planing, crossing,
               planing_length, heel_x, switch_radius) <= 0:
            raise ValueError("Source geometry needs positive parameters")
        planing_norm = (planing * planing + 1).sqrt()
        sin_planing = 1 / planing_norm
        cos_planing = planing / planing_norm
        planing_x = planing_length * cos_planing
        sin_heel = (heel_x - planing_x) / switch_radius + sin_planing
        if not 0 < sin_heel < 1:
            raise ValueError("The source switch circle has no valid heel")
        cos_heel = (1 - sin_heel * sin_heel).sqrt()
        heel_y = (planing_x / planing
                  + switch_radius * (cos_planing - cos_heel))
        crossing_norm = (crossing * crossing + 1).sqrt()
        sin_crossing = 1 / crossing_norm
        cos_crossing = crossing / crossing_norm
        end_y = gauge - 2 * flangeway
        if cos_heel <= cos_crossing or end_y <= heel_y:
            raise ValueError("The bounded source closure circle is absent")
        radius = (end_y - heel_y) / (cos_heel - cos_crossing)
        if radius <= gauge:
            raise ValueError("The source stock-rail radius is not positive")
        centre_x = heel_x - radius * sin_heel
        centre_y = heel_y + radius * cos_heel
        stock_radius = radius - gauge
        return {
            "centre_x_mm": centre_x, "centre_y_mm": centre_y,
            "closure_radius_mm": radius, "stock_radius_mm": stock_radius,
            "stock_heel_station_mm": heel_x - gauge * sin_heel,
            "curve_end_station_mm": centre_x + stock_radius * sin_crossing,
            "curve_end_y_mm": end_y + gauge * cos_crossing,
            "fine_point_mm": (centre_x + radius * sin_crossing
                              + 2 * flangeway * crossing),
            "crossing_ratio": crossing,
        }


def source_rail_geometry(parameters):
    """Return independent source circle, heel, join and fine point in mm.

    Inputs are the explicit scale, gauge, flangeway, crossing ratio and
    semi-curved switch parameters read from the bound Pascal source. This
    test helper covers its regular closure/crossing span only. A returned
    join is the binary64 conversion of the decimal-derived source value.
    """
    values = _source_geometry(parameters)
    result = {name: float(value) for name, value in values.items()}
    result["crossing_angle_rad"] = math.atan2(
        1.0, result["crossing_ratio"],
    )
    return result


def source_rail_pose(parameters, station_mm, side):
    """Return rail, branch, gauge offset and tangent at a source station.

    The independent public join defines this helper's binary64 branch
    boundary: below uses ``radcurve``; equality and above use
    ``turnoutst_main``. This is separate from roundoff in a product
    resolver's intermediate join. Source rail 1 is locally straight;
    source rail 4 uses aq3. Travel direction and host curvature do not
    select the local source branch.
    """
    if side not in ("MS", "TS"):
        raise ValueError("The source rail side must be MS or TS")
    station = _decimal(station_mm)
    values = _source_geometry(parameters)
    join = float(values["curve_end_station_mm"])
    if float(station) < float(values["stock_heel_station_mm"]):
        raise ValueError("The station precedes the bounded closure span")
    if side == "MS":
        branch, rail, aq_rail, y, angle = "main_straight", 1, None, 0.0, 0.0
    else:
        rail, aq_rail = 4, 3
        with localcontext() as context:
            context.prec = 60
            if float(station) < join:
                dx = station - values["centre_x_mm"]
                radius = values["stock_radius_mm"]
                if abs(dx) >= radius:
                    raise ValueError("The source circle has no rail point")
                leg = (radius * radius - dx * dx).sqrt()
                y = float(values["centre_y_mm"] - leg)
                angle = math.atan2(float(dx), float(leg))
                branch = "radcurve"
            else:
                y = float(values["curve_end_y_mm"]
                          + (station - values["curve_end_station_mm"])
                          / values["crossing_ratio"])
                angle = math.atan2(1.0, float(values["crossing_ratio"]))
                branch = "turnoutst_main"
    return {
        "source_branch": branch, "source_rail_code": rail,
        "aq_rail_code": aq_rail, "y_mm": y, "k_rad": angle,
        "curve_end_station_mm": join,
    }


def source_check_selection(bounds, station_mm, state=(None, None)):
    """Evaluate the fixed-flare source selector once for one support.

    Return its check-chair code and new working/extension counters. The
    counters reset per turnout and side. Stock/check companion records
    are two identities for this one invocation, not two selector calls.
    """
    values = tuple(float(_decimal(value)) for value in bounds)
    station = float(_decimal(station_mm))
    if len(values) != 4 or any(a >= b for a, b in zip(values, values[1:])):
        raise ValueError("The selector requires four ordered source bounds")
    if not isinstance(state, tuple) or len(state) != 2:
        raise ValueError("The selector requires working/extension counters")
    working, extension = state
    if any(value is not None and not math.isfinite(_decimal(value))
           for value in state):
        raise ValueError("The source selector state is invalid")
    code = 0
    if values[0] < station <= values[1]:
        if working is None:
            code, working = 1, station
        else:
            code = 0 if station < working else 2
    elif values[1] < station <= values[2]:
        code = 2
    elif values[2] < station <= values[3]:
        if extension is None:
            code, extension = 3, station
        else:
            code = 0 if station > extension else 2
    return {"check_chair": code, "state": (working, extension)}


@lru_cache(maxsize=1)
def _central():
    path = Path(__file__).with_name("central_check_source_oracle.py")
    if hashlib.sha256(path.read_bytes()).hexdigest() != CENTRAL_ORACLE_SHA256:
        raise ValueError("The accepted central source helper changed")
    spec = importlib.util.spec_from_file_location("check_source_math", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_world_frame(host, **source_parameters):
    """Use accepted source-only host interpolation, never product poses."""
    return _central().expected_world_frame(host, **source_parameters)


def world_point(frame, point):
    """Map a handed local source point to its canonical host XY frame."""
    return _central().world_point(frame, point)


def _parts(result, inventory):
    helper = _central()
    base = result["source_recipe"]["base"]
    faces = [
        {"vertices": [base["native_vertices_mm"][i] for i in face]}
        for face in base["native_faces"]
    ]
    names = {"L%d" % i: base["native_vertices_mm"][i] for i in range(32)}
    names.update(
        {"T%d" % i: base["native_vertices_mm"][64 + i] for i in range(4)}
    )
    untriangulated = [
        {"vertices": [names[name] for name in face]}
        for face in base["roof_faces"]
    ]
    untriangulated += [
        {"vertices": [
            base["native_vertices_mm"][j]
            for j in (i, (i + 1) % 32, (i + 1) % 32 + 32, i + 32)
        ]}
        for i in range(32)
    ]
    untriangulated += [{"vertices": base["native_vertices_mm"][32:64]}]
    symmetry = helper.x_symmetry(untriangulated)
    assert symmetry["exact_identity_quantum_face_coverage"]
    parts = {"base-plinth": {
        "kind": "base", "source_vertices_mm": helper.vertices(faces),
        "source_faces": faces, "source_untriangulated_faces": untriangulated,
        "source_insertion": {"rotation_rad": 0, "x_mm": 0, "y_mm": 0,
                             "z_mm": 0}, "native_object": "base_plinth",
    }}
    for semantic in result["semantic_parts"]:
        normal = helper.read(
            inventory / "context-native-02/components"
            / (semantic["request_id"] + ".normalisation.json")
        )
        assert normal["status"] == "PASS"
        part = next(
            p for p in normal["parts"] if p["name"] == semantic["part_name"]
        )
        parts[semantic["identity"]] = {
            "kind": "body", "source_vertices_mm": helper.vertices(
                part["faces"]
            ), "source_faces": part["faces"],
            "source_insertion": semantic["insertion"],
            "source_block": semantic["source_block"],
            "request_id": semantic["request_id"],
            "native_object": semantic["identity"].replace("-", "_"),
        }
    fixing = helper.read(inventory / "fixing_candidate/prepared-01.json")
    evidence = result["fixing_proof"]["source_fixings"]
    assert evidence["head_rotation_degrees"] == 0
    assert evidence["random_export_parity"] is False
    centres = evidence["placement"]["centres_source_mm"]
    assert centres == base["bolt_centres_mm"]
    for i, centre in enumerate(centres):
        for j, kind in enumerate(("boss", "ferrule", "pan", "head")):
            faces = fixing["parts"]["bolt:" + kind]["faces"]
            number = i * 4 + j
            parts["screw-%02d-%s" % (i + 1, kind)] = {
                "kind": "fixing", "source_vertices_mm": helper.vertices(
                    faces
                ), "source_faces": faces, "source_fixing_index": i + 1,
                "fixing_part": kind, "source_insertion": {
                    "rotation_rad": 0, "x_mm": centre[0],
                    "y_mm": centre[1], "z_mm": 0,
                }, "native_object": "SourceFixing"
                + ("%03d" % number if number else ""),
            }
    assert len(parts) == 33
    return parts, symmetry


def _jaw_arguments(result, requests, side, code, flare, angle):
    direction = -1 if code == 14 else 1
    aq_k = angle if side == "MS" else -angle
    shear = direction * aq_k * -1  # jm_h=-1, from the source RH flag.
    common = {
        "flangeway_mm": 1.0, "flare_mm": flare, "loose": False,
        "profile": "code75-a", "scale_mm_per_foot": 4.0,
    }
    expected_inner = dict(
        common, builder="inner", cc=True, crop_mm=0.5 + flare, ef=False,
        half_widen_mm=0.0, l1=False, sc=True, shear_rad=shear, swap=True,
    )
    expected_outer = dict(
        common, builder="outer-sc", cc_swap=True, crop_mm=0.0,
        shear_rad=-shear,
    )
    for names, expected in (
        (("MA", "MC"), expected_inner),
        (("MB", "MD"), expected_outer),
    ):
        component = next(
            p for p in result["source_recipe"]["components"]
            if p["source_block"] in names
        )
        # The only geometry-dependent name branch is WG/VG (DXF4285),
        # false for every MA/MC/TA/TC input. Other name uses label blocks.
        actual = {
            key: value for key, value in requests[
                component["request_id"]
            ].items() if key != "jaw_name"
        }
        assert actual == expected


def load(source_directory, inventory_directory, source_context_path):
    """Read bound private inputs and derive four contexts covering 16 IDs.

    Each context represents two hosts, A and B: eight assemblies in total.
    The selector uses one evaluation per rail/station after a per-turnout
    counter reset. Duplicate stock/check analysis records are witnesses of
    one assembly, not repeated selector calls. A changed input fails closed.
    This function writes no files and builds no geometry.
    """
    helper = _central()
    source, inventory = Path(source_directory), Path(inventory_directory)
    context_path = Path(source_context_path)
    bindings = {}
    for relative, expected in INVENTORY_HASHES.items():
        path = inventory / relative
        actual = helper.sha(path)
        if actual != expected:
            raise ValueError("Frozen check-end input changed: " + relative)
        bindings[str(path)] = actual
    if helper.sha(context_path) != SOURCE_CONTEXT_SHA256:
        raise ValueError("The frozen XO source context changed")
    bindings[str(context_path)] = SOURCE_CONTEXT_SHA256
    helper_path = Path(__file__).with_name("central_check_source_oracle.py")
    if helper.sha(helper_path) != CENTRAL_ORACLE_SHA256:
        raise ValueError("The accepted central source helper changed")
    bindings[str(helper_path)] = CENTRAL_ORACLE_SHA256
    oracle = helper._source_oracle()
    parameters = oracle.source_parameters(
        source, scale_mm_per_inch=1 / 3, gauge_mm=16.5, flangeway_mm=1.0,
        rail_head_width_mm=11 / 12, crossing_ratio=10,
    )
    bindings.update({
        str(source / name): value
        for name, value in parameters["source_hashes"].items()
    })
    family_source = source / "heave_chairs.pas"
    family_hash = helper.sha(family_source)
    if family_hash != (
        "91567df732faa78861c6e963cbb5abeaafd3f5f3b64bf3a6d70aae2ea368c588"
    ):
        raise ValueError("The frozen handed family source changed")
    bindings[str(family_source)] = family_hash
    paired_path = Path(__file__).with_name("paired_switch_source_oracle.py")
    bindings[str(paired_path)] = helper.sha(paired_path)
    results = helper.read(inventory / "context-native-02/result.json")
    recipes = helper.read(inventory / "turnout_context/assembly-recipes.json")
    requests = helper.read(inventory / "turnout_context/requests.json")
    positions = helper.read(context_path)["analysis"]["positions"]
    stationed = [
        p for p in positions
        if "local_x" in p["source_configuration"]["timber"]
    ]
    stationless = [p for p in positions if p not in stationed]
    assert len(stationed) == 300 and len(stationless) == 55
    assert not any(
        p["prototype_timber_identifier"] in ("X1-Z", "X5-B")
        for p in stationless
    )
    angle, flare, crossing = math.atan(1 / 18), 49 / 192, math.atan(1 / 10)
    outlong = 9.25 * (1 / 3)
    inlong = outlong + 1 + flare + 4 * (1 / 3) * math.sin(angle)
    chair_mod = (outlong - inlong) / 2
    rail_geometry = source_rail_geometry(parameters)
    fine_point = rail_geometry["fine_point_mm"]
    a_timber = fine_point + 0.125 / math.sin(crossing / 2) + 4 / 3
    main_bounds = (a_timber - 36 + 4 / 3, a_timber - 24,
                   a_timber + 4, a_timber + 16 - 4 / 3)
    check_fp = fine_point - 15.5 * math.sin(crossing)
    check_mid = (a_timber - check_fp) / math.cos(crossing)
    after = check_mid + 16 - 12
    before = 52 - after - 24
    # Rail flare k5 determines the selector interval; it is distinct from
    # the fixed chair jaw angle atan(1/18). Templot uses ARCSIN here.
    rail_flare = math.asin((19 / 12 - 1) / 12)
    ts_start = check_fp - before * math.cos(crossing)
    ts_end = check_fp + after * math.cos(crossing)
    assert before < 20 / math.cos(crossing)  # source straight-crossing leg
    ts_bounds = (
        ts_start - 12 / math.cos(rail_flare)
        * math.cos(crossing + rail_flare) + 4 / 3,
        ts_start, ts_end,
        ts_end + 12 / math.cos(rail_flare)
        * math.cos(crossing - rail_flare) - 4 / 3,
    )
    parts, symmetry, models = {}, {}, {}
    for family in ("CCL", "CCR"):
        result = results[family]
        assert result["status"] == "PASS"
        assert result["source_recipe"] == next(
            r for r in recipes if r["family"] == family
        )
        assert result["source_recipe"]["context"] == {
            "ccl_ccr_variable": False, "flare_mm": flare,
            "flare_angle_rad": angle, "fw_correction_check_mm": 0.0,
            "fw_mods_mm": 0.0,
        }
        base = result["source_recipe"]["base"]
        assert base["outlong_mm"] == outlong
        assert abs(base["inlong_mm"] - inlong) <= (
            4 * sys.float_info.epsilon * inlong
        )
        model = inventory / "context-native-02" / family / (family + ".FCStd")
        assert helper.sha(model) == result["fixing_proof"]["model_sha256"]
        models[family] = str(model)
        parts[family], symmetry[family] = _parts(result, inventory)
    symmetry["raw_bolt"] = helper.x_symmetry(
        helper.read(inventory / "source_generator/bolt.faces.json")["faces"]
    )
    fixing = helper.read(inventory / "fixing_candidate/prepared-01.json")
    symmetry["fixing_closures"] = [
        helper.x_symmetry([closure])
        for kind in ("boss", "ferrule", "pan", "head")
        for closure in fixing["parts"]["bolt:" + kind]["closures"]
    ]
    assert symmetry["raw_bolt"]["exact_identity_quantum_face_coverage"]
    assert all(
        item["exact_identity_quantum_face_coverage"]
        for item in symmetry["fixing_closures"]
    )
    contexts, selector_invocations, selector_states = {}, [], {}
    for timber, code in (("X1-Z", 14), ("X5-B", 16)):
        for side in ("MS", "TS"):
            road = "main-side" if side == "MS" else "turnout-side"
            selected = [
                p for p in positions
                if p["prototype_timber_identifier"] == timber
                and p["rail_name"] in (
                    road + " stock rail", road + " check rail"
                )
            ]
            assert len(selected) == 4
            stations = {
                p["source_configuration"]["timber"]["local_x"]
                for p in selected
            }
            assert len(stations) == 1
            station = stations.pop()
            bounds = main_bounds if side == "MS" else ts_bounds
            low, high = bounds[:2] if code == 14 else bounds[2:]
            assert low < station <= high
            # All 300 records with source stations, including other rails,
            # have no second station that could consume the end selector.
            # The 55 envelope/inherited records have no local source station.
            competing = {
                p["source_configuration"]["timber"]["local_x"]
                for p in stationed
                if low < p["source_configuration"]["timber"]["local_x"]
                <= high
            }
            assert competing == {station}
            family = (
                ("CCR" if code == 14 else "CCL") if side == "MS"
                else ("CCL" if code == 14 else "CCR")
            )
            _jaw_arguments(results[family], requests, side, code, flare, angle)
            pose = source_rail_pose(parameters, station, side)
            aq3, rail_angle = pose["y_mm"], pose["k_rad"]
            shift = chair_mod * math.sin(rail_angle) if side == "TS" else 0
            origin = (
                (shift * math.cos(rail_angle),
                 -aq3 - shift * math.sin(rail_angle), 0.0)
                if side == "TS" else (0.0, 0.0, 0.0)
            )
            for turnout in sorted({p["parent_turnout_identity"]
                                   for p in selected}):
                pair = [p for p in selected
                        if p["parent_turnout_identity"] == turnout]
                assert len(pair) == 2
                selector_key = (turnout, side)
                selection = source_check_selection(
                    bounds, station,
                    selector_states.get(selector_key, (None, None)),
                )
                selector_states[selector_key] = selection["state"]
                assert selection["check_chair"] == (1 if code == 14 else 3)
                selector_invocations.append({
                    "turnout_identity": turnout, "side": side,
                    "timber_id": timber, "source_station_mm": station,
                    "source_rail_code": pose["source_rail_code"],
                    "source_position_ids": [
                        p["stable_chair_position_identity"] for p in pair
                    ],
                    "check_chair": selection["check_chair"],
                    "state_after": selection["state"],
                })
            contexts["RH-" + side + "-" + timber] = {
                "side": side, "timber_id": timber, "family": family,
                "source_code": code, "station_mm": station,
                "aq3_mm": aq3, "chair_k_rad": rail_angle,
                "body_angle_rad": -rail_angle if side == "TS" else math.pi,
                "body_origin_mm": origin, "chair_mod_mm": chair_mod,
                "longitudinal_shift_before_rotation_mm": shift,
                "source_end_interval_mm": [low, high],
                "source_branch": pose["source_branch"],
                "source_rail_code": pose["source_rail_code"],
                "aq_rail_code": pose["aq_rail_code"],
                "curve_end_station_mm": pose["curve_end_station_mm"],
                "source_position_ids": [
                    p["stable_chair_position_identity"] for p in selected
                ],
            }
    identifiers = [
        identity for c in contexts.values()
        for identity in c["source_position_ids"]
    ]
    assert len(identifiers) == len(set(identifiers)) == 16
    assert len(selector_invocations) == 8
    return {
        "contexts": contexts, "parts_by_family": parts, "model_paths": models,
        "bindings": bindings, "references": REFERENCES,
        "finite_source_symmetry": symmetry, "parameters": {
            "fine_point_mm": fine_point, "a_timber_mm": a_timber,
            "crossing_angle_rad": crossing, "flare_angle_rad": angle,
            "selector_rail_flare_angle_rad": rail_flare,
            "flare_mm": flare, "keq_rad": 0.0, "fw_mm": 1.0,
            "fw_mods_mm": 0.0, "fw_correction_check_mm": 0.0,
            "head_rotation_rad": 0.0, "key_offset_mm": 0.0,
            "main_check_bounds_mm": main_bounds,
            "turnout_check_bounds_mm": ts_bounds,
            "rail_geometry": rail_geometry,
        },
        "selector_scan": {
            "stationed_record_count": len(stationed),
            "physical_support_count": 8,
            "selector_invocation_count": len(selector_invocations),
            "invocations": selector_invocations,
            "stationless_position_ids": [
                p["stable_chair_position_identity"] for p in stationless
            ],
        },
    }


def _part(data, context_id, part_id):
    context = data["contexts"][context_id]
    return context, data["parts_by_family"][context["family"]][part_id]


def _insertion(part):
    insertion = part["source_insertion"]
    return insertion["rotation_rad"], tuple(
        insertion[key] for key in ("x_mm", "y_mm", "z_mm")
    )


def retained_native_vertices(data, context_id, part_id):
    """Derive retained native vertices from each frozen source constituent."""
    helper = _central()
    _context, part = _part(data, context_id, part_id)
    angle, origin = _insertion(part)
    return [
        helper.chair_frame(helper.add(helper.rot(p, angle), origin))
        for p in part["source_vertices_mm"]
    ]


def source_target_vertices(data, context_id, part_id):
    """Calculate Pascal endpoint/hand placement without native poses."""
    helper = _central()
    context, part = _part(data, context_id, part_id)
    side, origin = context["side"], context["body_origin_mm"]
    crossing = context["chair_k_rad"]
    angle = context["body_angle_rad"]
    if part["kind"] == "base" and side == "MS":
        return [(p[0], -p[1], p[2]) for p in part["source_vertices_mm"]]
    if part["kind"] == "fixing":
        _angle, centre = _insertion(part)
        origin = (
            (centre[0], -centre[1], 0.0) if side == "MS"
            else helper.add(helper.rot(centre, -crossing), origin)
        )
        angle = 0.0  # source BOLTBOSS and deterministic BOLTHEAD convention
    elif part.get("source_block") in ("CCSEATCK", "CCKEY"):
        flare = data["parameters"]["flare_mm"]
        alpha = data["parameters"]["flare_angle_rad"]
        direction = -1 if context["source_code"] == 14 else 1
        if side == "MS":
            angle = math.pi - direction * alpha
            origin = (direction * flare * math.cos(alpha) / 2,
                      -flare - flare * math.sin(alpha) / 2, 0.0)
        else:
            angle = -crossing + direction * alpha
            shift = context["longitudinal_shift_before_rotation_mm"]
            origin = helper.add(
                helper.rot((shift, flare, 0.0), -crossing),
                (0.0, -context["aq3_mm"], 0.0),
            )
    return [
        helper.add(helper.rot(p, angle), origin)
        for p in part["source_vertices_mm"]
    ]


def native_to_target(data, context_id, part_id):
    """Propose proper rotations of retained parts; no reflection or rebuild."""
    helper = _central()
    context, part = _part(data, context_id, part_id)
    _angle, centre = _insertion(part)
    side, origin = context["side"], context["body_origin_mm"]
    if part["kind"] == "fixing":
        target = (
            (centre[0], -centre[1], 0.0) if side == "MS"
            else helper.add(
                helper.rot(centre, -context["chair_k_rad"]), origin
            )
        )
        return helper.matrix(math.pi, (
            target[0] - centre[0], target[1] - centre[1] - 0.45, -149 / 60,
        ))
    angle = context["body_angle_rad"] - math.pi
    delta = (0.0, 0.0, 0.0)
    if side == "TS" and part.get("source_block") in ("CCSEATCK", "CCKEY"):
        flare = data["parameters"]["flare_mm"]
        alpha = data["parameters"]["flare_angle_rad"]
        delta = helper.rot(
            (-centre[0], -flare * math.sin(alpha) / 2, 0.0),
            -context["chair_k_rad"],
        )
    rotated_datum = helper.rot(helper.NATIVE_DATUM, angle)
    translation = tuple(
        origin[i] + delta[i] - rotated_datum[i] for i in range(3)
    )
    return helper.matrix(angle, translation)


def analytical_admission(data):
    """Compare all finite vertices and expose the old TS seat-frame failure."""
    helper = _central()
    reports = {}
    for identity, context in data["contexts"].items():
        checks, transforms = {}, {}
        for name, part in data["parts_by_family"][context["family"]].items():
            native = retained_native_vertices(data, identity, name)
            expected = source_target_vertices(data, identity, name)
            transform = native_to_target(data, identity, name)
            actual = [helper.apply(transform, p) for p in native]
            if part["kind"] == "base" and context["side"] == "MS":
                errors = [
                    min(math.dist(p, q) for q in expected) for p in actual
                ]
                errors += [
                    min(math.dist(p, q) for q in actual) for p in expected
                ]
            else:
                errors = [math.dist(p, q) for p, q in zip(actual, expected)]
            scale = max(1.0, *(abs(c) for p in native + expected for c in p))
            budget = 64 * sys.float_info.epsilon * scale
            assert max(errors) <= budget
            checks[name] = {
                "vertex_count": len(expected),
                "maximum_residual_mm": max(errors),
                "floating_point_budget_mm": budget,
            }
            transforms[name] = {
                "native_object": part["native_object"], "matrix": transform,
            }
        witness = None
        if context["side"] == "TS":
            family_parts = data["parts_by_family"][context["family"]]
            name = next(
                n for n, p in family_parts.items()
                if p.get("source_block") == "CCSEATCK"
            )
            old = native_to_target(data, identity, "base-plinth")
            actual = [
                helper.apply(old, p)
                for p in retained_native_vertices(data, identity, name)
            ]
            expected = source_target_vertices(data, identity, name)
            witness = max(math.dist(p, q) for p, q in zip(actual, expected))
            assert witness > checks[name]["floating_point_budget_mm"]
            assert abs(witness - data["parameters"]["flare_mm"] / 2) <= (
                checks[name]["floating_point_budget_mm"]
            )
        reports[identity] = dict(
            context, analytical_checks=checks, components=transforms,
            uncorrected_ts_seat_residual_mm=witness,
        )
    return reports
