#!/usr/bin/env python3
"""Observe whole-directory publication and ownership on real Linux ext4.

Payloads are synthetic. This proof establishes namespace behaviour, not CAD
format, railway, durability, restart or hostile-namespace guarantees.
"""

import errno
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.adapters.export import (  # noqa: E402
    core_layout_set as files,
)


SENTINEL = "Core export atomic filesystem validation passed"


class ControlledInterruption(BaseException):
    """An explicit callback boundary, not arbitrary bytecode interruption."""


def witness(path):
    """Record independently observable identities and content recursively."""
    result = {}
    for item in [path, *sorted(path.rglob("*"))]:
        info = item.lstat()
        value = (info.st_dev, info.st_ino, info.st_mode, info.st_size)
        if item.is_symlink():
            value += ("symlink", os.readlink(item))
        elif item.is_file():
            value += ("file", hashlib.sha256(item.read_bytes()).hexdigest())
        result[item.relative_to(path).as_posix()] = value
    return result


def collision_witness(path):
    if path.is_dir() and not path.is_symlink():
        return witness(path)
    return path.lstat()


class AtomicFilesProof(unittest.TestCase):
    def setUp(self):
        temporary_root = ROOT / "tmp"
        temporary_root.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(
            prefix="core-set-files-proof-", dir=temporary_root,
        )
        self.root = Path(self.directory.name)
        self.parent = self.root / "outputs"
        self.parent.mkdir()
        self.previous = self.parent / "prior-complete-generation"
        self.previous.mkdir()
        (self.previous / "rail.step").write_bytes(b"previous evidence\n")
        self.previous_witness = witness(self.previous)
        self.adapters = []

    def tearDown(self):
        for adapter in self.adapters:
            adapter.cleanup()
        self.assertEqual(witness(self.previous), self.previous_witness)
        self.directory.cleanup()

    def plan(self, *, manifest=True, name="Core_Export_proof"):
        child = self.parent / name
        tasks = [
            {
                "path": str(child / ("rail." + extension)),
                "format": extension,
                "records": [{"record_id": "R1", "shape": object()}],
            }
            for extension in ("svg", "step")
        ]
        return {
            "output_directory": str(child), "tasks": tasks,
            "manifest_path": str(child / "manifest.csv") if manifest else "",
            "skipped": [{"reason": "synthetic unsupported output"}],
        }

    def adapter(self, plan):
        adapter = files.CoreLayoutExportSetFiles()
        self.adapters.append(adapter)
        self.assertIsNone(adapter.open(plan, self.parent))
        self.assertFalse(Path(plan["output_directory"]).exists())
        return adapter

    def stage_all(self, adapter, plan):
        expected = {}
        for task in plan["tasks"]:
            data = ("synthetic " + task["format"] + "\n").encode()
            expected[Path(task["path"]).name] = data
            adapter.stage(task["path"], lambda path, data=data:
                          Path(path).write_bytes(data))
        if plan["manifest_path"]:
            expected["manifest.csv"] = b"record_id,path\nR1,rail.step\n"
            adapter.stage(
                plan["manifest_path"],
                lambda path: Path(path).write_bytes(expected["manifest.csv"]),
                manifest=True,
            )
        return expected

    def stage_path(self):
        found = list(self.parent.glob(".tracktemplate_core_export_set_*"))
        self.assertEqual(len(found), 1)
        return found[0]

    def assert_payloads(self, path, expected):
        self.assertEqual({p.name for p in path.iterdir()}, set(expected))
        for name, data in expected.items():
            self.assertEqual((path / name).read_bytes(), data)

    def test_constructor_has_no_filesystem_or_library_io(self):
        with (
            mock.patch.object(files.os, "open", side_effect=AssertionError),
            mock.patch.object(
                files.ctypes, "CDLL", side_effect=AssertionError,
            ),
            mock.patch("builtins.open", side_effect=AssertionError),
        ):
            adapter = files.CoreLayoutExportSetFiles()
            self.assertFalse(adapter.published)
            self.assertEqual(adapter.publication_state, "not-published")
            self.assertEqual(adapter.output_directory, "")

    def test_real_complete_publication_with_and_without_csv(self):
        for manifest in (True, False):
            with self.subTest(manifest=manifest):
                plan = self.plan(
                    manifest=manifest, name="Core_" + str(manifest),
                )
                original_paths = [t["path"] for t in plan["tasks"]]
                records = [t["records"] for t in plan["tasks"]]
                tasks = list(plan["tasks"])
                adapter = self.adapter(plan)
                expected = self.stage_all(adapter, plan)
                stage = self.stage_path()
                stage_identity = (stage.stat().st_dev, stage.stat().st_ino)
                target = Path(plan["output_directory"])
                rename = files._rename_noreplace

                def observe(descriptor, source, destination):
                    self.assertFalse(target.exists())
                    self.assert_payloads(stage, expected)
                    rename(descriptor, source, destination)
                    self.assert_payloads(target, expected)

                with (
                    mock.patch.object(files, "_rename_noreplace", observe),
                    mock.patch.object(
                        files.os, "replace", side_effect=AssertionError,
                    ),
                    mock.patch.object(
                        files.os, "rename", side_effect=AssertionError,
                    ),
                    mock.patch.object(
                        files.os, "link", side_effect=AssertionError,
                    ),
                ):
                    adapter.validate()
                    adapter.publish()
                self.assertTrue(adapter.published)
                self.assertEqual(adapter.publication_state, "published")
                self.assertEqual(adapter.output_directory, str(target))
                self.assertEqual(
                    (target.stat().st_dev, target.stat().st_ino),
                    stage_identity,
                )
                self.assertFalse(stage.exists())
                before_cleanup = witness(target)
                self.assertEqual(adapter.cleanup(), [])
                self.assertEqual(witness(target), before_cleanup)
                self.assertEqual(original_paths, [t["path"] for t in tasks])
                for index, task in enumerate(plan["tasks"]):
                    self.assertIs(task, tasks[index])
                    self.assertIs(task["records"], records[index])
                with self.assertRaises(RuntimeError):
                    adapter.publish()

    def test_invalid_plans_acquire_no_stage(self):
        cases = ("outside-child", "hidden-child", "outside-member",
                 "duplicate", "manifest-duplicate", "dependency-duplicate",
                 "dependency-outside", "no-tasks")
        for case in cases:
            with self.subTest(case=case):
                plan = self.plan()
                if case == "outside-child":
                    plan["output_directory"] = str(self.root / "outside")
                elif case == "hidden-child":
                    plan["output_directory"] = str(self.parent / ".hidden")
                elif case == "outside-member":
                    plan["tasks"][0]["path"] = str(self.root / "outside.svg")
                elif case == "duplicate":
                    plan["tasks"][1]["path"] = plan["tasks"][0]["path"]
                elif case == "manifest-duplicate":
                    plan["manifest_path"] = plan["tasks"][0]["path"]
                elif case == "dependency-duplicate":
                    plan["dependency_manifest_path"] = plan["manifest_path"]
                elif case == "dependency-outside":
                    plan["dependency_manifest_path"] = str(self.root / "outside.json")
                else:
                    plan["tasks"] = []
                adapter = files.CoreLayoutExportSetFiles()
                self.adapters.append(adapter)
                with self.assertRaises(ValueError):
                    adapter.open(plan, self.parent)
                self.assertEqual(adapter.cleanup(), [])
                self.assertEqual(list(self.parent.glob(".*")), [])

    def test_open_rejects_existing_destination(self):
        for kind in ("empty", "nonempty", "file", "symlink"):
            with self.subTest(kind=kind):
                plan = self.plan(name="existing_" + kind)
                target = Path(plan["output_directory"])
                self.make_collision(target, kind)
                before = collision_witness(target)
                adapter = files.CoreLayoutExportSetFiles()
                self.adapters.append(adapter)
                with self.assertRaises(FileExistsError):
                    adapter.open(plan, self.parent)
                self.assertEqual(adapter.cleanup(), [])
                after = collision_witness(target)
                self.assertEqual(before, after)

    def make_collision(self, target, kind):
        if kind in ("empty", "nonempty"):
            target.mkdir()
            if kind == "nonempty":
                (target / "foreign").write_bytes(b"keep foreign bytes")
        elif kind == "file":
            target.write_bytes(b"foreign file")
        else:
            target.symlink_to(self.previous, target_is_directory=True)

    def test_real_late_collision_never_replaces_any_destination(self):
        for kind in ("empty", "nonempty", "file", "symlink"):
            with self.subTest(kind=kind):
                plan = self.plan(name="late_" + kind)
                adapter = self.adapter(plan)
                self.stage_all(adapter, plan)
                target = Path(plan["output_directory"])
                self.make_collision(target, kind)
                before = witness(self.parent)
                with self.assertRaises(OSError) as raised:
                    adapter.publish()
                self.assertEqual(raised.exception.errno, errno.EEXIST)
                self.assertFalse(adapter.published)
                self.assertEqual(adapter.publication_state, "not-published")
                self.assertEqual(witness(self.parent), before)
                self.assertEqual(adapter.cleanup(), [])
                self.assertTrue(target.exists())

    def test_preparation_failure_and_explicit_interruption(self):
        for error in (
            RuntimeError("writer failed"), ControlledInterruption("stop"),
        ):
            with self.subTest(error=type(error).__name__):
                plan = self.plan()
                adapter = self.adapter(plan)

                def fail(path):
                    Path(path).write_bytes(b"partial")
                    raise error

                with self.assertRaises(type(error)) as raised:
                    adapter.stage(plan["tasks"][0]["path"], fail)
                self.assertIs(raised.exception, error)
                self.assertFalse(Path(plan["output_directory"]).exists())
                self.assertEqual(adapter.cleanup(), [])
                self.assertEqual(list(self.parent.glob(".*")), [])

    def test_missing_empty_and_nonregular_payloads(self):
        for kind in ("missing", "empty", "directory", "symlink", "hardlink"):
            with self.subTest(kind=kind):
                plan = self.plan(name="bad_" + kind)
                adapter = self.adapter(plan)

                def write(path):
                    path = Path(path)
                    if kind == "empty":
                        path.touch()
                    elif kind == "directory":
                        path.mkdir()
                    elif kind == "symlink":
                        path.symlink_to(self.previous / "rail.step")
                    elif kind == "hardlink":
                        os.link(self.previous / "rail.step", path)

                with self.assertRaises(ValueError):
                    adapter.stage(plan["tasks"][0]["path"], write)
                stage = self.stage_path()
                errors = adapter.cleanup()
                if kind in ("directory", "symlink", "hardlink"):
                    self.assertTrue(errors)
                    self.assertTrue(stage.exists())
                    # Remove the disposable fixture after preservation proof.
                    entry = stage / "rail.svg"
                    entry.rmdir() if kind == "directory" else entry.unlink()
                    stage.rmdir()
                else:
                    self.assertEqual(errors, [])
                    self.assertFalse(stage.exists())

    def test_inventory_is_the_complete_plan(self):
        for omitted in ("task", "csv"):
            with self.subTest(omitted=omitted):
                plan = self.plan()
                adapter = self.adapter(plan)
                for task in plan["tasks"][:1 if omitted == "task" else 2]:
                    adapter.stage(
                        task["path"],
                        lambda path: Path(path).write_bytes(b"x"),
                    )
                with self.assertRaises(ValueError):
                    adapter.publish()
                self.assertFalse(Path(plan["output_directory"]).exists())
                self.assertEqual(adapter.cleanup(), [])

    def test_unplanned_member_is_preserved(self):
        plan = self.plan()
        adapter = self.adapter(plan)
        self.stage_all(adapter, plan)
        stage = self.stage_path()
        foreign = stage / "foreign.bin"
        foreign.write_bytes(b"unowned")
        before = foreign.stat()
        with self.assertRaises(ValueError):
            adapter.publish()
        self.assertTrue(adapter.cleanup())
        self.assertEqual(foreign.stat(), before)
        self.assertEqual(foreign.read_bytes(), b"unowned")

    def test_changed_member_and_hardlink_are_preserved(self):
        for change in ("replacement", "hardlink"):
            with self.subTest(change=change):
                plan = self.plan(name="changed_" + change)
                adapter = self.adapter(plan)
                self.stage_all(adapter, plan)
                stage = self.stage_path()
                member = stage / "rail.svg"
                if change == "replacement":
                    member.rename(self.root / "original.svg")
                    member.write_bytes(b"replacement")
                else:
                    os.link(member, self.root / "linked.svg")
                before = member.stat()
                with self.assertRaises(ValueError):
                    adapter.publish()
                self.assertTrue(adapter.cleanup())
                self.assertEqual(member.stat(), before)
                member.unlink()
                stage.rmdir()

    def test_parent_and_stage_substitution_preserve_foreign_state(self):
        plan = self.plan()
        adapter = self.adapter(plan)
        self.stage_all(adapter, plan)
        stage = self.stage_path()
        moved = self.root / "moved-stage"
        stage.rename(moved)
        stage.mkdir()
        (stage / "foreign").write_bytes(b"preserve")
        moved_before, foreign_before = witness(moved), witness(stage)
        with self.assertRaises(RuntimeError):
            adapter.publish()
        self.assertTrue(adapter.cleanup())
        self.assertEqual(witness(moved), moved_before)
        self.assertEqual(witness(stage), foreign_before)

        stage.joinpath("foreign").unlink()
        stage.rmdir()
        second = self.adapter(self.plan(name="second"))
        self.stage_all(second, self.plan(name="second"))
        moved_parent = self.root / "moved-parent"
        self.parent.rename(moved_parent)
        self.parent.mkdir()
        foreign_before = witness(self.parent)
        with self.assertRaises(RuntimeError):
            second.publish()
        self.assertTrue(second.cleanup())
        self.assertEqual(witness(self.parent), foreign_before)
        self.parent.rmdir()
        moved_parent.rename(self.parent)

    def test_unsupported_primitive_has_no_fallback(self):
        for code in (errno.ENOSYS, errno.EOPNOTSUPP, errno.EXDEV):
            with self.subTest(errno=code):
                plan = self.plan()
                adapter = self.adapter(plan)
                self.stage_all(adapter, plan)
                error = OSError(code, "unsupported injected primitive")
                with mock.patch.object(
                    files, "_rename_noreplace", side_effect=error,
                ):
                    with self.assertRaises(OSError) as raised:
                        adapter.publish()
                self.assertIs(raised.exception, error)
                self.assertFalse(adapter.published)
                self.assertFalse(Path(plan["output_directory"]).exists())
                self.assertEqual(adapter.cleanup(), [])

    def test_primitive_error_after_publication_is_reconciled(self):
        for error in (
            RuntimeError("after commit"),
            ControlledInterruption("after commit"),
        ):
            with self.subTest(error=type(error).__name__):
                plan = self.plan(name="after_" + type(error).__name__)
                adapter = self.adapter(plan)
                expected = self.stage_all(adapter, plan)
                rename = files._rename_noreplace

                def commit_then_raise(*args):
                    rename(*args)
                    raise error

                with mock.patch.object(
                    files, "_rename_noreplace", commit_then_raise,
                ):
                    with self.assertRaises(type(error)) as raised:
                        adapter.publish()
                self.assertIs(raised.exception, error)
                self.assertTrue(adapter.published)
                self.assertEqual(adapter.publication_state, "published")
                self.assertIn(
                    plan["output_directory"], " ".join(error.__notes__),
                )
                target = Path(plan["output_directory"])
                before = witness(target)
                self.assertEqual(adapter.cleanup(), [])
                self.assertEqual(witness(target), before)
                self.assert_payloads(target, expected)

    def test_primitive_interruption_before_publication(self):
        plan = self.plan()
        adapter = self.adapter(plan)
        self.stage_all(adapter, plan)
        error = ControlledInterruption("before commit")
        with mock.patch.object(files, "_rename_noreplace", side_effect=error):
            with self.assertRaises(ControlledInterruption) as raised:
                adapter.publish()
        self.assertIs(raised.exception, error)
        self.assertEqual(adapter.publication_state, "not-published")
        self.assertEqual(adapter.cleanup(), [])

    def test_uncertain_publication_preserves_every_observed_name(self):
        plan = self.plan()
        adapter = self.adapter(plan)
        self.stage_all(adapter, plan)
        stage = self.stage_path()
        moved = self.root / "unresolved-stage"
        error = RuntimeError("uncertain syscall outcome")

        def replace_source(*args):
            stage.rename(moved)
            stage.mkdir()
            (stage / "foreign").write_bytes(b"foreign")
            raise error

        with mock.patch.object(files, "_rename_noreplace", replace_source):
            with self.assertRaises(RuntimeError) as raised:
                adapter.publish()
        self.assertIs(raised.exception, error)
        self.assertEqual(adapter.publication_state, "uncertain")
        self.assertFalse(adapter.published)
        before = witness(self.root)
        diagnostics = adapter.cleanup()
        self.assertEqual(witness(self.root), before)
        self.assertIn(str(stage), " ".join(diagnostics))
        self.assertIn(plan["output_directory"], " ".join(diagnostics))

    def test_post_commit_faults_keep_publication(self):
        plan = self.plan()
        adapter = self.adapter(plan)
        self.stage_all(adapter, plan)
        validate = adapter._validate_members
        count = 0

        def fail_after_commit():
            nonlocal count
            count += 1
            if count == 2:
                raise RuntimeError("post-publication inspection failed")
            validate()

        with mock.patch.object(
            adapter, "_validate_members", fail_after_commit,
        ):
            with self.assertRaisesRegex(RuntimeError, "post-publication"):
                adapter.publish()
        self.assertTrue(adapter.published)
        target = Path(plan["output_directory"])
        before = witness(target)
        close = os.close

        def fail_close(descriptor):
            close(descriptor)
            raise OSError("controlled descriptor cleanup")

        with mock.patch.object(files.os, "close", fail_close):
            diagnostics = adapter.cleanup()
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual(witness(target), before)
        self.assertTrue(adapter.published)
        self.assertEqual(adapter.publication_state, "published")
        self.assertEqual(adapter.cleanup(), [])

    def test_unlink_failure_retains_owned_unpublished_stage(self):
        plan = self.plan()
        adapter = self.adapter(plan)
        self.stage_all(adapter, plan)
        stage = self.stage_path()
        before = witness(stage)
        with mock.patch.object(
            files.os, "unlink", side_effect=OSError("unlink fault"),
        ):
            diagnostics = adapter.cleanup()
        self.assertTrue(diagnostics)
        self.assertEqual(witness(stage), before)
        self.assertFalse(adapter.published)

    def test_non_ext4_mount_is_rejected_before_stage(self):
        if not Path("/dev/shm").is_dir():
            self.fail("The Linux tmpfs rejection fixture is unavailable.")
        with tempfile.TemporaryDirectory(
            prefix="core-set-reject-", dir="/dev/shm",
        ) as name:
            parent = Path(name)
            plan = self.plan()
            child = parent / "Core_rejected"
            plan["output_directory"] = str(child)
            for task in plan["tasks"]:
                task["path"] = str(child / Path(task["path"]).name)
            plan["manifest_path"] = str(child / "manifest.csv")
            adapter = files.CoreLayoutExportSetFiles()
            self.adapters.append(adapter)
            with self.assertRaisesRegex(RuntimeError, "qualified ext4"):
                adapter.open(plan, parent)
            self.assertEqual(adapter.cleanup(), [])
            self.assertEqual(list(parent.iterdir()), [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AtomicFilesProof)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
