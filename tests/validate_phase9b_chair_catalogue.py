#!/usr/bin/env python3
"""Exercise catalogue refusals with synthetic, non-native evidence.

Artificial BRep text is bookkeeping data only. These tests do not admit a
catalogue or qualify geometry. The private native proof owns actual models.
"""

import copy
from dataclasses import FrozenInstanceError
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
import warnings
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.application import (  # noqa: E402
    chair_catalogue as catalogue,
)


SENTINEL = "Phase 9B chair catalogue standalone validation passed"


def synthetic_document():
    """Make invented metadata and deliberately non-geometric BRep text."""
    return ET.fromstring('''<Document SchemaVersion="4" FileVersion="1">
<Objects><Object type="Part::Feature" name="Sample"/></Objects>
<ObjectData><Object name="Sample"><Properties>
<Property name="Shape" type="Part::PropertyPartShape">
<Part file="Sample.Shape.brp"/></Property>
<Property name="Label"><String value="Synthetic component"/></Property>
<Property name="Placement"><PropertyPlacement
Px="2.25" Py="-4.5" Pz="6" Q0="0" Q1="0" Q2="0.6" Q3="0.8"/>
</Property><Property name="ExpressionEngine"><ExpressionEngine count="0"/>
</Property></Properties></Object></ObjectData></Document>''')


def synthetic_archive(document=None, *, members=None, xml=None):
    """Encode test bookkeeping without invoking FreeCAD or source code."""
    if xml is None:
        xml = ET.tostring(
            synthetic_document() if document is None else document,
        )
    if members is None:
        members = [("Document.xml", xml),
                   ("Sample.Shape.brp", b"SYNTHETIC NON-GEOMETRIC TEST DATA")]
    stream = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in members:
                archive.writestr(name, data)
    return stream.getvalue()


def synthetic_index():
    """Make 29 artificial routing records, not an accepted catalogue."""
    labels = ["P", "CC", *[f"TEST{i}" for i in range(27)]]
    entries = [{
        "label": label, "project_status": "reference-only",
        "intended_use": "private-development",
        "acceptance": "NO_NEW_ACCEPTANCE",
        "selected_model": {"run": "basic-04", "selectable": True},
        "attempts": [{"run": "context-native-02", "selectable": True}],
    } for label in labels]
    return {
        "schema_version": 1, "status": "PRIVATE_REFERENCE_CATALOGUE",
        "active_label_count": 29, "native_pass_available_count": 29,
        "unsupported_count": 13, "production_accepted": False,
        "rights_cleared": False, "entries": entries,
    }, {"real": [{"members": labels}]}


class ArchiveContractTests(unittest.TestCase):
    """Reject document execution and altered component structure."""

    def reject(self, payload):
        with self.assertRaises((catalogue.CatalogueChairError, KeyError,
                                ValueError, TypeError, ET.ParseError)):
            catalogue._components(payload)

    def test_named_order_and_nonidentity_placement(self):
        result = catalogue._components(synthetic_archive())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Sample")
        self.assertEqual(result[0].label, "Synthetic component")
        self.assertEqual(result[0].xml_placement,
                         (2.25, -4.5, 6.0, 0.0, 0.0, 0.6, 0.8))
        self.assertEqual(result[0].brep_text,
                         "SYNTHETIC NON-GEOMETRIC TEST DATA")
        with self.assertRaises(FrozenInstanceError):
            result[0].name = "Changed"

    def test_schema_object_type_and_expression_refusals(self):
        mutations = (
            (".", "SchemaVersion", "5"),
            (".", "FileVersion", "2"),
            ("./Objects/Object", "type", "PartDesign::FeaturePython"),
            ("./ObjectData/Object", "name", "Other"),
            ("./ObjectData/Object/Properties/Property/Part",
             "file", "Elsewhere.Shape.brp"),
            (".//ExpressionEngine", "count", "1"),
            (".//PropertyPlacement", "Px", "nan"),
            (".//PropertyPlacement", "Q0", "inf"),
        )
        for xpath, attribute, value in mutations:
            with self.subTest(attribute=attribute, value=value):
                root = synthetic_document()
                node = root if xpath == "." else root.find(xpath)
                node.set(attribute, value)
                self.reject(synthetic_archive(root))
        root = synthetic_document()
        ET.SubElement(root.find(".//ExpressionEngine"), "Expression",
                      {"expression": "untrusted_call()"})
        self.reject(synthetic_archive(root))

    def test_empty_duplicate_and_missing_components(self):
        root = synthetic_document()
        root.find("Objects").append(copy.deepcopy(
            root.find("./Objects/Object"),
        ))
        self.reject(synthetic_archive(root))
        root = synthetic_document()
        root.find("ObjectData").remove(root.find("./ObjectData/Object"))
        self.reject(synthetic_archive(root))
        root = synthetic_document()
        properties = root.find(".//Properties")
        properties.append(copy.deepcopy(properties[0]))
        self.reject(synthetic_archive(root))
        xml = ET.tostring(synthetic_document())
        self.reject(synthetic_archive(members=[("Document.xml", xml)]))
        self.reject(synthetic_archive(members=[
            ("Document.xml", xml), ("Sample.Shape.brp", b" "),
        ]))

    def test_archive_traversal_duplicate_and_executable_members(self):
        xml = ET.tostring(synthetic_document())
        base = [("Document.xml", xml), ("Sample.Shape.brp", b"synthetic")]
        for extra in ("../outside", "/outside", "dir/file", "dir\\file",
                      "Proxy.py", "Extra.Shape.brp", "Sample.Shape.brp"):
            with self.subTest(extra=extra):
                self.reject(synthetic_archive(members=base + [(extra, b"x")]))
        self.reject(synthetic_archive(xml=b'<!DOCTYPE Document []>' + xml))
        self.reject(synthetic_archive(members=base + [
            ("large", b"x" * (catalogue._ARCHIVE_LIMIT + 1)),
        ]))
        self.reject(synthetic_archive(members=base + [
            (f"extra{i}", b"x") for i in range(catalogue._MEMBER_LIMIT)
        ]))


class RoutingTests(unittest.TestCase):
    """Keep the bounded retained-context route and acceptance flags."""

    def test_defaults_and_explicit_cc_context(self):
        index, inventory = synthetic_index()
        for entry in index["entries"]:
            _, selected = catalogue._selection(
                index, inventory, entry["label"], None,
            )
            self.assertEqual(selected["run"], "basic-04")
        _, selected = catalogue._selection(
            index, inventory, "CC", "context-native-02",
        )
        self.assertEqual(selected["run"], "context-native-02")

    def test_unknown_and_other_historical_runs_refused(self):
        index, inventory = synthetic_index()
        for label, run in (("NULL", None), ("../P", None), ([], None),
                           ("P", "context-native-02"), ("CC", "basic-03")):
            with self.subTest(label=label, run=run):
                with self.assertRaises(catalogue.CatalogueChairError):
                    catalogue._selection(index, inventory, label, run)

    def test_acceptance_escalation_and_failed_model_refused(self):
        for field, value in (("production_accepted", True),
                             ("rights_cleared", True),
                             ("active_label_count", 30)):
            index, inventory = synthetic_index()
            index[field] = value
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue._selection(index, inventory, "P", None)
        for field, value in (("project_status", "project-cleared"),
                             ("intended_use", "production"),
                             ("acceptance", "ACCEPTED")):
            index, inventory = synthetic_index()
            index["entries"][0][field] = value
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue._selection(index, inventory, "P", None)
        index, inventory = synthetic_index()
        index["entries"][0]["selected_model"]["selectable"] = False
        with self.assertRaises(catalogue.CatalogueChairError):
            catalogue._selection(index, inventory, "P", None)


class BindingTests(unittest.TestCase):
    """Prove genuine byte changes fail, without an arbitrary trust bypass."""

    def test_source_mutation_escape_and_symlink_refused(self):
        with tempfile.TemporaryDirectory(prefix="chair-catalogue-") as tmp:
            root = Path(tmp).resolve()
            source = root / "source.json"
            source.write_bytes(b"synthetic original")
            record = {"path": str(source), "sha256": hashlib.sha256(
                source.read_bytes(),
            ).hexdigest()}
            bindings = {}
            self.assertEqual(catalogue._bound(record, root, bindings),
                             b"synthetic original")
            source.write_bytes(b"synthetic changed")
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue._bound(record, root, {})
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue._bound(record, root / "contained", {})
            link = root / "link.json"
            link.symlink_to(source)
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue._read(link)

    def test_public_operation_rejects_synthetic_catalogue(self):
        index, _ = synthetic_index()
        with tempfile.TemporaryDirectory(prefix="chair-catalogue-") as tmp:
            path = Path(tmp).resolve() / "catalogue.json"
            content = json.dumps(index).encode()
            path.write_bytes(content)
            with self.assertRaisesRegex(catalogue.CatalogueChairError,
                                        "reviewed private catalogue"):
                catalogue.prepare_catalogue_chair(path, "P")
            self.assertEqual(path.read_bytes(), content)
            with self.assertRaises(TypeError):
                catalogue.prepare_catalogue_chair(
                    path, "P",
                    expected_sha256=hashlib.sha256(content).hexdigest(),
                )

    def test_strict_json_and_detached_metadata(self):
        for value in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
            with self.assertRaises(catalogue.CatalogueChairError):
                catalogue._json(value)
        chair = catalogue.CatalogueChair(
            "/synthetic", "TEST", "test-run", '{"value":[1]}',
            "/synthetic/model", "0" * 64, "0" * 64, (), (), (),
            '{"limits":["synthetic"]}',
        )
        chair.context["value"].append(2)
        chair.metadata["limits"].append("changed")
        self.assertEqual(chair.context, {"value": [1]})
        self.assertEqual(chair.metadata, {"limits": ["synthetic"]})
        with self.assertRaises(catalogue.CatalogueChairError):
            catalogue.verify_catalogue_sources(chair)
        with self.assertRaises(catalogue.CatalogueChairError):
            catalogue.verify_catalogue_sources({})


class CommandTests(unittest.TestCase):
    """Keep explicit catalogue selection and errors at the B16 boundary."""

    def test_factory_delegation_and_unavailable_refusal(self):
        from tracktemplate import api
        from tracktemplate.compatibility import transition_workflow
        from validate_phase9b_l1_reference_preview import _session

        calculation = _session()._calculation_session
        expected = {"document_name": "PrivatePreview"}
        factory = Mock(return_value=expected)
        session = transition_workflow.ModularCoreLayoutWorkflowSession(
            calculation, api.run_core_layout_export,
            private_catalogue_preview_factory=factory,
        )
        self.assertIs(session.preview_private_catalogue_chair(
            "/explicit/catalogue.json", "CC", run="context-native-02",
        ), expected)
        factory.assert_called_once_with(
            "/explicit/catalogue.json", "CC", run="context-native-02",
        )
        factory.side_effect = catalogue.CatalogueChairError("changed input")
        with self.assertRaisesRegex(catalogue.CatalogueChairError,
                                    "changed input"):
            session.preview_private_catalogue_chair("/explicit", "P")
        with self.assertRaises(transition_workflow.TransitionWorkflowError):
            _session().preview_private_catalogue_chair("/explicit", "P")
        self.assertFalse(any(name in sys.modules for name in (
            "FreeCAD", "FreeCADGui", "Part", "pivy",
        )))


def main():
    """Run standalone bookkeeping proof; native acceptance stays separate."""
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        return 1
    print(SENTINEL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
