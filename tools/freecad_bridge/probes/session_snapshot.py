"""Print a read-only JSON snapshot of the connected FreeCAD session."""

import collections
import json
import os

import FreeCAD as App

try:
    import FreeCADGui as Gui
except ImportError:
    Gui = None


def _property_value(obj, name, default=""):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _rss_mb():
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return None


documents = []
for name, document in App.listDocuments().items():
    type_counts = collections.Counter()
    role_counts = collections.Counter()
    for obj in list(document.Objects):
        type_counts[str(_property_value(obj, "TypeId", "Unknown"))] += 1
        role = str(_property_value(obj, "GeneratedRole", "") or "")
        if role:
            role_counts[role] += 1
    documents.append({
        "name": name,
        "label": str(document.Label),
        "file_name": str(document.FileName or ""),
        "object_count": len(document.Objects),
        "type_counts": dict(sorted(type_counts.items())),
        "generated_role_counts": dict(sorted(role_counts.items())),
    })

active_document = App.ActiveDocument
gui_document = Gui.ActiveDocument if Gui is not None else None
payload = {
    "freecad_version": ".".join(App.Version()[:3]),
    "process_id": os.getpid(),
    "resident_memory_mb": _rss_mb(),
    "paths": {
        name: str(App.ConfigGet(name) or "")
        for name in (
            "UserHomePath",
            "UserAppData",
            "AppTempPath",
            "UserParameter",
            "SystemParameter",
        )
    },
    "active_document": active_document.Name if active_document else None,
    "gui_active_document": gui_document.Document.Name if gui_document else None,
    "documents": documents,
}
print(json.dumps(payload, sort_keys=True))
