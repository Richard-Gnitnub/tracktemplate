"""Retain selected-export originals when ordinary rollback is incomplete.

Selected export keeps its existing per-file replacement policy. This
operation-local adapter supplies neither atomic whole-set publication nor
restart recovery. Its destination is an operator-controlled directory.
"""

import os
import stat
import tempfile


def _identity(info):
    return info.st_dev, info.st_ino


def _file_state(name, descriptor):
    try:
        info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("A selected-export entry is not a regular file.")
    return _identity(info), info.st_size, info.st_mtime_ns


class SelectedExportFiles:
    """Own one staging directory, prepared files and original backups."""

    def __init__(self):
        self.state = "preparation"
        self._path = ""
        self._output_path = ""
        self._directories = {}
        self._entries = []
        self._planned = set()
        self._retained_location_known = False

    @property
    def retained_staging_directory(self):
        """Return the confirmed retained location, or an empty string."""
        return self._path if self._retained_location_known else ""

    @property
    def destination_changed(self):
        """Treat incomplete or uncertain publication as changed."""
        return self.state in ("publishing", "rollback_incomplete", "published")

    def _open_directory(self, key, path):
        descriptor = os.open(
            path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            identity = _identity(os.fstat(descriptor))
        except BaseException:
            os.close(descriptor)
            raise
        self._directories[key] = (
            path, descriptor, identity,
        )

    def _directory(self, key):
        path, descriptor, identity = self._directories[key]
        info = os.stat(path, follow_symlinks=False)
        if (
            not stat.S_ISDIR(info.st_mode)
            or _identity(info) != identity
            or _identity(os.fstat(descriptor)) != identity
        ):
            raise RuntimeError(
                "The selected-export directory changed: " + path
            )
        return descriptor

    def open(self, plan, output_directory):
        """Check planned destinations before creating owned staging."""
        if self._directories or self._path:
            raise RuntimeError(
                "The selected-export file owner is already open."
            )
        self._output_path = os.path.abspath(str(output_directory))
        paths = [task["path"] for task in plan.get("tasks", [])]
        if plan.get("manifest_path"):
            paths.append(plan["manifest_path"])
        paths = [os.path.abspath(str(path)) for path in paths]
        if len(paths) != len(set(paths)):
            raise ValueError(
                "The selected export contains duplicate final paths."
            )
        if any(os.path.dirname(path) != self._output_path for path in paths):
            raise ValueError(
                "Selected exports must use the selected directory."
            )
        self._planned = set(paths)
        self._open_directory("output", self._output_path)
        self._path = tempfile.mkdtemp(
            prefix=".railway_selected_export_", dir=self._output_path,
        )
        self._open_directory("staging", self._path)

    def stage(self, final_path, writer, *, manifest=False):
        """Prepare a payload without changing an existing destination."""
        del manifest  # The final extension already identifies the format.
        final_path = os.path.abspath(str(final_path))
        if final_path not in self._planned or any(
            item["final_path"] == final_path for item in self._entries
        ):
            raise ValueError("The selected-export destination is not planned.")
        descriptor = self._directory("staging")
        name = "{:04d}_{}".format(
            len(self._entries) + 1, os.path.basename(final_path),
        )
        if name in os.listdir(descriptor):
            raise ValueError("The selected-export staging filename exists.")
        item = {
            "name": name, "final_path": final_path,
            "final_name": os.path.basename(final_path), "prepared": None,
            "original": None,
        }
        self._entries.append(item)
        try:
            writer(os.path.join(self._path, name))
        except BaseException as error:
            # Remember even a partial regular file after a writer failure.
            try:
                item["prepared"] = _file_state(
                    name, self._directory("staging"),
                )
            except Exception as inspection_error:
                error.add_note("Staging inspection: " + str(inspection_error))
            raise
        item["prepared"] = _file_state(name, self._directory("staging"))
        if item["prepared"] is None or item["prepared"][1] <= 0:
            raise ValueError("The exporter produced no valid file data.")

    def validate(self):
        """Reject missing, changed or unexpected prepared files."""
        descriptor = self._directory("staging")
        self._directory("output")
        if {item["final_path"] for item in self._entries} != self._planned:
            raise ValueError("The selected-export preparation is incomplete.")
        if set(os.listdir(descriptor)) != {
            item["name"] for item in self._entries
        }:
            raise ValueError(
                "Unexpected selected-export staging entries remain."
            )
        for item in self._entries:
            current = _file_state(item["name"], descriptor)
            if (
                current != item["prepared"] or current is None
                or current[1] <= 0
            ):
                raise ValueError("A prepared selected-export file changed.")

    def _replace(
        self, source, destination, *, source_directory_fd,
        destination_directory_fd,
    ):
        os.replace(
            source, destination, src_dir_fd=source_directory_fd,
            dst_dir_fd=destination_directory_fd,
        )

    def _unlink(self, name, *, directory_fd):
        os.unlink(name, dir_fd=directory_fd)

    def _rollback(self):
        errors = []
        for item in reversed(self._entries):
            try:
                output = self._directory("output")
                backups = self._directory("backups")
                final = _file_state(item["final_name"], output)
                backup = _file_state(item["name"], backups)
                original = item["original"]
                if final == original and backup is None:
                    continue
                if backup != original:
                    raise RuntimeError("The original backup is uncertain.")
                if final is not None:
                    if final != item["prepared"]:
                        raise RuntimeError("The destination is uncertain.")
                    self._unlink(item["final_name"], directory_fd=output)
                if original is not None:
                    self._replace(
                        item["name"], item["final_name"],
                        source_directory_fd=backups,
                        destination_directory_fd=output,
                    )
                if _file_state(item["final_name"], output) != original:
                    raise RuntimeError(
                        "The original destination was not restored."
                    )
            except Exception as error:
                errors.append("{}: {}".format(item["final_path"], error))
        self.state = "rollback_incomplete" if errors else "rolled_back"
        return errors

    def publish(self, overwrite_existing):
        """Keep prior bytes available until all replacements succeed."""
        self.validate()
        output = self._directory("output")
        staging = self._directory("staging")
        for item in self._entries:
            item["original"] = _file_state(item["final_name"], output)
            if item["original"] is not None and not overwrite_existing:
                raise ValueError(
                    "The planned filename appeared after preflight and was "
                    "not overwritten: " + item["final_path"]
                )
        os.mkdir(".backups", dir_fd=staging)
        self._open_directory("backups", os.path.join(self._path, ".backups"))
        self.state = "publishing"
        try:
            for item in self._entries:
                output = self._directory("output")
                staging = self._directory("staging")
                backups = self._directory("backups")
                if _file_state(item["final_name"], output) != item["original"]:
                    raise RuntimeError(
                        "The selected-export destination changed."
                    )
                if item["original"] is not None:
                    self._replace(
                        item["final_name"], item["name"],
                        source_directory_fd=output,
                        destination_directory_fd=backups,
                    )
                self._replace(
                    item["name"], item["final_name"],
                    source_directory_fd=staging,
                    destination_directory_fd=output,
                )
                if _file_state(item["final_name"], output) != item["prepared"]:
                    raise RuntimeError(
                        "The published selected export changed."
                    )
            self.state = "published"
        except Exception as error:
            self.state = "rollback_incomplete"
            rollback_errors = self._rollback()
            if rollback_errors:
                message = (
                    "Selected export commit failed; rollback is incomplete. "
                    "Destination files may have changed. "
                    "Last-known staging path: "
                    "{}\nReason: {}\nRollback diagnostics: {}"
                ).format(self._path, error, "; ".join(rollback_errors))
            else:
                message = (
                    "Selected export commit failed; original destination "
                    "files were restored. Reason: {}"
                ).format(error)
            raise RuntimeError(message) from error

    def _cleanup_owned(self):
        staging = self._directory("staging")
        self._directory("output")
        expected = {item["name"] for item in self._entries}
        if "backups" in self._directories:
            expected.add(".backups")
        if not set(os.listdir(staging)).issubset(expected):
            raise RuntimeError("Unexpected staging entries must be preserved.")
        # Inspect all entries before removing any. A changed entry grants no
        # cleanup authority over this retained operation directory.
        removals = []
        for key, field in (("staging", "prepared"), ("backups", "original")):
            if key not in self._directories:
                continue
            descriptor = self._directory(key)
            names = set(os.listdir(descriptor))
            if key == "staging":
                names.discard(".backups")
            if not names.issubset({item["name"] for item in self._entries}):
                raise RuntimeError(
                    "Unexpected backup entries must be preserved."
                )
            for item in self._entries:
                current = _file_state(item["name"], descriptor)
                if current is None:
                    continue
                if current != item[field]:
                    raise RuntimeError(
                        "Changed staging entries must be preserved."
                    )
                removals.append((key, item["name"], current))
        for key, name, expected in removals:
            descriptor = self._directory(key)
            if _file_state(name, descriptor) != expected:
                raise RuntimeError("The staging entry changed before cleanup.")
            self._unlink(name, directory_fd=descriptor)
        if "backups" in self._directories:
            self._directory("backups")
            os.rmdir(".backups", dir_fd=self._directory("staging"))
        self._directory("staging")
        os.rmdir(self._path)

    def _retention_message(self):
        try:
            self._directory("staging")
        except Exception as error:
            self._retained_location_known = False
            return (
                "Selected-export staging location is uncertain. "
                "Last-known path: {}. Reason: {}"
            ).format(self._path, error)
        self._retained_location_known = True
        return "Retained selected-export staging: " + self._path

    def cleanup(self):
        """Clean confirmed owned state; preserve incomplete rollback data."""
        errors = []
        try:
            if self.state in ("publishing", "rollback_incomplete"):
                errors.append(self._retention_message())
            elif self._path:
                self._cleanup_owned()
        except Exception as error:
            errors.append("{}\nCleanup: {}".format(
                self._retention_message(), error,
            ))
        finally:
            for directory in self._directories.values():
                try:
                    os.close(directory[1])
                except OSError as error:
                    errors.append(
                        "Selected-export descriptor cleanup: " + str(error)
                    )
            self._directories.clear()
        return errors
