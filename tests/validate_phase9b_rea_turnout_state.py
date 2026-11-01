#!/usr/bin/env python3
"""Exercise explicit B/C intent without FreeCAD or geometry construction."""

import copy
from dataclasses import FrozenInstanceError
import hashlib
import importlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE = {
    "schema_version": 1,
    "switch_size": "B",
    "crossing_ratio": 8.0,
    "source_context": "templot-556b-rea-bh-regular-auto-fit-square-on",
    "source_archive_sha256": (
        "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
    ),
    "calculation_revision": 1,
    "track_gauge_mm": 16.5,
    "flangeway_mm": 1.0,
    "model_scale": 76.2,
}
FACING = "Facing in host travel direction"
TRAILING = "Trailing against host travel direction"
SENTINEL = "Phase 9B REA trackwork intent checks passed"


def record(kind="turnout"):
    """Literal contract fixture; no product normalization supplies values."""
    crossover = kind == "crossover"
    return {
        "schema": "tracktemplate.rea-trackwork-intent",
        "schema_version": 1,
        "intent": {
            "entity_id": "Research-XO-001" if crossover else "Research-TO-001",
            "entity_kind": kind,
            "template_set_id": "SET-001",
            "host_names": ["HostA", "HostB"] if crossover else ["HostA"],
            "source_specification": copy.deepcopy(SOURCE),
            "reference_chainage_mm": 80.0,
            "handing": "Automatic handing" if crossover else "Left-hand",
            "orientation": None if crossover else FACING,
            "arrangement": "Facing crossover" if crossover else None,
            "minimum_radius_mm": 600.0 if crossover else None,
        },
    }


def encoded(value):
    return json.dumps(value, allow_nan=False, sort_keys=True,
                      separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return "sha256:" + hashlib.sha256(encoded(value).encode()).hexdigest()


def hosts(intent):
    return [
        {"object_name": name, "template_set_id": "SET-001",
         "state_signature": "sha256:" + str(index + 1) * 64}
        for index, name in enumerate(intent.host_names)
    ]


class ReaTrackworkStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = importlib.import_module(
            "tracktemplate.application.rea_turnout_state"
        )
        cls.error = cls.subject.ReaTrackworkStateError

    def load(self, value):
        return self.subject.rea_trackwork_intent_from_json(encoded(value))

    def test_literal_roundtrip_and_immutable_complete_source(self):
        for constant, value in (
            ("REA_RECORD_TYPE_PROPERTY", "TrackTemplateReaRecordType"),
            ("REA_INTENT_JSON_PROPERTY", "TrackTemplateReaIntentJSON"),
            ("REA_HOSTS_PROPERTY", "TrackTemplateReaHosts"),
        ):
            self.assertEqual(getattr(self.subject, constant), value)
        for kind in ("turnout", "crossover"):
            with self.subTest(kind=kind):
                original = record(kind)
                intent = self.load(original)
                self.assertEqual(intent.entity_kind, kind)
                self.assertEqual(intent.host_names,
                                 tuple(original["intent"]["host_names"]))
                self.assertEqual(intent.source_specification.to_record(),
                                 SOURCE)
                self.assertEqual(
                    self.subject.rea_trackwork_intent_to_json(intent),
                    encoded(original),
                )
                with self.assertRaises(FrozenInstanceError):
                    intent.entity_id = "Changed"
                with self.assertRaises(FrozenInstanceError):
                    intent.source_specification.switch_size = "C"
                original["intent"]["host_names"][0] = "Changed"
                self.assertEqual(intent.host_names[0], "HostA")

    def test_existing_placement_tokens_and_order_are_explicit(self):
        for orientation in (FACING, TRAILING):
            for handing in ("Left-hand", "Right-hand"):
                value = record()
                value["intent"].update(orientation=orientation,
                                       handing=handing)
                self.assertEqual(self.load(value).orientation, orientation)
        for arrangement in ("Facing crossover", "Trailing crossover"):
            for handing in ("Left-hand", "Right-hand", "Automatic handing"):
                value = record("crossover")
                value["intent"].update(arrangement=arrangement,
                                       handing=handing)
                self.assertEqual(self.load(value).arrangement, arrangement)
        value = record("crossover")
        value["intent"]["host_names"].reverse()
        self.assertEqual(self.load(value).host_names, ("HostB", "HostA"))

    def test_source_requires_every_exact_contract_field(self):
        for field in SOURCE:
            with self.subTest(missing=field):
                value = record()
                del value["intent"]["source_specification"][field]
                with self.assertRaises(self.error):
                    self.load(value)
        invalid = {
            "schema_version": (True, 1.0, 2, "1"),
            "switch_size": ("A", "b", True, None),
            "crossing_ratio": (True, "8", None, 0.49, 10 ** 400),
            "source_context": (None, "square-on", "", True),
            "source_archive_sha256": ("0" * 64, None, True),
            "calculation_revision": (True, 1.0, 2, "1"),
            "track_gauge_mm": (True, "16.5", 18.83),
            "flangeway_mm": (True, "1.0", 1.1),
            "model_scale": (True, "76.2", 87.1),
        }
        for field, candidates in invalid.items():
            for candidate in candidates:
                with self.subTest(field=field, candidate=candidate):
                    value = record()
                    value["intent"]["source_specification"][field] = candidate
                    with self.assertRaises(self.error):
                        self.load(value)
        value = record()
        value["intent"]["source_specification"]["force_eq"] = False
        with self.assertRaises(self.error):
            self.load(value)

    def test_unknown_partial_legacy_and_malformed_json_are_refused(self):
        for level in ("envelope", "intent"):
            fixture = record()
            target = fixture if level == "envelope" else fixture["intent"]
            for field in tuple(target):
                value = copy.deepcopy(fixture)
                changed = value if level == "envelope" else value["intent"]
                del changed[field]
                with self.subTest(level=level, missing=field):
                    with self.assertRaises(self.error):
                        self.load(value)
            target["unknown"] = 1
            with self.assertRaises(self.error):
                self.load(fixture)
        for payload in (
            "{", "[]", "null", "true", "8", '"text"',
            '{"schema": "a", "schema": "b"}',
            encoded(record()).replace('"crossing_ratio":8.0',
                                      '"crossing_ratio":NaN'),
            encoded(record()).replace('"crossing_ratio":8.0',
                                      '"crossing_ratio":Infinity'),
            encoded(record()).replace('"crossing_ratio":8.0',
                                      '"crossing_ratio":1e400'),
            encoded(record()).replace('"switch_size":"B"',
                                      '"switch_size":"B","switch_size":"C"'),
            '{"schema_version":1,"size":"REA C10 natural",'
            '"turnout_id":"TO-001"}',
        ):
            with self.subTest(payload=payload[:70]):
                with self.assertRaises(self.error):
                    self.subject.rea_trackwork_intent_from_json(payload)
        for value in (None, b"{}", {}, True):
            with self.assertRaises(self.error):
                self.subject.rea_trackwork_intent_from_json(value)

    def test_invalid_identity_placement_and_host_cardinality(self):
        cases = {
            "entity_id": (None, "", " TO-1", True, 1),
            "entity_kind": ("TO", "other", True),
            "template_set_id": (None, "", "SET-001 ", 1),
            "host_names": ([], ["A", "B"], [""], [True], "HostA"),
            "reference_chainage_mm": (True, "80", None, -1, 10 ** 400),
            "handing": ("Automatic handing", "left", True),
            "orientation": (None, "Facing", True),
            "arrangement": ("Facing crossover", True),
            "minimum_radius_mm": (600, True),
        }
        for field, values in cases.items():
            for candidate in values:
                value = record()
                value["intent"][field] = candidate
                with self.subTest(field=field, candidate=candidate):
                    with self.assertRaises(self.error):
                        self.load(value)
        for field, candidate in (
            ("host_names", ["A"]), ("host_names", ["A", "A"]),
            ("host_names", ["A", "B", "C"]), ("orientation", FACING),
            ("arrangement", None), ("minimum_radius_mm", None),
            ("minimum_radius_mm", True), ("minimum_radius_mm", 49.999),
        ):
            value = record("crossover")
            value["intent"][field] = candidate
            with self.subTest(crossover_field=field, candidate=candidate):
                with self.assertRaises(self.error):
                    self.load(value)
        value = record("crossover")
        value["intent"]["minimum_radius_mm"] = 50
        self.assertEqual(self.load(value).minimum_radius_mm, 50.0)

    def test_constructor_refuses_mutable_or_coerced_input(self):
        intent = self.load(record())
        fields = dict(vars(intent))
        for field, candidate in (
            ("host_names", ["HostA"]),
            ("source_specification", SOURCE),
            ("reference_chainage_mm", "80"),
            ("reference_chainage_mm", float("nan")),
            ("reference_chainage_mm", float("inf")),
        ):
            bad = dict(fields, **{field: candidate})
            with self.subTest(field=field):
                with self.assertRaises(self.error):
                    self.subject.ReaTrackworkIntent(**bad)

    def test_replacement_preserves_identity_and_change_back(self):
        original = self.load(record())
        changed = record()
        changed["intent"]["source_specification"].update(
            switch_size="C", crossing_ratio=12.0,
        )
        changed["intent"].update(reference_chainage_mm=90.0,
                                 host_names=["HostB"])
        replacement = self.load(changed)
        replace = self.subject.replace_rea_trackwork_intent
        self.assertIs(replace(original, self.load(record())), original)
        self.assertIs(replace(original, replacement), replacement)
        self.assertEqual(replace(replacement, original), original)
        self.assertEqual(original.source_specification.switch_size, "B")
        for field, value in (("entity_id", "Other"),
                             ("template_set_id", "SET-002")):
            other = record()
            other["intent"][field] = value
            with self.assertRaises(self.error):
                replace(original, self.load(other))
        other = record("crossover")
        other["intent"]["entity_id"] = original.entity_id
        with self.assertRaises(self.error):
            replace(original, self.load(other))

    def test_signature_binds_complete_intent_and_recovers_change_back(self):
        intent = self.load(record())
        signature = self.subject.rea_trackwork_intent_signature
        self.assertEqual(signature(intent), digest(record()))
        for field, candidate in (
            ("reference_chainage_mm", 81.0), ("handing", "Right-hand"),
            ("orientation", TRAILING), ("host_names", ["HostB"]),
            ("entity_id", "Other"), ("template_set_id", "SET-002"),
        ):
            value = record()
            value["intent"][field] = candidate
            self.assertNotEqual(signature(intent), signature(self.load(value)))
        for field, candidate in (("switch_size", "C"),
                                 ("crossing_ratio", 8.25)):
            value = record()
            value["intent"]["source_specification"][field] = candidate
            self.assertNotEqual(signature(intent), signature(self.load(value)))
        self.assertEqual(signature(self.load(record())), signature(intent))

    def test_geometry_signature_requires_complete_ordered_bindings(self):
        intent = self.load(record("crossover"))
        host_state = hosts(intent)
        occupancy = "sha256:" + "3" * 64
        signature = self.subject.rea_trackwork_geometry_signature
        observed = signature(intent, host_state=host_state,
                             occupancy=occupancy)
        self.assertEqual(observed, digest({
            "signature_format": "tracktemplate.rea-trackwork-geometry:1",
            "intent": record("crossover"),
            "host_state": host_state,
            "occupancy": occupancy,
        }))
        changed = copy.deepcopy(host_state)
        changed[1]["state_signature"] = "sha256:" + "4" * 64
        self.assertNotEqual(observed, signature(
            intent, host_state=changed, occupancy=occupancy,
        ))
        self.assertNotEqual(observed, signature(
            intent, host_state=host_state, occupancy="sha256:" + "5" * 64,
        ))
        variants = [host_state[::-1], host_state[:1], host_state + host_state,
                    None, {}, ["HostA", "HostB"]]
        for key, candidate in (("object_name", "Other"),
                               ("template_set_id", "SET-002"),
                               ("state_signature", "short"),
                               ("state_signature", True)):
            changed = copy.deepcopy(host_state)
            changed[0][key] = candidate
            variants.append(changed)
        for key in host_state[0]:
            changed = copy.deepcopy(host_state)
            del changed[0][key]
            variants.append(changed)
        changed = copy.deepcopy(host_state)
        changed[0]["unknown"] = 1
        variants.append(changed)
        for candidate in variants:
            with self.subTest(host_state=candidate):
                with self.assertRaises(self.error):
                    signature(intent, host_state=candidate,
                              occupancy=occupancy)
        for candidate in (None, True, "", "sha256:" + "A" * 64,
                          "sha256:" + "f" * 63, {}, []):
            with self.subTest(occupancy=candidate):
                with self.assertRaises(self.error):
                    signature(intent, host_state=host_state,
                              occupancy=candidate)

    def test_structured_diagnostics_and_version_rejection(self):
        for field, candidate in (("schema", "legacy"),
                                 ("schema_version", True),
                                 ("schema_version", 1.0),
                                 ("schema_version", 2)):
            value = record()
            value[field] = candidate
            with self.assertRaises(self.error) as caught:
                self.load(value)
            diagnostic = caught.exception.diagnostic()
            self.assertTrue(diagnostic["code"])
            self.assertTrue(diagnostic["path"].startswith("$"))
            self.assertTrue(diagnostic["message"])
            self.assertTrue(diagnostic["recoverable"])
            self.assertFalse(diagnostic["document_mutation"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReaTrackworkStateTests)
    )
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
