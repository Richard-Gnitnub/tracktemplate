"""Run selected export while preserving uncertain rollback data."""


def run_selected_production_export(
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
    """Keep inherited results and report incomplete rollback truthfully.

    The caller still owns preflight, overwrite confirmation, revision
    allocation and the serializer. The file adapter owns staging, per-file
    publication, original backups and cleanup. This command introduces no
    atomic-publication, physical-fit or restart-recovery guarantee.
    """
    files = None
    failed_task = None
    operation_error = None
    cleanup_errors = []
    skipped = list(plan.get("skipped") or []) + list(extra_skipped or [])
    skipped_outputs = []
    skipped_details = []
    manifest_path = str(plan.get("manifest_path") or "")
    prepared_count = 0
    formats = []
    output_directory = str(config.get("output_directory") or "")
    try:
        # Reporting must finish before any destination mutation.
        for item in skipped:
            summary, detail = skipped_export_report(item)
            skipped_outputs.append(summary)
            skipped_details.append(detail)
        formats = sorted({
            str(task.get("format") or "").upper()
            for task in plan.get("tasks", []) if task.get("format")
        })
        files = export_files_factory()
        files.open(plan, output_directory)
        dispatcher = (
            dispatch_export_task if exporter_override is None
            else exporter_override
        )
        results = []
        for task in plan.get("tasks", []):
            failed_task = task
            files.stage(
                task["path"],
                lambda destination, task=task: dispatcher(
                    doc, task, destination,
                ),
            )
            results.append({"task": task, "success": True, "error": ""})
            prepared_count += 1
        failed_task = None
        rows = build_manifest_rows(
            results, skipped, set_id, platform_config, formation_config,
            registration_config, template_assembly_config,
        )
        if manifest_path:
            files.stage(
                manifest_path,
                lambda destination: write_export_manifest(destination, rows),
                manifest=True,
            )
            prepared_count += 1
        files.validate()
        files.publish(bool(config.get("overwrite_existing", False)))
    except Exception as error:
        operation_error = error
    except BaseException as error:
        # Preserve the existing propagation boundary. Cleanup cannot erase
        # backups when publication was interrupted before a known result.
        try:
            cleanup_errors = files.cleanup() if files is not None else []
        except Exception as cleanup_error:
            cleanup_errors = [str(cleanup_error)]
        if cleanup_errors:
            error.add_note("\n".join(cleanup_errors))
        raise
    if files is not None:
        try:
            cleanup_errors = files.cleanup()
        except Exception as error:
            cleanup_errors = [
                "Selected-export cleanup failed: {}".format(error)
            ]

    state = files.state if files is not None else "preparation"
    published = state == "published"
    failures = []
    failure_details = []
    if operation_error is not None:
        error_text = str(operation_error)
        notes = getattr(operation_error, "__notes__", ())
        if notes:
            error_text += "\n" + "\n".join(str(note) for note in notes)
        if state == "preparation":
            disposition = "No destination export file was changed."
        elif state == "rolled_back":
            disposition = "Original destination files were restored."
        elif published:
            disposition = "The selected output files were published."
        else:
            disposition = (
                "Rollback is incomplete or uncertain. Destination files may "
                "have changed."
            )
        summary = "Selected export transaction: " + error_text
        detail = disposition + "\nReason: " + error_text
        if failed_task is not None:
            try:
                summary, task_detail = failed_export_report({
                    "task": failed_task, "error": error_text,
                })
                detail = task_detail + "\n" + disposition
            except Exception as report_error:
                detail += "\nFailure reporting: " + str(report_error)
        failures.append(summary)
        failure_details.append(detail)
    failures.extend(cleanup_errors)
    failure_details.extend(cleanup_errors)
    return {
        "output_directory": output_directory,
        "successful_files": prepared_count if published else 0,
        "failed_files": 1 if failures else 0,
        "skipped_objects": len(skipped),
        "formats": formats if published else [],
        "manifest_path": manifest_path if published else "",
        "manifest_requested": bool(config.get("create_manifest", True)),
        "failures": failures,
        "failure_details": failure_details,
        "skipped_outputs": skipped_outputs,
        "skipped_details": skipped_details,
    }
