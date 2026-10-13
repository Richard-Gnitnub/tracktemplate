"""Bind the selected dialog to one confirmed complete output directory."""

import hashlib

from tracktemplate.application.selected_export_set import (
    prepare_selected_export_plan,
)


def _snapshot(value):
    """Capture nested plan values, including mutable hydrated BRep content."""
    if isinstance(value, dict):
        return {key: _snapshot(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return tuple(_snapshot(item) for item in value)
    if isinstance(value, set):
        return frozenset(_snapshot(item) for item in value)
    serializer = getattr(value, "exportBrepToString", None)
    if callable(serializer):
        return hashlib.sha256(serializer().encode("utf-8")).hexdigest()
    return value


class SelectedExportConfiguration(dict):
    """Mark a live selected-dialog request without changing stored fields."""

    def __init__(self, values, context):
        super().__init__(values)
        self.context = context


class SelectedExportPolicy:
    """Keep one child through preview, confirmation, preflight and execution."""

    NAMESPACE_NAMES = (
        "plan_selected_production_export", "selected_export_preflight_config",
        "confirm_selected_export_operation",
    )
    DIALOG_NAMES = ("_current_config", "refresh_preview", "export_selected")

    def __init__(self, namespace):
        self.namespace = namespace
        self.dialog = namespace["SelectedProductionExportDialog"]
        self.original_plan = namespace[self.NAMESPACE_NAMES[0]]
        self.original_preflight_config = namespace[self.NAMESPACE_NAMES[1]]
        self.original_confirmation = namespace[self.NAMESPACE_NAMES[2]]
        self.original_values = self.dialog._current_config
        self.original_preview = self.dialog.refresh_preview
        self.original_export = self.dialog.export_selected
        originals = (
            self.original_plan, self.original_preflight_config,
            self.original_confirmation, self.original_values,
            self.original_preview, self.original_export,
        )
        if any(getattr(value, "__globals__", None) is not namespace
               for value in originals):
            raise RuntimeError("The inherited selected policy is incomplete.")

        def values(dialog):
            context = getattr(dialog, "_tracktemplate_selected_set", None)
            if context is None:
                context = {}
                dialog._tracktemplate_selected_set = context
            result = SelectedExportConfiguration(
                self.original_values(dialog), context,
            )
            result["overwrite_existing"] = False
            return result

        def preview(dialog, *args):
            self.update_controls(dialog)
            result = self.original_preview(dialog, *args)
            if dialog.plan and not self._selection_settled(dialog):
                # The inherited preview expands physical representations
                # and selects those rows after it has prepared the plan.
                result = self.original_preview(dialog, *args)
                if dialog.plan and not self._selection_settled(dialog):
                    dialog.plan = None
                    dialog.export_button.setEnabled(False)
                    dialog.summary_label.setText(
                        "Selected export selection did not settle. "
                        "Choose the required rows and refresh the preview."
                    )
            return result

        def export(dialog):
            return self.export(dialog)

        self.values = values
        self.preview = preview
        self.exporter = export
        self.planner = self.plan
        self.preflight_config = self.check_config
        self.confirmation = self.confirm

    @staticmethod
    def _selection_settled(dialog):
        return set(dialog.scope.get("highlighted_record_ids") or []) == (
            dialog._highlighted_record_ids()
        )

    def update_controls(self, dialog):
        """Keep the parent selector and make replacement unavailable."""
        explanation = (
            "Each selected export creates a new folder inside this directory. "
            "Previous outputs are preserved."
        )
        box = dialog.overwrite_box
        blocked = box.blockSignals(True)
        try:
            box.setChecked(False)
        finally:
            box.blockSignals(blocked)
        box.setEnabled(False)
        box.setText("New folder for each export")
        box.setToolTip(explanation)
        dialog.output_box.setToolTip(explanation)
        dialog.manifest_box.setToolTip(
            "Include an optional CSV inventory in the completed folder."
        )

    def plan(self, records, config, set_id, scope):
        """Retain the intended child only while the complete request agrees."""
        if not isinstance(config, SelectedExportConfiguration):
            return self.original_plan(records, config, set_id, scope)
        request = _snapshot((records, dict(config), set_id, scope))
        context = config.context
        directory = (
            context.get("directory") if context.get("request") == request
            else None
        )
        plan = prepare_selected_export_plan(
            records, config, set_id, scope, plan_export=self.original_plan,
            output_directory=directory,
        )
        context.update(request=request, directory=plan["output_directory"])
        return plan

    def check_config(self, config, plan):
        """Preserve used-format narrowing and check the intended child."""
        result = self.original_preflight_config(config, plan)
        if isinstance(config, SelectedExportConfiguration):
            result = dict(result, output_directory=plan["output_directory"],
                          overwrite_existing=False)
        return result

    def confirm(self, scope, matching_count, export_count, plan, config,
                issues, skipped):
        """Show final member paths and the no-replacement publication policy."""
        if not isinstance(config, SelectedExportConfiguration):
            return self.original_confirmation(
                scope, matching_count, export_count, plan, config, issues,
                skipped,
            )
        ns = self.namespace
        warnings = [item for item in issues if item.get("severity")
                    == ns["PRODUCTION_PREFLIGHT_SEVERITY_WARNING"]]
        rows = ns["selected_export_plan_rows"](plan, config)
        all_skipped = list(plan.get("skipped") or []) + list(skipped or [])
        informative = (
            "Scope: {}\nProduction records selected: {}\n"
            "Records with compatible formats: {}\nFiles to produce: {}\n"
            "Completed output folder: {}\nRecords to skip: {}\n"
            "Preflight warnings: {}\n\n"
            "The complete requested set becomes available in this new folder "
            "through one directory operation. Previous outputs are preserved."
        ).format(
            ns["selected_export_scope_description"](scope), matching_count,
            export_count, len(rows), plan["output_directory"],
            len(all_skipped), len(warnings),
        )
        details = ["PLANNED FILES"] + [
            "- {} [{}]".format(row["Full path"], row["Format"])
            for row in rows
        ]
        if all_skipped:
            details.append("\nSKIPPED RECORDS")
            details.extend(
                "- {}: {}".format(
                    ns["_export_record_report_name"](item.get("record") or {}),
                    item.get("reason") or "No reason recorded",
                ) for item in all_skipped
            )
        if warnings:
            details.append("\nPREFLIGHT WARNINGS")
            details.extend("- {}: {}".format(
                item.get("issue_code", "WARNING"), item.get("message", ""),
            ) for item in warnings)
        widgets = ns["QtWidgets"]
        box = widgets.QMessageBox()
        box.setWindowTitle(ns["versioned_dialog_title"](
            "Confirm selected production export",
        ))
        box.setIcon(widgets.QMessageBox.Question)
        box.setText("Export the selected production items?")
        box.setInformativeText(informative)
        box.setDetailedText("\n".join(details))
        yes, no = widgets.QMessageBox.Yes, widgets.QMessageBox.No
        box.setStandardButtons(yes | no)
        box.setDefaultButton(no)
        return ns["dialog_exec"](box) == yes

    def _confirmation_snapshot(self, dialog, config, issues):
        warning = self.namespace["PRODUCTION_PREFLIGHT_SEVERITY_WARNING"]
        return _snapshot((
            dialog.current_set_id(),
            dialog.plan, dict(config), dialog.scope, dialog.matching_records,
            dialog.export_records, dialog.preliminary_skipped,
            [item for item in issues if item.get("severity") == warning],
        ))

    def export(self, dialog):
        """Reconfirm semantic changes and execute only the confirmed plan."""
        ns = self.namespace
        dialog.refresh_preview()
        if not dialog.plan or not dialog.plan.get("tasks"):
            self._error(dialog, "No valid selected export task is available.")
            return
        blocking = ns["preflight_blocking_report"](dialog.issues)
        if blocking:
            self._error(dialog, blocking)
            return
        config = dialog._current_config()
        confirmed = self._confirmation_snapshot(dialog, config, dialog.issues)
        if not self._confirm_dialog(dialog, config, dialog.issues):
            return
        try:
            # Only the parent may be created; the publisher owns the child.
            ns["ensure_production_export_directory"](config)
            config = dialog._current_config()
            set_id = dialog.current_set_id()
            dialog.plan = self.plan(
                dialog.export_records, config, set_id, dialog.scope,
            )
            settings = ns["settings_for_template_set"](dialog.doc, set_id)
            issues = ns["run_production_preflight"](
                dialog.doc,
                ns["selected_export_validation_records"](
                    dialog.catalogue_records, dialog.matching_records,
                    dialog.scope,
                ),
                dialog.export_records, self.check_config(config, dialog.plan),
                set_id, ns["read_section_config"](settings),
                ns["read_registration_config"](settings),
                ns["read_template_assembly_config"](settings),
                settings_obj=settings, plan=dialog.plan,
                include_export_checks=True, probe_export_bounds=False,
                filename_issues_override=ns["selected_export_filename_issues"](
                    dialog.plan, config, set_id,
                ),
            )
            blocking = ns["preflight_blocking_report"](issues)
            if blocking:
                raise ValueError(blocking)
            current = self._confirmation_snapshot(dialog, config, issues)
            if current != confirmed:
                if not self._confirm_dialog(dialog, config, issues):
                    return
                if self._confirmation_snapshot(
                    dialog, dialog._current_config(), issues,
                ) != current:
                    raise ValueError(
                        "The selected export changed during confirmation. "
                        "Refresh the preview and confirm it again."
                    )
            platforms = ns["read_platform_configs"](settings)
            summary = ns["run_selected_production_export"](
                dialog.doc, dialog.plan, config, set_id,
                platforms[0] if platforms else ns["default_platform_config"](),
                ns["read_formation_config"](settings),
                ns["read_registration_config"](settings),
                ns["read_template_assembly_config"](settings),
                extra_skipped=dialog.preliminary_skipped,
            )
            self.show_summary(summary)
            config.context.clear()
            dialog.refresh_preview()
        except Exception as error:
            self._error(dialog, str(error))

    def _confirm_dialog(self, dialog, config, issues):
        return self.namespace["confirm_selected_export_operation"](
            dialog.scope, len(dialog.matching_records),
            len(dialog.export_records), dialog.plan, config, issues,
            dialog.preliminary_skipped,
        )

    def _error(self, dialog, message):
        ns = self.namespace
        ns["QtWidgets"].QMessageBox.critical(
            dialog, ns["versioned_dialog_title"]("Selected export error"),
            message,
        )

    def show_summary(self, summary):
        """Offer the completed folder only after confirmed publication."""
        ns = self.namespace
        widgets = ns["QtWidgets"]
        published = summary["publication_state"] == "published"
        box = widgets.QMessageBox()
        box.setWindowTitle(ns["versioned_dialog_title"](
            "Selected production export result",
        ))
        box.setIcon(widgets.QMessageBox.Information if published
                    and not summary["failures"] else widgets.QMessageBox.Warning)
        box.setText(
            "The complete selected output set was published." if published
            else "The selected output set was not confirmed published."
        )
        box.setInformativeText(
            "Output directory: {}\nSuccessful files: {}\n"
            "Failed outputs or diagnostics: {}\nSkipped outputs: {}\n"
            "Formats produced: {}\nManifest: {}".format(
                summary["output_directory"], summary["successful_files"],
                summary["failed_files"], summary["skipped_objects"],
                ", ".join(summary["formats"]) or "None",
                summary["manifest_path"] or (
                    "Requested but not created" if summary["manifest_requested"]
                    else "Not requested"
                ),
            ),
        )
        details = summary["failure_details"] + summary["skipped_details"]
        if details:
            box.setDetailedText("\n\n".join(details))
        box.setStandardButtons(widgets.QMessageBox.Ok)
        open_button = None
        if published:
            open_button = box.addButton(
                "Open output folder", widgets.QMessageBox.ActionRole,
            )
        ns["dialog_exec"](box)
        if open_button is not None and box.clickedButton() is open_button:
            ns["open_export_directory"](summary["output_directory"])

    def snapshot(self):
        """Capture all replaced selected bindings for rollback."""
        return tuple(self.namespace[name] for name in self.NAMESPACE_NAMES) + (
            tuple(getattr(self.dialog, name) for name in self.DIALOG_NAMES)
        )

    def restore(self, previous):
        """Restore exactly the bindings captured before composition."""
        for name, value in zip(self.NAMESPACE_NAMES, previous[:3]):
            self.namespace[name] = value
        for name, value in zip(self.DIALOG_NAMES, previous[3:]):
            setattr(self.dialog, name, value)

    def bind(self):
        """Install the normal selected route without replacing comparison APIs."""
        self.restore((self.planner, self.preflight_config, self.confirmation,
                      self.values, self.preview, self.exporter))

    def validate(self):
        """Reject changed or partially rebound dialog policy."""
        if self.snapshot() != (
            self.planner, self.preflight_config, self.confirmation,
            self.values, self.preview, self.exporter,
        ) or (
            self.namespace.get("SelectedProductionExportDialog")
            is not self.dialog
        ):
            raise RuntimeError("The selected output-directory policy is mixed.")
