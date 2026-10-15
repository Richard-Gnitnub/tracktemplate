#!/usr/bin/env python3
"""Reject false source-line attribution and unsafe monitoring ownership."""

import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import threading
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import core_generate_attribution as attribution  # noqa: E402
from tools import core_generate_line_observer as lines  # noqa: E402


SENTINEL = "Core Generate source-line validation passed"
SOURCE = """def run_macro(failure=None, repeat=False):
    value = sum(
        (1, 2, 3),
    )
    if repeat:
        return run_macro()
    if failure is not None:
        raise failure
    for item in (1, 2):
        value += item
    return value
"""


def reject(operation, exception=ValueError):
    try:
        operation()
    except exception:
        return
    raise AssertionError("Invalid line evidence was accepted")


def action_for(observer):
    root = observer.spans[0]
    return {
        clock + "_ms": (
            root[clock + "_end_ns"] - root[clock + "_start_ns"] + 1000
        )
        / 1000000
        for clock in lines.CLOCKS
    }


def synthetic(function):
    observer = lines.LineObserver(function)
    with (
        mock.patch.object(
            lines.time, "perf_counter_ns", side_effect=(100, 110, 140, 180)
        ),
        mock.patch.object(
            lines.time, "process_time_ns", side_effect=(20, 21, 30, 50)
        ),
    ):
        observer._start(function.__code__, 0)
        observer._line(function.__code__, 2)
        observer._line(function.__code__, 11)
        observer._return(function.__code__, 0, 9)
    observer.restored = True
    action = {"wall_ms": 100 / 1000000, "process_cpu_ms": 35 / 1000000}
    return action, observer.result(action)


def validate_arithmetic_and_source(function, path):
    action, record = synthetic(function)
    root, first, second = record["spans"]
    assert root["remainder_ns"] == {"wall": 10, "process_cpu": 1}
    assert first["remainder_ns"] == {"wall": 30, "process_cpu": 9}
    assert second["remainder_ns"] == {"wall": 40, "process_cpu": 20}
    assert record["boundary_remainder_ns"] == {"wall": 20, "process_cpu": 5}
    mapping = {item["line"]: item for item in record["source"]["lines"]}
    assert mapping[2]["statement_start"] == 2
    assert mapping[2]["statement_end"] == 4
    assert mapping[2]["statement_type"] == "Assign"
    for change in (
        lambda data: data["spans"][1].update(source_line=9999),
        lambda data: data["spans"][1].update(name="native call"),
        lambda data: data["spans"][2].update(parent=1),
        lambda data: data["spans"][1].update(wall_end_ns=139),
        lambda data: data["spans"][2].update(wall_start_ns=139),
        lambda data: data["source"].update(source_sha256="0" * 64),
        lambda data: data["source"].update(bytecode_sha256="invalid"),
        lambda data: data["source"].update(first_line=2),
        lambda data: data["source"].update(first_line=True),
        lambda data: data["source"].update(source_compilation_verified=False),
        lambda data: data["source"].update(python_version=[3]),
        lambda data: data["source"]["lines"][1].update(text="invented"),
        lambda data: data["mapping"][0].update(first_line=2),
        lambda data: data.update(code_identity_preserved=False),
    ):
        damaged = copy.deepcopy(record)
        change(damaged)
        reject(lambda: lines.validate_lines(action, damaged))
    damaged = copy.deepcopy(record)
    damaged["spans"][2]["wall_start_ns"] = 141
    damaged["spans"][2]["remainder_ns"]["wall"] = 39
    damaged["spans"][0]["remainder_ns"]["wall"] = 11
    attribution.validate_attribution(action, damaged)
    reject(lambda: lines.validate_lines(action, damaged))
    other_runtime = copy.deepcopy(record)
    other_runtime["source"]["python_version"] = [3, 13, 15]
    lines.validate_lines(action, other_runtime)
    path.write_text(SOURCE + "# source changed\n")
    try:
        reject(lambda: lines.validate_lines(action, record))
    finally:
        path.write_text(SOURCE)
    original = function.__code__
    function.__code__ = original.replace(co_firstlineno=2)
    try:
        reject(lambda: lines.LineObserver(function))
    finally:
        function.__code__ = original


def validate_lifecycle(function):
    monitoring = sys.monitoring
    original_profile, original_trace = sys.getprofile(), sys.gettrace()
    observer = lines.LineObserver(function)
    with observer:
        assert function() == 9
    assert observer.restored and not observer.errors
    record = observer.result(action_for(observer))
    assert len(record["spans"]) > len(
        {item["name"] for item in record["spans"]}
    )
    assert monitoring.get_tool(observer.slot) is None
    assert monitoring.get_local_events(observer.slot, function.__code__) == 0
    for event in observer.callbacks:
        assert monitoring.register_callback(observer.slot, event, None) is None
    assert sys.getprofile() is original_profile
    assert sys.gettrace() is original_trace

    for failure in (
        RuntimeError("product"),
        SystemExit("exit"),
        KeyboardInterrupt("interrupt"),
    ):
        observer = lines.LineObserver(function)
        try:
            with observer:
                function(failure)
        except BaseException as error:
            assert error is failure
        else:
            raise AssertionError("Product exception changed")
        assert observer.restored and observer.errors
        reject(lambda: observer.result({}))

    observer = lines.LineObserver(function)
    with mock.patch.object(
        lines.time, "perf_counter_ns", side_effect=SystemExit("observer clock")
    ):
        with observer:
            assert function() == 9
    assert observer.restored and observer.errors
    reject(lambda: observer.result({}))

    observer = lines.LineObserver(function)
    with observer:
        assert function(repeat=True) == 9
    assert observer.restored and observer.errors
    reject(lambda: observer.result({}))

    observer = lines.LineObserver(function)
    with observer:
        thread = threading.Thread(target=function)
        thread.start()
        thread.join()
    assert observer.restored and observer.errors
    reject(lambda: observer.result({}))


def validate_ownership(function):
    monitoring = sys.monitoring
    assert all(monitoring.get_tool(slot) is None for slot in range(3, 6))
    for slot in range(3, 6):
        monitoring.use_tool_id(slot, "test existing owner")
    try:
        reject(lambda: lines.LineObserver(function).__enter__(), RuntimeError)
        assert all(
            monitoring.get_tool(slot) == "test existing owner"
            for slot in range(3, 6)
        )
    finally:
        for slot in range(3, 6):
            monitoring.free_tool_id(slot)

    def previous(*_args):
        return None

    monitoring.use_tool_id(3, "test dirty slot")
    monitoring.register_callback(3, monitoring.events.CALL, previous)
    monitoring.free_tool_id(3)
    try:
        reject(lambda: lines.LineObserver(function).__enter__(), RuntimeError)
        assert monitoring.get_tool(3) is None
        assert (
            monitoring.register_callback(3, monitoring.events.CALL, None)
            is previous
        )
    finally:
        monitoring.register_callback(3, monitoring.events.CALL, None)

    monitoring.use_tool_id(3, "test old configuration")
    monitoring.set_local_events(3, function.__code__, monitoring.events.LINE)
    monitoring.free_tool_id(3)
    try:
        reject(lambda: lines.LineObserver(function).__enter__(), RuntimeError)
        assert (
            monitoring.get_local_events(3, function.__code__)
            == monitoring.events.LINE
        )
    finally:
        monitoring.use_tool_id(3, "test configuration cleanup")
        monitoring.set_local_events(3, function.__code__, 0)
        monitoring.free_tool_id(3)

    original_set = monitoring.set_local_events

    def fail_after_activation(slot, code, mask):
        original_set(slot, code, mask)
        if mask:
            raise RuntimeError("injected after activation")

    observer = lines.LineObserver(function)
    with mock.patch.object(
        monitoring, "set_local_events", side_effect=fail_after_activation
    ):
        reject(observer.__enter__, RuntimeError)
    assert monitoring.get_tool(observer.slot) is None
    assert monitoring.get_local_events(observer.slot, function.__code__) == 0
    for event in observer.callbacks:
        assert monitoring.register_callback(observer.slot, event, None) is None


def validate_profile_separation(function):
    spec = importlib.util.spec_from_file_location(
        "retained_attribution_test",
        ROOT / "tests/validate_core_generate_attribution.py",
    )
    retained = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retained)
    samples = retained._samples()
    attribution.summarize(samples)
    reject(lambda: attribution.summarize(samples, lines.PROFILE))
    action, record = synthetic(function)
    for sample in samples:
        probe = sample["probe"]
        probe.update(profile_id=lines.PROFILE, sentinel=lines.SENTINEL)
        probe["action"].update(action)
        probe["attribution"] = (
            copy.deepcopy(record) if sample["mode"] == "observed" else None
        )
    before = copy.deepcopy(samples)
    summary = attribution.summarize(samples, lines.PROFILE)
    assert before == samples
    assert "exclusive_areas" not in summary
    areas = summary["inclusive_source_line_areas"]
    assert areas["source_line_2"]["wall_ns"]["values"] == [30, 30, 30]
    assert sum(area["wall_ns"]["values"][0] for area in areas.values()) == 100
    samples[1]["probe"]["attribution"]["source"]["python_version"] = [
        3,
        13,
        15,
    ]
    reject(lambda: attribution.summarize(samples, lines.PROFILE))
    reject(lambda: attribution.summarize(samples))
    reject(lambda: attribution.profile_settings("unknown"))


def main():
    with tempfile.TemporaryDirectory(prefix="tt-source-lines-") as directory:
        path = Path(directory) / "synthetic.py"
        path.write_text(SOURCE)
        namespace = {}
        exec(compile(SOURCE, str(path), "exec"), namespace)
        function = namespace["run_macro"]
        validate_arithmetic_and_source(function, path)
        validate_lifecycle(function)
        validate_ownership(function)
        validate_profile_separation(function)
    print(SENTINEL)


if __name__ == "__main__":
    main()
