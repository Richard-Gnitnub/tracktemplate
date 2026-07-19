"""Print structured state from B14's non-modal trackwork manager."""

import json
import sys

try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets

module = sys.modules.get("tracktemplate_b14_session")
manager = getattr(module, "_automation_trackwork_manager", None) if module else None
if manager is None:
    raise RuntimeError("The automated B14 trackwork manager is not open")


def _combo_state(combo):
    return {
        "count": combo.count(),
        "current_index": combo.currentIndex(),
        "current_text": combo.currentText(),
        "items": [combo.itemText(index) for index in range(combo.count())],
    }


def _table_state(table):
    return {
        "rows": table.rowCount(),
        "columns": table.columnCount(),
        "selected_rows": sorted({index.row() for index in table.selectedIndexes()}),
    }


def _buttons(widget):
    return [
        {
            "text": button.text(),
            "enabled": button.isEnabled(),
            "visible": button.isVisible(),
        }
        for button in widget.findChildren(QtWidgets.QPushButton)
        if button.text() and button.isVisible()
    ]


crossover = manager.crossover_panel
payload = {
    "window_title": manager.windowTitle(),
    "visible": manager.isVisible(),
    "active_tab_index": manager.mode_tabs.currentIndex(),
    "tabs": [manager.mode_tabs.tabText(index) for index in range(manager.mode_tabs.count())],
    "document": {
        "name": manager.doc.Name,
        "label": manager.doc.Label,
        "file_name": manager.doc.FileName or "",
        "object_count": len(manager.doc.Objects),
    },
    "turnout": {
        "entities": len(manager.turnouts),
        "hosts": len(manager.hosts),
        "host_combo": _combo_state(manager.host_combo),
        "table": _table_state(manager.table),
        "buttons": _buttons(manager.turnout_scroll_area),
    },
    "crossover": {
        "entities": len(crossover.crossovers),
        "hosts": len(crossover.hosts),
        "host_a_combo": _combo_state(crossover.host_a_combo),
        "host_b_combo": _combo_state(crossover.host_b_combo),
        "table": _table_state(crossover.table),
        "buttons": _buttons(crossover),
    },
}
print(json.dumps(payload, sort_keys=True))
