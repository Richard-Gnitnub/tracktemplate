#!/usr/bin/env python3
"""Exercise actual native-validator frame checks without a FreeCAD host.

Supply a SHA-bound private native receipt explicitly. Retain no private
receipt in source control. Shapes and the geometry comparison are stubs;
these checks prove receipt handling, never native geometry or lifecycle.
"""

import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tests/freecad_validate_phase9b_catalogue_crossing_exit.py"
CENTRAL = ROOT / "tests/freecad_validate_phase9b_catalogue_central_check.py"
COMPONENT = ROOT / "tests/freecad_validate_phase9b_catalogue_p_placement.py"
FRAME_FIELDS = ("origin_mm", "x_axis", "y_axis")
SENTINEL = "Phase 9B crossing-exit component frame validation passed"


def _definitions(path, names, namespace):
    """Load exact named source definitions, without host imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    selected, found = [], set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(node)
            found.add(node.name)
        elif isinstance(node, ast.Assign):
            assigned = {target.id for target in node.targets
                        if isinstance(target, ast.Name)}
            if assigned & names:
                assert assigned <= names
                selected.append(node)
                found.update(assigned)
    assert found == names, (str(path), names - found)
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)


class _FrameBoundary:
    """Keep real assertions up to the explicitly stubbed shape boundary."""

    def __init__(self, receipt):
        constants = {}
        _definitions(COMPONENT, {"EPSILON_MM"}, constants)
        central = {"math": math, "p": SimpleNamespace(**constants)}
        _definitions(CENTRAL, {"_near_frame"}, central)
        self.frame_calls = []
        self.geometry_calls = []
        self.expected_calls = []
        self.frame_keys = {}
        self.references, self.prepared, self.witnesses = {}, {}, {}
        self.layers, self.child_bindings = {}, {}
        self.namespace = {"central": SimpleNamespace(
            _near_frame=self._near_frame,
        ), "p": SimpleNamespace(_compare_component=self._compare_component)}
        _definitions(VALIDATOR, {
            "CROSSING_GROUPS", "EXIT_GROUPS", "NEW_COUNTS", "_assert_new",
        }, self.namespace)
        self.original_near_frame = central["_near_frame"]
        self.result = copy.deepcopy(receipt["preview"])
        for group in self.namespace["NEW_COUNTS"]:
            record = receipt["preview"]["families"][group]
            source_witness = receipt["source_witnesses"][
                record["placements"][0]["position_id"]]
            self.prepared[group] = SimpleNamespace(
                model_sha256=record["source_model_sha256"],
                run=record["run"], context=record["context"],
                label=source_witness["family"],
            )
            names = tuple(item["source_name"] for item in record["components"])
            self.references[group] = {name: object() for name in names}
            for index, placement in enumerate(record["placements"]):
                identity = placement["position_id"]
                witness = receipt["source_witnesses"][identity]
                frames = {name: SimpleNamespace(**fields) for name, fields in
                          witness["expected_component_frames"].items()}
                self.witnesses[identity] = dict(
                    group=witness["group"], family=witness["family"],
                    components=frames,
                )
                for name in names:
                    key = (group, identity, name)
                    self.expected_calls.append(key)
                    self.frame_keys[id(frames[name])] = key
                    layer_name = group.replace("-", "_") + "_" + name
                    children = self.layers.setdefault(layer_name, [])
                    child = object()
                    assert len(children) == index
                    children.append(child)
                    self.child_bindings[id(child)] = (
                        key, self.references[group][name], frames[name],
                    )
        self.document = SimpleNamespace(getObject=self._get_object)

    def _near_frame(self, actual, expected):
        self.frame_calls.append(self.frame_keys[id(expected)])
        self.original_near_frame(actual, expected)

    def _get_object(self, name):
        children = self.layers[name]
        return SimpleNamespace(Shape=SimpleNamespace(
            childShapes=lambda: tuple(children),
        ))

    def _compare_component(self, actual, reference, frame):
        key, expected_reference, expected_frame = self.child_bindings[id(actual)]
        assert reference is expected_reference
        assert frame is expected_frame
        self.geometry_calls.append(key)
        return {"geometry_stub_only": True}

    def run(self):
        return self.namespace["_assert_new"](
            self.result, self.document, self.references, self.prepared,
            self.witnesses,
        )

    def placements(self, group):
        return self.result["families"][group]["placements"]


class ComponentFrameContract(unittest.TestCase):
    receipt = None

    def boundary(self):
        return _FrameBoundary(self.receipt)

    def test_all_retained_frames_reach_the_geometry_boundary(self):
        boundary = self.boundary()
        checks = boundary.run()
        self.assertEqual(len(boundary.witnesses), 24)
        self.assertEqual(len(boundary.references), 11)
        self.assertEqual(len(checks), 702)
        self.assertEqual(boundary.frame_calls, boundary.expected_calls)
        self.assertEqual(boundary.geometry_calls, boundary.expected_calls)
        self.assertEqual({witness["side"] for witness in
                          self.receipt["source_witnesses"].values()}, {"A", "B"})
        self.assertNotIn("FreeCAD", sys.modules)

    def test_crossing_parent_frames_are_required_and_checked(self):
        groups = self.boundary().namespace["CROSSING_GROUPS"]
        for group in groups:
            for field in FRAME_FIELDS:
                for mutation in ("missing", "corrupt", "nonfinite"):
                    with self.subTest(group=group, field=field,
                                      mutation=mutation):
                        boundary = self.boundary()
                        placement = boundary.placements(group)[0]
                        component = placement["components"][0]
                        self.assertFalse(any(name in component
                                             for name in FRAME_FIELDS))
                        key = (group, placement["position_id"],
                               component["source_name"])
                        error = self._mutate_frame(placement, field, mutation)
                        with self.assertRaises(error) as caught:
                            boundary.run()
                        self.assertEqual(boundary.frame_calls[-1], key)
                        if mutation == "missing":
                            self.assertEqual(caught.exception.args, (field,))

    def test_exit_component_frames_are_required_and_checked(self):
        groups = self.boundary().namespace["EXIT_GROUPS"]
        for group in groups:
            for field in FRAME_FIELDS:
                for mutation in ("missing", "corrupt", "nonfinite"):
                    with self.subTest(group=group, field=field,
                                      mutation=mutation):
                        boundary = self.boundary()
                        placement = boundary.placements(group)[0]
                        component = placement["components"][0]
                        key = (group, placement["position_id"],
                               component["source_name"])
                        error = self._mutate_frame(component, field, mutation)
                        with self.assertRaises(error) as caught:
                            boundary.run()
                        self.assertEqual(boundary.frame_calls[-1], key)
                        if mutation == "missing":
                            self.assertEqual(caught.exception.args, (field,))

    @staticmethod
    def _mutate_frame(record, field, mutation):
        if mutation == "missing":
            del record[field]
            return KeyError
        record[field][0] = (record[field][0] + 1.0
                            if mutation == "corrupt" else float("nan"))
        return AssertionError

    def test_actual_exit_fixing_overrides_cannot_use_parent_frame(self):
        pristine = self.boundary()
        overrides = []
        for group in pristine.namespace["EXIT_GROUPS"]:
            for index, placement in enumerate(pristine.placements(group)):
                different = [
                    item for item in placement["components"]
                    if any(item[field] != placement[field]
                           for field in FRAME_FIELDS)
                ]
                if different:
                    self.assertTrue(all("Fixing" in item["source_name"]
                                        for item in different))
                    overrides.append((group, index,
                                      different[0]["source_name"]))
        self.assertEqual({(group, index) for group, index, _name in overrides},
                         {("ExitS1", 1), ("ExitS1", 3),
                          ("ExitL1", 0), ("ExitL1", 1)})
        for group, index, name in overrides:
            with self.subTest(group=group, placement_index=index):
                boundary = self.boundary()
                placement = boundary.placements(group)[index]
                component = next(
                    item for item in placement["components"]
                    if item["source_name"] == name
                )
                key = (group, placement["position_id"], component["source_name"])
                for field in FRAME_FIELDS:
                    component[field] = list(placement[field])
                with self.assertRaises(AssertionError):
                    boundary.run()
                self.assertEqual(boundary.frame_calls[-1], key)

    def test_component_identity_mismatch_and_absence_are_rejected(self):
        for mutation in ("wrong_placement", "missing_placement", "wrong_source"):
            with self.subTest(mutation=mutation):
                boundary = self.boundary()
                group = boundary.namespace["CROSSING_GROUPS"][0]
                component = boundary.placements(group)[0]["components"][0]
                if mutation == "wrong_placement":
                    component["placement_identity"][0] = "incorrect-owner"
                    error = AssertionError
                elif mutation == "missing_placement":
                    del component["placement_identity"]
                    error = KeyError
                else:
                    component["source_name"] = "incorrect-source"
                    error = AssertionError
                with self.assertRaises(error) as caught:
                    boundary.run()
                self.assertEqual(boundary.frame_calls, [])
                self.assertEqual(boundary.geometry_calls, [])
                if mutation == "missing_placement":
                    self.assertEqual(caught.exception.args,
                                     ("placement_identity",))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--receipt-sha256", required=True)
    args = parser.parse_args()
    content = args.receipt.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != args.receipt_sha256:
        parser.error("Private native receipt SHA256 does not match")
    ComponentFrameContract.receipt = json.loads(content)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        ComponentFrameContract,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({
        "receipt_sha256": digest,
        "validator_sha256": hashlib.sha256(VALIDATOR.read_bytes()).hexdigest(),
        "frame_comparator_sha256": hashlib.sha256(CENTRAL.read_bytes()).hexdigest(),
        "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors),
        "scope": "Standalone frame caller only; native shapes are stubbed",
    }), flush=True)
    if result.wasSuccessful():
        print(SENTINEL, flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
