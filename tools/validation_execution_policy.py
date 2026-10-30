#!/usr/bin/env python3
"""Prevent accidental use of the standard local FreeCAD proof routes.

An exception reference acknowledges an existing owner decision. This tool
does not authenticate that decision or approve its workload and inputs.
The resource guard and direct FreeCAD commands remain separate controls.
"""

import argparse
import json


EXCEPTION_ENV = "TRACKTEMPLATE_LOCAL_VALIDATION_EXCEPTION"
SENTINEL = "TRACKTEMPLATE_LOCAL_VALIDATION_EXCEPTION="


def require_local_exception(workload, reference):
    """Reject local proofs without an explicit owner-decision reference."""
    if (
        not isinstance(reference, str)
        or not reference
        or len(reference) > 512
        or reference.strip() != reference
        or not reference.isprintable()
    ):
        raise ValueError(
            "GitHub-hosted execution is required for this validation route. "
            "Use an approved hosted workload or supply an explicit local "
            "owner-exception reference. No local fallback is permitted. "
            "See reference/VALIDATION.md#validation-execution-location."
        )
    return {
        "workload": workload,
        "owner_exception_reference": reference,
        "owner_authority_authenticated": False,
    }


def report_exception(receipt):
    """Expose the acknowledgement without claiming owner acceptance."""
    print(SENTINEL + json.dumps(receipt, sort_keys=True), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True)
    parser.add_argument(
        "--local-owner-exception",
        help=(
            "Reference to the owner's explicit local execution exception; "
            "this acknowledgement neither authenticates nor grants authority"
        ),
    )
    arguments = parser.parse_args(argv)
    try:
        receipt = require_local_exception(
            arguments.workload, arguments.local_owner_exception,
        )
    except ValueError as error:
        parser.error(str(error))
    report_exception(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
