"""Offline protection checks for private inputs and readable evidence."""

import copy
import hashlib
import io
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import l1_private_payload as payload  # noqa: E402


class PayloadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="l1-dummy-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = {"schema": 1, "inputs": [], "controls": []}
        for group, names in (("inputs", payload.INPUT_IDS),
                             ("controls", payload.REQUIRED_CONTROLS)):
            for name in names:
                path = self.root / name
                content = ("private-dummy-" + name).encode()
                path.write_bytes(content)
                path.chmod(0o600)
                self.manifest[group].append({
                    "id": name, "member": payload.member_name(group, name),
                    "path": str(path), "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                })

    def archive(self):
        target = self.root / "inputs.tar"
        payload.create_archive(self.manifest, target)
        return target

    def malicious_archive(self, member, content=b"bad", kind=None):
        target = self.root / "malicious.tar"
        with tarfile.open(target, "w") as archive:
            info = tarfile.TarInfo(member)
            info.size = len(content)
            if kind is not None:
                info.type = kind
                info.linkname = "../../outside"
                info.size = 0
            archive.addfile(info, io.BytesIO(content))
        return target

    def test_exact_roundtrip_and_restrictive_modes(self):
        archive = self.archive()
        receipt = payload.file_identity(archive)
        self.assertEqual(receipt["bytes"], archive.stat().st_size)
        self.assertEqual(payload.read_manifest(archive), self.manifest)
        destination = self.root / "unpacked"
        result = payload.extract_archive(archive, self.manifest, destination)
        self.assertEqual(set(result), {
            item["id"] for group in ("inputs", "controls")
            for item in self.manifest[group]
        })
        for group in ("inputs", "controls"):
            for item in self.manifest[group]:
                path = result[item["id"]]
                self.assertEqual(path.read_bytes(),
                                 Path(item["path"]).read_bytes())
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o700)

    def test_readable_evidence_route_has_no_owner_key_requirement(self):
        self.assertEqual(set(payload.REQUIRED_CONTROLS),
                         {"run-config", "recovery"})
        self.assertFalse(hasattr(payload, "encrypt_evidence"))
        payload.validate_manifest(self.manifest)
        with self.assertRaises(payload.PayloadError):
            payload.member_name("controls", "owner-public-key")

    def test_pack_rejects_changed_input_and_preserves_existing_output(self):
        first = self.manifest["inputs"][0]
        Path(first["path"]).write_text("changed")
        with self.assertRaises(payload.PayloadError):
            self.archive()
        existing = self.root / "existing"
        existing.write_text("preserve")
        with self.assertRaises(payload.PayloadError):
            payload.create_archive(self.manifest, existing)
        self.assertEqual(existing.read_text(), "preserve")

    def test_pack_rejects_symlink_and_incomplete_allowlist(self):
        first = self.manifest["inputs"][0]
        link = self.root / "linked"
        link.symlink_to(first["path"])
        first["path"] = str(link)
        with self.assertRaises(payload.PayloadError):
            self.archive()
        self.manifest["inputs"].pop()
        with self.assertRaises(payload.PayloadError):
            payload.validate_manifest(self.manifest)

    def test_rejects_traversal_absolute_links_and_unknown_members(self):
        for index, (name, kind) in enumerate((
            ("../escape", None), ("/absolute", None),
            ("inputs/catalogue", tarfile.SYMTYPE),
            ("inputs/catalogue", tarfile.LNKTYPE), ("unexpected", None),
        )):
            with self.subTest(name=name, kind=kind):
                source = self.malicious_archive(name, kind=kind)
                with self.assertRaises(payload.PayloadError):
                    payload.extract_archive(
                        source, self.manifest, self.root / f"out-{index}",
                    )
        self.assertFalse((self.root / "escape").exists())

    def test_rejects_duplicate_members_and_wrong_size(self):
        source = self.archive()
        first = self.manifest["inputs"][0]
        bad = copy.deepcopy(self.manifest)
        bad["inputs"][0]["bytes"] += 1
        with self.assertRaises(payload.PayloadError):
            payload.extract_archive(source, bad, self.root / "size")
        with tarfile.open(source, "a") as archive:
            info = tarfile.TarInfo(first["member"])
            info.size = first["bytes"]
            archive.addfile(info, io.BytesIO(Path(first["path"]).read_bytes()))
        with self.assertRaises(payload.PayloadError):
            payload.extract_archive(source, self.manifest, self.root / "dup")

    def test_rejects_hash_mismatch_and_existing_extraction_root(self):
        source = self.archive()
        bad = copy.deepcopy(self.manifest)
        bad["inputs"][0]["sha256"] = "0" * 64
        with self.assertRaises(payload.PayloadError):
            payload.extract_archive(source, bad, self.root / "hash")
        with self.assertRaises(payload.PayloadError):
            payload.extract_archive(source, self.manifest, self.root)

    def test_control_bounds_and_manifest_shape(self):
        for edit in (
            lambda data: data.update(extra="private"),
            lambda data: data["inputs"][0].update(member="../escape"),
            lambda data: data["controls"][0].update(bytes=2 ** 20 + 1),
            lambda data: data["inputs"][0].update(bytes=True),
        ):
            with self.subTest(edit=edit):
                manifest = copy.deepcopy(self.manifest)
                edit(manifest)
                with self.assertRaises(payload.PayloadError):
                    payload.validate_manifest(manifest)

    def test_public_summary_rejects_unapproved_text_and_nonfinite_metrics(self):
        summary = payload.empty_public_summary("a" * 40, "b" * 40, 1, 1,
                                               "readiness")
        self.assertEqual(payload.validate_public_summary(summary), summary)
        for edit in (
            lambda data: data.update(exception="private path"),
            lambda data: data.update(outcome="private detail"),
            lambda data: data["timings_seconds"].update(total=float("nan")),
            lambda data: data["counts"].update(private_name=1),
            lambda data: data["flags"].update(cleanup=1),
            lambda data: data.update(outcome="PASS"),
        ):
            with self.subTest(edit=edit):
                changed = copy.deepcopy(summary)
                edit(changed)
                with self.assertRaises(payload.PayloadError):
                    payload.validate_public_summary(changed)

    def test_outer_process_failure_is_private(self):
        secret = "PRIVATE_FAILURE_MARKER"
        log = self.root / "child.log"
        output = io.StringIO()
        from contextlib import redirect_stdout, redirect_stderr
        with redirect_stdout(output), redirect_stderr(output):
            result = payload.capture_private_process(
                [sys.executable, "-c", f"raise RuntimeError('{secret}')"],
                log, {"PATH": os.environ["PATH"]}, timeout=10,
            )
        self.assertEqual(result, {"outcome": "FAILED", "returncode": 1})
        self.assertNotIn(secret, output.getvalue())
        self.assertIn(secret, log.read_text())
        missing = self.root / "missing-private-command"
        result = payload.capture_private_process(
            [str(missing)], self.root / "launch.log", {}, timeout=10,
        )
        self.assertEqual(result["outcome"], "LAUNCH_FAILED")
        self.assertIn(str(missing), (self.root / "launch.log").read_text())

    def test_public_pass_requires_all_native_counts_and_cleanup(self):
        summary = payload.empty_public_summary("a" * 40, "b" * 40, 1, 1,
                                               "native")
        summary.update(outcome="PASS")
        summary["counts"].update(
            expected_tests=1, observed_tests=1, expected_frames=150,
            observed_frames=150, expected_components=138,
            observed_components=138, successful_components=690,
            rolled_back_components=230,
        )
        summary["flags"] = dict.fromkeys(summary["flags"], True)
        summary["evidence"].update(sha256="c" * 64, bytes=100, asset_id=12)
        self.assertEqual(payload.validate_public_summary(summary), summary)
        for edit in (
            lambda data: data["counts"].update(rolled_back_components=0),
            lambda data: data["counts"].update(successful_components=230),
            lambda data: data["counts"].update(skips=1),
            lambda data: data["flags"].update(cleanup=False),
            lambda data: data["evidence"].update(bytes=0),
            lambda data: data["evidence"].update(asset_id=0),
            lambda data: data["evidence"].update(url="private-url"),
        ):
            with self.subTest(edit=edit):
                changed = copy.deepcopy(summary)
                edit(changed)
                with self.assertRaises(payload.PayloadError):
                    payload.validate_public_summary(changed)

    def test_child_credentials_are_rejected_before_execution(self):
        for name in ("GITHUB_TOKEN", "L1_PRIVATE_INPUT_READ_TOKEN",
                     "L1_PRIVATE_INPUT_PASSPHRASE"):
            with self.subTest(name=name):
                with self.assertRaises(payload.PayloadError):
                    payload.capture_private_process(
                        [sys.executable, "-c", "pass"],
                        self.root / f"{name}.log", {name: "secret"}, timeout=1,
                    )


class EncryptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="l1-gpg-dummy-")
        cls.root = Path(cls.temporary.name)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=self.root)
        self.addCleanup(self.temporary.cleanup)
        self.case = Path(self.temporary.name)
        self.source = self.case / "failure.tar"
        self.source.write_bytes(b"private traceback\nfailed result\n")
        self.source.chmod(0o600)

    def passphrase_fd(self, value=b"dummy-passphrase\n"):
        read, write = os.pipe()
        os.write(write, value)
        os.close(write)
        self.addCleanup(os.close, read)
        return read

    def test_symmetric_roundtrip_and_ciphertext_tamper_rejection(self):
        encrypted = self.case / "inputs.gpg"
        identity = payload.encrypt_inputs(
            self.source, encrypted, self.passphrase_fd(),
            self.case / "encrypt.log",
        )
        decrypted = self.case / "inputs.tar"
        payload.decrypt_inputs(
            encrypted, decrypted, self.passphrase_fd(), identity["sha256"],
            identity["bytes"], self.case / "decrypt.log",
        )
        self.assertEqual(decrypted.read_bytes(), self.source.read_bytes())
        with self.assertRaises(payload.PayloadError):
            payload.decrypt_inputs(
                encrypted, self.case / "wrong.tar",
                self.passphrase_fd(b"wrong\n"), identity["sha256"],
                identity["bytes"], self.case / "wrong.log",
            )
        damaged = bytearray(encrypted.read_bytes())
        damaged[len(damaged) // 2] ^= 1
        encrypted.write_bytes(damaged)
        with self.assertRaises(payload.PayloadError):
            payload.decrypt_inputs(
                encrypted, self.case / "tampered.tar", self.passphrase_fd(),
                identity["sha256"], identity["bytes"],
                self.case / "tampered.log",
            )
        # Also reach GPG's integrity check with the damaged envelope's hash.
        damaged_identity = payload.file_identity(encrypted)
        with self.assertRaises(payload.PayloadError):
            payload.decrypt_inputs(
                encrypted, self.case / "integrity.tar", self.passphrase_fd(),
                damaged_identity["sha256"], damaged_identity["bytes"],
                self.case / "integrity.log",
            )

    def test_failed_input_encryption_never_overwrites(self):
        existing = self.case / "existing.gpg"
        existing.write_bytes(b"preserved ciphertext")
        with self.assertRaises(payload.PayloadError):
            payload.encrypt_inputs(self.source, existing, self.passphrase_fd(),
                                   self.case / "overwrite.log")
        self.assertEqual(existing.read_bytes(), b"preserved ciphertext")


if __name__ == "__main__":
    unittest.main(verbosity=2)
