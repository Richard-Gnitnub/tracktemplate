"""Owned filesystem staging for one prepared Core export invocation.

This adapter supplies preparation and per-file publication, not a
whole-output-set transaction or a cross-process recovery protocol.
"""

import os
import stat
import tempfile


def _identity(info):
    return info.st_dev, info.st_ino


def _require_staging_directory(area):
    """Reject a replaced staging pathname before using the owned directory."""
    info = os.stat(area["path"], follow_symlinks=False)
    if (
        not stat.S_ISDIR(info.st_mode)
        or _identity(info) != area["identity"]
        or _identity(os.fstat(area["descriptor"])) != area["identity"]
    ):
        raise RuntimeError("The owned Core export staging directory changed.")
    output_info = os.stat(area["output_directory"], follow_symlinks=False)
    if (
        not stat.S_ISDIR(output_info.st_mode)
        or _identity(output_info) != area["output_identity"]
        or _identity(os.fstat(area["output_descriptor"]))
        != area["output_identity"]
    ):
        raise RuntimeError("The selected Core export directory changed.")


def _remember_staged_file(area, name):
    _require_staging_directory(area)
    try:
        info = os.stat(
            name, dir_fd=area["descriptor"], follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("A staged Core export is not an owned regular file.")
    area["files"][name] = _identity(info)


def _validate_staged_file(area, name):
    _require_staging_directory(area)
    info = os.stat(
        name, dir_fd=area["descriptor"], follow_symlinks=False,
    )
    if (
        not stat.S_ISREG(info.st_mode)
        or _identity(info) != area["files"].get(name)
        or info.st_size <= 0
    ):
        raise ValueError("A staged Core export is missing, changed or empty.")


def _stage_file(area, name, writer):
    _require_staging_directory(area)
    if name in os.listdir(area["descriptor"]):
        raise ValueError("A Core export staging filename already exists.")
    path = os.path.join(area["path"], name)
    try:
        writer(path)
    except BaseException as error:
        try:
            _remember_staged_file(area, name)
        except Exception as inspection_error:
            error.add_note("Staging inspection: {}".format(inspection_error))
        raise
    _remember_staged_file(area, name)
    _validate_staged_file(area, name)
    return path


def _cleanup_staging(area):
    """Remove only this invocation's unchanged, named staging entries."""
    if area is None:
        return []
    errors = []
    descriptor = area.get("descriptor")
    try:
        if descriptor is None or area.get("identity") is None:
            raise RuntimeError("Staging ownership was not established.")
        _require_staging_directory(area)
        for name, identity in area["files"].items():
            _require_staging_directory(area)
            try:
                info = os.stat(
                    name, dir_fd=descriptor, follow_symlinks=False,
                )
            except FileNotFoundError:
                continue  # An authorised replacement can consume this file.
            if not stat.S_ISREG(info.st_mode) or _identity(info) != identity:
                errors.append("Changed staging entry preserved: {}".format(name))
                continue
            try:
                os.unlink(name, dir_fd=descriptor)
            except OSError as error:
                errors.append("Staging entry retained: {}: {}".format(name, error))
        _require_staging_directory(area)
        if os.listdir(descriptor):
            errors.append("Unremoved staging entries preserved: {}".format(
                area["path"],
            ))
        else:
            os.rmdir(area["path"])
    except Exception as error:
        errors.append("Staging directory preserved: {}: {}".format(
            area["path"], error,
        ))
    finally:
        for descriptor in (descriptor, area.get("output_descriptor")):
            if descriptor is None:
                continue
            try:
                os.close(descriptor)
            except OSError as error:
                errors.append("Staging descriptor cleanup: {}".format(error))
    return errors


def _publish_staged_file(
    source_path,
    final_path,
    overwrite_existing,
    *,
    source_directory_fd,
    destination_directory_fd,
):
    """Publish one prepared file, without any whole-set rollback claim."""
    try:
        info = os.stat(
            os.path.basename(final_path), dir_fd=destination_directory_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        pass
    else:
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("The final Core export is not a regular file.")
    if overwrite_existing:
        os.replace(
            os.path.basename(source_path), os.path.basename(final_path),
            src_dir_fd=source_directory_fd,
            dst_dir_fd=destination_directory_fd,
        )
    else:
        # Unlike exists()+replace(), link cannot overwrite a late collision.
        os.link(
            os.path.basename(source_path), os.path.basename(final_path),
            src_dir_fd=source_directory_fd,
            dst_dir_fd=destination_directory_fd,
            follow_symlinks=False,
        )


def _validate_final_paths(plan, output_directory):
    paths = [task["path"] for task in plan["tasks"]]
    if plan.get("manifest_path"):
        paths.append(plan["manifest_path"])
    absolute = [os.path.abspath(str(path)) for path in paths]
    if len(set(absolute)) != len(absolute):
        raise ValueError("The Core export contains duplicate final paths.")
    if any(os.path.dirname(path) != output_directory for path in absolute):
        raise ValueError("Every Core export must use the selected directory.")


class CoreLayoutExportFiles:
    """Own one invocation's staging directory and publication descriptors."""

    def __init__(self):
        """Construct an unopened, operation-local adapter without I/O."""
        self._area = None
        self._entries = {}

    def open(self, plan, output_directory):
        """Validate final paths and acquire the owned staging resources."""
        output_directory = os.path.abspath(str(output_directory))
        _validate_final_paths(plan, output_directory)
        self._area = {
            "path": "",
            "identity": None,
            "descriptor": None,
            "files": {},
            "output_directory": output_directory,
            "output_descriptor": None,
        }
        area = self._area
        area["output_descriptor"] = os.open(
            output_directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        area["output_identity"] = _identity(os.fstat(
            area["output_descriptor"],
        ))
        area["path"] = tempfile.mkdtemp(
            prefix=".tracktemplate_core_export_", dir=output_directory,
        )
        area["identity"] = _identity(os.stat(
            area["path"], follow_symlinks=False,
        ))
        area["descriptor"] = os.open(
            area["path"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        _require_staging_directory(area)

    def stage(self, final_path, writer, *, manifest=False):
        """Write one payload while retaining its original final pathname."""
        extension = (
            ".csv" if manifest
            else os.path.splitext(os.path.basename(final_path))[1]
        )
        name = "{:04d}{}".format(len(self._entries) + 1, extension)
        path = _stage_file(self._area, name, writer)
        self._entries[final_path] = (name, path)

    def validate(self):
        """Reject changed, empty or unexpected staged entries."""
        area = self._area
        _require_staging_directory(area)
        if set(os.listdir(area["descriptor"])) != set(area["files"]):
            raise ValueError("Unexpected Core export staging entries remain.")
        for name in area["files"]:
            _validate_staged_file(area, name)

    def publish(self, final_path, overwrite_existing):
        """Publish one validated payload without a whole-set rollback."""
        area = self._area
        name, path = self._entries[final_path]
        _validate_staged_file(area, name)
        _publish_staged_file(
            path, final_path, overwrite_existing,
            source_directory_fd=area["descriptor"],
            destination_directory_fd=area["output_descriptor"],
        )

    def cleanup(self):
        """Clean owned staging and return every observed cleanup failure."""
        return _cleanup_staging(self._area)
