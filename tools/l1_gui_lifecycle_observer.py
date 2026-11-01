"""Observe one unchanged hosted GUI journey without changing host state.

Importing this module does nothing. ``install`` verifies fixed source bytes
and arms a thread-local trace before the original suite schedules its test.
Capture errors are retained separately and never replace product exceptions.
COMPLETE describes diagnostic capture, never a product qualification.
"""

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
from types import CodeType


ROOT = Path(__file__).resolve().parents[1]
EVENTS = "lifecycle-events.jsonl"
REPORT = "lifecycle-diagnostic.json"
MAX_EVENTS = 256
MAX_EVENT_BYTES = 65536
MAX_REPORT_BYTES = 32768
SOURCE_HASHES = {
    "tests/hosted_l1_gui_suite.py":
        "1150aab0a68d75a9048bbfd096f60f270d8f452c7333ab692ba063fd878e7012",
    "tracktemplate/adapters/freecad/chair_reference_preview.py":
        "3869a12c81d7ed0eca56547dfe66da87283adfa29952b19a7967149652424604",
    "tracktemplate/adapters/freecad/core_export_document.py":
        "5193247bbc5b744ff8221b478f01def148b78b771f8cdf12a7016e12a936f837",
}
_PREDICATES = ("active", "registry", "selection", "preselection")
_CASES = (("reference-600", 600.0), ("changed-900", 900.0),
          ("returned-600", 600.0))
_GUARD_LINES = frozenset(range(402, 407))
_EVENT_NAMES = frozenset({
    "test_start", "entry", "baseline", "pre_guard", "helper_return",
    "guard_evaluated", "product_exception", "after_cleanup",
    "product_return", "test_exception", "test_finished",
})


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _code_key(code):
    return code.co_filename, code.co_firstlineno, code.co_name


def _nested_codes(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _nested_codes(value)


def _source_codes(root):
    """Compile verified sources without importing or executing their code."""
    wanted = {
        "test": "L1Gui.test_authorised_gui_stage",
        "journey": "L1Gui._journey", "target": "_materialise_preview",
        "require": "_require", "active": "_active_document",
        "registry": "_same_registry", "selection": "_selection_snapshot",
        "preselection": "_preselection_snapshot",
    }
    result = {}
    for name, digest in SOURCE_HASHES.items():
        path = root / name
        _require(not path.is_symlink(), "Diagnostic source is a symlink")
        source = path.read_bytes()
        _require(hashlib.sha256(source).hexdigest() == digest,
                 "Diagnostic source identity differs: " + name)
        compiled = compile(source, str(path), "exec", dont_inherit=True,
                           optimize=0)
        for code in _nested_codes(compiled):
            for key, qualname in wanted.items():
                if code.co_qualname == qualname:
                    _require(key not in result, "Ambiguous diagnostic code")
                    result[key] = code
    _require(set(result) == set(wanted), "Diagnostic code binding incomplete")
    return result


def _directory(path):
    path = Path(path).absolute()
    _require(path == path.resolve(strict=True),
             "Diagnostic directory must not traverse a symlink")
    metadata = path.stat()
    _require(stat.S_ISDIR(metadata.st_mode) and metadata.st_uid == os.getuid()
             and not metadata.st_mode & 0o022,
             "Diagnostic directory is not privately owned")
    return path


def _text(value, limit=512):
    _require(isinstance(value, str) and len(value) <= limit,
             "Diagnostic text exceeds its bound")
    return value


def _token(value, name=None):
    if value is None:
        return None
    return {"identity": hex(id(value)),
            "name": _text(value.Name if name is None else name)}


def _registry(documents):
    _require(len(documents) <= 32, "Diagnostic registry exceeds its bound")
    return [_token(document, name) for name, document in documents.items()]


def _selection(value):
    _require(len(value) <= 64, "Diagnostic selection exceeds its bound")
    result = []
    for name, obj_name, document, obj, subnames, points, whole in value:
        _require(len(subnames) == len(points) <= 64,
                 "Diagnostic selection points exceed their bound")
        result.append({
            "document": _token(document, name),
            "object": _token(obj, obj_name),
            "subelements": [_text(item) for item in subnames],
            "points": points, "whole": whole,
        })
    return result


def _preselection(value):
    if value is None:
        return None
    name, obj_name, document, obj, subname, point = value
    return {"document": _token(document, name),
            "object": _token(obj, obj_name),
            "subelement": _text(subname), "point": point}


def _exception(error, line=None):
    try:
        message = str(error)[:1024]
    except BaseException:
        message = "Exception text unavailable"
    return {"type": type(error).__name__[:128], "message": message,
            "line": line}


def _coverage(events):
    """Require the intended boundary, with the unchanged case continuation."""
    entries = [row for row in events if row["event"] == "entry"]
    guards = [row for row in events if row["event"] == "guard_evaluated"]
    failed = [row for row in guards if row["condition"] is False]
    expected = _CASES[:2] if failed else _CASES
    _require([(row["case"], row["radius_mm"]) for row in entries]
             == list(expected), "Diagnostic case coverage is incomplete")
    _require(len(guards) == len(entries), "Diagnostic guards are incomplete")
    _require(not failed or (len(failed) == 1
                           and failed[0]["case"] == "changed-900"),
             "Diagnostic failure is outside the selected boundary")
    for entry in entries:
        records = [row for row in events
                   if row.get("invocation") == entry["invocation"]]
        phases = [row["event"] for row in records]
        for phase in ("entry", "baseline", "pre_guard", "guard_evaluated",
                      "product_return"):
            _require(phases.count(phase) == 1,
                     "Diagnostic boundary missing or repeated: " + phase)
        guard = next(row for row in records
                     if row["event"] == "guard_evaluated")
        actual = guard["predicates"]
        _require(set(actual) == set(_PREDICATES),
                 "Actual guard predicates are incomplete")
        evaluated = [actual[key] for key in _PREDICATES]
        if guard["condition"] is True:
            _require(evaluated == [True] * 4,
                     "Successful guard return observations disagree")
        else:
            _require(False in evaluated, "False guard operand was not observed")
            first_false = evaluated.index(False)
            _require(evaluated[:first_false] == [True] * first_false
                     and evaluated[first_false + 1:]
                     == ["NOT_EVALUATED"] * (3 - first_false),
                     "Guard short-circuit observations disagree")
            _require("product_exception" in phases
                     and phases.count("after_cleanup") == 1,
                     "Diagnostic failure cleanup was not captured")
    return bool(failed)


class _Observer:
    """Keep only bounded scalar records, never host frames or geometry."""

    def __init__(self, directory, codes):
        self.directory = _directory(directory)
        self.codes = codes
        self.lookup = {_code_key(code): key for key, code in codes.items()}
        self.bound = {}
        self.invocations = {}
        self.calls = 0
        self.events = []
        self.errors = []
        self.digest = hashlib.sha256()
        self.original_test_exception = None
        self.test_finished = False
        self.trace_restored = False
        self.callback = self._trace
        self.event_stream = None
        self.report_stream = None
        self.readers = None
        self.started = None

    def start(self):
        _require(sys.gettrace() is None, "A trace is already installed")
        _require(not sys.flags.optimize, "Optimised diagnostic code is unsafe")
        for name in (EVENTS, REPORT):
            path = self.directory / name
            if path.exists() or path.is_symlink():
                raise FileExistsError(str(path))
        try:
            for name, attribute in ((EVENTS, "event_stream"),
                                    (REPORT, "report_stream")):
                descriptor = os.open(
                    self.directory / name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                )
                setattr(self, attribute,
                        os.fdopen(descriptor, "w", encoding="utf-8"))
            self._report("INCOMPLETE")
            self.started = time.monotonic()
            sys.settrace(self.callback)
            _require(sys.gettrace() is self.callback,
                     "Diagnostic trace installation failed")
        except BaseException:
            for stream in (self.event_stream, self.report_stream):
                if stream is not None:
                    stream.close()
            raise

    def _latch(self, error, context):
        if len(self.errors) < 16:
            self.errors.append({"context": context, **_exception(error)})

    def _emit(self, event, invocation=None, **fields):
        _require(event in _EVENT_NAMES, "Unknown diagnostic event")
        _require(len(self.events) < MAX_EVENTS,
                 "Diagnostic event count exceeds its bound")
        row = {"schema": 1, "sequence": len(self.events) + 1,
               "event": event,
               "elapsed_seconds": time.monotonic() - self.started, **fields}
        if invocation is not None:
            row.update(invocation=invocation["number"],
                       case=invocation["case"],
                       radius_mm=invocation["radius_mm"])
        text = json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
        encoded = text.encode("utf-8")
        _require(len(encoded) <= MAX_EVENT_BYTES,
                 "Diagnostic event size exceeds its bound")
        self.event_stream.write(text)
        self.event_stream.flush()
        self.digest.update(encoded)
        self.events.append(row)

    def _case(self, frame):
        caller = frame.f_back
        while caller is not None:
            if caller.f_code is self.bound.get("journey"):
                label = caller.f_locals.get("label")
                radius = caller.f_locals.get("radius")
                _require((label, radius) in _CASES,
                         "Diagnostic case identity is not the original case")
                return label, radius
            caller = caller.f_back
        raise ValueError("Original diagnostic journey frame is absent")

    def _snapshot(self, frame, phase):
        local = frame.f_locals
        if phase == "test_finished":
            app, gui = local["app"], local["gui"]
            read_selection, read_preselection = self.readers
        else:
            app = frame.f_globals["App"]
            gui = local.get("gui") or sys.modules.get("FreeCADGui")
            read_selection = frame.f_globals["_selection_snapshot"]
            read_preselection = frame.f_globals["_preselection_snapshot"]
        observed = dict(app.listDocuments())
        method = app.activeDocument()
        attribute = app.ActiveDocument
        selection = read_selection(app, gui)
        preselection = read_preselection(app, gui)
        gui_state = None
        if gui is not None:
            gui_state = {}
            for name, document in (("method", gui.activeDocument()),
                                   ("attribute", gui.ActiveDocument)):
                gui_state[name] = (
                    None if document is None else _token(document.Document)
                )
                view = None if document is None else document.activeView()
                gui_state[name + "_view_identity"] = (
                    None if view is None else hex(id(view))
                )
                gui_state[name + "_camera"] = (
                    None if view is None else _text(view.getCamera(), 8192)
                )
        result = {
            "app_active_method": _token(method),
            "app_active_attribute": _token(attribute),
            "app_active_references_agree": method is attribute,
            "registry": _registry(observed), "selection": _selection(selection),
            "preselection": _preselection(preselection), "gui": gui_state,
            "local_view_identity": (
                hex(id(local["view"])) if "view" in local else None
            ),
            "local_view_camera": (
                _text(local["view"].getCamera(), 8192)
                if "view" in local and observed.get(local.get("name"))
                is local.get("document") else None
            ),
            "expected": None, "sampled_predicates": {},
        }
        if phase in ("entry", "test_finished"):
            return result
        expected = local["expected"] if phase == "pre_guard" else local["previous"]
        active = local["document"] if phase == "pre_guard" else local["active"]
        result["expected"] = {
            "registry": _registry(expected),
            "active": _token(active),
            "selection": _selection(local["selection"]),
            "preselection": _preselection(local["preselection"]),
        }
        result["sampled_predicates"] = {
            "active": method is attribute and method is active,
            "registry": set(observed) == set(expected) and all(
                observed[name] is document
                for name, document in expected.items()
            ),
            "selection": selection == local["selection"],
            "preselection": preselection == local["preselection"],
        }
        return result

    def _trace(self, frame, event, arg):
        # A trace exception would disable tracing and alter product control
        # flow. Latch all capture errors and let original cleanup continue.
        try:
            return self._dispatch(frame, event, arg)
        except BaseException as error:
            self._latch(error, event + ":" + frame.f_code.co_name)
            if (id(frame) in self.invocations
                    or frame.f_code is self.bound.get("test")):
                return self.callback
            return None

    def _dispatch(self, frame, event, arg):
        key = self.lookup.get(_code_key(frame.f_code))
        if key is None:
            return None
        if event == "call":
            _require(frame.f_code == self.codes[key],
                     "Executed diagnostic code differs from fixed source")
            self.bound[key] = frame.f_code
            if key == "journey":
                return None
            if key == "test":
                frame.f_trace_lines = False
                self._emit("test_start")
                return self.callback
            if key == "target":
                self.readers = (frame.f_globals["_selection_snapshot"],
                                frame.f_globals["_preselection_snapshot"])
                label, radius = self._case(frame)
                self.calls += 1
                invocation = {
                    "number": self.calls, "case": label,
                    "radius_mm": radius, "seen": set(),
                    "predicates": dict.fromkeys(_PREDICATES, "NOT_EVALUATED"),
                    "exception": None,
                }
                self.invocations[id(frame)] = invocation
                self._emit("entry", invocation,
                           state=self._snapshot(frame, "entry"))
                return self.callback
            parent = frame.f_back
            invocation = self.invocations.get(id(parent))
            if invocation is None or parent.f_lineno not in _GUARD_LINES:
                return None
            if key == "require":
                condition = frame.f_locals["condition"]
                _require(type(condition) is bool and frame.f_locals["message"]
                         == "preview changed unrelated document or selection state",
                         "Original lifecycle guard binding differs")
                self._emit("guard_evaluated", invocation, condition=condition,
                           predicates=dict(invocation["predicates"]))
                return None
            if key in _PREDICATES:
                frame.f_trace_lines = False
                return self.callback
            return None
        if key == "test":
            if event == "exception":
                self.original_test_exception = _exception(arg[1], frame.f_lineno)
                self._emit("test_exception", exception=self.original_test_exception)
            elif event == "return":
                self._finish(frame)
            return self.callback
        if key in _PREDICATES and event == "return":
            parent = frame.f_back
            invocation = self.invocations[id(parent)]
            if key == "active":
                value = arg is parent.f_locals["document"]
                observed = _token(arg)
                expected = _token(parent.f_locals["document"])
            elif key == "registry":
                value = arg
                observed = _registry(frame.f_locals["observed"])
                expected = _registry(frame.f_locals["expected"])
            else:
                value = arg == parent.f_locals[key]
                serialise = _selection if key == "selection" else _preselection
                observed = serialise(arg)
                expected = serialise(parent.f_locals[key])
            _require(type(value) is bool, "Actual predicate is not a boolean")
            invocation["predicates"][key] = value
            self._emit("helper_return", invocation, predicate=key, value=value,
                       observed=observed, expected=expected)
            return self.callback
        if key != "target":
            return self.callback
        invocation = self.invocations[id(frame)]
        if event == "line":
            phase = {350: "baseline", 402: "pre_guard",
                     422: "after_cleanup"}.get(frame.f_lineno)
            if phase is not None and phase not in invocation["seen"]:
                invocation["seen"].add(phase)
                fields = {"state": self._snapshot(frame, phase)}
                if phase == "after_cleanup":
                    fields.update(
                        cleanup_errors=[_text(item, 1024)
                                        for item in frame.f_locals["errors"]],
                        cleanup_interruption=(
                            None if frame.f_locals["interruption"] is None
                            else _exception(frame.f_locals["interruption"])
                        ),
                    )
                self._emit(phase, invocation, **fields)
        elif event == "exception":
            invocation["exception"] = _exception(arg[1], frame.f_lineno)
            self._emit("product_exception", invocation,
                       exception=invocation["exception"],
                       before_cleanup=frame.f_lineno in _GUARD_LINES,
                       state=self._snapshot(frame, "pre_guard")
                       if frame.f_lineno in _GUARD_LINES else None)
        elif event == "return":
            self._emit("product_return", invocation,
                       exception=invocation["exception"],
                       returned_result=isinstance(arg, dict))
            del self.invocations[id(frame)]
        return self.callback

    def _report(self, status):
        report = {
            "schema": 1, "status": status, "source_hashes": SOURCE_HASHES,
            "events_file": EVENTS, "events_sha256": self.digest.hexdigest(),
            "event_count": len(self.events), "errors": self.errors,
            "test_finished": self.test_finished,
            "trace_restored": self.trace_restored,
            "observed_failure": any(
                row["event"] == "guard_evaluated" and row["condition"] is False
                for row in self.events
            ),
            "original_test_exception": self.original_test_exception,
        }
        text = json.dumps(report, sort_keys=True, allow_nan=False) + "\n"
        _require(len(text.encode("utf-8")) <= MAX_REPORT_BYTES,
                 "Diagnostic report exceeds its bound")
        self.report_stream.seek(0)
        self.report_stream.write(text)
        self.report_stream.truncate()
        self.report_stream.flush()

    def _finish(self, frame):
        self.test_finished = True
        try:
            if sys.gettrace() is self.callback:
                sys.settrace(None)
                self.trace_restored = sys.gettrace() is None
            _require(self.trace_restored, "Diagnostic trace ownership changed")
            self._emit("test_finished",
                       state=self._snapshot(frame, "test_finished"))
            _coverage(self.events)
        except BaseException as error:
            self._latch(error, "finish")
        try:
            status = "COMPLETE" if not self.errors else "INCOMPLETE"
            self._report(status)
        except BaseException as error:
            self._latch(error, "report")
        finally:
            for stream in (self.event_stream, self.report_stream):
                try:
                    stream.close()
                except BaseException as error:
                    self._latch(error, "close")


def install(output_directory):
    """Arm one observer; source/output/setup failures stop before the test."""
    _require(sys.gettrace() is None, "A trace is already installed")
    capture = _Observer(Path(output_directory), _source_codes(ROOT))
    capture.start()
    return capture


def _read(path, maximum):
    metadata = path.lstat()
    _require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
             and metadata.st_uid == os.getuid() and metadata.st_size <= maximum,
             "Unsafe or oversized diagnostic evidence file")
    return path.read_bytes()


def assess(directory):
    """Validate bounded file identities independently of the product result."""
    result = {"status": "INCOMPLETE", "observed_failure": False,
              "event_count": 0, "errors": [], "test_finished": False,
              "trace_restored": False}
    try:
        directory = _directory(directory)
        report_bytes = _read(directory / REPORT, MAX_REPORT_BYTES)
        event_bytes = _read(directory / EVENTS, MAX_EVENTS * MAX_EVENT_BYTES)
        report = json.loads(report_bytes)
        _require(report.get("schema") == 1
                 and report.get("source_hashes") == SOURCE_HASHES
                 and report.get("events_file") == EVENTS,
                 "Diagnostic report binding differs")
        result.update(report_sha256=hashlib.sha256(report_bytes).hexdigest(),
                      events_sha256=hashlib.sha256(event_bytes).hexdigest())
        _require(report.get("events_sha256") == result["events_sha256"],
                 "Diagnostic event hash differs")
        lines = event_bytes.splitlines()
        _require(len(lines) <= MAX_EVENTS
                 and all(len(line) < MAX_EVENT_BYTES for line in lines),
                 "Diagnostic event bounds differ")
        events = [json.loads(line) for line in lines]
        _require(type(report.get("event_count")) is int
                 and report["event_count"] == len(events),
                 "Diagnostic event count differs")
        for index, row in enumerate(events, 1):
            _require(row.get("schema") == 1 and row.get("sequence") == index
                     and row.get("event") in _EVENT_NAMES,
                     "Diagnostic event schema differs")
        for name in ("test_finished", "trace_restored", "observed_failure"):
            _require(type(report.get(name)) is bool,
                     "Diagnostic result flag is invalid")
            result[name] = report[name]
        result["event_count"] = len(events)
        _require(isinstance(report.get("errors"), list)
                 and len(report["errors"]) <= 16,
                 "Diagnostic capture errors are invalid")
        result["errors"] = report["errors"]
        observed = _coverage(events)
        _require(report["observed_failure"] is observed,
                 "Diagnostic failure flag differs")
        _require(report.get("status") == "COMPLETE" and not result["errors"]
                 and report["test_finished"] and report["trace_restored"]
                 and sum(row["event"] == "test_start" for row in events) == 1
                 and events[-1]["event"] == "test_finished",
                 "Diagnostic capture did not complete")
        result["status"] = "COMPLETE"
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        result["errors"] = [*result["errors"], _exception(error)]
    return result
