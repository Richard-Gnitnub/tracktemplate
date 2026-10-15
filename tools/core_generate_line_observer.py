"""Measure inclusive source-line visits in one unchanged run_macro call.

Only the selected code object's local monitoring events are enabled.
Intervals include called Python/native code, modal GUI and harness work,
and observer cost. They are not pure native-call or product-stage costs.
"""

import ast
import hashlib
from pathlib import Path
import sys
import threading
import time
import types


PROFILE = "phase9b-core-generate-lines-v1"
SENTINEL = "CORE_GENERATE_LINES_PASS"
CLOCKS = ("wall", "process_cpu")


def _source_mapping(path, first_line, line_numbers):
    if type(first_line) is not int or first_line < 1:
        raise ValueError("Invalid source first line")
    source = path.read_bytes()
    tree = ast.parse(source, filename=str(path))
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_macro"
        and node.lineno == first_line
    ]
    if len(functions) != 1:
        raise ValueError("Source function identity is ambiguous")
    function = functions[0]
    statements = [
        node for node in ast.walk(function) if isinstance(node, ast.stmt)
    ]
    text = source.decode("utf-8").splitlines()
    mapping = []
    if (
        not line_numbers
        or any(type(line) is not int for line in line_numbers)
        or line_numbers != sorted(set(line_numbers))
    ):
        raise ValueError("Executable source lines are invalid")
    for line in line_numbers:
        contexts = [
            node
            for node in statements
            if node.lineno <= line <= node.end_lineno
        ]
        if not contexts:
            raise ValueError("Executable line has no source context")
        context = min(
            contexts,
            key=lambda node: (node.end_lineno - node.lineno, -node.col_offset),
        )
        mapping.append(
            {
                "line": line,
                "text": text[line - 1],
                "statement_start": context.lineno,
                "statement_end": context.end_lineno,
                "statement_type": type(context).__name__,
            }
        )
    return {
        "filename": str(path),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "first_line": first_line,
        "last_line": function.end_lineno,
        "qualname": "run_macro",
        "lines": mapping,
    }


def source_record(code):
    """Prove code/source equality in its own runtime before observing it."""
    path = Path(code.co_filename).resolve(strict=True)
    compiled = compile(path.read_bytes(), code.co_filename, "exec")
    candidates = [
        item
        for item in compiled.co_consts
        if isinstance(item, types.CodeType)
        and item.co_name == "run_macro"
        and item.co_firstlineno == code.co_firstlineno
    ]
    if (
        len(candidates) != 1
        or candidates[0] != code
        or code.co_qualname != "run_macro"
    ):
        raise ValueError("Live run_macro differs from its source")
    record = _source_mapping(
        path,
        code.co_firstlineno,
        sorted({line for _, _, line in code.co_lines() if line}),
    )
    record.update(
        bytecode_sha256=hashlib.sha256(code.co_code).hexdigest(),
        python_version=list(sys.version_info[:3]),
        source_compilation_verified=True,
    )
    return record


def validate_lines(action, record):
    """Reject invented provenance, gaps, overlaps or unlabelled visits."""
    from tools import core_generate_attribution as attribution

    attribution.validate_attribution(action, record)
    metadata = record.get("source", {})
    path = Path(metadata.get("filename", "")).resolve(strict=True)
    version = metadata.get("python_version")
    digest = metadata.get("bytecode_sha256", "")
    if (
        not isinstance(version, list)
        or len(version) != 3
        or any(type(value) is not int or value < 0 for value in version)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
        or metadata.get("source_compilation_verified") is not True
    ):
        raise ValueError("Missing host code/source verification")
    # The launcher uses Python 3.12; qualified FreeCAD uses Python 3.13.
    # Bytecode is host provenance, not a cross-version comparison oracle.
    expected_source = _source_mapping(
        path,
        metadata.get("first_line"),
        [item.get("line") for item in metadata.get("lines", [])],
    )
    expected_source.update(
        python_version=version,
        bytecode_sha256=digest,
        source_compilation_verified=True,
    )
    if metadata != expected_source:
        raise ValueError("Line-source provenance differs")
    if record.get("code_identity_preserved") is not True:
        raise ValueError("Live code identity changed")
    expected = {
        "name": "run_macro",
        "classification": "operator action",
        "filename": metadata["filename"],
        "first_line": metadata["first_line"],
        "qualname": metadata["qualname"],
    }
    if record.get("mapping") != [expected]:
        raise ValueError("Root source mapping differs")
    spans = record["spans"]
    root, visits = spans[0], spans[1:]
    valid_lines = {item["line"] for item in metadata["lines"]}
    if not visits:
        raise ValueError("No source-line visits")
    for index, visit in enumerate(visits):
        line = visit.get("source_line")
        if (
            type(line) is not int
            or line not in valid_lines
            or visit["parent"] != 0
            or visit["name"] != "source_line_{}".format(line)
            or visit["classification"] != "nested component"
        ):
            raise ValueError("Invalid source-line visit")
        for clock in CLOCKS:
            next_start = (
                visits[index + 1][clock + "_start_ns"]
                if index + 1 < len(visits)
                else root[clock + "_end_ns"]
            )
            if visit[clock + "_end_ns"] != next_start:
                raise ValueError("Source-line visits are not consecutive")
    return record


class LineObserver:
    """Own one unused monitoring slot, without global profile dispatch."""

    def __init__(self, function):
        self.function = function
        self.code = function.__code__
        self.source = source_record(self.code)
        self.mapping = [
            {
                "name": "run_macro",
                "classification": "operator action",
                **{
                    key: self.source[key]
                    for key in ("filename", "first_line", "qualname")
                },
            }
        ]
        self.valid_lines = {item["line"] for item in self.source["lines"]}
        self.spans = []
        self.errors = []
        self.restored = False
        self.slot = None
        self.active = None
        self.returned = False
        self.thread = threading.get_ident()
        self.monitoring = sys.monitoring
        events = self.monitoring.events
        self.callbacks = {
            events.PY_START: self._start,
            events.LINE: self._line,
            events.PY_RETURN: self._return,
        }
        self.mask = events.PY_START | events.LINE | events.PY_RETURN
        self.owner = "TrackTemplate source lines {}".format(id(self))

    def _start(self, code, offset):
        self._event("start", code, offset)

    def _line(self, code, line):
        self._event("line", code, line)

    def _return(self, code, offset, _value):
        self._event("return", code, offset)

    def _event(self, event, code, position):
        try:
            if code is not self.code or threading.get_ident() != self.thread:
                raise ValueError("Unexpected code or thread in local observer")
            if self.errors:
                return
            stamp = {
                "wall": time.perf_counter_ns(),
                "process_cpu": time.process_time_ns(),
            }
            if event == "start":
                if self.spans:
                    raise ValueError("Repeated or reentrant run_macro")
                self.spans.append(
                    {
                        "id": 0,
                        "parent": None,
                        "name": "run_macro",
                        "classification": "operator action",
                        **{
                            clock + "_start_ns": value
                            for clock, value in stamp.items()
                        },
                    }
                )
                return
            if not self.spans or self.returned:
                raise ValueError("Event outside the one run_macro call")
            if self.active is not None:
                self.active.update(
                    {
                        clock + "_end_ns": value
                        for clock, value in stamp.items()
                    }
                )
            if event == "line":
                if position not in self.valid_lines:
                    raise ValueError("Line is absent from compiled source")
                self.active = {
                    "id": len(self.spans),
                    "parent": 0,
                    "name": "source_line_{}".format(position),
                    "source_line": position,
                    "classification": "nested component",
                    **{
                        clock + "_start_ns": value
                        for clock, value in stamp.items()
                    },
                }
                self.spans.append(self.active)
            else:
                self.spans[0].update(
                    {
                        clock + "_end_ns": value
                        for clock, value in stamp.items()
                    }
                )
                self.returned = True
                self.active = None
        except BaseException as error:
            # Instrumentation must not replace a product exception.
            self.errors.append(type(error).__name__ + ": " + str(error))

    def __enter__(self):
        monitoring = self.monitoring
        slots = [
            slot for slot in range(3, 6) if monitoring.get_tool(slot) is None
        ]
        if not slots:
            raise RuntimeError("No unused monitoring slot")
        self.slot = slots[0]
        if monitoring.get_events(self.slot) or monitoring.get_local_events(
            self.slot, self.code
        ):
            raise RuntimeError("Unused slot has existing event configuration")
        monitoring.use_tool_id(self.slot, self.owner)
        try:
            # CPython has no callback getter. Inspect and restore before
            # installing anything; even an unclaimed slot can be dirty.
            for event in sorted(set(vars(monitoring.events).values())):
                if not event or event & (event - 1):
                    continue
                previous = monitoring.register_callback(self.slot, event, None)
                if previous is not None:
                    monitoring.register_callback(self.slot, event, previous)
                    raise RuntimeError("Unused slot has an existing callback")
            for event, callback in self.callbacks.items():
                monitoring.register_callback(self.slot, event, callback)
            monitoring.set_local_events(self.slot, self.code, self.mask)
        except BaseException:
            monitoring.set_local_events(self.slot, self.code, 0)
            for event, callback in self.callbacks.items():
                previous = monitoring.register_callback(self.slot, event, None)
                if previous is not None and previous is not callback:
                    monitoring.register_callback(self.slot, event, previous)
            monitoring.free_tool_id(self.slot)
            raise
        return self

    def __exit__(self, kind, _value, _traceback):
        monitoring = self.monitoring
        try:
            if monitoring.get_tool(self.slot) != self.owner:
                raise RuntimeError("Monitoring slot ownership changed")
            if (
                monitoring.get_events(self.slot)
                or monitoring.get_local_events(self.slot, self.code)
                != self.mask
            ):
                self.errors.append("Monitoring event configuration changed")
            monitoring.set_local_events(self.slot, self.code, 0)
            foreign = False
            for event, callback in self.callbacks.items():
                previous = monitoring.register_callback(self.slot, event, None)
                if previous is not callback:
                    self.errors.append("Monitoring callback ownership changed")
                    if previous is not None:
                        foreign = True
                        monitoring.register_callback(
                            self.slot, event, previous
                        )
            if foreign or monitoring.get_events(self.slot):
                raise RuntimeError("Foreign monitoring state retained")
            monitoring.free_tool_id(self.slot)
            self.restored = (
                monitoring.get_tool(self.slot) is None
                and monitoring.get_local_events(self.slot, self.code) == 0
                and monitoring.get_events(self.slot) == 0
            )
        except BaseException as error:
            self.errors.append(type(error).__name__ + ": " + str(error))
        if kind is not None or not self.returned:
            self.errors.append("Action raised or run_macro did not return")
        if self.function.__code__ is not self.code:
            self.errors.append("Live run_macro code identity changed")
        return False

    def result(self, action):
        from tools import core_generate_attribution as attribution

        if self.errors or not self.restored or not self.returned:
            raise ValueError("Invalid line observer: " + repr(self.errors))
        record = attribution.reconcile_spans(action, self.spans, self.mapping)
        record.update(source=self.source, code_identity_preserved=True)
        return validate_lines(action, record)
