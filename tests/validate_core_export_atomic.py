#!/usr/bin/env python3
"""Check the Core whole-set application and its bounded UI policy."""

import copy
import csv
import inspect
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.application.core_export_set import (
    prepare_core_export_plan,
)  # noqa: E402
from tracktemplate.adapters.export.core_layout_set import (
    CoreLayoutExportSetFiles,
)  # noqa: E402
from tracktemplate.compatibility.core_export_policy import (
    CoreExportConfiguration,
    CoreExportPolicy,
)  # noqa: E402
import validate_core_export_staging as staging  # noqa: E402


SENTINEL = "Core atomic export application validation passed"


def inputs(root, *, manifest=True):
    plan, config = staging.inputs(root, existing=True)
    child = root / "Core_Export_test"
    for task in plan["tasks"]:
        task["path"] = str(child / Path(task["path"]).name)
    plan["manifest_path"] = str(child / "core.csv") if manifest else ""
    plan["output_directory"] = str(child)
    return plan, config


def run_case(root, *, manifest=True, fault=None, adapter=None,
             interruption=None):
    plan, config = inputs(root, manifest=manifest)
    before = staging.file_witness(root)
    saved_plan, saved_config = copy.deepcopy(plan), copy.deepcopy(config)
    document = object()
    class Collaborators(staging.Collaborators):
        def assert_finals_unchanged(self):
            observed = staging.file_witness(self.root)
            assert all(observed[name] == witness
                       for name, witness in self.before.items())
            assert not Path(self.plan["output_directory"]).exists()

    collaborators = Collaborators(
        document, plan, root, fault, interruption,
    )
    keywords = collaborators.keywords()
    if fault == ("skipped-report", None):
        def broken_report(_item):
            raise RuntimeError("controlled skipped-report failure")
        keywords["skipped_export_report"] = broken_report
    if not manifest:
        def forbidden(*_args):
            raise AssertionError("Unrequested CSV was constructed")
        keywords.update(build_manifest_rows=forbidden,
                        write_export_manifest=forbidden)
    result = api.run_atomic_core_layout_export(
        document, plan, config, "SET-STAGING", {}, {}, {}, {},
        export_files_factory=adapter or CoreLayoutExportSetFiles,
        **keywords,
    )
    assert plan == saved_plan and config == saved_config
    for item, task in zip(result["results"], plan["tasks"]):
        assert item["task"] is task
    after = staging.file_witness(root)
    assert all(after[name] == witness for name, witness in before.items())
    assert not any(name.startswith(".tracktemplate") for name in after)
    return result, plan, collaborators


def validate_application():
    cases = 0
    with tempfile.TemporaryDirectory(prefix="tt-atomic-application-") as area:
        base = Path(area)
        for manifest in (True, False):
            root = base / ("csv" if manifest else "no-csv")
            root.mkdir()
            result, plan, _ = run_case(root, manifest=manifest)
            assert result["publication_state"] == "published"
            assert result["successful_files"] == 4 + int(manifest)
            assert result["failed_files"] == 0
            assert result["output_directory"] == plan["output_directory"]
            child = Path(result["output_directory"])
            expected = {"core." + name for name in staging.FORMATS}
            if manifest:
                expected.add("core.csv")
                with open(result["manifest_path"], newline="") as handle:
                    rows = list(csv.DictReader(handle))
                assert [row["path"] for row in rows] == [
                    task["path"] for task in plan["tasks"]
                ]
            else:
                assert result["manifest_path"] == ""
            assert {path.name for path in child.iterdir()} == expected
            for task in plan["tasks"]:
                assert Path(task["path"]).read_bytes() == staging.payload(task)
            cases += 1

        faults = [("generation", index) for index in range(4)] + [
            ("manifest-build", None), ("manifest-write", None),
            ("skipped-report", None),
        ]
        for index, fault in enumerate(faults):
            root = base / ("fault-" + str(index))
            root.mkdir()
            result, plan, _ = run_case(root, fault=fault)
            assert result["successful_files"] == 0
            assert result["publication_state"] == "not-published"
            assert result["failed_files"] >= 4
            assert result["output_directory"] == str(root)
            assert not Path(plan["output_directory"]).exists()
            cases += 1

        class BeforePublication(CoreLayoutExportSetFiles):
            def publish(self):
                raise OSError("controlled publication failure")

        class AfterPublication(CoreLayoutExportSetFiles):
            def publish(self):
                super().publish()
                raise OSError("controlled error after publication")

        class AfterCleanup(CoreLayoutExportSetFiles):
            def cleanup(self):
                return super().cleanup() + ["controlled cleanup diagnostic"]

        for adapter, published in (
            (BeforePublication, False), (AfterPublication, True),
            (AfterCleanup, True),
        ):
            root = base / adapter.__name__
            root.mkdir()
            result, plan, _ = run_case(root, adapter=adapter)
            assert result["successful_files"] == (5 if published else 0)
            assert result["publication_state"] == (
                "published" if published else "not-published"
            )
            assert result["failed_files"] > 0
            assert bool(result["manifest_path"]) is published
            assert Path(plan["output_directory"]).exists() is published
            cases += 1

        for after in (False, True):
            interruption = staging.ControlledInterruption("explicit boundary")

            class Interrupted(CoreLayoutExportSetFiles):
                def publish(self):
                    if after:
                        super().publish()
                    raise interruption

            root = base / ("interrupt-after" if after else "interrupt-before")
            root.mkdir()
            try:
                run_case(root, adapter=Interrupted)
            except staging.ControlledInterruption as error:
                assert error is interruption
                state = "published" if after else "not-published"
                assert any("state: " + state in note
                           for note in error.__notes__)
                assert (root / "Core_Export_test").exists() is after
            else:
                raise AssertionError("Interruption was swallowed")
            cases += 1
    return cases


def validate_policy():
    namespace = {"__name__": "core_policy_fixture"}
    exec("""
def plan_production_export(records, config, set_id):
    observed.append(('plan', config, records))
    return {'tasks': [{'path': config['output_directory'] + '/member.dxf',
                      'records': records}], 'manifest_path': '', 'skipped': []}
def run_production_preflight(doc, catalogue_records, export_records, config,
                             set_id, *args, plan=None, **kwargs):
    observed.append(('preflight', config, plan))
    return ['unchanged checks']
class CurveInputDialog:
    def _update_production_export_controls(self, *args):
        self.production_overwrite_box.setEnabled(True)
    def _production_export_values(self):
        return {'output_directory': '/parent', 'overwrite_existing': True}
""", namespace)
    namespace["observed"] = []
    policy = CoreExportPolicy(namespace)
    previous = policy.snapshot()
    policy.bind()
    policy.validate()
    records = [object()]
    config = {"output_directory": "/parent", "overwrite_existing": True}
    plain_plan = namespace["plan_production_export"](records, config, "SET")
    assert "output_directory" not in plain_plan
    assert namespace["observed"][-1][1] is config
    dialog = namespace["CurveInputDialog"]()
    marked = dialog._production_export_values()
    assert isinstance(marked, CoreExportConfiguration)
    assert marked["overwrite_existing"] is False
    assert json.loads(json.dumps(marked)) == dict(marked)
    first = namespace["plan_production_export"](records, marked, "SET")
    second = namespace["plan_production_export"](records, marked, "SET")
    assert first["output_directory"] != second["output_directory"]
    assert Path(first["output_directory"]).parent == Path("/parent")
    assert first["tasks"][0]["records"] is records
    before = dict(marked)
    assert namespace["run_production_preflight"](
        None, records, records, marked, "SET", plan=first,
    ) == ["unchanged checks"]
    assert namespace["observed"][-1][1]["output_directory"] == (
        first["output_directory"]
    )
    assert marked == before
    namespace["run_production_preflight"](
        None, records, records, config, "SET", plan=plain_plan,
    )
    assert namespace["observed"][-1][1] is config
    namespace["plan_production_export"] = object()
    try:
        policy.validate()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Mixed policy accepted")
    policy.restore(previous)
    assert policy.snapshot() == previous


def main():
    assert "run_atomic_core_layout_export" in api.__all__
    assert inspect.signature(api.run_atomic_core_layout_export) == (
        inspect.signature(api.run_staged_core_layout_export)
    )
    validate_policy()
    cases = validate_application()
    print(SENTINEL + ": {} application cases; isolated policy checks".format(cases))


if __name__ == "__main__":
    main()
