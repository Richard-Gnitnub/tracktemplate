"""Offline checks for the exact compatibility publication boundary."""

import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import compatibility_evidence_output as output  # noqa: E402

CAPSULE = ROOT / "tests/fixtures/compatibility-evidence-scope.json"
ASSESSMENT = "tests/compatibility_assessment_fixture.py"
ASSESSMENT_BYTES = (
    b"def run():\n"
    b'    assert False, "source assertion failed"\n'
    b'    raise RuntimeError("source runtime failed")\n'
)
ASSESSMENT_SHA256 = hashlib.sha256(ASSESSMENT_BYTES).hexdigest()


def chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def png():
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\0\xff\0\0\0\0\xff"))
        + chunk(b"IEND", b"")
    )


class EvidenceOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.approved_scope = output.load_scope_capsule(CAPSULE, ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="compatibility-output-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "evidence"
        self.source.mkdir(mode=0o700)
        self.destination = self.root / "published"
        assessment = self.root / "assessment.py"
        assessment.write_bytes(ASSESSMENT_BYTES)
        self.scope = self.approved_scope
        for group in self.scope.groups:
            self.scope = output.bind_assessment_source(
                self.scope,
                group,
                ASSESSMENT,
                assessment,
                ASSESSMENT_SHA256,
            )

    def observation(self, group_id="readiness"):
        group = self.scope.groups[group_id]
        value = {
            "status": "PASS",
            "assessment_entry_sha256": ASSESSMENT_SHA256,
            "runtime": copy.deepcopy(output.RUNTIME),
            "sentinel": group.sentinel,
            "returncode": 0,
            "sessions": group.sessions,
            "inputs": [
                {
                    "id": "approved-base",
                    "sha256": output.BASE_SHA256,
                    "bytes": output.BASE_BYTES,
                }
            ],
            "document_preservation": {
                "source_sha256_before": output.BASE_SHA256,
                "source_sha256_after": output.BASE_SHA256,
                "original_unchanged": True,
                "copy_only": True,
                "object_count_before": 9,
                "object_count_after": 9,
                "undo": "NOT_APPLICABLE",
                "redo": "NOT_APPLICABLE",
                "save_reopen": "NOT_APPLICABLE",
            },
            "cleanup": {
                "owned_pids": [123],
                "remaining_pids": [],
                "complete": True,
            },
            "failure": None,
        }
        if group_id == "readiness":
            value.update(
                pre_geometry_readiness=True,
                source_copy_only=True,
                geometry_builds=0,
                renderer={
                    "gui_up": True,
                    "widget_valid": True,
                    "platform": "xcb",
                    "vendor": "Mesa/X.org",
                    "renderer": "llvmpipe (LLVM 20.1.8, 256 bits)",
                    "version": "4.5 (Compatibility Profile) Mesa 25.2.8",
                },
            )
        if group_id == "straight-generation":
            value.update(
                macro_sha256="a" * 64,
                generated_document={
                    "id": "b14-long-straight-generated.FCStd",
                    "sha256": "b" * 64,
                    "bytes": 700000,
                },
                comparison_witness_sha256="496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d",
                source_document_semantic_sha256="80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5",
                timings={"generation": 1.0, "save_reopen": 0.5},
                straight_checks=dict.fromkeys(
                    (
                        "length_1500_mm",
                        "length_450_mm",
                        "curve_preserved",
                        "history_preserved",
                        "semantic_save_reopen",
                    ),
                    True,
                ),
            )
        return value

    def write_images(self, group_id):
        for member in self.scope.groups[group_id].images:
            path = self.source / member
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png())

    def write_result(self, group_id, observation):
        result = output.build_result(
            self.scope,
            group_id,
            observation,
            self.source,
        )
        target = self.source / self.scope.groups[group_id].result
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2) + "\n")
        return result

    def seal(self, observations):
        return output.seal_outputs(
            self.scope,
            self.source,
            self.destination,
            list(observations),
            observations,
        )

    def failure(self, group_id="readiness", reason="source assertion failed"):
        observation = self.observation(group_id)
        observation.update(status="FAIL", sentinel="", returncode=1)
        observation["failure"] = {
            "exception_type": "AssertionError",
            "source_relative_file": ASSESSMENT,
            "line": 2,
            "reason_code": "ASSERTION_FAILED",
        }
        diagnostic = (
            "Traceback (most recent call last):\n"
            f'  File "{ASSESSMENT}", line 2, in run\n'
            '    assert False, "source assertion failed"\n'
            f"AssertionError: {reason}\n"
        ).encode()
        target = self.source / self.scope.groups[group_id].failure
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(diagnostic)
        return observation, target, diagnostic

    def test_exact_capsule_and_group_counts(self):
        self.assertEqual(
            hashlib.sha256(CAPSULE.read_bytes()).hexdigest(),
            output.CAPSULE_SHA256,
        )
        self.assertEqual(len(self.scope.groups), 24)
        self.assertEqual(
            sum(len(group.images) for group in self.scope.groups.values()), 160
        )
        self.assertEqual(
            output.export_scope_capsule(self.approved_scope),
            CAPSULE.read_bytes(),
        )
        self.assertNotIn(b"/home/", CAPSULE.read_bytes())
        self.assertNotIn(b"historical", CAPSULE.read_bytes())

    def test_scope_identity_cannot_be_replaced_by_valid_json(self):
        for content in (b"{}", b" " * output.SCOPE_BYTES):
            path = self.root / "scope.json"
            path.write_bytes(content)
            with self.assertRaises(output.EvidenceError):
                output.load_scope(path, ROOT)
        path = self.root / "capsule.json"
        path.write_bytes(CAPSULE.read_bytes() + b" ")
        with self.assertRaises(output.EvidenceError):
            output.load_scope_capsule(path, ROOT)

    def test_capsule_rejects_changed_bound_source(self):
        repository = self.root / "repository"
        for relative, text in self.approved_scope.sources.items():
            path = repository / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        first = next(iter(self.approved_scope.sources))
        (repository / first).write_text("changed")
        with self.assertRaises(output.EvidenceError):
            output.load_scope_capsule(CAPSULE, repository)

    def test_all_24_result_and_160_image_paths_roundtrip(self):
        observations = {}
        for identity in self.scope.groups:
            self.write_images(identity)
            observation = self.observation(identity)
            self.write_result(identity, observation)
            observations[identity] = observation
        inventory = self.seal(observations)
        self.assertEqual(len(inventory), 184)
        self.assertEqual(sum(name.endswith(".png") for name in inventory), 160)
        for name, identity in inventory.items():
            source = (self.source / name).read_bytes()
            published = (self.destination / name).read_bytes()
            self.assertEqual(source, published)
            self.assertEqual(
                identity["sha256"], hashlib.sha256(source).hexdigest()
            )
            self.assertEqual(
                (self.destination / name).stat().st_mode & 0o777, 0o600
            )
        result = json.loads(
            (self.destination / "gui/readiness/result.json").read_text()
        )
        self.assertEqual(result["images"][0]["width"], 2)
        self.assertEqual(result["images"][0]["height"], 1)

    def test_pass_needs_every_exact_group_image(self):
        with self.assertRaises(output.EvidenceError):
            self.write_result("readiness", self.observation())
        self.write_images("readiness")
        result = self.write_result("readiness", self.observation())
        self.assertEqual(
            result["images"][0]["sha256"], hashlib.sha256(png()).hexdigest()
        )

    def test_mesa_git_suffix_seals_exact_version_and_rejects_other_text(self):
        self.write_images("readiness")
        value = self.observation()
        version = "4.6 (Compatibility Profile) Mesa 26.2.7"
        suffix = " (git-b69adc2adf)"
        for invalid in (
            " (git-b69adc2ad)", " (git-b69adc2adff)", " (git-B69adc2adf)",
            " (git-b69adc2adz)", " (git-/home/user)", suffix + "\n",
            suffix + " token=secret", suffix + suffix,
        ):
            with self.subTest(suffix=invalid), self.assertRaisesRegex(
                output.EvidenceError, "^renderer version differs$"
            ):
                value["renderer"]["version"] = version + invalid
                self.write_result("readiness", value)
        value["renderer"]["version"] = version + suffix
        result = self.write_result("readiness", value)
        self.assertEqual(result["renderer"]["version"], version + suffix)
        self.seal({"readiness": value})
        sealed = self.destination / "gui/readiness/result.json"
        self.assertEqual(json.loads(sealed.read_bytes()), result)

    def test_source_specific_sessions_sentinel_and_readiness(self):
        self.write_images("readiness")
        for change in (
            {"sessions": 0},
            {"sentinel": ""},
            {"returncode": 1},
            {"geometry_builds": 1},
            {"pre_geometry_readiness": False},
            {"source_copy_only": False},
            {"assessment_entry_sha256": "c" * 64},
        ):
            with self.subTest(change=change):
                value = self.observation()
                value.update(change)
                with self.assertRaises(output.EvidenceError):
                    self.write_result("readiness", value)
        with self.assertRaises(output.EvidenceError):
            output.build_result(
                self.approved_scope,
                "readiness",
                self.observation(),
                self.source,
            )

    def test_nested_payloads_unknown_keys_bool_and_nonfinite_rejected(self):
        self.write_images("readiness")
        changes = (
            lambda value: value.update(raw_geometry=[1, 2, 3]),
            lambda value: value["runtime"].update(
                private_path="/home/private"
            ),
            lambda value: value["runtime"]["freecad"].__setitem__(0, True),
            lambda value: value["inputs"][0].update(path="private.FCStd"),
            lambda value: value["document_preservation"].update(vertices=[1]),
            lambda value: value["document_preservation"].update(
                object_count_before=True
            ),
            lambda value: value["cleanup"].update(credential="secret"),
            lambda value: value["cleanup"].update(owned_pids=[True]),
            lambda value: value["renderer"].update(vendor="SECRET"),
            lambda value: value["renderer"].update(version="token=secret"),
            lambda value: value.update(sessions=float("nan")),
            lambda value: value.update(geometry_builds=True),
        )
        for change in changes:
            with self.subTest(change=change):
                value = self.observation()
                change(value)
                with self.assertRaises(output.EvidenceError):
                    self.write_result("readiness", value)
        value = self.observation("straight-generation")
        value["timings"]["generation"] = float("inf")
        with self.assertRaises(output.EvidenceError):
            self.write_result("straight-generation", value)

    def test_original_safe_failure_bytes_survive(self):
        value, path, original = self.failure()
        self.write_result("readiness", value)
        inventory = self.seal({"readiness": value})
        member = self.scope.groups["readiness"].failure
        self.assertEqual((self.destination / member).read_bytes(), original)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(
            inventory[member]["sha256"], hashlib.sha256(original).hexdigest()
        )

    def test_unsafe_original_is_preserved_and_publication_refused(self):
        for reason in (
            "/home/private/operator.FCStd",
            "token=secret",
            "vertices=[(1,2,3)]",
            "unknown dynamic safe message",
        ):
            with self.subTest(reason=reason):
                value, path, original = self.failure(reason=reason)
                with self.assertRaises(output.EvidenceError):
                    self.write_result("readiness", value)
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse(self.destination.exists())

    def test_forged_traceback_paths_frames_and_lines_rejected(self):
        for replace, replacement in (
            (ASSESSMENT, "/home/private/source.py"),
            (ASSESSMENT, "../source.py"),
            ("line 2", "line 3"),
            ('    assert False, "source assertion failed"', "    SECRET"),
            ("source assertion failed\n", "source runtime failed\n"),
        ):
            with self.subTest(replacement=replacement):
                value, path, original = self.failure()
                path.write_bytes(
                    original.replace(replace.encode(), replacement.encode())
                )
                with self.assertRaises(output.EvidenceError):
                    self.write_result("readiness", value)

    def test_traceback_function_must_match_bound_executable_source(self):
        for function in ("PRIVATE_CREDENTIAL_VALUE", "<module>", "missing"):
            with self.subTest(function=function):
                value, path, original = self.failure()
                changed = original.replace(
                    b"in run\n", f"in {function}\n".encode()
                )
                path.write_bytes(changed)
                with self.assertRaises(output.EvidenceError):
                    self.write_result("readiness", value)
                self.assertEqual(path.read_bytes(), changed)
                self.assertFalse(self.destination.exists())

    def test_early_failure_does_not_invent_observations(self):
        value, _path, _original = self.failure()
        value.update(
            runtime=None,
            renderer=None,
            returncode=None,
            sessions=0,
            inputs=[],
            document_preservation=None,
            cleanup=None,
            geometry_builds=None,
            source_copy_only=None,
            pre_geometry_readiness=None,
        )
        result = self.write_result("readiness", value)
        self.assertIsNone(result["runtime"])
        self.assertIsNone(result["renderer"])
        self.assertEqual(result["images"], [])
        self.seal({"readiness": value})
        value["status"] = "PASS"
        with self.assertRaises(output.EvidenceError):
            self.write_result("readiness", value)

    def test_missing_or_unreferenced_failure_refused(self):
        value, path, _original = self.failure()
        path.unlink()
        with self.assertRaises(output.EvidenceError):
            self.write_result("readiness", value)
        value, _path, _original = self.failure()
        value["failure"] = None
        with self.assertRaises(output.EvidenceError):
            self.write_result("readiness", value)

    def test_unlisted_working_document_and_missing_result_refused(self):
        self.write_images("readiness")
        value = self.observation()
        self.write_result("readiness", value)
        excluded = self.source / "working.FCStd"
        excluded.write_bytes(b"private")
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})
        self.assertFalse(self.destination.exists())
        excluded.unlink()
        (self.source / self.scope.groups["readiness"].result).unlink()
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})

    def test_stored_result_must_equal_typed_projection(self):
        self.write_images("readiness")
        value = self.observation()
        result = self.write_result("readiness", value)
        target = self.source / self.scope.groups["readiness"].result
        for changed in (
            dict(result, schema_version=True),
            dict(result, raw={"private": "secret"}),
            dict(result, images=[dict(result["images"][0], width=999)]),
            dict(result, images=[dict(result["images"][0], sha256="0" * 64)]),
        ):
            target.write_text(json.dumps(changed))
            with self.assertRaises(output.EvidenceError):
                self.seal({"readiness": value})
        target.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})

    def test_png_type_trailer_text_crc_and_pixel_stream_rejected(self):
        self.write_images("readiness")
        path = self.source / self.scope.groups["readiness"].images[0]
        for content in (
            b"private",
            png() + b"SECRET",
            png()[:-1] + b"x",
            png()[:-12] + chunk(b"tEXt", b"SECRET") + chunk(b"IEND", b""),
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"too much private pixel data"))
            + chunk(b"IEND", b""),
        ):
            with self.subTest(content=content[:8]):
                path.write_bytes(content)
                with self.assertRaises(output.EvidenceError):
                    self.write_result("readiness", self.observation())

    def test_symlink_members_ancestors_hardlinks_and_fifo_refused(self):
        self.write_images("readiness")
        value = self.observation()
        self.write_result("readiness", value)
        image = self.source / self.scope.groups["readiness"].images[0]
        original = self.root / "original.png"
        image.rename(original)
        image.symlink_to(original)
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})
        image.unlink()
        os.link(original, image)
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})
        image.unlink()
        os.mkfifo(image)
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})
        image.unlink()
        image.write_bytes(original.read_bytes())
        linked = self.root / "linked"
        linked.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(output.EvidenceError):
            output.seal_outputs(
                self.scope,
                linked,
                self.destination,
                ["readiness"],
                {"readiness": value},
            )

    def test_existing_destination_and_source_overlap_refused(self):
        self.write_images("readiness")
        value = self.observation()
        self.write_result("readiness", value)
        self.destination.mkdir()
        marker = self.destination / "keep"
        marker.write_text("preserve")
        with self.assertRaises(output.EvidenceError):
            self.seal({"readiness": value})
        self.assertEqual(marker.read_text(), "preserve")
        with self.assertRaises(output.EvidenceError):
            output.seal_outputs(
                self.scope,
                self.source,
                self.source / "new",
                ["readiness"],
                {"readiness": value},
            )

    def test_started_group_boundary_cannot_imply_unobserved_success(self):
        self.write_images("readiness")
        value = self.observation()
        self.write_result("readiness", value)
        for groups in ([], ["readiness", "readiness"], ["native57"]):
            with self.assertRaises(output.EvidenceError):
                output.seal_outputs(
                    self.scope,
                    self.source,
                    self.destination,
                    groups,
                    {"readiness": value},
                )


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceOutputTests),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Compatibility evidence output checks passed")
