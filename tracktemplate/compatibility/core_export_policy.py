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
        self.preflight_signature = inspect.signature(self.original_preflight)
        originals = (
            self.original_plan, self.original_preflight,
            self.original_controls, self.original_values,
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
                "directory. Previous outputs are preserved."
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

        def values(dialog):
            result = CoreExportConfiguration(self.original_values(dialog))
            result["overwrite_existing"] = False
            return result

        self.controls = update_controls
        self.values = values
        self.planner = self.plan
        self.preflight = self.check

    def plan(self, records, config, set_id):
        """Use a fresh directory only for the marked Core dialog request."""
        if not isinstance(config, CoreExportConfiguration):
            return self.original_plan(records, config, set_id)
        return prepare_core_export_plan(
            records, config, set_id, plan_export=self.original_plan,
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
        """Keep the four replaced bindings for transactional composition."""
        return (
            self.namespace["plan_production_export"],
            self.namespace["run_production_preflight"],
            self.dialog._update_production_export_controls,
            self.dialog._production_export_values,
        )

    def restore(self, previous):
        """Restore exactly the bindings captured before failed composition."""
        (self.namespace["plan_production_export"],
         self.namespace["run_production_preflight"],
         self.dialog._update_production_export_controls,
         self.dialog._production_export_values) = previous

    def bind(self):
        """Install only the normal Core policy."""
        self.restore((self.planner, self.preflight, self.controls, self.values))

    def validate(self):
        """Reject partial or replaced policy bindings before launch."""
        if self.snapshot() != (
            self.planner, self.preflight, self.controls, self.values,
        ):
            raise RuntimeError("The Core output-directory policy is mixed.")
        if self.namespace.get("CurveInputDialog") is not self.dialog:
            raise RuntimeError("The Core output-directory dialog changed.")
