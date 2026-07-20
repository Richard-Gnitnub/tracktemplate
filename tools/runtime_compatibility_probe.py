#!/usr/bin/env python3
"""Print and optionally qualify non-sensitive Python/FreeCAD runtime data."""

import argparse
import importlib
import json
import os
import pathlib
import platform
import sys


SENTINEL = "TRACKTEMPLATE_RUNTIME_PROBE="
DEFAULT_CONTRACT_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "reference"
    / "contracts"
    / "phase1-compatibility.json"
)


def _qt_data():
    for module_name in ("PySide6", "PySide"):
        try:
            binding = importlib.import_module(module_name)
            qt_core = importlib.import_module(module_name + ".QtCore")
        except ImportError:
            continue
        return {
            "binding": module_name,
            "qt_version": str(qt_core.qVersion()),
            "binding_version": str(
                getattr(
                    binding,
                    "__version__",
                    getattr(qt_core, "__version__", "unknown"),
                )
            ),
        }
    return {
        "binding": "unavailable",
        "qt_version": "unavailable",
        "binding_version": "unavailable",
    }


def _optional_freecad_data():
    try:
        import FreeCAD as App
        import Part
    except ImportError:
        return {
            "available": False,
            "version": [],
            "version_info": [],
            "opencascade_version": "unavailable",
            "qt_binding": "unavailable",
            "qt_version": "unavailable",
            "pyside_version": "unavailable",
            "coin_version": "unavailable",
        }

    qt = _qt_data()

    try:
        from pivy import coin

        coin_version = str(coin.SoDB.getVersion())
    except ImportError:
        coin_version = "unavailable"

    opencascade_version = str(
        getattr(
            Part,
            "OCC_VERSION_STRING",
            getattr(Part, "OCC_VERSION", "unknown"),
        )
    )
    return {
        "available": True,
        "version": [str(item) for item in App.Version()],
        "version_info": [int(item) for item in App.Version()[:3]],
        "opencascade_version": opencascade_version,
        "qt_binding": qt["binding"],
        "qt_version": qt["qt_version"],
        "pyside_version": qt["binding_version"],
        "coin_version": coin_version,
    }


def runtime_record():
    return {
        "schema_version": 1,
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "version_info": list(sys.version_info[:3]),
        },
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "packaging": (
                "flatpak" if os.environ.get("FLATPAK_ID", "") else "native-or-unknown"
            ),
            "flatpak_id": str(os.environ.get("FLATPAK_ID", "")),
        },
        "freecad": _optional_freecad_data(),
    }


def _path_value(record, dotted_path):
    value = record
    for component in dotted_path.split("."):
        if not isinstance(value, dict) or component not in value:
            return None
        value = value[component]
    return value


def evaluate_runtime(record, contract):
    """Return a fail-closed qualification result for one runtime record."""
    if not isinstance(record, dict) or not isinstance(contract, dict):
        return {
            "status": "invalid-input",
            "matched_profile_id": "",
            "mismatches": ["runtime record and contract must both be objects"],
        }
    if not bool((record.get("freecad") or {}).get("available")):
        return {
            "status": "not-freecad-runtime",
            "matched_profile_id": "",
            "mismatches": ["FreeCAD modules are unavailable"],
        }
    profiles = (
        (contract.get("runtime_baseline") or {}).get("qualified_profiles") or []
    )
    if not isinstance(profiles, list) or not profiles:
        return {
            "status": "contract-has-no-qualified-profile",
            "matched_profile_id": "",
            "mismatches": ["no qualified runtime profile is declared"],
        }
    closest_profile = ""
    closest_mismatches = None
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        expected = profile.get("exact_match") or {}
        mismatches = []
        for dotted_path in sorted(expected):
            observed = _path_value(record, dotted_path)
            if observed != expected[dotted_path]:
                mismatches.append(
                    "{} expected {!r}, observed {!r}".format(
                        dotted_path,
                        expected[dotted_path],
                        observed,
                    )
                )
        if not mismatches:
            return {
                "status": "qualified",
                "matched_profile_id": str(profile.get("profile_id") or ""),
                "mismatches": [],
            }
        if closest_mismatches is None or len(mismatches) < len(closest_mismatches):
            closest_profile = str(profile.get("profile_id") or "")
            closest_mismatches = mismatches
    return {
        "status": "unqualified",
        "matched_profile_id": closest_profile,
        "mismatches": closest_mismatches or ["no usable qualified profile"],
    }


def _load_contract(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=pathlib.Path,
        default=DEFAULT_CONTRACT_PATH,
        help="Phase 1 compatibility contract to evaluate when present.",
    )
    parser.add_argument(
        "--require-qualified",
        action="store_true",
        help="Return a non-zero status unless the FreeCAD runtime is qualified.",
    )
    arguments, _unknown = parser.parse_known_args(argv)
    payload = runtime_record()
    if arguments.contract.is_file():
        try:
            payload["compatibility_evaluation"] = evaluate_runtime(
                payload,
                _load_contract(arguments.contract),
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            payload["compatibility_evaluation"] = {
                "status": "contract-load-failed",
                "matched_profile_id": "",
                "mismatches": [str(error)],
            }
    else:
        payload["compatibility_evaluation"] = {
            "status": "contract-unavailable",
            "matched_profile_id": "",
            "mismatches": ["compatibility contract was not found"],
        }
    print(
        SENTINEL + json.dumps(payload, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    if arguments.require_qualified:
        return int(
            payload["compatibility_evaluation"].get("status") != "qualified"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
elif __name__ == "runtime_compatibility_probe":
    _freecad_status = main()
    if _freecad_status:
        raise RuntimeError("FreeCAD runtime did not match a qualified profile")
