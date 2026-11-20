#!/usr/bin/env python3
"""Prepare the fixed, isolated runtime assessment without running FreeCAD.

Only frozen public source and the approved synthetic base enter this tree.
An assessment contract is not a runtime admission. The original checkout
and all product, bootstrap and legacy oracle bytes remain unchanged.
"""

import argparse
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile


BASE_COMMIT = "dcb326e531bde7d861ce4a316776dd00dab297e8"
CANONICAL_PATH = "reference/contracts/phase1-compatibility.json"
CANONICAL_SHA256 = (
    "6539ff066b8abcd81cb111c3127124580e6bca44eb19c09ea8ae93175de7113f"
)
CANDIDATE_SHA256 = (
    "285192eeb388e0d2d6be64a47170e1cafa9ffb8efbf6ee3b43d51edc3769c7e7"
)
CANDIDATE_PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.16-qt6.11.3-coin4.0.10"
)
BASE_SHA256 = (
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c"
)
PUBLIC_CAPSULE_SHA256 = (
    "d70635526b325d392a1074b721602118fb4ae7a587302472cf713bd93b8800f5"
)
PUBLIC_CAPSULE_BYTES = 34914
BASE_BYTES = 636344
BASE_PATH = (
    "benchmark-output/freecad-bridge/fixtures/"
    "b14-default-base-regenerated.FCStd"
)
PREVIOUS_113 = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
PREVIOUS_114 = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"
)
DECISION_INPUTS = {
    "assessment-compatibility.json": (17402, CANDIDATE_SHA256),
    "qualification-matrix-input-map.json": (
        105804,
        "7da43a08757c529f7a90f7656c109c1b979a956d4a2618241054889f749aabbc",
    ),
    "compatibility-gui-output-handling-proposal-v2.json": (
        157516,
        "0dc9d0d13eeb9722e6d3e9e9d4c7ecdf14131fe1e8724be65bfd2ab726a2930b",
    ),
}

# These fixed substitutions only bind the candidate's exact profile. Each
# original file hash and single literal occurrence are mandatory. The
# Phase 3 child and B4 comparison helper close known indirect launch/import
# paths; this table is not expanded dynamically from arbitrary source.
PROFILE_ADAPTATIONS = (
    (
        'tests/freecad_validate_core_export_staging.py',
        'a0650e4ce9719e17cde89d4ac91c4e29c795827132538f4755f8ea48f72bcb2c',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase2_foundation.py',
        '4729d4f8bec2614ca38895091dea393929a90b8cda7766902315b533f84ec9dc',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase3_transition_slice.py',
        '57747dc039214abff14593044a20266ddf0c25f8675c6db7904f10f0e1a5cb5d',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase4_chair_definition.py',
        'eec0bfb60760a0a695fa701ccd43691f3be8233c1fca2b957fba7eac5fe446ea',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase4_transition_persistence.py',
        '3a1e5b1369edf293392692e23e8e8d058ab4657bcfbbd776f916218474537aa7',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase4_transition_state.py',
        '964dac836a9bd6585efea3195a99676186d165f3812dcf81430234a09d1829c4',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase6_transition_dxf_export.py',
        'e75c26d40a76b100c4d6cc486bb6279854832cc4b659dea2a1f535b5993063c0',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase6_transition_exact_contract.py',
        '50d62debc8c1b7f21cf84158b0c4f5ba925d47db916664d4221fcddf950950fc',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase6_transition_exact_geometry.py',
        'e9df630ef1a33a20b52b0bd961dd4255e9e23ad8344f8832718a095baee7cf51',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_clothoid_exit.py',
        'c70ab5a572bed5bc597917e19874921a829c2a67521230f4b8a2c3bd37774faa',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_common_straight_extensions.py',
        '575fde15ff2f90e894533c8f1d0ff1f627b3c05a2cb98c946ae12d70a1b50523',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_concentric_core.py',
        'ae6d2f55f6d6db888ba0eaf3cce7e160f87ab01aa8d33fa41e7ab763d398f757',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_connected_straight_validation.py',
        '00aa8f2127b20a63679ffb667fccedb249feaa0072873ff3d4e42489be82b66f',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_core_layout_export.py',
        '30364a56a9105520f74beca788278a7982667dcfadf359cba59ae21c94ba4269',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_main_circle_centre.py',
        'b2262904546a0ed8133448476555001702ac694eef72aabdef0cdf6da55eed3d',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_platform_core.py',
        '633f22b6a541a0462ce54e1fcf007276fb9ade3c1b0776cf37eafeff37fc1c06',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_platform_heading_coverage.py',
        'dc03dc4698b142e345e6fdaca353e60722c8d8e4c60d25f54818673d7f04ae1d',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_platform_input_validation.py',
        '68c5e7e013430775a117cf5ebdb252204403adc4a289490529494e906e125e5e',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_platform_longitudinal_bounds.py',
        'cf0860828bfbd65300d6c22cf6cad7158e91044314cb2fb4b8f610f9b4520fb3',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_platform_top_heights.py',
        '39ea194df400cd7ed0dc30a1cc6f2764a68dc300bc1617274a44440569931b22',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_platform_transitions.py',
        '1332dff68849cf5261e86a81507cca11b12b5c4d85fd9d0dd9b9b78ddbb98926',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_straight_route.py',
        '2966f6f33811e23effdf76df2c738979f5d1726a39d600c204bf6f161c5923c5',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase7_track_alignment_preparation.py',
        '2ea63ccfef3610feae74fc0de3ed2d6a131ab9ae58e8d6378225f31533fafab3',
        PREVIOUS_114,
    ),
    (
        'tests/freecad_validate_phase8_crossover_b4_recovery.py',
        '670404a948f9bfae8098b63bc19999e4e9766447237ffe7cb259d396b544e9d6',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_crossover_edit_recovery.py',
        'd4c95244c3eb0dbeb53441e9937b2efa584c3fe783fae3f434635fba24e84f17',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_crossover_host_integration_recovery.py',
        '42cc5d577a5e0891ab0f26870683921d31a60f2e518fe3a05dec580db4c1e441',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_crossover_preflight.py',
        'e05b42b69892e5028f349058efb2613607dd782c1bb318ba89b10158c645542f',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_crossover_selected_export.py',
        'dfd2f72262bf438ebd75e1e97aa9fd0c99edb70f7350d6ff944e2697ef6dbc26',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_curved_host_crossover.py',
        'df580546e3fb3a649b7a1f9fe8d601276aaffbe29eb186a923c9912349699af7',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_curved_host_turnout.py',
        'cc6d7b79df6da6843b1d990ead56eec2d26fa3528dc0ddff01f0651004c30ed3',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_straight_crossover_b4.py',
        'b0deac544bd5543c93addd630ce89463d3c4dec235386662c87c1ccca82d340c',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_straight_host_crossover.py',
        '36994938a2b0b1f322da146078799cc877c2a25d1d5d1540fc4e12502e3a64c1',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_straight_host_turnout.py',
        '9a1cd383b7f35cf857c81f3a53ce320db0ee311fe01ceeaaf0dcc5fda77b53aa',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_turnout_host_integration_recovery.py',
        'c3e252d4e017747ca7ebcde9b575732158a523614c4adf579aaabc2e60b5a610',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_turnout_selected_export.py',
        '3d00a5588090f9ddad9bccee8daed5fea736fa35c1b283741eaa0dd3480c5bc8',
        PREVIOUS_113,
    ),
    (
        'tests/freecad_validate_phase8_turnout_toe_range.py',
        'f8a2be94d66fc53208296ec13f2a2c1bc9aa07c7a7048be208c23d8b0cf4acec',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/compare_phase8_straight_crossover_b4_modes.py',
        '90adc999542fc9d73a0a3ef2bbf73a1564423ca059cb2c1f58cf7262fb1d6e52',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase3_transition_workflow.py',
        '4cad49afbd9622b0a0c67870b74f9881760e08712f5039266cf6f3a475120118',
        PREVIOUS_114,
    ),
    (
        'tools/freecad_bridge/run_phase5_transition_viewprovider.py',
        '17cc6a0e2db06d849ca5e19de13ac8d48cfc6d21502c572cc17fbc47a4429cbd',
        PREVIOUS_114,
    ),
    (
        'tools/freecad_bridge/run_phase7_core_layout_export_workflow.py',
        'b8fc72c5c1e21de5f3423081a9d046b896670ace8988d2a5ac161e997b9ee99c',
        PREVIOUS_114,
    ),
    (
        'tools/freecad_bridge/run_phase8_crossover_b4_recovery_gui.py',
        'c87269b7b83cb7547a25e4219e52a36ea15cf9c27be01543eae222fe447f6c98',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_crossover_edit_recovery_gui.py',
        '06ca874aac2b34ba002f4671edc5f86aa78354e30b0644372554e952adee97b3',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_crossover_host_integration_recovery_gui.py',
        'ade8cf56ad1ab15306dee3a3410afe2223fc40b73ae661c794508bf80bc499e1',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_crossover_selected_export_gui.py',
        '67338113c1e4df4c4638459073afc9c92d8feefefd32d9df4b3a0b2d6f7a51d7',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_straight_crossover_b4_gui.py',
        '54adc499c654803bd0e69d4b6be6a1a6e4919a34094deab805f4a2c87c474b7d',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_straight_host_crossover_gui.py',
        '51d9a5b324e24b8998140f8a8c6d10014e767fe298778b828a29af2041e52a87',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_straight_host_turnout_gui.py',
        '538fde1b468909e410599e42c6cdabbb8b48d3e3f75dfad51a6f1196deb4ca1e',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_turnout_host_integration_recovery_gui.py',
        '73fd6b082406f18f2fdd1084c886516684571e52e5a4db370fcfbb5168f57539',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_turnout_selected_export_gui.py',
        '809933449d71baa98cad9bdfc77c3e91474fb4799a2aef524d98993ec1509124',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_phase8_turnout_toe_gui.py',
        'b51686adc67bc2419dd96d2a1fd190e87bb4b22463ce9bd17baacd41b792e052',
        PREVIOUS_113,
    ),
    (
        'tools/freecad_bridge/run_selected_export_document_gui.py',
        'ffd8b9e146e9d6517ff8fb679574bd4f2dc22eff0c2ba61f4c02e55194ecb9d8',
        PREVIOUS_114,
    ),
    (
        'tools/freecad_bridge/run_selected_export_rollback_gui.py',
        '40220fa45cc497f713363e35f971bf4f74a2ef73a725253e19f9c3793a9f3eb6',
        PREVIOUS_114,
    ),
    (
        'tools/freecad_bridge/run_selected_export_set_gui.py',
        'cbb63473c73fb325a330c95165a3f6bad66b6c25e93e2eacccecdcfc3c2e87fd',
        PREVIOUS_114,
    ),
)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _identity(data):
    return {"bytes": len(data), "sha256": _sha256(data)}


def _read_regular(path):
    """Reject links in every path component before reading regular bytes."""
    path = Path(path).absolute()
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("Symbolic links are not assessment inputs")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Assessment input is not a regular file")
        return stream.read()


def _relative_name(value):
    path = Path(value)
    if (path.is_absolute() or not path.parts
            or any(part in {".", ".."} for part in path.parts)
            or "\\" in value or str(path) != value):
        raise ValueError("Unsafe assessment member name")
    return path


def _frozen_source(source_root):
    """Read an exact commit, without archive extraction or Git mutation."""
    completed = subprocess.run(
        ["git", "archive", "--format=tar", BASE_COMMIT],
        cwd=source_root, check=True, capture_output=True, timeout=30,
    )
    files = {}
    modes = {}
    with tarfile.open(fileobj=io.BytesIO(completed.stdout)) as archive:
        for member in archive:
            if member.isdir():
                continue
            _relative_name(member.name)
            if not member.isfile() or member.name in files:
                raise ValueError("Archive contains a non-regular member")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("Archive member has no content")
            with stream:
                files[member.name] = stream.read()
            modes[member.name] = 0o755 if member.mode & 0o111 else 0o644
    if len(files) != 811:
        raise ValueError("Frozen source inventory changed")
    if _sha256(files[CANONICAL_PATH]) != CANONICAL_SHA256:
        raise ValueError("Canonical compatibility contract changed")
    return files, modes


def _public_capsule(decision_root):
    path = Path(decision_root)
    if path.is_file() or path.is_symlink():
        capsule = _read_regular(path)
    else:
        records = {}
        for name, (size, digest) in DECISION_INPUTS.items():
            data = _read_regular(path / name)
            if len(data) != size or _sha256(data) != digest:
                raise ValueError("Assessment decision input changed: " + name)
            records[name] = data
        matrix = json.loads(records["qualification-matrix-input-map.json"])
        capsule = _json_bytes({
            "schema_version": 1,
            "assessment_contract_utf8": records[
                "assessment-compatibility.json"
            ].decode(),
            "matrix": {
                kind: [{key: entry[key] for key in ("path", "bytes", "sha256")}
                       for entry in matrix[kind]]
                for kind in ("native_entries", "gui_entries")
            },
            "source_identities": {
                name: _identity(data) for name, data in sorted(records.items())
            },
        })
    if (len(capsule) != PUBLIC_CAPSULE_BYTES
            or _sha256(capsule) != PUBLIC_CAPSULE_SHA256):
        raise ValueError("Public assessment capsule changed")
    return capsule


def export_assessment_inputs(decision_root, destination_file):
    """Write the fixed public projection, with no local evidence paths.

    The capsule contains the exact isolated candidate contract, the 79
    selected source identities, and identities of the three original
    decision inputs. It contains no historical commands or private paths.
    """
    capsule = _public_capsule(decision_root)
    destination_file = Path(destination_file).absolute()
    if not destination_file.parent.is_dir():
        raise ValueError("Public capsule parent must already exist")
    for component in (destination_file.parent, *destination_file.parent.parents):
        if component.is_symlink():
            raise ValueError("Public capsule destination contains a link")
    _write_new(destination_file, capsule)
    return _identity(capsule)


def _adapt_source(original, decisions):
    """Apply only the reviewed profile, contract and raw fixture bindings."""
    adapted = dict(original)
    for name, digest, old_profile in PROFILE_ADAPTATIONS:
        data = original[name]
        if _sha256(data) != digest or data.count(old_profile.encode()) != 1:
            raise ValueError("Profile adaptation source drift: " + name)
        adapted[name] = data.replace(
            old_profile.encode(), CANDIDATE_PROFILE.encode(), 1,
        )
    name = "reference/contracts/phase1-crossover-feasibility.json"
    data = original[name]
    if _sha256(data) != (
        "bfa5c2ca19888cadcdf4dcec87f8f15759b078205bb916d6b6d2b8fde8c8a5a3"
    ):
        raise ValueError("Crossover feasibility source drift")
    replacements = (
        (b"b14-default-base.FCStd", b"b14-default-base-regenerated.FCStd"),
        (
            b"59d06cf57d65d9560dd53915fce2bef19130c534d214f92c9699066060dc4357",
            BASE_SHA256.encode(),
        ),
    )
    for before, after in replacements:
        if data.count(before) != 1:
            raise ValueError("Crossover fixture binding changed")
        data = data.replace(before, after, 1)
    adapted[name] = data
    name = "tools/freecad_bridge/run_phase8_crossover_preflight_gui.py"
    data = adapted[name]
    if (_sha256(original[name]) != (
        "b0d35344d3d454a5617f5b500e9ab0fe0663761455760e2c78b23d72cd841e09"
    ) or data.count(b"b14-default-base.FCStd") != 1):
        raise ValueError("Crossover GUI fixture binding changed")
    adapted[name] = data.replace(*replacements[0], 1)
    adapted[CANONICAL_PATH] = decisions["assessment_contract_utf8"].encode()
    return adapted


def _check_current_sources(source_root, original, matrix):
    names = {CANONICAL_PATH, "TrackTemplate.FCMacro"}
    names.update(name for name in original if name.startswith("tracktemplate/"))
    names.update(name for name, _, _ in PROFILE_ADAPTATIONS)
    for kind, count in (("native_entries", 57), ("gui_entries", 22)):
        if len(matrix[kind]) != count:
            raise ValueError("Fixed qualification matrix count changed")
        for entry in matrix[kind]:
            name = entry["path"]
            if _identity(original[name]) != {
                "bytes": entry["bytes"], "sha256": entry["sha256"],
            }:
                raise ValueError("Matrix source identity changed: " + name)
            names.add(name)
    names.update((
        "AdvancedTurnout.FCMacro",
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro",
        "reference/contracts/phase1-crossover-feasibility.json",
    ))
    for name in sorted(names):
        if _read_regular(Path(source_root) / name) != original[name]:
            raise ValueError("Current source differs from frozen base: " + name)


def _new_destination(destination, source_root):
    destination = Path(destination).absolute()
    if (destination.exists() or destination.is_symlink()
            or destination == Path(source_root).resolve()
            or destination == Path.home() or destination == Path("/")):
        raise ValueError("Assessment destination must be a new directory")
    if not destination.parent.is_dir():
        raise ValueError("Assessment parent directory must already exist")
    for component in (destination.parent, *destination.parent.parents):
        if component.is_symlink():
            raise ValueError("Assessment destination contains a symbolic link")
    return destination


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _write_new(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
    path.chmod(mode)


def prepare_assessment(source_root, decision_root, base_fixture, destination):
    """Create one new assessment tree and return its frozen manifest.

    Inputs must match the fixed source commit, decision manifests and
    approved synthetic base. Existing targets and source drift are errors.
    A partial failed tree is retained for diagnosis and is never reused.
    This function starts no FreeCAD process and grants no execution authority.
    """
    source_root = Path(source_root).resolve(strict=True)
    destination = _new_destination(destination, source_root)
    capsule = _public_capsule(decision_root)
    decisions = json.loads(capsule)
    base = _read_regular(base_fixture)
    if len(base) != BASE_BYTES or _sha256(base) != BASE_SHA256:
        raise ValueError("Base fixture is not the approved exact input")
    original, modes = _frozen_source(source_root)
    matrix = decisions["matrix"]
    _check_current_sources(source_root, original, matrix)
    adapted = _adapt_source(original, decisions)
    differences = []
    records = []
    for name, data in sorted(adapted.items()):
        changed = data != original[name]
        records.append({
            "path": name, "original": _identity(original[name]),
            "assessment": _identity(data), "mode": modes[name],
            "adapted": changed,
        })
        if changed:
            differences.extend(difflib.unified_diff(
                original[name].decode().splitlines(keepends=True),
                data.decode().splitlines(keepends=True),
                fromfile="original/" + name,
                tofile="assessment/" + name,
            ))
    diff_bytes = "".join(differences).encode()
    manifest = {
        "schema_version": 1,
        "status": "ASSESSMENT_PREPARED_NOT_EXECUTION_OR_ADMISSION",
        "base_commit": BASE_COMMIT,
        "candidate_profile": CANDIDATE_PROFILE,
        "canonical_default_sha256": CANONICAL_SHA256,
        "decisions": decisions["source_identities"],
        "public_input_capsule": _identity(capsule),
        "source_files": records,
        "adaptation_diff": _identity(diff_bytes),
        "base_fixture": {"path": BASE_PATH, **_identity(base)},
        "native_entry_count": 57,
        "gui_group_count": 22,
        "authority": "Preparation only; runtime admission and ZY stay blocked.",
    }
    destination.mkdir(mode=0o700)
    for name, data in sorted(adapted.items()):
        _write_new(destination / name, data, modes[name])
    _write_new(destination / BASE_PATH, base)
    _write_new(destination / "_assessment/adaptations.diff", diff_bytes)
    _write_new(destination / "_assessment/manifest.json", _json_bytes(manifest))
    verify_assessment(destination, manifest)
    if _sha256(_read_regular(source_root / CANONICAL_PATH)) != CANONICAL_SHA256:
        raise ValueError("Canonical contract changed during preparation")
    if _read_regular(base_fixture) != base:
        raise ValueError("Approved source fixture changed during preparation")
    return manifest


def verify_assessment(destination, expected_manifest):
    """Verify the entire fresh tree against a caller-held frozen manifest.

    Call before execution writes any runtime outputs. Do not obtain the
    expected manifest from the unverified tree itself. Additional files,
    symlinks, byte drift and mode drift are all rejected.
    """
    destination = Path(destination).absolute()
    if destination.is_symlink():
        raise ValueError("Assessment root is a symbolic link")
    expected = {}
    for row in expected_manifest["source_files"]:
        name = row["path"]
        _relative_name(name)
        if name in expected:
            raise ValueError("Duplicate assessment source member")
        expected[name] = (row["assessment"], row["mode"])
    base = expected_manifest["base_fixture"]
    expected[base["path"]] = (
        {key: base[key] for key in ("bytes", "sha256")}, 0o644,
    )
    expected["_assessment/adaptations.diff"] = (
        expected_manifest["adaptation_diff"], 0o644,
    )
    expected["_assessment/manifest.json"] = (
        _identity(_json_bytes(expected_manifest)), 0o644,
    )
    actual = set()
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise ValueError("Assessment contains a symbolic link")
        if path.is_dir():
            continue
        name = path.relative_to(destination).as_posix()
        if name not in expected:
            raise ValueError("Unexpected assessment member: " + name)
        identity, mode = expected[name]
        if (_identity(_read_regular(path)) != identity
                or stat.S_IMODE(path.stat().st_mode) != mode):
            raise ValueError("Assessment member changed: " + name)
        actual.add(name)
    if actual != set(expected):
        raise ValueError("Assessment member missing")
    return {"status": "PASS", "verified_members": len(actual)}


def main(argv=None):
    """Prepare the fixed assessment input set; never dispatch validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--decision-root", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = prepare_assessment(
        args.source_root, args.decision_root, args.base, args.destination,
    )
    print("TRACKTEMPLATE_RUNTIME_ASSESSMENT=" + json.dumps({
        "status": "PASS", "source_files": len(manifest["source_files"]),
        "adapted_files": sum(row["adapted"]
                             for row in manifest["source_files"]),
        "manifest_sha256": _sha256(_json_bytes(manifest)),
        "runtime_admitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
