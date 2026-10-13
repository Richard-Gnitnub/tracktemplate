#!/usr/bin/env python3
"""Reject incomplete Core Generate diagnostics without a latency budget."""

import copy
import contextlib
import io
import json
import pathlib
import sys
import tempfile
import types
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import core_generate_baseline as baseline  # noqa: E402


SENTINEL = "Core Generate baseline validation passed"
HOST = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"
)
LABELS = (
    "first-generate",
    "same-process-regeneration-1",
    "same-process-regeneration-2",
)
CHECKS = (
    "repeated_contract_equal",
    "previous_outputs_preserved",
    "actual_export_geometry_verified",
    "document_registry_preserved",
    "routing_preserved",
    "dependency_classification_verified",
    "preferences_restored",
    "pending_configuration_restored",
)
METRICS = ("wall_ms", "process_cpu_ms", "rss_before_mb", "rss_after_mb")
OBJECT_COUNTS = ("objects_before", "objects_after")


def _sample(index):
    """Make synthetic observations with deliberately different action costs."""
    offset = (9.0, 1.0, 4.0)[index]
    actions = []
    for action_index, label in enumerate(LABELS):
        base = 100.0 * (action_index + 1)
        actions.append({
            "label": label,
            "status": "completed",
            "previous_outputs_preserved": True,
            "wall_ms": base + offset,
            "process_cpu_ms": base / 2.0 + offset,
            "rss_before_mb": 500.0 + base + offset,
            "rss_after_mb": 490.0 + base + offset,
            "objects_before": 9,
            "objects_after": 9,
            "payload_count": 13,
            "output_contract_sha256": "a" * 64,
            "output_dir": "/synthetic/sample-{}/output-{}".format(
                index, action_index,
            ),
        })
    return {
        "status": "completed",
        "cleanup": {"remaining": []},
        "source_before": {"synthetic.py": "b" * 64},
        "source_after": {"synthetic.py": "b" * 64},
        "fixture_before": baseline.FIXTURE_SHA256,
        "fixture_after": baseline.FIXTURE_SHA256,
        "probe": {
            "schema_version": 1,
            "profile_id": "phase9b-core-generate-diagnostic-v1",
            "host_profile_id": HOST,
            "status": "completed",
            "sentinel": "CORE_GENERATE_BASELINE_PASS",
            "checks": {name: True for name in CHECKS},
            "actions": actions,
        },
    }


def _reject(label, operation):
    try:
        operation()
    except ValueError:
        return
    raise AssertionError("Accepted invalid diagnostic: " + label)


def _probe_change(label, mutate):
    report = _sample(0)["probe"]
    mutate(report)
    _reject(label, lambda: baseline.validate_probe(report))


def _series_change(label, mutate):
    samples = [_sample(index) for index in range(3)]
    mutate(samples)
    _reject(label, lambda: baseline.summarize(samples))


def validate_positive_summary():
    samples = [_sample(index) for index in range(3)]
    preserved = copy.deepcopy(samples)
    assert baseline.validate_probe(samples[0]["probe"]) == samples[0]["probe"]
    summary = baseline.summarize(samples)
    assert tuple(summary) == LABELS
    for index, label in enumerate(LABELS):
        base = 100.0 * (index + 1)
        starts = {
            "wall_ms": base,
            "process_cpu_ms": base / 2.0,
            "rss_before_mb": 500.0 + base,
            "rss_after_mb": 490.0 + base,
        }
        expected = {
            name: {
                "values": [start + 9.0, start + 1.0, start + 4.0],
                "median": start + 4.0,
                "minimum": start + 1.0,
                "maximum": start + 9.0,
            }
            for name, start in starts.items()
        }
        expected.update({name: {
            "values": [9, 9, 9], "median": 9, "minimum": 9, "maximum": 9,
        } for name in OBJECT_COUNTS})
        assert summary[label] == expected, (label, summary[label])
    assert samples == preserved, "Validation changed the input evidence"
    # A lower final RSS is valid. It is not a negative absolute measurement.
    zero = copy.deepcopy(samples[0]["probe"])
    for action in zero["actions"]:
        action.update({name: 0 for name in METRICS})
    baseline.validate_probe(zero)


def validate_identity_and_checks():
    for key in ("schema_version", "profile_id", "host_profile_id",
                "status", "sentinel"):
        _probe_change("missing " + key, lambda report: report.pop(key))
    for key, value in (
        ("schema_version", 2), ("profile_id", "phase6-profile"),
        ("host_profile_id", ""), ("host_profile_id", None),
        ("status", "failed"), ("status", "incomplete"),
        ("sentinel", "ANOTHER_PROBE_PASS"),
    ):
        _probe_change(key + "=" + repr(value),
                      lambda report: report.update({key: value}))
    for value in (None, {}, {"unrelated": True}):
        _probe_change("incomplete check set",
                      lambda report: report.update(checks=value))
    for name in CHECKS:
        _probe_change("missing check " + name,
                      lambda report: report["checks"].pop(name))
        for value in (False, 1, "true", None):
            _probe_change("failed check " + name,
                          lambda report: report["checks"].update({
                              name: value,
                          }))


def validate_action_rejections():
    _probe_change("missing action", lambda report: report["actions"].pop())
    _probe_change("extra action", lambda report: report["actions"].append(
        copy.deepcopy(report["actions"][0]),
    ))
    _probe_change("wrong action order",
                  lambda report: report["actions"].reverse())
    for key in ("status", "previous_outputs_preserved"):
        _probe_change("missing action " + key,
                      lambda report: report["actions"][1].pop(key))
    for key, value in (
        ("status", "failed"), ("status", "incomplete"),
        ("previous_outputs_preserved", False),
        ("previous_outputs_preserved", 1),
        ("payload_count", 12), ("payload_count", 14),
        ("payload_count", "13"), ("payload_count", None),
        ("output_dir", ""), ("output_dir", None),
        ("output_contract_sha256", "a" * 63),
        ("output_contract_sha256", "g" * 64),
        ("output_contract_sha256", "b" * 64),
    ):
        _probe_change("action " + key + "=" + repr(value),
                      lambda report: report["actions"][1].update({key: value}))
    _probe_change("repeated publication directory", lambda report:
                  report["actions"][1].update(
                      output_dir=report["actions"][0]["output_dir"],
                  ))
    for key in METRICS:
        _probe_change("missing " + key,
                      lambda report: report["actions"][0].pop(key))
        for value in (None, True, False, "1", -0.001,
                      float("nan"), float("inf"), -float("inf")):
            _probe_change("invalid " + key + "=" + repr(value),
                          lambda report: report["actions"][0].update({
                              key: value,
                          }))
    for key in OBJECT_COUNTS:
        _probe_change("missing " + key,
                      lambda report: report["actions"][0].pop(key))
        for value in (None, True, False, "9", -1, 9.5, float("nan")):
            _probe_change("invalid " + key + "=" + repr(value),
                          lambda report: report["actions"][0].update({
                              key: value,
                          }))


def validate_series_rejections():
    for count in (0, 1, 2, 4):
        samples = [_sample(index % 3) for index in range(count)]
        _reject("sample count " + str(count),
                lambda: baseline.summarize(samples))
    for key in ("status", "cleanup", "source_before", "source_after",
                "fixture_before", "fixture_after"):
        _series_change("missing sample " + key,
                       lambda samples: samples[1].pop(key))
    for key, value in (
        ("status", "failed"), ("status", "started"),
        ("cleanup", {"remaining": ["LeakedDocument"]}),
        ("cleanup", {}), ("source_before", {}),
        ("source_after", {"synthetic.py": "c" * 64}),
        ("fixture_before", "c" * 64), ("fixture_after", "c" * 64),
    ):
        _series_change("sample " + key + "=" + repr(value),
                       lambda samples: samples[1].update({key: value}))
    _series_change("failed probe", lambda samples:
                   samples[1]["probe"].update(status="failed"))
    _series_change("mixed host profiles", lambda samples:
                   samples[1]["probe"].update(host_profile_id="other-host"))
    _series_change("different preserved source", lambda samples:
                   samples[1].update(
                       source_before={"synthetic.py": "c" * 64},
                       source_after={"synthetic.py": "c" * 64},
                   ))
    _series_change("different sample contract", lambda samples: [
        action.update(output_contract_sha256="c" * 64)
        for action in samples[1]["probe"]["actions"]
    ])
    _series_change("repeated publication between processes", lambda samples:
                   samples[1]["probe"]["actions"][0].update(
                       output_dir=samples[0]["probe"]["actions"][0][
                           "output_dir"
                       ],
                   ))


def validate_cleanup_rpc_and_failure_preservation():
    """RPC calls have fresh namespaces; client exits must retain evidence."""
    documents = {"copied-input": object(), "generated-copy": object()}
    freecad = types.ModuleType("FreeCAD")
    freecad.listDocuments = lambda: dict(documents)
    freecad.closeDocument = documents.pop

    class Client:
        def execute_code(self, source):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(source, {})
            return {"output": output.getvalue()}

    with mock.patch.dict(sys.modules, {"FreeCAD": freecad}):
        assert baseline._close_documents(Client()) == {"remaining": []}
        assert documents == {}
        documents["leaked-copy"] = object()
        freecad.closeDocument = lambda name: None
        try:
            baseline._close_documents(Client())
        except RuntimeError:
            pass
        else:
            raise AssertionError("Cleanup accepted a remaining document")

    with tempfile.TemporaryDirectory() as temporary:
        directory = pathlib.Path(temporary)
        fixture = directory / "fixture"
        fixture.write_bytes(b"synthetic fixture")
        for failure in (SystemExit("rpc fault"), RuntimeError("rpc fault")):
            record = {"status": "completed", "probe": {"status": "completed"}}
            with mock.patch.object(baseline, "_close_documents",
                                   side_effect=failure), mock.patch.object(
                baseline, "_sources", return_value={"source.py": "a" * 64},
            ):
                baseline._finish_sample(record, fixture, directory, object())
            saved = json.loads((directory / "sample.json").read_text())
            assert saved["status"] == "failed"
            assert saved["cleanup_error"].startswith(type(failure).__name__)
            assert saved["source_after"] == {"source.py": "a" * 64}
            assert saved["fixture_after"] == baseline._hash(fixture)
            assert saved["probe"] == {"status": "completed"}
        record = {"status": "failed", "error": "original probe failure"}
        with mock.patch.object(baseline, "_close_documents",
                               return_value={"remaining": []}), \
                mock.patch.object(baseline, "_sources",
                                  side_effect=SystemExit("source failure")):
            baseline._finish_sample(record, fixture, directory, object())
        saved = json.loads((directory / "sample.json").read_text())
        assert saved["status"] == "failed"
        assert saved["error"] == "original probe failure"
        assert saved["preservation_error"] == "SystemExit: source failure"


def main():
    validate_positive_summary()
    validate_identity_and_checks()
    validate_action_rejections()
    validate_series_rejections()
    validate_cleanup_rpc_and_failure_preservation()
    print(SENTINEL)


if __name__ == "__main__":
    main()
