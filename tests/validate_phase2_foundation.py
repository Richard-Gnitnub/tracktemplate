#!/usr/bin/env python3
"""Validate the bounded Phase 2 package, loading and comparison foundation."""

import ast
import copy
import hashlib
import importlib.abc
import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tools import runtime_compatibility_probe  # noqa: E402
from tools import semantic_compare  # noqa: E402
from tracktemplate import DEVELOPMENT_CHECKPOINT  # noqa: E402
from tracktemplate import bootstrap  # noqa: E402


SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
PILOT_FUNCTIONS = {
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
}
EXPECTED_MODULES = {
    "tracktemplate": ("package", ["DEVELOPMENT_CHECKPOINT"]),
    "tracktemplate.api": ("api", ["DEVELOPMENT_CHECKPOINT"]),
    "tracktemplate.bootstrap": (
        "bootstrap",
        [
            "RuntimeQualificationError",
            "evaluate_runtime",
            "load_contract",
            "require_qualified_runtime",
            "runtime_record",
        ],
    ),
    "tracktemplate.domain": ("domain", []),
    "tracktemplate.domain.alignment": ("domain", []),
}
CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-compatibility.json"
TRANSITION_PATH = ROOT / "reference" / "contracts" / "phase1-transition-pilot.json"
FOUNDATION_PATH = ROOT / "reference" / "PHASE2_FOUNDATION.md"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _top_level_functions(tree):
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _qualified_record(contract):
    profile = contract["runtime_baseline"]["qualified_profiles"][0]
    record = {"freecad": {"available": True}}
    for dotted_path, value in profile["exact_match"].items():
        target = record
        components = dotted_path.split(".")
        for component in components[:-1]:
            target = target.setdefault(component, {})
        target[components[-1]] = copy.deepcopy(value)
    return record


def _validate_clean_import(errors):
    script = textwrap.dedent(
        """
        import importlib.abc
        import json
        import pathlib
        import sys

        forbidden = {{"FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6", "pivy"}}
        attempted = []

        class Blocked(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                root = fullname.split(".", 1)[0]
                if root in forbidden:
                    attempted.append(fullname)
                    raise AssertionError("forbidden import attempted: " + fullname)
                return None

        sys.meta_path.insert(0, Blocked())
        sys.path.insert(0, {root!r})
        import tracktemplate
        import tracktemplate.api
        import tracktemplate.domain
        import tracktemplate.domain.alignment
        print(json.dumps({{
            "attempted": attempted,
            "checkpoint": tracktemplate.DEVELOPMENT_CHECKPOINT,
            "api": list(tracktemplate.api.__all__),
            "domain": list(tracktemplate.domain.__all__),
            "alignment": list(tracktemplate.domain.alignment.__all__),
            "python": list(sys.version_info[:3]),
        }}, sort_keys=True))
        """
    ).format(root=str(ROOT))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        errors.append("isolated package import failed: {}".format(result.stderr))
        return
    payload = json.loads(result.stdout)
    if payload != {
        "alignment": [],
        "api": ["DEVELOPMENT_CHECKPOINT"],
        "attempted": [],
        "checkpoint": "10.2A8A7B16",
        "domain": [],
        "python": list(sys.version_info[:3]),
    }:
        errors.append("isolated package import result drifted")


def _validate_structure(errors):
    report = modular_structure.structure_report(ROOT)
    errors.extend(modular_structure.validate_report(report))
    modules = {item["module"]: item for item in report["modules"]}
    if set(modules) != set(EXPECTED_MODULES):
        errors.append("Phase 2 package module set is not minimal")
    for module, (layer, exports) in EXPECTED_MODULES.items():
        record = modules.get(module, {})
        if record.get("layer") != layer or record.get("public_exports") != exports:
            errors.append("{} layer/public boundary drifted".format(module))
    if report.get("import_edges") != [
        {"from": "tracktemplate.api", "to": "tracktemplate"},
        {"from": "tracktemplate.bootstrap", "to": "tracktemplate"},
    ]:
        errors.append("Phase 2 internal import edge set drifted")
    if (report.get("launcher") or {}).get("definitions") != [
        "_launcher_root",
        "_load_foundation",
        "run_macro",
    ] or (report.get("launcher") or {}).get("launch_calls") != 1:
        errors.append("B16 composition-root structure drifted")

    mutated = copy.deepcopy(report)
    mutated["cycles"].append(["tracktemplate.api", "tracktemplate.api"])
    if not modular_structure.validate_report(mutated):
        errors.append("cycle mutation did not fail closed")
    mutated = copy.deepcopy(report)
    mutated["domain_forbidden_imports"].append(
        {"module": "tracktemplate.domain.alignment", "import_root": "FreeCAD"}
    )
    if not modular_structure.validate_report(mutated):
        errors.append("forbidden-domain-import mutation did not fail closed")

    with tempfile.TemporaryDirectory(prefix="tracktemplate-structure-") as temp:
        fixture_root = pathlib.Path(temp)
        fixture_package = fixture_root / "tracktemplate"
        fixture_domain = fixture_package / "domain"
        fixture_domain.mkdir(parents=True)
        (fixture_package / "__init__.py").write_text(
            "from .api import VALUE\nVALUE = 1\n__all__ = ('VALUE',)\n",
            encoding="utf-8",
        )
        (fixture_package / "api.py").write_text(
            "from tracktemplate import VALUE\n__all__ = ('VALUE',)\n",
            encoding="utf-8",
        )
        (fixture_domain / "__init__.py").write_text(
            "__all__ = ()\n",
            encoding="utf-8",
        )
        (fixture_domain / "alignment.py").write_text(
            "import FreeCAD\n__all__ = ()\n",
            encoding="utf-8",
        )
        (fixture_root / "TrackTemplate.FCMacro").write_text(
            "def run_macro():\n    return None\nFOUNDATION_RESULT = run_macro()\n",
            encoding="utf-8",
        )
        fixture_report = modular_structure.structure_report(fixture_root)
        fixture_failures = modular_structure.validate_report(fixture_report)
        if not fixture_report["cycles"] or not fixture_report[
            "prohibited_layer_edges"
        ] or not fixture_report["domain_forbidden_imports"]:
            errors.append("structure analyser missed a synthetic boundary violation")
        if len(fixture_failures) < 3:
            errors.append("synthetic structure violations did not fail closed")


def _validate_runtime_guard(errors):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    record = _qualified_record(contract)
    result = bootstrap.require_qualified_runtime(CONTRACT_PATH, record=record)
    if (
        result.get("development_checkpoint") != "10.2A8A7B16"
        or (result.get("compatibility_evaluation") or {}).get("status")
        != "qualified"
    ):
        errors.append("qualified runtime guard result drifted")
    try:
        json.dumps(result, sort_keys=True)
    except (TypeError, ValueError):
        errors.append("runtime guard result is not JSON compatible")

    unqualified = copy.deepcopy(record)
    unqualified["freecad"]["version_info"] = [1, 1, 0]
    try:
        bootstrap.require_qualified_runtime(CONTRACT_PATH, record=unqualified)
    except bootstrap.RuntimeQualificationError as error:
        if error.evaluation.get("status") != "unqualified":
            errors.append("unqualified runtime diagnostic status drifted")
    else:
        errors.append("unqualified runtime did not fail closed")

    try:
        bootstrap.require_qualified_runtime(ROOT / "missing-contract.json", record=record)
    except bootstrap.RuntimeQualificationError as error:
        if error.evaluation.get("status") != "contract-load-failed":
            errors.append("missing-contract diagnostic status drifted")
    else:
        errors.append("missing runtime contract did not fail closed")

    if runtime_compatibility_probe.evaluate_runtime is not bootstrap.evaluate_runtime:
        errors.append("runtime qualification has more than one implementation")
    if runtime_compatibility_probe.runtime_record is not bootstrap.runtime_record:
        errors.append("runtime-record collection has more than one implementation")
    if runtime_compatibility_probe.load_contract is not bootstrap.load_contract:
        errors.append("runtime-contract loading has more than one implementation")

    blocked_process = subprocess.run(
        [sys.executable, str(ROOT / "TrackTemplate.FCMacro")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    sentinel = "TRACKTEMPLATE_B16_FOUNDATION="
    records = [
        line[len(sentinel):]
        for line in blocked_process.stdout.splitlines()
        if line.startswith(sentinel)
    ]
    if blocked_process.returncode == 0 or len(records) != 1:
        errors.append("standalone B16 launcher did not fail closed exactly once")
    else:
        blocked = json.loads(records[0])
        if (
            blocked.get("status") != "blocked-before-composition"
            or blocked.get("document_mutation") is not False
            or (blocked.get("compatibility_evaluation") or {}).get("status")
            != "not-freecad-runtime"
        ):
            errors.append("standalone B16 blocked diagnostic drifted")


def _validate_comparison_harness(errors):
    legacy = {
        "values": (1.25, 2.5, 0.125),
        "ordered_ids": ["track:A", "track:B"],
        "diagnostics": [{"code": "OK", "severity": "information"}],
        "output_metadata": {"schema_version": 2, "category": "rail"},
    }
    equal = semantic_compare.compare_structures(legacy, copy.deepcopy(legacy))
    if not equal["equal"] or equal["difference_count"] != 0 or (
        equal["legacy_digest"] != equal["successor_digest"]
    ):
        errors.append("equal structured comparison drifted")

    changed = copy.deepcopy(legacy)
    changed["ordered_ids"].reverse()
    changed["diagnostics"][0]["code"] = "WARN"
    changed["output_metadata"]["category"] = "timber"
    changed["values"] = (1.25, 2.75, 0.125)
    report = semantic_compare.compare_structures(legacy, changed)
    paths = {item["path"] for item in report["differences"]}
    required_paths = {
        '$["values"][1]',
        '$["ordered_ids"][0]',
        '$["ordered_ids"][1]',
        '$["diagnostics"][0]["code"]',
        '$["output_metadata"]["category"]',
    }
    if report["equal"] or not required_paths <= paths:
        errors.append("comparison harness lost a required evidence dimension")
    typed = semantic_compare.compare_structures({"value": 1}, {"value": True})
    if [item.get("kind") for item in typed["differences"]] != ["type"]:
        errors.append("comparison harness no longer preserves exact value types")
    signed_zero = semantic_compare.compare_structures(-0.0, 0.0)
    if signed_zero["equal"] or signed_zero["legacy_digest"] == signed_zero[
        "successor_digest"
    ]:
        errors.append("comparison harness lost exact floating-point representation")
    same_nan = semantic_compare.compare_structures(float("nan"), float("nan"))
    if not same_nan["equal"] or same_nan["legacy_digest"] != same_nan[
        "successor_digest"
    ]:
        errors.append("comparison harness reports inconsistent canonical NaN values")
    try:
        semantic_compare.compare_structures({"unsupported": {1, 2}}, {})
    except TypeError:
        pass
    else:
        errors.append("comparison harness accepted unsupported opaque state")


def validate():
    errors = []
    if DEVELOPMENT_CHECKPOINT != "10.2A8A7B16":
        errors.append("B16 development checkpoint drifted")
    for relative, digest in SOURCE_HASHES.items():
        if _sha256(ROOT / relative) != digest:
            errors.append("{} immutable source fingerprint drifted".format(relative))

    alignment_tree = _tree(ROOT / "tracktemplate" / "domain" / "alignment.py")
    api_tree = _tree(ROOT / "tracktemplate" / "api.py")
    launcher_tree = _tree(ROOT / "TrackTemplate.FCMacro")
    for label, tree in (
        ("alignment", alignment_tree),
        ("api", api_tree),
        ("launcher", launcher_tree),
    ):
        moved = _top_level_functions(tree) & PILOT_FUNCTIONS
        if moved:
            errors.append("{} prematurely implements {}".format(label, sorted(moved)))
    if any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == "GEOMETRY_TOLERANCE"
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
        )
        for node in alignment_tree.body
    ):
        errors.append("Phase 3 geometry constant moved during Phase 2")

    transition = json.loads(TRANSITION_PATH.read_text(encoding="utf-8"))
    if transition.get("status") != (
        "selected-contract-frozen-phase2-foundation-implemented-"
        "calculation-movement-not-started"
    ) or (transition.get("successor") or {}).get(
        "compatibility_launcher_status"
    ) != "phase2-foundation-created-not-routed":
        errors.append("transition contract does not record the Phase 2 foundation")

    foundation_text = " ".join(
        FOUNDATION_PATH.read_text(encoding="utf-8").split()
    )
    for marker in (
        "No transition calculation has moved",
        "one authoritative runtime implementation",
        "tests/validate_phase2_foundation.py",
        "tests/freecad_validate_phase2_foundation.py",
        "P1-X10",
        "Phase 3",
        "28/28 passed",
        "foundation-loaded-not-routed",
        "No real-GUI workflow run is claimed",
    ):
        if marker not in foundation_text:
            errors.append("Phase 2 foundation evidence marker is missing: {}".format(marker))

    _validate_clean_import(errors)
    _validate_structure(errors)
    _validate_runtime_guard(errors)
    _validate_comparison_harness(errors)
    if errors:
        raise AssertionError("\n".join(errors))
    print("Phase 2 modular foundation validation passed")


if __name__ == "__main__":
    validate()
