"""Independent source oracle for the private central CC preview proof.

This source-informed comparison follows Templot5 revision 556b, copyright
Martin Wynne and OpenTemplot contributors, under GPL-3.0-or-later. See
NOTICE.md and reference/PROVENANCE.md. Inputs remain reference-only;
this helper grants no physical-fit, production, rights or phase acceptance.

No FreeCAD or product-placement imports are used. The paired source oracle
supplies frozen Pascal parameter reading, switch/closure circle equations
and independent canonical-host interpolation; that reuse is explicit.
CC placement equations and finite component checks are owned here. Private
geometry and receipts are read from caller-supplied paths and never bundled.
The base uses its retained pre-quantisation convention, not complete source
DXF equivalence. Deterministic zero-angle heads give no random-export parity.
All distances are model mm and all angles radians.
"""

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

SOURCE_CONTEXT_SHA256 = (
    "925462e8e080f7d1b7f08c2eb6680ccd832b36d6cc3e6730ca155dbb41f03e71"
)
SOURCE_ORACLE_SHA256 = (
    "334fb0f179705de0844ea6810f9430c1df15e474de759bbad7be088579bed318"
)
INVENTORY_HASHES = {
    "context-native-02/CC/CC.FCStd": "b28b574a517e677c86fc35e26cab9a966e41504cb2242968db45e7c07ac81637",
    "context-native-02/components/04f5464f083c8ca02d0a.normalisation.json": "fa1bf68ac8f13242b9a14a44a774aada0098ad098a3a095ad976c593b0e4e239",
    "context-native-02/components/1c07a95ca47aaca476e4.normalisation.json": "7d079880d6a547a0b083cee2f2ea767ec65a1900abce061c40f829246b24bdd0",
    "context-native-02/components/20201f40e44d15b37a6a.normalisation.json": "efcab620c41e362e50e990a6046442adad806ee3b2d36ec728c6f89b7ae49953",
    "context-native-02/components/423e88aa43f52473c8e3.normalisation.json": "540ae60b49f6fa890d517bdd8e12da411e304ee92e9101622728095448e8b789",
    "context-native-02/components/515fe85189c68fd841eb.normalisation.json": "a2f0636651eac7acdc94c8fa4185e818dc615084e4f20c7ff2897df73fee7d08",
    "context-native-02/components/5e9ae18f2c8aa15e4bab.normalisation.json": "60d8a385470ddedf02ee8fad41713d9a9f12ff6d18e58b5fcfd68f37537e120a",
    "context-native-02/components/7f86841a7011e33b9885.normalisation.json": "1b2246b1997293fc8a64098c90d9b10a152587730cd93d37afd947303653bc82",
    "context-native-02/components/fe618a6c4da5480c984a.normalisation.json": "b57a4def2b7b678b4adcc9ad37b365b637d8fda83d7a35477add7da05d6a5b0f",
    "context-native-02/result.json": "794e14a1a395cb63a22692d2f2ab7cf5e19bf103274faf4f0f8679ae719a8237",
    "context_native.py": "2fffe64936463ece57f7c5d042706393c639a0edc0646415413479837497d763",
    "family_assembly.py": "447c59290cb9648b1a65e77d2e6d75da1ac8df29fcf19a11617f5cfbf317ee38",
    "fixing_candidate/prepared-01.json": "d977520baca779d8bb165a2e9e6bd764e2d1c74dc99d5c797230c4ca83e9d778",
    "source_generator/bolt.faces.json": "a6cd7fda8decb63fe707291a7f0c41b535b77cbab94ef38052414edec0eb5115",
    "turnout_context/assembly-recipes.json": "e484b241fb8edc435b12a162f5eec99ba6c3a3f36100d47fb624fd07956e90a9",
}

IDENTITY_QUANTUM_MM = 1e-12
NATIVE_DATUM = (0.0, -0.45, 149 / 60)
REFERENCES = {
    "selection": "math_unit.pas:4140-4176,4359-4381,4480-4518,26696-26820,30144-30181,31622-31647",
    "base_dimensions": "chairs_unit.pas:1059-1072; math_unit.pas:29297-29321",
    "base_and_centres": "math_unit.pas:30225-30270,31690-31736,24152-24237,24377-24407",
    "jaw_seat_key": "math_unit.pas:28266-28313,28360-28413,28465-28535,30428-30441,31904-31917",
    "insertions": "dxf_unit.pas:11880-11910,11980-12010,12048-12078",
    "zero_shear_crop": "dxf_unit.pas:6894-6908,7033-7039",
    "fixed_boss_random_head": "dxf_unit.pas:2534-2542,8543-8571",
    "source_offset": "math_unit.pas:3026-3072,9035-9103,17792-17932",
}


def sha(path):
    """Return the byte identity of an existing evidence file."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    """Read private JSON evidence without changing its contents."""
    return json.loads(Path(path).read_text())


def rot(point, angle):
    """Rotate a model-mm XYZ point about Z by an angle in radians."""
    c, s = math.cos(angle), math.sin(angle)
    return (c * point[0] - s * point[1], s * point[0] + c * point[1], point[2])


def add(a, b):
    """Add two model-mm coordinate triples."""
    return tuple(x + y for x, y in zip(a, b))


def matrix(angle, translation):
    """Return a homogeneous rigid transform from radians and model mm."""
    c, s = math.cos(angle), math.sin(angle)
    return [
        [c, -s, 0.0, translation[0]],
        [s, c, 0.0, translation[1]],
        [0.0, 0.0, 1.0, translation[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def apply(m, p):
    """Apply a homogeneous matrix to a model-mm XYZ point."""
    return tuple(
        sum(m[i][j] * p[j] for j in range(3)) + m[i][3] for i in range(3)
    )


def chair_frame(p):
    """Map the retained source rail-top datum to its native chair datum."""
    return (-p[0], -p[1] - 0.45, p[2] + 149 / 60)


def vertices(faces):
    """Return all distinct finite source-face vertices in model mm."""
    return sorted(
        {tuple(float(c) for c in p) for f in faces for p in f["vertices"]}
    )


def face_key(points):
    """Identify a face at the retained numerical identity quantum."""
    return tuple(
        sorted(
            tuple(round(c / IDENTITY_QUANTUM_MM) for c in p) for p in points
        )
    )


def x_symmetry(faces):
    """Check complete finite face coverage under an X reflection."""
    actual = {face_key(f["vertices"]) for f in faces}
    reflected = {
        face_key([(-p[0], p[1], p[2]) for p in f["vertices"]]) for f in faces
    }
    return {
        "face_count": len(faces),
        "exact_identity_quantum_face_coverage": actual == reflected,
    }


def _source_oracle():
    path = Path(__file__).with_name("paired_switch_source_oracle.py")
    if sha(path) != SOURCE_ORACLE_SHA256:
        raise ValueError("The independent paired source oracle changed")
    spec = importlib.util.spec_from_file_location("paired_source_math", path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    return oracle


def expected_world_frame(host, **source_parameters):
    """Use independent canonical-host interpolation from the paired oracle.

    This shared source calculation is an explicit independence limitation;
    it imports no product placement code and reads no placement result.
    """
    return _source_oracle().expected_world_frame(host, **source_parameters)


def world_point(frame, point):
    """Map a handed local source point into the canonical host XY frame."""
    return _source_oracle().world_point(frame, point)


def load(source_directory, inventory_directory, source_context_path):
    """Read frozen private inputs and return six source CC contexts.

    Parameters are existing directories and the frozen XO source JSON.
    Changed source, geometry, receipts or source context raise ValueError.
    No files are written and no native application is loaded. Returned
    source coordinates use mm and radians; X is relative to each timber,
    main gauge Y=0 after RH reflection, and rail-top Z=0.
    """
    source_directory = Path(source_directory)
    inventory_directory = Path(inventory_directory)
    source_context_path = Path(source_context_path)
    bindings = {}
    for relative, expected in INVENTORY_HASHES.items():
        path = inventory_directory / relative
        actual = sha(path)
        if actual != expected:
            raise ValueError(
                "Frozen CC geometry/evidence changed: " + relative
            )
        bindings[str(path)] = actual
    if sha(source_context_path) != SOURCE_CONTEXT_SHA256:
        raise ValueError("The frozen XO source context changed")
    bindings[str(source_context_path)] = SOURCE_CONTEXT_SHA256
    result_path = inventory_directory / "context-native-02/result.json"
    result = read(result_path)["CC"]
    recipe = result["source_recipe"]
    recipes_path = (
        inventory_directory / "turnout_context/assembly-recipes.json"
    )
    assert recipe == next(r for r in read(recipes_path) if r["family"] == "CC")
    assert recipe["context"] == {
        "ccl_ccr_variable": False,
        "flare_mm": 0.0,
        "flare_angle_rad": 0.0,
        "fw_correction_check_mm": 0.0,
        "fw_mods_mm": 0.0,
    }
    model = inventory_directory / "context-native-02/CC/CC.FCStd"
    assert sha(model) == result["fixing_proof"]["model_sha256"]
    assert (
        sha(model)
        == "b28b574a517e677c86fc35e26cab9a966e41504cb2242968db45e7c07ac81637"
    )
    assert (
        result["fixing_proof"]["source_fixings"]["head_rotation_degrees"] == 0
    )
    assert (
        result["fixing_proof"]["source_fixings"]["random_export_parity"]
        is False
    )
    # Source-only reader/math is shared with the independent paired oracle.
    # No product placement, catalogue adapter or generator is imported.
    oracle_path = Path(__file__).with_name("paired_switch_source_oracle.py")
    oracle = _source_oracle()
    bindings[str(oracle_path)] = SOURCE_ORACLE_SHA256
    parameters = oracle.source_parameters(
        source_directory,
        scale_mm_per_inch=1 / 3,
        gauge_mm=16.5,
        flangeway_mm=1.0,
        rail_head_width_mm=11 / 12,
        crossing_ratio=10,
    )
    bindings.update(
        {
            str(source_directory / name): value
            for name, value in parameters["source_hashes"].items()
        }
    )
    circles = oracle._circles(parameters)
    k = math.atan(1 / 10)
    r, centre_x, _centre_y = circles["closure"]
    fine_point = centre_x + r * math.sin(k) + 20.0
    a = fine_point + (0.25 / 2) / math.sin(k / 2) + 4 / 3
    # The square-on regular-crossing branch. Offset follows the straight
    # aq3 leg: aq2 + gauge/cos(k), with aq2=gauge+(x-fpx)*tan(k).
    main_interval = (a - 24.0, a + 4.0)
    check_fp = fine_point - 15.5 * math.sin(k)
    check_mid = (a - check_fp) / math.cos(k)
    after = check_mid + 16.0 - 12.0
    before = 52.0 - after - 24.0
    ts_interval = (
        check_fp - before * math.cos(k),
        check_fp + after * math.cos(k),
    )
    context = read(source_context_path)
    targets = {}
    for timber in ("X2-Y", "X3-X", "X4-A"):
        selected = [
            p
            for p in context["analysis"]["positions"]
            if p["prototype_timber_identifier"] == timber
            and p["rail_name"]
            in (
                "main-side stock rail",
                "turnout-side stock rail",
                "main-side check rail",
                "turnout-side check rail",
            )
        ]
        assert len(selected) == 8
        stations = {
            p["source_configuration"]["timber"]["local_x"] for p in selected
        }
        assert len(stations) == 1
        x = stations.pop()
        aq3 = 16.5 + (x - fine_point) * math.tan(k) + 16.5 / math.cos(k)
        for side in ("MS", "TS"):
            low, high = main_interval if side == "MS" else ts_interval
            assert low < x <= high
            d = 0.0 if side == "MS" else -0.5 * math.sin(k)
            origin = (
                (0.0, 0.0, 0.0)
                if side == "MS"
                else (d * math.cos(k), -aq3 - d * math.sin(k), 0.0)
            )
            body_angle = math.pi if side == "MS" else -k
            native_angle = body_angle - math.pi
            native_translation = add(
                origin, rot((0.0, -0.45, -149 / 60), body_angle)
            )
            identity = "RH-" + side + "-" + timber
            targets[identity] = {
                "side": side,
                "timber_id": timber,
                "station_mm": x,
                "aq3_mm": aq3,
                "chair_k_rad": 0.0 if side == "MS" else k,
                "longitudinal_shift_before_rotation_mm": d,
                "source_parallel_interval_mm": [low, high],
                "body_angle_rad": body_angle,
                "body_origin_mm": origin,
                "body_source_to_target": matrix(body_angle, origin),
                "body_native_to_target": matrix(
                    native_angle, native_translation
                ),
                "source_position_ids": [
                    p["stable_chair_position_identity"]
                    for p in selected
                    if ("main-side" if side == "MS" else "turnout-side")
                    in p["rail_name"]
                ],
            }
    parts = {}
    base = recipe["base"]
    base_faces = [
        {"vertices": [base["native_vertices_mm"][i] for i in face]}
        for face in base["native_faces"]
    ]
    names = {("L%d" % i): base["native_vertices_mm"][i] for i in range(32)}
    names.update(
        {("T%d" % i): base["native_vertices_mm"][64 + i] for i in range(4)}
    )
    source_base_faces = [
        {"vertices": [names[name] for name in face]}
        for face in base["roof_faces"]
    ]
    source_base_faces += [
        {
            "vertices": [
                base["native_vertices_mm"][j]
                for j in (i, (i + 1) % 32, (i + 1) % 32 + 32, i + 32)
            ]
        }
        for i in range(32)
    ]
    source_base_faces += [{"vertices": base["native_vertices_mm"][32:64]}]
    base_symmetry = x_symmetry(source_base_faces)
    assert base_symmetry["exact_identity_quantum_face_coverage"]
    parts["base-plinth"] = {
        "kind": "base",
        "source_vertices_mm": vertices(base_faces),
        "source_faces": base_faces,
        "native_object": "base_plinth",
        "source_untriangulated_faces": source_base_faces,
    }
    for semantic in result["semantic_parts"]:
        path = (
            inventory_directory
            / "context-native-02/components"
            / (semantic["request_id"] + ".normalisation.json")
        )
        bindings[str(path)] = sha(path)
        normal = read(path)
        assert normal["status"] == "PASS"
        part = next(
            p for p in normal["parts"] if p["name"] == semantic["part_name"]
        )
        insertion = semantic["insertion"]
        assert set(insertion.values()) == {0.0}
        parts[semantic["identity"]] = {
            "kind": "body",
            "source_vertices_mm": vertices(part["faces"]),
            "source_faces": part["faces"],
            "native_object": semantic["identity"].replace("-", "_"),
            "request_id": semantic["request_id"],
        }
    fixing_path = inventory_directory / "fixing_candidate/prepared-01.json"
    bindings[str(fixing_path)] = sha(fixing_path)
    fixing = read(fixing_path)
    raw_bolt_path = inventory_directory / "source_generator/bolt.faces.json"
    bindings[str(raw_bolt_path)] = sha(raw_bolt_path)
    fixing_symmetry = x_symmetry(read(raw_bolt_path)["faces"])
    assert fixing_symmetry["exact_identity_quantum_face_coverage"]
    closure_symmetry = [
        x_symmetry([closure])
        for kind in ("boss", "ferrule", "pan", "head")
        for closure in fixing["parts"]["bolt:" + kind]["closures"]
    ]
    assert all(
        c["exact_identity_quantum_face_coverage"] for c in closure_symmetry
    )
    centres = result["fixing_proof"]["source_fixings"]["placement"][
        "centres_source_mm"
    ]
    for i, centre in enumerate(centres):
        for j, kind in enumerate(("boss", "ferrule", "pan", "head")):
            primitive = fixing["parts"]["bolt:" + kind]
            number = i * 4 + j
            name = "screw-%02d-%s" % (i + 1, kind)
            parts[name] = {
                "kind": "fixing",
                "source_vertices_mm": vertices(primitive["faces"]),
                "source_faces": primitive["faces"],
                "source_centre_mm": [*centre, 0.0],
                "native_object": "SourceFixing"
                + ("%03d" % number if number else ""),
                "source_fixing_index": i + 1,
                "fixing_part": kind,
            }
    assert len(parts) == 33
    source_ids = [
        identity
        for target in targets.values()
        for identity in target["source_position_ids"]
    ]
    assert len(source_ids) == len(set(source_ids)) == 24
    return {
        "contexts": targets,
        "parts": parts,
        "bindings": bindings,
        "references": REFERENCES,
        "model_path": str(model),
        "parameters": {
            "fine_point_mm": fine_point,
            "a_timber_mm": a,
            "crossing_angle_rad": k,
            "keq_rad": 0.0,
            "fw_mm": 1.0,
            "fw_mods_mm": 0.0,
            "fw_correction_check_mm": 0.0,
            "head_rotation_rad": 0.0,
        },
        "finite_source_symmetry": {
            "base": base_symmetry,
            "fixing_raw_faces": fixing_symmetry,
            "fixing_closure_rings": closure_symmetry,
            "identity_quantum_mm": IDENTITY_QUANTUM_MM,
        },
    }


def source_target_vertices(data, context_id, part_id):
    """Direct Pascal-placement route, independent of native-to-target matrix."""
    context, part = data["contexts"][context_id], data["parts"][part_id]
    if part["kind"] == "base" and context["side"] == "MS":
        # Source hand changes Y only; the proposed proper rotation is
        # independently justified by complete finite X-reflection coverage.
        return [(p[0], -p[1], p[2]) for p in part["source_vertices_mm"]]
    if part["kind"] != "fixing":
        return [
            add(rot(p, context["body_angle_rad"]), context["body_origin_mm"])
            for p in part["source_vertices_mm"]
        ]
    centre = part["source_centre_mm"]
    if context["side"] == "MS":
        target_centre = (centre[0], -centre[1], 0.0)
    else:
        target_centre = add(
            rot(centre, -context["chair_k_rad"]), context["body_origin_mm"]
        )
    # dxf BOLTBOSS remains angle zero; choose the source-permitted integer
    # zero BOLTHEAD angle. No random-export parity is claimed.
    return [add(p, target_centre) for p in part["source_vertices_mm"]]


def retained_native_vertices(data, part_id):
    """Derive native XYZ vertices from the frozen source constituent."""
    part = data["parts"][part_id]
    centre = part.get("source_centre_mm", (0.0, 0.0, 0.0))
    return [chair_frame(add(p, centre)) for p in part["source_vertices_mm"]]


def native_to_target(data, context_id, part_id):
    """Return the proposed native-to-source matrix for one constituent."""
    context, part = data["contexts"][context_id], data["parts"][part_id]
    if part["kind"] != "fixing":
        return context["body_native_to_target"]
    centre = part["source_centre_mm"]
    target_centre = (
        (centre[0], -centre[1], 0.0)
        if context["side"] == "MS"
        else add(
            rot(centre, -context["chair_k_rad"]), context["body_origin_mm"]
        )
    )
    return matrix(
        math.pi,
        (
            target_centre[0] - centre[0],
            target_centre[1] - centre[1] - 0.45,
            -149 / 60,
        ),
    )


def analytical_admission(data):
    """Check finite component mappings without host or file side effects."""
    reports = {}
    for identity, context in data["contexts"].items():
        checks, transforms = {}, {}
        for name, part in data["parts"].items():
            native = retained_native_vertices(data, name)
            expected = source_target_vertices(data, identity, name)
            transform = native_to_target(data, identity, name)
            transforms[name] = {
                "native_object": part["native_object"],
                "matrix": transform,
            }
            transformed = [apply(transform, p) for p in native]
            if part["kind"] == "base" and context["side"] == "MS":
                errors = [
                    min(math.dist(p, q) for q in expected) for p in transformed
                ]
                errors += [
                    min(math.dist(p, q) for q in transformed) for p in expected
                ]
            else:
                errors = [
                    math.dist(p, q) for p, q in zip(transformed, expected)
                ]
            # This is a floating-point operation budget, not railway fit or
            # OCCT tolerance. Distances only; no angular/mixed-unit comparison.
            scale = max(1.0, *(abs(c) for p in expected + native for c in p))
            budget = 64 * sys.float_info.epsilon * scale
            assert max(errors) <= budget
            checks[name] = {
                "vertex_count": len(expected),
                "maximum_residual_mm": max(errors),
                "floating_point_budget_mm": budget,
            }
        reports[identity] = {
            **context,
            "components": transforms,
            "analytical_checks": checks,
        }
    # Retain the failed whole-assembly route explicitly, using raw faceted
    # boss vertices. This is a vertex-identity witness, not a surface distance.
    boss = data["parts"]["screw-01-boss"]["source_vertices_mm"]
    k = data["parameters"]["crossing_angle_rad"]
    mismatch = max(min(math.dist(rot(p, -k), q) for q in boss) for p in boss)
    assert mismatch > IDENTITY_QUANTUM_MM
    result = {
        "schema_version": 1,
        "status": "PASS_COMPONENT_PLACEMENT_ANALYTIC",
        "native_admission": "PENDING",
        "whole_rigid_RH_TS": "FAIL_FIXED_BOSS_ORIENTATION",
        "whole_rigid_failure_maximum_nearest_vertex_offset_mm": mismatch,
        "whole_rigid_failure_classification": "proposed route incompatible with source insertion; not a user-scope blocker",
        "contexts": reports,
        "bindings": data["bindings"],
        "references": REFERENCES,
        "parameters": data["parameters"],
        "model_path": data["model_path"],
        "finite_source_symmetry": data["finite_source_symmetry"],
        "component_count": len(data["parts"]),
        "source_position_count": 24,
        "head_rotation_degrees": 0,
        "random_export_parity": False,
        "geometry_rebuilt": False,
        "base_convention": "retained pre-quantisation branch",
        "limits": [
            "Native vertices/faces/BRep admission still required",
            "Common host transform and actual GUI placement still require proof",
            "No physical-fit, production, rights or phase acceptance",
        ],
        "oracle_sha256": sha(__file__),
    }
    return result
