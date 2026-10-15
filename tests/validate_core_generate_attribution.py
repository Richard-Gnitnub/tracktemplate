#!/usr/bin/env python3
"""Reject false attribution, mixed evidence and lost failure records."""

import copy
import functools
import json
import pathlib
import sys
import tempfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import core_generate_attribution as diagnostic  # noqa: E402


SENTINEL = "Core Generate attribution validation passed"


def _attribution():
    spans = []
    for identity, parent, name, start, end, remainder in (
        (0, None, "run_macro", 0, 100, 30),
        (1, 0, "geometry", 10, 50, 30),
        (2, 1, "kernel", 20, 30, 10),
        (3, 0, "export", 60, 90, 30),
    ):
        spans.append(
            {
                "id": identity,
                "parent": parent,
                "name": name,
                "classification": "operator action"
                if parent is None
                else "nested component",
                "wall_start_ns": start,
                "wall_end_ns": end,
                "process_cpu_start_ns": start // 2,
                "process_cpu_end_ns": end // 2,
                "remainder_ns": {
                    "wall": remainder,
                    "process_cpu": remainder // 2,
                },
            }
        )
    return {
        "spans": spans,
        "mapping": [],
        "boundary_remainder_ns": {"wall": 20, "process_cpu": 10},
    }


def _samples():
    samples = []
    for block, modes in enumerate(diagnostic.ORDER, 1):
        for mode in modes:
            action = {
                "label": "first-generate",
                "status": "completed",
                "wall_ms": 120 / 1000000,
                "process_cpu_ms": 60 / 1000000,
                "rss_before_mb": 10,
                "rss_after_mb": 9,
                "objects_before": 9,
                "objects_after": 9,
                "payload_count": 13,
                "previous_outputs_preserved": True,
                "output_contract_sha256": "a" * 64,
                "output_dir": "/synthetic/{}-{}".format(block, mode),
            }
            if mode == "control":
                action["wall_ms"] -= block / 1000000
                action["process_cpu_ms"] -= block / 1000000
            samples.append(
                {
                    "block": block,
                    "mode": mode,
                    "status": "completed",
                    "cleanup": {"remaining": []},
                    "source_before": {"source.py": "b" * 64},
                    "source_after": {"source.py": "b" * 64},
                    "fixture_before": diagnostic.baseline.FIXTURE_SHA256,
                    "fixture_after": diagnostic.baseline.FIXTURE_SHA256,
                    "isolated_instance_id": str(len(samples) + 1),
                    "probe": {
                        "schema_version": 1,
                        "profile_id": diagnostic.PROFILE,
                        "mode": mode,
                        "status": "completed",
                        "sentinel": diagnostic.SENTINEL,
                        "host_profile_id": "synthetic-qualified-host",
                        "checks": {name: True for name in diagnostic.CHECKS},
                        "action": action,
                        "attribution": _attribution()
                        if mode == "observed"
                        else None,
                    },
                }
            )
    return samples


def _reject(operation):
    try:
        operation()
    except ValueError:
        return
    raise AssertionError("Invalid evidence was accepted")


def validate_reconciliation():
    samples = _samples()
    before = copy.deepcopy(samples)
    summary = diagnostic.summarize(samples)
    assert samples == before, "Summarizing changed source evidence"
    for clock in diagnostic.CLOCKS:
        differences = summary["observer_difference"][clock + "_ms"]["values"]
        assert all(
            abs(actual - expected / 1000000) < 1e-18
            for actual, expected in zip(differences, (1, 2, 3))
        )
    areas = summary["exclusive_areas"]
    assert areas["geometry"]["wall_ns"]["values"] == [30, 30, 30]
    assert sum(area["wall_ns"]["values"][0] for area in areas.values()) == 120
    assert (
        sum(area["process_cpu_ns"]["values"][0] for area in areas.values())
        == 60
    )
    action = samples[1]["probe"]["action"]
    for mutate in (
        lambda data: data["spans"][3].update(wall_start_ns=40),
        lambda data: data["spans"][2].update(wall_end_ns=51),
        lambda data: data["spans"][1].update(wall_end_ns=9),
        lambda data: data["spans"][1].update(id=0),
        lambda data: data["spans"][1].update(parent=1),
        lambda data: data["spans"][0].update(parent=0),
        lambda data: data["spans"][0].pop("remainder_ns"),
        lambda data: data["spans"][0]["remainder_ns"].update(wall=31),
        lambda data: data["spans"][0]["remainder_ns"].update(wall=-1),
        lambda data: data["spans"][0]["remainder_ns"].update(
            wall=float("nan")
        ),
        lambda data: data["spans"][0].update(process_cpu_end_ns=float("inf")),
        lambda data: data.pop("boundary_remainder_ns"),
        lambda data: data["boundary_remainder_ns"].update(wall=19),
        lambda data: data["spans"][0].update(
            classification="estimated product"
        ),
    ):
        data = _attribution()
        mutate(data)
        _reject(lambda: diagnostic.validate_attribution(action, data))


def validate_preservation_rejections():
    mutations = [
        lambda samples: samples.reverse(),
        lambda samples: samples.pop(),
        lambda samples: samples[0].update(status="failed"),
        lambda samples: samples[0].update(cleanup={"remaining": ["leak"]}),
        lambda samples: samples[0].pop("cleanup"),
        lambda samples: samples[0].update(
            source_after={"source.py": "c" * 64}
        ),
        lambda samples: samples[0].update(source_before={}, source_after={}),
        lambda samples: samples[0].update(fixture_after="c" * 64),
        lambda samples: samples[1].update(isolated_instance_id="1"),
        lambda samples: samples[0]["probe"].update(
            host_profile_id="other-host"
        ),
        lambda samples: samples[0]["probe"].update(
            profile_id=diagnostic.baseline.PROFILE
        ),
        lambda samples: samples[0]["probe"].update(status="failed"),
        lambda samples: samples[0]["probe"].update(attribution=_attribution()),
        lambda samples: samples[0]["probe"]["action"].update(payload_count=12),
        lambda samples: samples[0]["probe"]["action"].update(
            previous_outputs_preserved=False
        ),
        lambda samples: samples[0]["probe"]["action"].update(
            output_contract_sha256="c" * 64
        ),
    ]
    for key in diagnostic.CHECKS:
        mutations.append(
            lambda samples, key=key: samples[0]["probe"]["checks"].update(
                {key: False}
            )
        )
    for key in ("wall_ms", "process_cpu_ms", "rss_before_mb", "rss_after_mb"):
        for value in (-1, float("nan"), float("inf"), True, "1"):
            mutations.append(
                lambda samples, key=key, value=value: samples[0]["probe"][
                    "action"
                ].update({key: value})
            )
    for mutate in mutations:
        samples = _samples()
        mutate(samples)
        _reject(lambda: diagnostic.summarize(samples))


def validate_observer_and_restoration():
    def child():
        return 1

    def run_macro(failure=None):
        child()
        if failure is not None:
            raise failure
        return child()

    targets = [
        ("run_macro", "operator action", run_macro.__code__),
        ("child", "nested component", child.__code__),
    ]
    for failure in (
        None,
        RuntimeError("product failure"),
        SystemExit("exit"),
        KeyboardInterrupt("interrupt"),
    ):
        observer = diagnostic.Observer(targets)
        try:
            with observer:
                run_macro(failure)
        except BaseException as error:
            assert error is failure
        assert observer.restored and sys.getprofile() is None
        assert not observer.errors and not observer.stack
        root = observer.spans[0]
        action = {
            clock + "_ms": (
                root[clock + "_end_ns"] - root[clock + "_start_ns"] + 1000
            )
            / 1000000
            for clock in diagnostic.CLOCKS
        }
        diagnostic.validate_attribution(action, observer.result(action))
    observer = diagnostic.Observer(targets)
    with mock.patch.object(
        diagnostic.time,
        "perf_counter_ns",
        side_effect=SystemExit("clock failure"),
    ):
        with observer:
            assert run_macro() == 1
    assert observer.restored and observer.errors and sys.getprofile() is None
    _reject(lambda: observer.result({}))
    _reject(lambda: diagnostic.Observer(targets + targets))
    assert (
        diagnostic.callable_code(functools.partial(run_macro))
        is run_macro.__code__
    )

    def existing(_frame, _event, _argument):
        return None

    sys.setprofile(existing)
    try:
        try:
            with diagnostic.Observer(targets):
                raise AssertionError("An existing profiler was replaced")
        except RuntimeError:
            pass
        assert sys.getprofile() is existing
    finally:
        sys.setprofile(None)


def validate_definition_loader_and_failed_receipts():
    namespace = {}
    exec(
        diagnostic.baseline_definitions(
            "def _run():\n    raise AssertionError('must not execute')\n_run()\n",
            "synthetic.py",
        ),
        namespace,
    )
    assert callable(namespace["_run"])
    for source in ("_run(1)", "result = _run()", "other()"):
        _reject(
            lambda: diagnostic.baseline_definitions(source, "synthetic.py")
        )
    with tempfile.TemporaryDirectory() as temporary:
        directory = pathlib.Path(temporary)
        fixture = directory / "fixture"
        fixture.write_bytes(b"unchanged fixture")
        for failure in (
            RuntimeError("RPC failed"),
            SystemExit("RPC exited"),
            KeyboardInterrupt("interrupted"),
        ):
            record = {"status": "failed", "error": "original failure"}
            with (
                mock.patch.object(
                    diagnostic.baseline,
                    "_close_documents",
                    side_effect=failure,
                ),
                mock.patch.object(
                    diagnostic,
                    "_sources",
                    return_value={"source.py": "d" * 64},
                ),
            ):
                diagnostic._finish_sample(record, fixture, directory, object())
            saved = json.loads((directory / "sample.json").read_text())
            assert saved["status"] == "failed"
            assert saved["error"] == "original failure"
            assert saved["cleanup_error"] == repr(failure)
            assert saved["fixture_after"] == diagnostic.baseline._hash(fixture)
            assert fixture.read_bytes() == b"unchanged fixture"
        with (
            mock.patch.object(
                diagnostic.baseline,
                "_close_documents",
                return_value={"remaining": []},
            ),
            mock.patch.object(
                diagnostic,
                "_sources",
                side_effect=SystemExit("source exited"),
            ),
        ):
            record = {"status": "completed"}
            diagnostic._finish_sample(record, fixture, directory, object())
        saved = json.loads((directory / "sample.json").read_text())
        assert saved["status"] == "failed" and "preservation_error" in saved


def main():
    validate_reconciliation()
    validate_preservation_rejections()
    validate_observer_and_restoration()
    validate_definition_loader_and_failed_receipts()
    print(SENTINEL)


if __name__ == "__main__":
    main()
