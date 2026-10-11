"""Application orchestration for the inherited core-layout export contract."""

import os


__all__ = ("run_core_layout_export", "run_staged_core_layout_export")


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


def run_staged_core_layout_export(
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
    dispatch_export_task,
    build_manifest_rows,
    write_export_manifest,
    failed_export_report,
    skipped_export_report,
    export_files_factory,
):
    """Prepare all payloads before publishing any Core export member.

    Preparation failure preserves every final file. Publication remains
    per-file: a later publication failure can leave earlier files changed,
    and then the prepared success CSV is withheld. Success counts describe
    published files only. Cleanup failures add diagnostics and increase
    ``failed_files`` independently of the requested file count.

    The caller owns preflight, confirmation and the committed document.
    This operation does not supply a whole-set transaction or recovery
    protocol. BaseException interruptions propagate after owned cleanup.
    """
    results = [
        {"task": task, "success": False,
         "error": "Not published: Core export preparation did not complete."}
        for task in plan["tasks"]
    ]
    manifest_path = plan.get("manifest_path", "")
    manifest_success = False
    files = None
    operation_error = ""
    cleanup_errors = []
    interrupted = None
    phase = "preparation"
    failed_item = None
    try:
        files = export_files_factory()
        files.open(plan, config["output_directory"])
        dispatcher = (
            dispatch_export_task if exporter_override is None
            else exporter_override
        )
        for item in results:
            failed_item = item
            task = item["task"]
            files.stage(
                task["path"],
                lambda destination, task=task: dispatcher(
                    doc, task, destination,
                ),
            )
        failed_item = None
        prepared_results = [
            {"task": item["task"], "success": True, "error": ""}
            for item in results
        ]
        manifest_rows = build_manifest_rows(
            prepared_results, plan["skipped"], set_id, platform_config,
            formation_config, registration_config, template_assembly_config,
        )
        if manifest_path:
            files.stage(
                manifest_path,
                lambda destination: write_export_manifest(
                    destination, manifest_rows,
                ),
                manifest=True,
            )
        files.validate()
        phase = "publication"
        overwrite = bool(config.get("overwrite_existing", False))
        for item in results:
            failed_item = item
            files.publish(item["task"]["path"], overwrite)
            item["success"] = True
            item["error"] = ""
        failed_item = None
        if manifest_path:
            files.publish(manifest_path, overwrite)
            manifest_success = True
    except Exception as error:
        operation_error = "Core export {} failed: {}".format(phase, error)
        if failed_item is not None:
            failed_item["error"] = operation_error
        for item in results:
            if not item["success"] and item is not failed_item:
                item["error"] = "Not published: {}".format(operation_error)
    except BaseException as error:
        interrupted = error
        raise
    finally:
        try:
            cleanup_errors = files.cleanup() if files is not None else []
        except Exception as error:
            cleanup_errors = ["Core export staging cleanup failed: {}".format(
                error,
            )]
        if interrupted is not None and cleanup_errors:
            interrupted.add_note("\n".join(cleanup_errors))

    failures = []
    failure_details = []
    for item in results:
        if not item["success"]:
            summary, detail = failed_export_report(item)
            failures.append(summary)
            failure_details.append(detail)
    if operation_error and failed_item is None:
        failures.append(operation_error)
        failure_details.append(operation_error)
    failures.extend(cleanup_errors)
    failure_details.extend(cleanup_errors)
    skipped_outputs = []
    skipped_details = []
    for item in plan.get("skipped", []):
        summary, detail = skipped_export_report(item)
        skipped_outputs.append(summary)
        skipped_details.append(detail)
    successful = [item for item in results if item["success"]]
    return {
        "output_directory": config["output_directory"],
        "successful_files": len(successful) + int(manifest_success),
        "failed_files": len(failures),
        "skipped_objects": len(plan.get("skipped", [])),
        "formats": sorted({item["task"]["format"].upper()
                           for item in successful}),
        "manifest_path": manifest_path if manifest_success else "",
        "manifest_requested": bool(manifest_path),
        "failures": failures,
        "failure_details": failure_details,
        "skipped_outputs": skipped_outputs,
        "skipped_details": skipped_details,
        "results": results,
    }
