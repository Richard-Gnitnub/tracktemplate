"""Development bootstrap and fail-closed FreeCAD runtime qualification."""

import importlib
import json
import os
import pathlib
import platform
import sys

from tracktemplate import DEVELOPMENT_CHECKPOINT


__all__ = (
    "RuntimeQualificationError",
    "evaluate_runtime",
    "load_contract",
    "require_qualified_runtime",
    "runtime_record",
)


class RuntimeQualificationError(RuntimeError):
    """Raised before composition when the development host is not qualified."""

    def __init__(self, evaluation):
        self.evaluation = dict(evaluation)
        status = str(self.evaluation.get("status") or "unknown")
        mismatches = self.evaluation.get("mismatches") or []
        detail = "; ".join(str(item) for item in mismatches) or "no detail"
        super().__init__(
            "Track Template {} runtime qualification failed: {} ({})".format(
                DEVELOPMENT_CHECKPOINT,
                status,
                detail,
            )
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
        app = importlib.import_module("FreeCAD")
        part = importlib.import_module("Part")
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
        coin = importlib.import_module("pivy.coin")
        coin_version = str(coin.SoDB.getVersion())
    except ImportError:
        coin_version = "unavailable"

    opencascade_version = str(
        getattr(
            part,
            "OCC_VERSION_STRING",
            getattr(part, "OCC_VERSION", "unknown"),
        )
    )
    version = app.Version()
    return {
        "available": True,
        "version": [str(item) for item in version],
        "version_info": [int(item) for item in version[:3]],
        "opencascade_version": opencascade_version,
        "qt_binding": qt["binding"],
        "qt_version": qt["qt_version"],
        "pyside_version": qt["binding_version"],
        "coin_version": coin_version,
    }


def runtime_record():
    """Return a non-sensitive, JSON-compatible record of the current host."""
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
                "flatpak"
                if os.environ.get("FLATPAK_ID", "")
                else "native-or-unknown"
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


def load_contract(path):
    """Load a runtime-compatibility contract from an explicit path."""
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def require_qualified_runtime(contract_path, record=None):
    """Return qualification evidence or raise before composition can mutate."""
    try:
        contract = load_contract(contract_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeQualificationError(
            {
                "status": "contract-load-failed",
                "matched_profile_id": "",
                "mismatches": [str(error)],
            }
        ) from error

    observed = runtime_record() if record is None else record
    evaluation = evaluate_runtime(observed, contract)
    if evaluation.get("status") != "qualified":
        raise RuntimeQualificationError(evaluation)
    return {
        "schema_version": 1,
        "development_checkpoint": DEVELOPMENT_CHECKPOINT,
        "runtime": observed,
        "compatibility_evaluation": evaluation,
    }
