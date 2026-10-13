"""Bind isolated selected serialization and rollback to the GUI caller.

The modular command owns the normal B16 route. The frozen B15 command stays
comparison evidence until its migration and removal receive owner acceptance.
"""

from tracktemplate.application.selected_export import (
    run_selected_production_export,
)
from tracktemplate.application.selected_export_set import (
    run_atomic_selected_production_export,
)
from tracktemplate.compatibility.selected_export_policy import (
    SelectedExportPolicy,
)


HOST_BINDING = "run_selected_production_export"
HOST_OPERATIONS = (
    ("dispatch_export_task", "dispatch_freecad_export"),
    ("build_manifest_rows", "build_manifest_rows"),
    ("write_export_manifest", "write_export_manifest"),
    ("failed_export_report", "_failed_export_report"),
    ("skipped_export_report", "_skipped_export_report"),
)


class SelectedExportBinding:
    """Keep inherited arguments and bind only the selected-export command."""

    def __init__(self, namespace, *, export_files_factory,
                 export_dispatcher_factory, atomic=False):
        self.namespace = namespace
        self.export_files_factory = export_files_factory
        self._expected_factory = export_files_factory
        self.export_dispatcher_factory = export_dispatcher_factory
        self._expected_dispatcher_factory = export_dispatcher_factory
        self.atomic = atomic
        self._expected_atomic = atomic
        self.original_command = namespace.get(HOST_BINDING)
        self.dialog = namespace.get("SelectedProductionExportDialog")
        self.caller = getattr(self.dialog, "export_selected", None)
        originals = [self.original_command, self.caller]
        for field, name in HOST_OPERATIONS:
            operation = namespace.get(name)
            originals.append(operation)
            setattr(self, field, operation)
        code = getattr(self.caller, "__code__", None)
        if (
            any(not callable(value) or getattr(value, "__globals__", None)
                is not namespace for value in originals)
            or code is None or HOST_BINDING not in code.co_names
            or not callable(export_files_factory)
            or not callable(export_dispatcher_factory)
        ):
            raise RuntimeError(
                "The inherited selected-export route is incomplete."
            )
        self.policy = SelectedExportPolicy(namespace) if atomic else None

    def __call__(
        self, doc, plan, config, set_id, platform_config, formation_config,
        registration_config, template_assembly_config, extra_skipped=None,
        exporter_override=None,
    ):
        serializer = (
            self.dispatch_export_task if exporter_override is None
            else exporter_override
        )
        operations = {
            field: getattr(self, field) for field, _name in HOST_OPERATIONS
        }
        operations["dispatch_export_task"] = (
            self.export_dispatcher_factory(serializer)
        )
        command = (run_atomic_selected_production_export if self.atomic
                   else run_selected_production_export)
        return command(
            doc, plan, config, set_id, platform_config, formation_config,
            registration_config, template_assembly_config, extra_skipped,
            None,
            **operations,
            export_files_factory=self.export_files_factory,
        )

    def snapshot(self):
        command = self.namespace[HOST_BINDING]
        return (command, self.policy.snapshot()) if self.policy else command

    def restore(self, previous):
        if self.policy is not None:
            self.namespace[HOST_BINDING] = previous[0]
            self.policy.restore(previous[1])
        else:
            self.namespace[HOST_BINDING] = previous

    def bind(self):
        if self.policy is not None:
            self.policy.bind()
        self.namespace[HOST_BINDING] = self

    def validate(self):
        """Reject mixed commands, callbacks or GUI callers before launch."""
        caller = self.policy.exporter if self.policy else self.caller
        if self.policy is not None:
            self.policy.validate()
        if (
            self.namespace.get(HOST_BINDING) is not self
            or self.namespace.get("SelectedProductionExportDialog")
            is not self.dialog
            or getattr(self.dialog, "export_selected", None) is not caller
            or self.export_files_factory is not self._expected_factory
            or self.export_dispatcher_factory
            is not self._expected_dispatcher_factory
            or self.atomic is not self._expected_atomic
            or any(self.namespace.get(name) is not getattr(self, field)
                   for field, name in HOST_OPERATIONS)
        ):
            raise RuntimeError(
                "The selected-export command has a mixed binding."
            )
