"""Plan and publish one complete Core Generate output directory."""

import os
import uuid


def prepare_core_export_plan(records, config, set_id, *, plan_export,
                             dependency_manifest=False):
    """Allocate paths without creating a directory or changing inputs.

    The inherited planner retains its member names and ordering. Each
    invocation selects a new directory; publication must reject a collision.
    The selected parent remains the caller's stored output preference.
    """
    parent = os.path.abspath(config["output_directory"])
    directory = os.path.join(parent, "Core_Export_" + uuid.uuid4().hex)
    selected = dict(config, output_directory=directory,
                    overwrite_existing=False)
    plan = plan_export(records, selected, set_id)
    result = dict(plan, output_directory=directory)
    if dependency_manifest:
        result["dependency_manifest_path"] = os.path.join(
            directory, "Core_Dependency_Manifest.json",
        )
    return result


def run_atomic_core_layout_export(
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
    prepare_dependency_manifest=None,
):
    """Prepare all requested members, then publish their directory once.

    Confirmed publication survives later diagnostics. Uncertain publication
    is reported explicitly and grants no cleanup authority. This operation
    does not promise durability or restart recovery. The caller supplies
    preflight, document isolation, and an already committed Generate result.
    """
    results = [
        {"task": task, "success": False,
         "error": "Not confirmed published: Core export did not complete."}
        for task in plan["tasks"]
    ]
    manifest_path = plan.get("manifest_path", "")
    dependency_path = plan.get("dependency_manifest_path", "")
    files = None
    operation_error = ""
    cleanup_errors = []
    interrupted = None
    phase = "preparation"
    failed_item = None
    skipped_outputs = []
    skipped_details = []
    formats = []
    try:
        # Reporting callbacks must finish before publication, too.
        for item in plan.get("skipped", []):
            summary, detail = skipped_export_report(item)
            skipped_outputs.append(summary)
            skipped_details.append(detail)
        formats = sorted({item["task"]["format"].upper()
                          for item in results})
        dependency_builder = None
        if prepare_dependency_manifest is not None and not dependency_path:
            raise ValueError("The Core dependency manifest is missing from the plan.")
        if dependency_path:
            if not callable(prepare_dependency_manifest):
                raise ValueError("The Core dependency inventory is unavailable.")
            dependency_builder = prepare_dependency_manifest(
                doc, plan, config, set_id,
            )
            if not callable(dependency_builder):
                raise ValueError("The Core dependency inventory is invalid.")
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
        if manifest_path:
            prepared = [
                {"task": item["task"], "success": True, "error": ""}
                for item in results
            ]
            rows = build_manifest_rows(
                prepared, plan["skipped"], set_id, platform_config,
                formation_config, registration_config,
                template_assembly_config,
            )
            files.stage(
                manifest_path,
                lambda destination: write_export_manifest(destination, rows),
                manifest=True,
            )
        if dependency_builder is not None:
            files.stage_dependency_manifest(
                dependency_builder(files.artifact_inventory()),
            )
        files.validate()
        phase = "publication"
        files.publish()
    except Exception as error:
        operation_error = "Core export {} failed: {}".format(phase, error)
        notes = getattr(error, "__notes__", ())
        if notes:
            operation_error += "\n" + "\n".join(str(note) for note in notes)
    except BaseException as error:
        interrupted = error
        raise
    finally:
        try:
            cleanup_errors = files.cleanup() if files is not None else []
        except Exception as error:
            cleanup_errors = ["Core export cleanup failed: {}".format(error)]
        if interrupted is not None:
            state = files.publication_state if files else "not-published"
            interrupted.add_note(
                "Core export publication state: {}; intended directory: {}"
                .format(state, plan.get("output_directory", "unallocated"))
            )
            if cleanup_errors:
                interrupted.add_note("\n".join(cleanup_errors))

    state = files.publication_state if files else "not-published"
    published = files.published if files else False
    failures = []
    failure_details = []
    for item in results:
        if published:
            item.update(success=True, error="")
        else:
            item["error"] = "Not confirmed published: {}".format(
                operation_error or "Core export did not complete."
            )
            summary, detail = failed_export_report(item)
            failures.append(summary)
            failure_details.append(detail)
    if operation_error and (published or failed_item is None):
        failures.append(operation_error)
        failure_details.append(operation_error)
    if state == "uncertain":
        diagnostic = (
            "Publication is uncertain. Preserve the destination and staging "
            "data for inspection. Intended directory: {}"
        ).format(plan.get("output_directory", "unallocated"))
        failures.append(diagnostic)
        failure_details.append(diagnostic)
    failures.extend(cleanup_errors)
    failure_details.extend(cleanup_errors)
    return {
        "output_directory": (
            plan["output_directory"] if published
            else config["output_directory"]
        ),
        "successful_files": (
            len(results) + int(bool(manifest_path)) + int(bool(dependency_path))
            if published else 0
        ),
        "failed_files": len(failures),
        "skipped_objects": len(plan.get("skipped", [])),
        "formats": formats if published else [],
        "manifest_path": manifest_path if published else "",
        "manifest_requested": bool(manifest_path),
        **({"dependency_manifest_path": dependency_path if published else ""}
           if dependency_path else {}),
        "failures": failures,
        "failure_details": failure_details,
        "skipped_outputs": skipped_outputs,
        "skipped_details": skipped_details,
        "results": results,
        "publication_state": state,
    }
