"""Application orchestration for the inherited core-layout export contract."""

import os


__all__ = ("run_core_layout_export",)


def run_core_layout_export(
    doc,
    plan,
    config,
    set_id,
    platform_config,
    formation_config,
    registration_config,
    template_assembly_config,
    exporter_override=None,
    *,
    execute_export_tasks,
    build_manifest_rows,
    write_export_manifest,
    failed_export_report,
    skipped_export_report,
):
    """Run one prepared export plan through explicit host operations."""
    results = execute_export_tasks(doc, plan, config, exporter_override)
    manifest_rows = build_manifest_rows(
        results, plan["skipped"], set_id, platform_config, formation_config,
        registration_config, template_assembly_config,
    )
    manifest_path = plan.get("manifest_path", "")
    manifest_error = ""
    manifest_success = False
    if manifest_path:
        try:
            write_export_manifest(manifest_path, manifest_rows)
            manifest_success = True
        except Exception as error:
            manifest_error = str(error)

    successful = [item for item in results if item["success"]]
    failed = [item for item in results if not item["success"]]
    formats = sorted(set(item["task"]["format"].upper() for item in successful))

    failures = []
    failure_details = []
    for item in failed:
        summary, detail = failed_export_report(item)
        failures.append(summary)
        failure_details.append(detail)
    if manifest_error:
        manifest_summary = "CSV manifest '{}': {}".format(
            os.path.basename(manifest_path) or "unnamed manifest",
            manifest_error,
        )
        failures.append(manifest_summary)
        failure_details.append("\n".join([
            "Output type: CSV manifest",
            "Filename: {}".format(
                os.path.basename(manifest_path) or "unnamed manifest"
            ),
            "Full path: {}".format(manifest_path or "Not allocated"),
            "Reason: {}".format(manifest_error),
        ]))

    skipped_outputs = []
    skipped_details = []
    for item in plan.get("skipped", []):
        summary, detail = skipped_export_report(item)
        skipped_outputs.append(summary)
        skipped_details.append(detail)

    return {
        "output_directory": config["output_directory"],
        "successful_files": len(successful) + (1 if manifest_success else 0),
        "failed_files": len(failed) + (1 if manifest_error else 0),
        "skipped_objects": len(plan.get("skipped", [])),
        "formats": formats,
        "manifest_path": manifest_path if manifest_success else "",
        "manifest_requested": bool(manifest_path),
        "failures": failures,
        "failure_details": failure_details,
        "skipped_outputs": skipped_outputs,
        "skipped_details": skipped_details,
        "results": results,
    }
