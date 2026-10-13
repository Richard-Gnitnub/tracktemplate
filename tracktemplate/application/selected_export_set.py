"""Plan and publish one complete selected-production output directory."""

import os
import uuid

from tracktemplate.application.core_export_set import (
    run_atomic_core_layout_export,
)


def prepare_selected_export_plan(
    records, config, set_id, scope, *, plan_export, output_directory=None,
):
    """Keep selected member naming inside one intended new directory.

    Planning creates no files. Replanning can retain the intended directory;
    an existing child is rejected instead of allocating member revisions.
    The configuration keeps the operator's parent-directory preference.
    """
    parent_text = str(config.get("output_directory") or "")
    if not parent_text.strip():
        raise ValueError("Select a parent folder for the selected export.")
    parent = os.path.abspath(parent_text)
    directory = output_directory or os.path.join(
        parent, "Selected_Export_" + uuid.uuid4().hex,
    )
    directory = os.path.abspath(directory)
    if os.path.dirname(directory) != parent:
        raise ValueError("The selected export must use a new child folder.")
    if os.path.lexists(directory):
        raise FileExistsError(
            "The intended selected-export folder already exists: " + directory
        )
    selected = dict(config, output_directory=directory,
                    overwrite_existing=False)
    plan = plan_export(records, selected, set_id, scope)
    return dict(plan, output_directory=directory)


def run_atomic_selected_production_export(
    doc,
    plan,
    config,
    set_id,
    platform_config,
    formation_config,
    registration_config,
    template_assembly_config,
    extra_skipped=None,
    exporter_override=None,
    *,
    dispatch_export_task,
    build_manifest_rows,
    write_export_manifest,
    failed_export_report,
    skipped_export_report,
    export_files_factory,
):
    """Publish the confirmed selected plan using the shared set operation.

    The caller owns scope, confirmation, preflight and isolated dispatch.
    Preliminary skipped records join plan skips in diagnostics and optional
    CSV. The established operation retains published counts after late
    errors and preserves uncertain state. No restart recovery is promised.
    """
    selected = dict(
        plan, skipped=list(plan.get("skipped") or []) + list(extra_skipped or []),
    )
    return run_atomic_core_layout_export(
        doc, selected, config, set_id, platform_config, formation_config,
        registration_config, template_assembly_config, exporter_override,
        dispatch_export_task=dispatch_export_task,
        build_manifest_rows=build_manifest_rows,
        write_export_manifest=write_export_manifest,
        failed_export_report=failed_export_report,
        skipped_export_report=skipped_export_report,
        export_files_factory=export_files_factory,
    )
