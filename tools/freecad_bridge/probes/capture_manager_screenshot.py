"""Save the isolated B14 or B15 manager into the ignored bridge output area."""

import json
import os
import pathlib
import sys

module = next(
    (
        sys.modules.get(name)
        for name in ("tracktemplate_b15_session", "tracktemplate_b14_session")
        if sys.modules.get(name) is not None
    ),
    None,
)
manager = getattr(module, "_automation_trackwork_manager", None) if module else None
if manager is None:
    raise RuntimeError("The automated trackwork manager is not open")

output_dir = pathlib.Path(os.environ["TRACKTEMPLATE_REPO"]) / "benchmark-output" / "freecad-bridge" / "screenshots"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "trackwork-manager.png"
if not manager.grab().save(str(output_path), "PNG"):
    raise RuntimeError("Qt could not save the manager screenshot")

print(json.dumps({
    "path": str(output_path),
    "width": manager.width(),
    "height": manager.height(),
}, sort_keys=True))
