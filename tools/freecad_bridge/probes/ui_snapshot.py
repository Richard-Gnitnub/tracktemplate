"""Print a bounded read-only JSON inventory of visible FreeCAD Qt controls."""

import json

try:
    from PySide6 import QtWidgets
except ImportError:
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets


def _safe_call(widget, method_name, default=None):
    try:
        method = getattr(widget, method_name)
        return method()
    except Exception:
        return default


def _short_text(value, limit=240):
    text = str(value or "").replace("\x00", "")
    return text if len(text) <= limit else text[:limit] + "…"


records = []
all_top_levels = list(QtWidgets.QApplication.topLevelWidgets())
top_levels = [
    widget for widget in all_top_levels
    if widget.isVisible() and isinstance(widget, QtWidgets.QDialog)
]
if not top_levels:
    top_levels = [
        widget for widget in all_top_levels
        if widget.isVisible() and isinstance(widget, QtWidgets.QMainWindow)
    ]
for top_index, top_level in enumerate(top_levels):
    widgets = [top_level] + list(top_level.findChildren(QtWidgets.QWidget))
    for widget_index, widget in enumerate(widgets[:1500]):
        if not isinstance(widget, (
            QtWidgets.QAbstractButton,
            QtWidgets.QComboBox,
            QtWidgets.QDialog,
            QtWidgets.QDoubleSpinBox,
            QtWidgets.QGroupBox,
            QtWidgets.QLabel,
            QtWidgets.QLineEdit,
            QtWidgets.QSpinBox,
            QtWidgets.QTabWidget,
            QtWidgets.QTableWidget,
        )):
            continue
        record = {
            "top_index": top_index,
            "widget_index": widget_index,
            "class": type(widget).__name__,
            "object_name": _short_text(_safe_call(widget, "objectName", "")),
            "visible": bool(_safe_call(widget, "isVisible", False)),
            "enabled": bool(_safe_call(widget, "isEnabled", False)),
        }
        for method_name, key in (
            ("windowTitle", "window_title"),
            ("title", "title"),
            ("text", "text"),
            ("currentText", "current_text"),
        ):
            value = _safe_call(widget, method_name)
            if value not in (None, ""):
                record[key] = _short_text(value)
        if isinstance(widget, QtWidgets.QTableWidget):
            record["rows"] = widget.rowCount()
            record["columns"] = widget.columnCount()
            record["selected_rows"] = sorted({index.row() for index in widget.selectedIndexes()})
        records.append(record)

payload = {
    "all_top_level_count": len(all_top_levels),
    "inspected_top_level_count": len(top_levels),
    "widget_count": len(records),
    "widgets": records,
}
print(json.dumps(payload, sort_keys=True))
