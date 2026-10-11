"""Publish one complete Core export directory on qualified Linux ext4.

The caller owns the operator-controlled parent namespace. Identity checks
detect observed changes; they do not exclude hostile concurrent writers.
Publication is one no-replace directory rename, without durability or
restart recovery guarantees.
"""

import ctypes
import errno
import os
import stat
import sys
import uuid


def _identity(info):
    return info.st_dev, info.st_ino


def _mount_id(descriptor):
    path = "/proc/self/fdinfo/{}".format(descriptor)
    with open(path, encoding="ascii") as stream:
        for line in stream:
            if line.startswith("mnt_id:"):
                return int(line.split(":", 1)[1])
    raise RuntimeError("The Core export mount identity is unavailable.")


def _require_ext4(descriptor):
    if sys.platform != "linux":
        raise RuntimeError("Core export sets require qualified Linux ext4.")
    mount_id = _mount_id(descriptor)
    with open("/proc/self/mountinfo", encoding="utf-8") as stream:
        for line in stream:
            before, separator, after = line.partition(" - ")
            if separator and int(before.split()[0]) == mount_id:
                if after.split()[0] != "ext4":
                    raise RuntimeError(
                        "The Core export directory is not on qualified ext4."
                    )
                return mount_id
    raise RuntimeError("The Core export filesystem cannot be identified.")


def _rename_noreplace(descriptor, source, destination):
    """Use the Linux no-replace primitive; never substitute another route."""
    library = ctypes.CDLL(None, use_errno=True)
    try:
        rename = library.renameat2
    except AttributeError as error:
        raise OSError(
            errno.ENOSYS, "Linux renameat2 is unavailable."
        ) from error
    rename.argtypes = (
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
        ctypes.c_uint,
    )
    rename.restype = ctypes.c_int
    result = rename(
        descriptor, os.fsencode(source), descriptor,
        os.fsencode(destination), 1,  # Linux RENAME_NOREPLACE.
    )
    if result != 0:
        raise OSError(ctypes.get_errno(), "Core export set rename failed.")


def _path(value):
    text = os.fspath(value)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("A Core export pathname is empty or invalid.")
    return os.path.abspath(text)


def _inspect_name(descriptor, name):
    try:
        return os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


class CoreLayoutExportSetFiles:
    """Own unpublished files and publish their directory once.

    Construction performs no I/O. Published or uncertain state is retained.
    """

    def __init__(self):
        self._area = None
        self._expected = {}
        self._completed = set()
        self._manifest_path = ""
        self._output_directory = ""
        self._opened = False
        self._closed = False
        self._attempted = False
        self._published = False
        self._publication_state = "not-published"

    @property
    def output_directory(self):
        """Return the planned final directory, including before publication."""
        return self._output_directory

    @property
    def published(self):
        """Return whether publication of the complete set was confirmed."""
        return self._published

    @property
    def publication_state(self):
        """Return not-published, published or uncertain without I/O."""
        return self._publication_state

    def open(self, plan, parent):
        """Validate a preplanned child and acquire a private sibling stage."""
        if self._opened:
            raise RuntimeError("A Core export set adapter cannot be reopened.")
        self._opened = True
        parent = _path(parent)
        child = _path(plan["output_directory"])
        name = os.path.basename(child)
        if os.path.dirname(child) != parent or name.startswith("."):
            raise ValueError("The Core export must use a new visible child.")
        if not plan["tasks"]:
            raise ValueError("The Core export set contains no output tasks.")
        paths = [_path(task["path"]) for task in plan["tasks"]]
        manifest = plan.get("manifest_path")
        if manifest:
            self._manifest_path = _path(manifest)
            paths.append(self._manifest_path)
        if len(paths) != len(set(paths)):
            raise ValueError("The Core export contains duplicate final paths.")
        if any(os.path.dirname(path) != child for path in paths):
            raise ValueError("Every Core export must use the planned child.")
        self._expected = {path: os.path.basename(path) for path in paths}
        self._output_directory = child
        self._area = {
            "parent": parent, "parent_fd": None, "parent_identity": None,
            "final_name": name, "stage_name": "", "stage_fd": None,
            "stage_identity": None, "files": {},
        }
        area = self._area
        area["parent_fd"] = os.open(
            parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        area["parent_identity"] = _identity(os.fstat(area["parent_fd"]))
        mount_id = _require_ext4(area["parent_fd"])
        self._require_parent()
        if _inspect_name(area["parent_fd"], name) is not None:
            raise FileExistsError("The Core export directory already exists.")
        area["stage_name"] = (
            ".tracktemplate_core_export_set_" + uuid.uuid4().hex
        )
        os.mkdir(area["stage_name"], mode=0o700, dir_fd=area["parent_fd"])
        info = os.stat(
            area["stage_name"], dir_fd=area["parent_fd"],
            follow_symlinks=False,
        )
        area["stage_fd"] = os.open(
            area["stage_name"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=area["parent_fd"],
        )
        if _identity(info) != _identity(os.fstat(area["stage_fd"])):
            raise RuntimeError("Core export staging ownership is uncertain.")
        area["stage_identity"] = _identity(info)
        if (
            info.st_dev != area["parent_identity"][0]
            or _mount_id(area["stage_fd"]) != mount_id
        ):
            raise RuntimeError("Core export staging is on a different mount.")
        self._require_stage()

    def _require_parent(self):
        area = self._area
        info = os.stat(area["parent"], follow_symlinks=False)
        if (
            not stat.S_ISDIR(info.st_mode)
            or _identity(info) != area["parent_identity"]
            or _identity(os.fstat(area["parent_fd"]))
            != area["parent_identity"]
        ):
            raise RuntimeError("The selected Core export directory changed.")

    def _require_stage(self):
        self._require_parent()
        area = self._area
        info = _inspect_name(area["parent_fd"], area["stage_name"])
        if (
            info is None or not stat.S_ISDIR(info.st_mode)
            or _identity(info) != area["stage_identity"]
            or _identity(os.fstat(area["stage_fd"]))
            != area["stage_identity"]
        ):
            raise RuntimeError(
                "The owned Core export staging directory changed."
            )

    def _remember_file(self, name):
        self._require_stage()
        info = _inspect_name(self._area["stage_fd"], name)
        if info is None:
            return
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError(
                "A staged Core export is not an owned regular file."
            )
        self._area["files"][name] = _identity(info)

    def _validate_members(self):
        area = self._area
        expected = set(self._expected.values())
        if (
            self._completed != expected
            or set(os.listdir(area["stage_fd"])) != expected
        ):
            raise ValueError(
                "The complete Core export inventory is missing or changed."
            )
        for name in expected:
            info = _inspect_name(area["stage_fd"], name)
            if (
                info is None or not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1 or info.st_size <= 0
                or _identity(info) != area["files"].get(name)
            ):
                raise ValueError(
                    "A staged Core export is missing, changed or empty."
                )

    def stage(self, final_path, writer, *, manifest=False):
        """Write a member and retain its ownership on writer failure."""
        if self._closed or self._attempted:
            raise RuntimeError("The Core export set no longer accepts files.")
        final_path = _path(final_path)
        if final_path not in self._expected:
            raise ValueError("The Core export member is not in the plan.")
        if bool(manifest) != (final_path == self._manifest_path):
            raise ValueError(
                "The Core export manifest flag differs from the plan."
            )
        self._require_stage()
        area = self._area
        name = self._expected[final_path]
        if _inspect_name(area["stage_fd"], name) is not None:
            raise FileExistsError(
                "A Core export staging member already exists."
            )
        path = os.path.join(area["parent"], area["stage_name"], name)
        try:
            writer(path)
        except BaseException as error:
            try:
                self._remember_file(name)
            except Exception as inspection_error:
                error.add_note("Staging inspection: {}: {}".format(
                    path, inspection_error,
                ))
            raise
        self._remember_file(name)
        info = _inspect_name(area["stage_fd"], name)
        if info is None or info.st_size <= 0:
            raise ValueError("A staged Core export is missing or empty.")
        self._completed.add(name)

    def validate(self):
        """Require all planned files and no unplanned or changed entries."""
        if self._closed or self._attempted:
            raise RuntimeError("The Core export set is no longer preparable.")
        self._require_stage()
        self._validate_members()

    def _publication_note(self):
        area = self._area
        return "Core export publication {}: {}; staging: {}".format(
            self._publication_state, self._output_directory,
            os.path.join(area["parent"], area["stage_name"]),
        )

    def _reconcile_publication(self):
        self._require_parent()
        area = self._area
        source = _inspect_name(area["parent_fd"], area["stage_name"])
        final = _inspect_name(area["parent_fd"], area["final_name"])
        source_owned = (
            source is not None and stat.S_ISDIR(source.st_mode)
            and _identity(source) == area["stage_identity"]
        )
        final_owned = (
            final is not None and stat.S_ISDIR(final.st_mode)
            and _identity(final) == area["stage_identity"]
        )
        if final_owned and source is None:
            self._validate_members()
            self._published = True
            self._publication_state = "published"
        elif source_owned and not final_owned:
            self._publication_state = "not-published"

    def publish(self):
        """Publish the complete directory once; preserve ambiguous residue."""
        if self._attempted:
            raise RuntimeError(
                "Core export publication was already attempted."
            )
        self.validate()
        self._attempted = True
        self._publication_state = "uncertain"
        area = self._area
        try:
            _rename_noreplace(
                area["parent_fd"], area["stage_name"], area["final_name"],
            )
        except BaseException as error:
            try:
                self._reconcile_publication()
            except Exception as inspection_error:
                error.add_note("Publication inspection: {}".format(
                    inspection_error,
                ))
            error.add_note(self._publication_note())
            raise
        self._published = True
        self._publication_state = "published"
        self._require_parent()
        final = _inspect_name(area["parent_fd"], area["final_name"])
        if (
            final is None or not stat.S_ISDIR(final.st_mode)
            or _identity(final) != area["stage_identity"]
            or _inspect_name(area["parent_fd"], area["stage_name"]) is not None
        ):
            raise RuntimeError("The published Core export directory changed.")
        self._validate_members()

    def cleanup(self):
        """Remove owned unpublished members and close descriptors once."""
        if self._closed or self._area is None:
            return []
        self._closed = True
        area = self._area
        errors = []
        try:
            if self._publication_state == "uncertain":
                errors.append(self._publication_note())
            elif not self._published and area["stage_name"]:
                self._require_stage()
                for name, identity in area["files"].items():
                    self._require_stage()
                    info = _inspect_name(area["stage_fd"], name)
                    if info is None:
                        continue
                    if (
                        not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                        or _identity(info) != identity
                    ):
                        errors.append(
                            "Changed staging member preserved: " + name
                        )
                        continue
                    try:
                        os.unlink(name, dir_fd=area["stage_fd"])
                    except OSError as error:
                        errors.append("Staging member retained: {}: {}".format(
                            name, error,
                        ))
                self._require_stage()
                if os.listdir(area["stage_fd"]):
                    errors.append(
                        "Unremoved staging entries preserved: {}".format(
                            os.path.join(area["parent"], area["stage_name"]),
                        )
                    )
                else:
                    os.rmdir(area["stage_name"], dir_fd=area["parent_fd"])
        except Exception as error:
            errors.append("Core export staging preserved: {}: {}".format(
                os.path.join(area["parent"], area["stage_name"]), error,
            ))
        finally:
            for key in ("stage_fd", "parent_fd"):
                descriptor = area[key]
                area[key] = None
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError as error:
                        errors.append(
                            "Core export descriptor cleanup: {}".format(error)
                        )
        return errors
