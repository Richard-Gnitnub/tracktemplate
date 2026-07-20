#!/usr/bin/env python3
"""Validate the blocked Phase 1 Templot5 556b S1 oracle contract."""

import copy
import json
import pathlib
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import templot_s1_oracle as oracle  # noqa: E402


SPEC_PATH = (
    ROOT / "reference" / "oracles" / "templot5-556b-s1-oracle.json"
)
EXPECTED_COMPONENTS = ("S1OUTJAW", "S1INJAW", "S1SEAT", "KEY")
EXPECTED_ARCHIVE_SHA256 = (
    "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
)
EXPECTED_REJECTED_EXECUTABLE_SHA256 = (
    "3df2cb480f828876967e5f7b5172111f5a1f1a159529c52a16456ebb627731f5"
)
EXPECTED_MEMBER_SHA256 = {
    "T556B_ZIPPED_FOR_UPLOAD/README.md": "fe57740b1548651674895b96b7f50a633410ce4a6218d07fe2d6461e19aa8671",
    "T556B_ZIPPED_FOR_UPLOAD/OpenTemplot2024.lpi": "fbc24f99e79c79ae3a23ea4b4218b7f0186dada33457e11faf3edb964f98b80f",
    "T556B_ZIPPED_FOR_UPLOAD/OpenTemplot2024.lpr": "ceefe944c2300f5dedea7eb64778d4048f0b1545daa4052cf023aa02d67d5766",
    "T556B_ZIPPED_FOR_UPLOAD/control_room.lfm": "27d1ec9d1ef4ae9a69494af39ffdf9d36ee31c775060d46470a46c2556a494cf",
    "T556B_ZIPPED_FOR_UPLOAD/control_room.pas": "60f44096afdef770488debd3feaa70bede22066acc7f539f6ee7d159f7b9d19e",
    "T556B_ZIPPED_FOR_UPLOAD/dxf_unit.pas": "f6bd9cbe8ef63397f4a632535f7160a7e6f82498a334bcde8580c9d0ed5b4f8d",
    "T556B_ZIPPED_FOR_UPLOAD/chairs_unit_x.pas": "aff0e0079c4749c1132aac0ff15a742afef3f13080178c2ad66545be7235d92a",
}


def _pair(code, value):
    return [str(code), str(value)]


def _face(offset=0):
    result = _pair(0, "3DFACE") + _pair(8, "CHAIRS")
    vertices = (
        (offset + 0.0, 0.0, 0.0),
        (offset + 1.0, 0.0, 0.0),
        (offset + 0.0, 1.0, 0.5),
        (offset + 0.0, 1.0, 0.5),
    )
    for index, vertex in enumerate(vertices):
        result += _pair(10 + index, vertex[0])
        result += _pair(20 + index, vertex[1])
        result += _pair(30 + index, vertex[2])
    return result


def _insert(name, x):
    return (
        _pair(0, "INSERT")
        + _pair(2, name)
        + _pair(10, x)
        + _pair(20, 2.0)
        + _pair(30, 0.5)
        + _pair(41, 1.0)
        + _pair(42, 1.0)
        + _pair(43, 1.0)
        + _pair(50, 0.0)
    )


def _synthetic_dxf(components=EXPECTED_COMPONENTS, direct_face=True, extra_insert=None):
    lines = _pair(0, "SECTION") + _pair(2, "BLOCKS")
    for index, name in enumerate(components):
        lines += _pair(0, "BLOCK") + _pair(2, name) + _pair(70, 0)
        lines += _face(index * 2)
        lines += _pair(0, "ENDBLK")
    lines += _pair(0, "ENDSEC")
    lines += _pair(0, "SECTION") + _pair(2, "ENTITIES")
    if direct_face:
        lines += _face(20)
    for index, name in enumerate(EXPECTED_COMPONENTS):
        lines += _insert(name, index * 3)
    if extra_insert is not None:
        lines += _insert(extra_insert, 99)
    lines += _pair(0, "ENDSEC") + _pair(0, "EOF")
    return "\n".join(lines) + "\n"


def _synthetic_stl():
    return """solid synthetic-s1
facet normal 0 0 0
outer loop
vertex 0 0 0
vertex 1 0 0
vertex 0 1 0.5
endloop
endfacet
facet normal 0 0 0
outer loop
vertex 1 0 0
vertex 1 1 0.5
vertex 0 1 0.5
endloop
endfacet
endsolid synthetic-s1
"""


def _expect_oracle_error(callback, expected_text):
    try:
        callback()
    except oracle.OracleValidationError as exc:
        assert expected_text in str(exc), str(exc)
    else:
        raise AssertionError("expected OracleValidationError: {}".format(expected_text))


def validate():
    document = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert oracle.validate_spec(document) == []
    spec = oracle.load_spec(SPEC_PATH)
    assert spec["status"] == "blocked"
    assert spec["permitted_role"] == "local comparison oracle only"
    assert tuple(
        spec["semantic_contract"]["dxf"]["required_block_names"]
    ) == EXPECTED_COMPONENTS
    assert tuple(
        spec["semantic_contract"]["dxf"]["required_insert_names"]
    ) == EXPECTED_COMPONENTS
    assert spec["capture_recipe"]["raw_artifacts_tracked"] is False
    assert spec["capture_recipe"]["isolated_profile_required"] is True
    assert spec["capture_recipe"]["existing_user_profile_allowed"] is False
    assert spec["capture_recipe"]["fixture"]["status"] == "missing"
    assert spec["acceptance_gate"]["canonical_production_input"] is False
    assert [item["blocker_id"] for item in spec["blockers"]] == [
        "exact-556b-executable",
        "isolated-556b-environment",
        "frozen-s1-fixture-and-settings",
        "frozen-s1-artifacts",
    ]
    settings = spec["capture_recipe"]["settings"]
    assert settings["track_scale_mm_per_foot"] == 4.0
    assert settings["model_scale_denominator"] == 76.2
    assert settings["track_gauge_mm"] == 16.5
    assert settings["export_mode"] == "3-D CAD"
    assert settings["print_scaled_output"] is False
    assert settings["jaw_policy"] == "all solid outer jaws"
    assert spec["source"]["archive"]["sha256"] == EXPECTED_ARCHIVE_SHA256
    assert spec["source"]["observed_candidate"]["sha256"] == (
        EXPECTED_REJECTED_EXECUTABLE_SHA256
    )
    assert spec["source"]["observed_candidate"]["detected_version"] == "5.55.a"
    assert {
        item["path"]: item["sha256"]
        for item in spec["source"]["required_members"]
    } == EXPECTED_MEMBER_SHA256

    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/benchmark-output/" in ignored
    assert "/reference/t5_files_556b_06_feb_2025.zip" in ignored

    archive_path = ROOT / spec["source"]["archive"]["path"]
    if archive_path.is_file():
        source_result = oracle.probe_source_archive(archive_path, spec)
        assert source_result["status"] == "exact-source-verified-build-blocked"
        assert source_result["s1_component_route_confirmed"] is True
        assert source_result["self_contained_build_ready"] is False
        assert set(source_result["missing_declared_build_inputs"]) == {
            "HTML_VIEWER_MODS",
            "FrameViewer09",
            "synapse_units",
        }
        assert len(source_result["required_members"]) == 7

    changed = copy.deepcopy(document)
    changed["status"] = "accepted"
    assert any("must remain blocked" in item for item in oracle.validate_spec(changed))

    changed = copy.deepcopy(document)
    changed["capture_recipe"]["raw_artifacts_tracked"] = True
    assert any("must remain untracked" in item for item in oracle.validate_spec(changed))

    changed = copy.deepcopy(document)
    changed["semantic_contract"]["dxf"]["required_insert_names"].remove("KEY")
    assert any(
        "same parts" in item for item in oracle.validate_spec(changed)
    )

    with tempfile.TemporaryDirectory(prefix="tracktemplate-s1-oracle-") as temp_name:
        temp = pathlib.Path(temp_name)
        old_executable = temp / "templot-555a.exe"
        old_executable.write_bytes(b"MZ\x00synthetic\x005.55.a\x00")
        old_result = oracle.inspect_executable(old_executable, spec)
        assert old_result["pe_signature"] is True
        assert old_result["detected_versions"] == ["5.55.a"]
        assert old_result["eligible_for_isolated_capture"] is False

        exact_executable = temp / "templot-556b.exe"
        exact_executable.write_bytes(
            b"MZ\x00synthetic\x00version  556b       February  2025\x00"
        )
        exact_result = oracle.inspect_executable(exact_executable, spec)
        assert exact_result["matched_required_markers"] == [
            "version  556b       February  2025"
        ]
        assert exact_result["eligible_for_isolated_capture"] is True

        dxf_path = temp / "s1.dxf"
        stl_path = temp / "s1.stl"
        dxf_path.write_text(_synthetic_dxf(), encoding="ascii")
        stl_path.write_text(_synthetic_stl(), encoding="ascii")
        summary = oracle.inspect_artifacts(dxf_path, stl_path, spec)
        assert summary["status"] == "semantically-valid-unaccepted-capture"
        assert summary["canonical_production_input"] is False
        dxf_summary = summary["artifacts"]["dxf"]["semantics"]
        assert dxf_summary["required_insert_counts"] == {
            name: 1 for name in EXPECTED_COMPONENTS
        }
        assert dxf_summary["direct_entity_3dface_count"] == 1
        assert dxf_summary["direct_entity_bounds_mm"] == {
            "min": [20.0, 0.0, 0.0],
            "max": [21.0, 1.0, 0.5],
        }
        assert all(
            item["face_count"] == 1
            for item in dxf_summary["required_blocks"].values()
        )
        stl_summary = summary["artifacts"]["stl"]["semantics"]
        assert stl_summary["facet_count"] == 2
        assert stl_summary["vertex_record_count"] == 6
        assert stl_summary["bounds_mm"] == {
            "min": [0.0, 0.0, 0.0],
            "max": [1.0, 1.0, 0.5],
        }

        missing_block = temp / "missing-key.dxf"
        missing_block.write_text(
            _synthetic_dxf(components=EXPECTED_COMPONENTS[:-1]),
            encoding="ascii",
        )
        _expect_oracle_error(
            lambda: oracle.inspect_dxf(missing_block, spec),
            "required S1 block is missing: KEY",
        )

        unequal = temp / "unequal-inserts.dxf"
        unequal.write_text(
            _synthetic_dxf(extra_insert="S1OUTJAW"), encoding="ascii"
        )
        _expect_oracle_error(
            lambda: oracle.inspect_dxf(unequal, spec),
            "INSERT counts must be equal and non-zero",
        )

        no_base = temp / "no-direct-base.dxf"
        no_base.write_text(_synthetic_dxf(direct_face=False), encoding="ascii")
        _expect_oracle_error(
            lambda: oracle.inspect_dxf(no_base, spec),
            "no direct assembly/base 3DFACE entities",
        )

        broken_stl = temp / "broken.stl"
        broken_stl.write_text(
            _synthetic_stl().replace("endfacet\n", "", 1), encoding="ascii"
        )
        _expect_oracle_error(
            lambda: oracle.inspect_ascii_stl(broken_stl, spec),
            "facet/vertex records are incomplete",
        )

    print("Phase 1 Templot5 556b S1 oracle validation passed")


if __name__ == "__main__":
    validate()
