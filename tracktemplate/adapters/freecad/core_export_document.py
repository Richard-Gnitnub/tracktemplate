"""Keep Core serializer objects outside every editable FreeCAD document.

Each call owns one hidden document. It must close that document and restore
the document registry, active document and GUI selection before returning a
prepared payload. No filesystem publication or restart recovery is supplied.
"""

import uuid


def _same_registry(observed, expected):
    return set(observed) == set(expected) and all(
        observed[name] is document for name, document in expected.items()
    )


def _active_document(app):
    active = app.activeDocument()
    if app.ActiveDocument is not active:
        raise RuntimeError("The Core export active-document state disagrees.")
    return active


def _reserve_source_labels(document, labels):
    """Preserve FreeCAD's label allocation without copying source geometry."""
    for label in dict.fromkeys(labels):
        name = "CoreExportLabel_" + uuid.uuid4().hex
        if name in labels or document.getObject(name) is not None:
            raise RuntimeError("The Core export label reservation conflicts.")
        holder = document.addObject("App::FeaturePython", name)
        if document.getObject(name) is not holder:
            raise RuntimeError("The Core export label holder is unregistered.")
        holder.Label = label
        if holder.Label != label:
            raise RuntimeError("The Core export source label was not retained.")


def _selection_snapshot(app, gui):
    if gui is None:
        return ()
    documents = app.listDocuments()
    result = []
    for selected in gui.Selection.getSelectionEx("*", 0):
        name = selected.DocumentName
        document = documents.get(name)
        obj = selected.Object
        if (
            document is None
            or document.getObject(selected.ObjectName) is not obj
            or len(selected.SubElementNames) != len(selected.PickedPoints)
        ):
            raise RuntimeError("Core export selection ownership is unclear.")
        result.append((
            name, selected.ObjectName, document, obj,
            tuple(selected.SubElementNames),
            tuple((point.x, point.y, point.z)
                  for point in selected.PickedPoints),
            gui.Selection.isSelected(obj, "", 0),
        ))
    return tuple(result)


def _preselection_snapshot(app, gui):
    if gui is None:
        return None
    selected = gui.Selection.getPreselection()
    if not selected.DocumentName and not selected.ObjectName:
        return None
    document = app.listDocuments().get(selected.DocumentName)
    obj = selected.Object
    if (
        document is None
        or document.getObject(selected.ObjectName) is not obj
        or len(selected.SubElementNames) != 1
        or len(selected.PickedPoints) != 1
    ):
        raise RuntimeError("Core export preselection ownership is unclear.")
    point = selected.PickedPoints[0]
    return (
        selected.DocumentName, selected.ObjectName, document, obj,
        selected.SubElementNames[0], (point.x, point.y, point.z),
    )


def _restore_preselection(app, gui, selection):
    if gui is None or _preselection_snapshot(app, gui) == selection:
        return
    if selection is None:
        gui.Selection.clearPreselection()
    else:
        name, object_name, document, obj, subname, point = selection
        if (
            app.listDocuments().get(name) is not document
            or document.getObject(object_name) is not obj
        ):
            raise RuntimeError("Core export preselection identity changed.")
        gui.Selection.setPreselection(obj, subname, *point)
    if _preselection_snapshot(app, gui) != selection:
        raise RuntimeError("Core export did not restore exact preselection.")


def _restore_selection(app, gui, selection):
    if gui is None or _selection_snapshot(app, gui) == selection:
        return
    documents = app.listDocuments()
    for name, object_name, document, obj, subnames, points, _whole in selection:
        if (
            documents.get(name) is not document
            or document.getObject(object_name) is not obj
        ):
            raise RuntimeError("Core export cannot restore replaced selection.")
        if len(points) != len(subnames):
            raise RuntimeError("Core export selection point count is unclear.")
    gui.Selection.clearSelection()
    for name, object_name, _document, _obj, subnames, points, whole in selection:
        if whole:
            gui.Selection.addSelection(
                name, object_name, "", 0.0, 0.0, 0.0, False,
            )
        for subname, point in zip(subnames, points):
            gui.Selection.addSelection(
                name, object_name, subname, *point, False,
            )
    if _selection_snapshot(app, gui) != selection:
        raise RuntimeError("Core export did not restore the exact selection.")


def _cleanup(app, gui, owned, previous, active, selection, preselection):
    errors = []
    interruption = None

    def attempt(operation, context=""):
        nonlocal interruption
        try:
            operation()
        except BaseException as error:
            detail = str(error) or type(error).__name__
            errors.append(context + detail)
            if not isinstance(error, Exception) and interruption is None:
                interruption = error

    def close_owned():
        if owned is None:
            return
        name, document = owned
        if app.listDocuments().get(name) is not document:
            raise RuntimeError("Core export temporary ownership changed.")
        app.closeDocument(name)
        if app.listDocuments().get(name) is document:
            raise RuntimeError("Core export temporary document remained open.")

    def restore_active():
        if active is not None and (
            app.listDocuments().get(active.Name) is not active
        ):
            raise RuntimeError("Core export previous active document changed.")
        if app.ActiveDocument is not active or app.activeDocument() is not active:
            app.setActiveDocument(active.Name if active is not None else "")
        if _active_document(app) is not active:
            raise RuntimeError("Core export did not restore the active document.")

    attempt(
        close_owned,
        "Temporary document '{}': ".format(owned[0]) if owned else "",
    )
    attempt(restore_active)
    attempt(lambda: _restore_selection(app, gui, selection))
    attempt(lambda: _restore_preselection(app, gui, preselection))
    try:
        observed = dict(app.listDocuments())
        if not _same_registry(observed, previous):
            names = sorted(
                name for name in set(observed) | set(previous)
                if observed.get(name) is not previous.get(name)
            )
            errors.append(
                "Core export document registry was not restored: "
                + ", ".join(names)
            )
    except BaseException as error:
        errors.append("Core export document registry check failed: " + str(error))
        if not isinstance(error, Exception) and interruption is None:
            interruption = error
    return errors, interruption


class CoreExportDocument:
    """Wrap one serializer without acquiring FreeCAD state in construction."""

    def __init__(self, serializer, *, app=None, gui=None):
        if not callable(serializer):
            raise TypeError("The Core export serializer must be callable.")
        self._serializer = serializer
        self._app = app
        self._gui = gui

    def __call__(self, editable_doc, task, staged_path):
        """Serialize one unchanged task in a proven invocation-owned document."""
        app = self._app
        if app is None:
            import FreeCAD as app
        gui = self._gui
        if gui is None and app.GuiUp:
            import FreeCADGui as gui
        previous = dict(app.listDocuments())
        if previous.get(editable_doc.Name) is not editable_doc:
            raise RuntimeError("The Core export editable document changed.")
        source_labels = tuple(obj.Label for obj in editable_doc.Objects)
        active = _active_document(app)
        if active is not None and previous.get(active.Name) is not active:
            raise RuntimeError("The Core export active document is unregistered.")
        selection = _selection_snapshot(app, gui)
        preselection = _preselection_snapshot(app, gui)
        name = "TrackTemplateCoreExport_" + uuid.uuid4().hex
        if name in previous:
            raise RuntimeError("The Core export temporary name is already used.")
        owned = None
        original_error = None
        try:
            if not _same_registry(dict(app.listDocuments()), previous):
                raise RuntimeError("The Core export document registry changed.")
            document = app.newDocument(
                name, "TrackTemplate temporary Core export", True, True,
            )
            observed = dict(app.listDocuments())
            if (
                document is not None
                and observed.get(name) is document
                and all(document is not item for item in previous.values())
            ):
                owned = (name, document)
            expected = dict(previous, **{name: document})
            if (
                owned is None
                or document.Name != name
                or document.FileName
                or document.Temporary is not True
                or not _same_registry(observed, expected)
            ):
                raise RuntimeError("Core export temporary ownership is unclear.")
            _reserve_source_labels(document, source_labels)
            self._serializer(document, task, staged_path)
        except BaseException as error:
            original_error = error
            raise
        finally:
            errors, interruption = _cleanup(
                app, gui, owned, previous, active, selection,
                preselection,
            )
            if errors:
                diagnostic = "Core export document cleanup failed: " + "; ".join(
                    errors,
                )
                if original_error is not None:
                    original_error.add_note(diagnostic)
                elif interruption is not None:
                    interruption.add_note(diagnostic)
                    raise interruption
                else:
                    raise RuntimeError(diagnostic)
