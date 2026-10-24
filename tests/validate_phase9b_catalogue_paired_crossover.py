#!/usr/bin/env python3
"""Exercise paired-frame and refusal contracts without private geometry.

Invented records test the finite binding boundary. The separate native
proof owns actual source recipes, all twenty anchors and retained BReps.
"""

import copy
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.application.chair_pair_catalogue import (  # noqa: E402
    CONTEXT_IDS,
    prepare_paired_catalogue,
)
from tracktemplate.compatibility import chair_pair_placement as pairs  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement,
    transition_workflow,
)
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
    place_paired_chair,
)

SENTINEL = "Phase 9B paired crossover standalone validation passed"


def invented_source():
    """Make two straight hosts with twenty explicitly identified supports."""
    hosts = {}
    data = {}
    configuration = {"crossover_id": "XO-001"}
    positions, timbers = {}, []
    recipes = {}
    for side in ("A", "B"):
        name = "Host" + side
        hosts[name] = SimpleNamespace(
            Name=name, Shape=SimpleNamespace(
                isNull=lambda: False, isValid=lambda: True,
            ),
        )
        data[name] = {
            "points": [SimpleNamespace(x=0.0, y=0.0),
                       SimpleNamespace(x=1000.0, y=0.0)],
            "headings": [0.0, 0.0], "stations": [0.0, 1000.0],
            "total": 1000.0,
        }
        owner = "Owner" + side
        configuration["turnout_" + side.lower() + "_id"] = owner
        configuration["turnout_" + side.lower() + "_config"] = {
            "host_object": name, "toe_chainage": 500.0,
            "orientation": "facing" if side == "A" else "trailing",
            "handing": "Right-hand", "track_gauge": 16.5,
        }
        for number in range(1, 6):
            timber_id = "S" + str(number + 7)
            timber_identity = side + ":" + timber_id
            station = 60.0 + number * 10
            timbers.append({
                "stable_identity": timber_identity,
                "source_configuration": {"local_x": station},
            })
            for rail_side in ("MS", "TS"):
                identity = timber_identity + ":" + rail_side
                context_id = f"RH-{rail_side}-{number}P"
                code = 11 if number <= 2 else 12
                positions[identity] = {
                    "chair_code": code, "timber_identity": timber_identity,
                    "prototype_timber_identifier": timber_id,
                    "rail_name": ("main-side stock rail" if rail_side == "MS"
                                  else "turnout-side stock rail"),
                    "parent_turnout_identity": owner,
                    "rail_identity": side + ":" + rail_side,
                }
                recipes[context_id] = {
                    "context_sha256": "invented", "station_mm": station,
                    "timber_id": timber_id, "chair_code": code,
                    "native_frame": {"common_timber_curving_applied": False},
                    "context": {"side": rail_side},
                }
    document = SimpleNamespace(getObject=lambda name: hosts.get(name))
    module = SimpleNamespace(
        TURNOUT_HAND_RIGHT="Right-hand",
        turnout_host_alignment=lambda obj: data[obj.Name],
        _turnout_orientation_sign=lambda value: 1 if value == "facing" else -1,
        interpolate_alignment_station=lambda _data, station:
            (SimpleNamespace(x=station, y=0.0), 0.0),
    )
    signature = json.dumps({"configuration": configuration}, sort_keys=True)
    host_records, _data, _objects = pairs._host_context(
        module, document, configuration,
    )
    metadata = {
        "source_context_sha256": hashlib.sha256(signature.encode()).hexdigest(),
        "host_context_sha256": hashlib.sha256(
            pairs._encoded(host_records).encode(),
        ).hexdigest(),
    }
    selections = tuple(SimpleNamespace(
        run=identity, metadata=copy.deepcopy(metadata),
        context=recipes[identity], model_sha256="invented-model",
    ) for identity in CONTEXT_IDS)
    return module, document, signature, positions, timbers, selections, data


def prepare(source):
    module, document, signature, positions, timbers, selections, _data = source
    with patch.object(pairs, "prepare_paired_catalogue", return_value=selections):
        return pairs.prepare_crossover_pairs(
            module, document, signature, positions, timbers, 0.8,
            "invented-private-manifest",
        )


class PairedFrameTests(unittest.TestCase):
    def test_common_rigid_frame_and_mounting_plane(self):
        for heading in (0.0, math.pi / 2, math.pi, -0.7):
            with self.subTest(heading=heading):
                frame = place_paired_chair(
                    "position", "rail", "timber", (10, 20), heading,
                    0.8, 8.25, 0.45,
                )
                self.assertIsInstance(frame, PairedChairPlacement)
                # Inverse retained XY maps this point to source (2, 3).
                actual = frame.transform_point((-2, -3.45, 0))
                expected = (10 + 2 * math.cos(heading) - 11.25 * math.sin(heading),
                            20 + 2 * math.sin(heading) + 11.25 * math.cos(heading),
                            0.8)
                for first, second in zip(actual, expected):
                    self.assertAlmostEqual(first, second, places=12)

    def test_complete_twenty_positions_and_late_host_refusal(self):
        source = invented_source()
        groups, witnesses, verify = prepare(source)
        self.assertEqual(tuple(groups), CONTEXT_IDS)
        self.assertEqual({len(values) for values in groups.values()}, {2})
        self.assertEqual(set(witnesses), set(source[3]))
        self.assertEqual(len(witnesses), 20)
        verify()
        source[-1]["HostA"]["points"][0].x += 1
        with self.assertRaisesRegex(ValueError, "host changed"):
            verify()

    def test_missing_position_station_and_context_changes_refuse(self):
        for change in ("missing", "station", "source", "host"):
            with self.subTest(change=change):
                source = invented_source()
                if change == "missing":
                    source[3].pop(next(iter(source[3])))
                elif change == "station":
                    source[4][0]["source_configuration"]["local_x"] += 1
                elif change == "source":
                    source[5][0].metadata["source_context_sha256"] = "different"
                else:
                    source[-1]["HostB"]["headings"][0] = 0.1
                with self.assertRaises(ValueError):
                    prepare(source)

    def test_nonfinite_frame_is_refused(self):
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                place_paired_chair("p", "r", "t", (0, 0), value, 0, 8.25, 0.45)

    def test_caller_cannot_supply_catalogue_digest(self):
        with self.assertRaises(TypeError):
            prepare_paired_catalogue("invented", sha256="caller-supplied")

    def test_session_forwards_explicit_supplement(self):
        session = SimpleNamespace(
            module=object(), _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        operation = Mock(return_value="receipt")
        with patch.object(chair_catalogue_placement,
                          "preview_private_catalogue_crossover_chairs", operation):
            session_type = transition_workflow.ModularCoreLayoutWorkflowSession
            result = session_type.preview_private_catalogue_crossover_chairs(
                session, "document", "XO-001", "catalogue",
                paired_contexts_path="supplement",
            )
        self.assertEqual(result, "receipt")
        operation.assert_called_once_with(
            session.module, "document", "XO-001", "catalogue",
            session._private_catalogue_crossover_preview_factory,
            paired_contexts_path="supplement",
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PairedFrameTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
