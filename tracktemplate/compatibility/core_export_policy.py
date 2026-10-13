"""Apply the new output-directory policy only to Core Generate."""

import inspect

from tracktemplate.application.core_export_set import prepare_core_export_plan


class CoreExportConfiguration(dict):
    """Mark one live Core dialog result without adding persisted fields."""


class CoreExportPolicy:
    """Bind Core-only planning, preflight and dialog controls.

    Other callers keep plain configuration dictionaries and the inherited
    operations. JSON stores only the existing configuration fields.
    """

    def __init__(self, namespace):
        self.namespace = namespace
        self.dialog = namespace["CurveInputDialog"]
        self.original_plan = namespace["plan_production_export"]
        self.original_preflight = namespace["run_production_preflight"]
        self.original_controls = self.dialog._update_production_export_controls
        self.original_values = self.dialog._production_export_values
        self.original_summary = namespace["show_production_export_summary"]
        self.preflight_signature = inspect.signature(self.original_preflight)
        originals = (
            self.original_plan, self.original_preflight,
            self.original_controls, self.original_values,
            self.original_summary,
        )
        if any(getattr(value, "__globals__", None) is not namespace
               for value in originals):
            raise RuntimeError("The inherited Core export policy is incomplete.")

        def update_controls(dialog, *args):
            self.original_controls(dialog, *args)
            if not hasattr(dialog, "production_overwrite_box"):
                return
            explanation = (
                "Each Core export creates a new folder inside the selected "
                "directory, with a dependency JSON for private development. "
                "Previous outputs are preserved. Dependency inventories are "
                "currently supported for curved plain-line templates and "
                "centrelines only; unsupported inventories prevent export."
            )
            box = dialog.production_overwrite_box
            box.setChecked(False)
            box.setEnabled(False)
            box.setText("New folder for each export")
            box.setToolTip(explanation)
            labels = dialog.findChildren(namespace["QtWidgets"].QLabel)
            for label in labels:
                if label.text() in ("Overwrite existing files:",
                                    "Preserve previous outputs:"):
                    label.setText("Preserve previous outputs:")
                    label.setToolTip(explanation)
            dialog.production_export_directory_box.setToolTip(explanation)
            dialog.production_manifest_box.setToolTip(
                "Include an optional CSV inventory in the completed folder."
            )
            dialog.production_manifest_box.setText(
                "Optional CSV; dependency JSON is always included"
            )

        def values(dialog):
            result = CoreExportConfiguration(self.original_values(dialog))
            result["overwrite_existing"] = False
            return result

        def show_summary(summary):
            if "dependency_manifest_path" not in summary:
                return self.original_summary(summary)
            csv_path = summary.get("manifest_path") or (
                "Requested but not created" if summary.get("manifest_requested")
                else "Not requested"
            )
            dependency_path = summary["dependency_manifest_path"] or "Not created"
            # These labels affect only the inherited dialog's text. The
            # command result retains its separate CSV and JSON path fields.
            display = dict(summary, manifest_path=(
                "CSV: {}\nDependency JSON: {}\n"
                "Private development only; output rights remain unresolved."
            ).format(csv_path, dependency_path))
            return self.original_summary(display)

        self.controls = update_controls
        self.values = values
        self.planner = self.plan
        self.preflight = self.check
        self.summary = show_summary

    def plan(self, records, config, set_id):
        """Use a fresh directory only for the marked Core dialog request."""
        if not isinstance(config, CoreExportConfiguration):
            return self.original_plan(records, config, set_id)
        return prepare_core_export_plan(
            records, config, set_id, plan_export=self.original_plan,
            dependency_manifest=True,
        )

    def check(self, *args, **kwargs):
        """Run existing preflight against the intended child paths."""
        bound = self.preflight_signature.bind(*args, **kwargs)
        config = bound.arguments["config"]
        if isinstance(config, CoreExportConfiguration):
            plan = bound.arguments.get("plan")
            if plan is None:
                plan = self.plan(
                    bound.arguments["export_records"], config,
                    bound.arguments["set_id"],
                )
                bound.arguments["plan"] = plan
            bound.arguments["config"] = dict(
                config, output_directory=plan["output_directory"],
                overwrite_existing=False,
            )
        return self.original_preflight(*bound.args, **bound.kwargs)

    def snapshot(self):
        """Keep replaced bindings for transactional composition."""
        return (
            self.namespace["plan_production_export"],
            self.namespace["run_production_preflight"],
            self.dialog._update_production_export_controls,
            self.dialog._production_export_values,
            self.namespace["show_production_export_summary"],
        )

    def restore(self, previous):
        """Restore exactly the bindings captured before failed composition."""
        (self.namespace["plan_production_export"],
         self.namespace["run_production_preflight"],
         self.dialog._update_production_export_controls,
         self.dialog._production_export_values,
         self.namespace["show_production_export_summary"]) = previous

    def bind(self):
        """Install only the normal Core policy."""
        self.restore((self.planner, self.preflight, self.controls, self.values,
                      self.summary))

    def validate(self):
        """Reject partial or replaced policy bindings before launch."""
        if self.snapshot() != (
            self.planner, self.preflight, self.controls, self.values,
            self.summary,
        ):
            raise RuntimeError("The Core output-directory policy is mixed.")
        if self.namespace.get("CurveInputDialog") is not self.dialog:
            raise RuntimeError("The Core output-directory dialog changed.")
