#!/usr/bin/env python3
"""Print and optionally qualify non-sensitive Python/FreeCAD runtime data."""

import argparse
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tracktemplate.bootstrap import (  # noqa: E402
    evaluate_runtime,
    load_contract,
    runtime_record,
)


SENTINEL = "TRACKTEMPLATE_RUNTIME_PROBE="
DEFAULT_CONTRACT_PATH = (
    ROOT
    / "reference"
    / "contracts"
    / "phase1-compatibility.json"
)

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
                load_contract(arguments.contract),
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
