#!/usr/bin/env python3
"""Build an immutable B14 base fixture in a dedicated empty FreeCAD session."""

import argparse
import datetime
import json
import os
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(TOOL_ROOT / "src"))

from freecad_cli.client import FreeCADClient  # noqa: E402
from tools.freecad_bridge.orchestration import (  # noqa: E402
    execute,
    execute_file,
    parse_json_output,
    sha256,
    submit_and_wait,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=(
            PROJECT_ROOT
            / "benchmark-output"
            / "freecad-bridge"
            / "fixtures"
            / "b14-default-base.FCStd"
        ),
    )
    parser.add_argument("--port", type=int, default=19875)
    parser.add_argument("--timeout", type=float, default=900.0)
    args = parser.parse_args()

    output_path = args.output.resolve()
    manifest_path = output_path.with_suffix(".manifest.json")
    if output_path.exists() or manifest_path.exists():
        raise SystemExit(
            "Refusing to overwrite fixture or manifest: {} / {}".format(
                output_path,
                manifest_path,
            )
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        ".{}.building-{}{}".format(output_path.stem, os.getpid(), output_path.suffix)
    )
    temporary_manifest = manifest_path.with_name(
        ".{}.building-{}.json".format(manifest_path.stem, os.getpid())
    )
    if temporary_path.exists() or temporary_manifest.exists():
        raise SystemExit(
            "Temporary fixture publication path already exists: {} / {}".format(
                temporary_path,
                temporary_manifest,
            )
        )

    token_path = PROJECT_ROOT / "benchmark-output" / "freecad-bridge" / "rpc-token"
    if not token_path.is_file():
        raise SystemExit("Bridge token not found; launch the dedicated FreeCAD session first")
    client = FreeCADClient(
        host="127.0.0.1",
        port=args.port,
        timeout=30.0,
        token=token_path.read_text(encoding="utf-8").strip(),
    )
    if not client.ping():
        raise RuntimeError("FreeCAD bridge did not answer ping")

    published_output = False
    try:
        session_before = parse_json_output(execute_file(
            client,
            PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "session_snapshot.py",
        ))
        if session_before.get("documents"):
            raise RuntimeError("B14 base construction requires an empty FreeCAD session")
        load_job = submit_and_wait(
            client,
            (PROJECT_ROOT / "tools" / "freecad_bridge" / "probes" / "load_b14.py").read_text(
                encoding="utf-8"
            ),
            "load B14",
            300.0,
        )
        execute(
            client,
            "import os; os.environ['TRACKTEMPLATE_B14_BASE_OUTPUT'] = {!r}".format(
                str(temporary_path)
            ),
        )
        build_job = submit_and_wait(
            client,
            (
                PROJECT_ROOT
                / "tools"
                / "freecad_bridge"
                / "probes"
                / "build_b14_default_base.py"
            ).read_text(encoding="utf-8"),
            "build B14 base",
            args.timeout,
        )
        build_result = parse_json_output(build_job)
        if pathlib.Path(build_result["output"]).resolve() != temporary_path:
            raise RuntimeError("FreeCAD reported an unexpected fixture output path")
        if not temporary_path.is_file() or temporary_path.stat().st_size == 0:
            raise RuntimeError("B14 base construction did not create the temporary fixture")

        fixture_sha256 = sha256(temporary_path)
        manifest = {
            "schema_version": 1,
            "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "recipe": "B14 default two-track curve; centreline identities plus chainage",
            "bridge_upstream_commit": "660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7",
            "macro": "AdvancedTurnout.FCMacro",
            "macro_sha256": sha256(PROJECT_ROOT / "AdvancedTurnout.FCMacro"),
            "fixture": str(output_path),
            "fixture_bytes": temporary_path.stat().st_size,
            "fixture_sha256": fixture_sha256,
            "semantic_sha256": build_result["snapshot"]["semantic_sha256"],
            "semantic": build_result["snapshot"]["semantic"],
            "dialog_contract": build_result["dialog"]["input_contract"],
            "freecad_session": session_before,
            "macro_load": parse_json_output(load_job),
        }
        temporary_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(str(temporary_path), str(output_path))
        published_output = True
        os.replace(str(temporary_manifest), str(manifest_path))
        print("B14 base fixture: {}".format(output_path))
        print("Manifest: {}".format(manifest_path))
        print("FCStd SHA-256: {}".format(fixture_sha256))
        print("Semantic SHA-256: {}".format(manifest["semantic_sha256"]))
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        if temporary_manifest.exists():
            temporary_manifest.unlink()
        if published_output and output_path.exists() and not manifest_path.exists():
            output_path.unlink()


if __name__ == "__main__":
    main()
