"""Qualify a small test setup in FreeCAD without constructing geometry.

This fixture checks retained runner failure classes. It does not qualify
the XO-001 candidate, its inputs, or any complete product validation.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SENTINEL = "TRACKTEMPLATE_HARNESS_READINESS="
COMPARATOR = ROOT / "tests/freecad_validate_phase9b_catalogue_central_check.py"


def load_comparator():
    """Import the accepted comparison helper under an inert module name."""
    spec = importlib.util.spec_from_file_location(
        "_readiness_central_comparator", COMPARATOR,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._near_frame


def check_frames(compare):
    """Exercise actual frame assertions with synthetic input contracts."""
    actual = {
        "origin_mm": (1.25, -2.5, 3.75),
        "x_axis": (0.6, 0.8),
        "y_axis": (-0.8, 0.6),
    }
    expected = SimpleNamespace(**actual)
    compare(actual, expected)
    rejected = []
    for field in actual:
        incomplete = dict(actual)
        del incomplete[field]
        try:
            compare(incomplete, expected)
        except KeyError as error:
            assert error.args == (field,)
            rejected.append("missing-" + field)
        else:
            raise AssertionError("Comparator accepted missing " + field)
        different = dict(actual)
        different[field] = tuple(value + 1 for value in actual[field])
        try:
            compare(different, expected)
        except AssertionError:
            rejected.append("different-" + field)
        else:
            raise AssertionError("Comparator accepted different " + field)
    try:
        compare(actual, SimpleNamespace(x_axis=actual["x_axis"],
                                        y_axis=actual["y_axis"]))
    except AttributeError:
        rejected.append("missing-expected-origin_mm")
    else:
        raise AssertionError("Comparator accepted incomplete expected frame")
    return {"valid_frames": 1, "rejected_inputs": rejected}


def check_assets(directory):
    """Check synthetic local assets through the existing safety audit."""
    from tools import repository_safety_audit as safety

    isolated = directory / "isolated"
    isolated.mkdir()
    asset = isolated / "reference.bin"
    asset.write_bytes(b"TrackTemplate synthetic readiness input\n")
    expected = hashlib.sha256(asset.read_bytes()).hexdigest()
    specification = {
        "path": Path("reference.bin"), "kind": "test-fixture",
        "required": True, "expected_sha256": expected,
    }
    assert safety._asset_record(isolated, specification)["hash_matches"]
    wrong = dict(specification, expected_sha256="0" * 64)
    assert safety._asset_record(isolated, wrong)["hash_matches"] is False
    missing = dict(specification, path=Path("missing.bin"))
    assert safety._asset_record(isolated, missing)["present"] is False
    outside = directory / "outside.bin"
    outside.write_bytes(asset.read_bytes())
    escaped = isolated / "escaped.bin"
    escaped.symlink_to(outside)
    try:
        safety._asset_record(isolated, dict(specification, path=escaped))
    except safety.SafetyAuditError as error:
        assert str(error) == "local asset escaped the repository root"
    else:
        raise AssertionError("Escaped asset passed isolation")
    return {"valid_assets": 1,
            "rejected_inputs": ["wrong-hash", "missing", "escaped-path"]}


def main(argv=None):
    """Emit readiness evidence only after every bounded check passes."""
    del argv
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import FreeCAD as App
    from tracktemplate.bootstrap import (
        evaluate_runtime, load_contract, runtime_record,
    )

    assert not App.GuiUp, "This readiness fixture is native-only"
    before = tuple(App.listDocuments())
    assert not before, "Readiness requires a fresh private process"
    runtime = runtime_record()
    qualification = evaluate_runtime(
        runtime,
        load_contract(ROOT / "reference/contracts/phase1-compatibility.json"),
    )
    assert qualification["status"] == "qualified", qualification
    compare = load_comparator()
    frames = check_frames(compare)
    temporary_root = ROOT / "tmp"
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="harness-readiness-", dir=temporary_root,
    ) as temporary:
        assets = check_assets(Path(temporary))
    assert tuple(App.listDocuments()) == before
    result = {
        "status": "PASS", "scope": "synthetic-harness-readiness-only",
        "entry_name": __name__, "runtime": qualification,
        "comparator_module": compare.__module__,
        "comparator_sha256": hashlib.sha256(
            COMPARATOR.read_bytes(),
        ).hexdigest(),
        "frames": frames, "assets": assets,
        "documents_before": list(before), "documents_after": list(before),
        "geometry_constructed": False, "xo001_qualified": False,
    }
    print(SENTINEL + json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ in ("__main__", Path(__file__).stem):
    main()
