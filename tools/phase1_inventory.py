#!/usr/bin/env python3
"""Create a deterministic, read-only structural inventory of the legacy macros.

The inventory is evidence for Phase 1.  It deliberately does not import or
execute either macro, and its responsibility labels are static signals for
review rather than architectural decisions.
"""

import argparse
import ast
import hashlib
import json
import pathlib
import re


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MACROS = (
    ("B14", "AdvancedTurnout.FCMacro"),
    (
        "B15",
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro",
    ),
)
DEFAULT_CANDIDATES = (
    (
        "curve_easement_station",
        (
            "solve_transition_length",
            "alignment_station_data",
            "interpolate_alignment_station",
        ),
    ),
    (
        "transition_length_solver",
        ("solve_transition_length",),
    ),
    (
        "alignment_station_index",
        ("alignment_station_data",),
    ),
    (
        "alignment_station_interpolation",
        ("interpolate_alignment_station",),
    ),
    (
        "chair_analysis_core",
        (
            "normalise_chair_analysis_settings",
            "generate_chair_positions",
            "validate_chair_positions",
            "analyse_chair_position_records",
        ),
    ),
)

PLATFORM_NAMES = {
    "freecad": {"App", "FreeCAD", "FreeCADGui", "Part"},
    "qt": {"QtCore", "QtGui", "QtWidgets"},
    "filesystem": {"ET", "csv", "os", "open", "shutil", "tempfile"},
    "process": {"subprocess"},
}
MUTABLE_CONSTRUCTORS = {"dict", "list", "set", "bytearray", "defaultdict"}
DOCUMENT_PARAMETER_NAMES = {
    "doc",
    "document",
    "obj",
    "object",
    "group",
    "view",
    "view_object",
}
RESPONSIBILITY_KEYWORDS = {
    "application": (
        "analyse",
        "analyze",
        "create",
        "edit",
        "invalidate",
        "preflight",
        "remove",
        "status",
        "validate",
        "workflow",
    ),
    "compatibility": ("compat", "legacy", "migrat", "upgrade"),
    "domain": (
        "alignment",
        "chair",
        "chainage",
        "crossover",
        "curve",
        "easement",
        "formation",
        "platform",
        "rail",
        "station",
        "timber",
        "track",
        "transition",
        "turnout",
    ),
    "export": ("dxf", "export", "manifest", "mesh", "step", "stl", "svg"),
    "presentation": (
        "display",
        "marker",
        "preview",
        "render",
        "scene",
        "visibility",
        "visible",
    ),
    "ui": ("dialog", "panel", "widget", "window"),
}


def _call_path(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_path(node.value)
        return "{}.{}".format(prefix, node.attr) if prefix else node.attr
    return ""


def _target_paths(node):
    if isinstance(node, (ast.Name, ast.Attribute)):
        path = _call_path(node)
        return [path] if path else []
    if isinstance(node, (ast.Tuple, ast.List)):
        return [path for item in node.elts for path in _target_paths(item)]
    return []


def _module_scope(statements, context=()):
    """Yield statements that execute in module scope without entering defs."""

    for statement in statements:
        yield statement, context
        line = getattr(statement, "lineno", 0)
        if isinstance(statement, ast.If):
            yield from _module_scope(statement.body, context + ("if@{}".format(line),))
            yield from _module_scope(statement.orelse, context + ("else@{}".format(line),))
        elif isinstance(statement, (ast.For, ast.While)):
            kind = statement.__class__.__name__.lower()
            yield from _module_scope(statement.body, context + ("{}@{}".format(kind, line),))
            yield from _module_scope(statement.orelse, context + ("else@{}".format(line),))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            yield from _module_scope(statement.body, context + ("with@{}".format(line),))
        elif isinstance(statement, ast.Try):
            yield from _module_scope(statement.body, context + ("try@{}".format(line),))
            for handler in statement.handlers:
                yield from _module_scope(
                    handler.body,
                    context + ("except@{}".format(getattr(handler, "lineno", line)),),
                )
            yield from _module_scope(statement.orelse, context + ("else@{}".format(line),))
            yield from _module_scope(statement.finalbody, context + ("finally@{}".format(line),))


def _value_kind(value):
    if value is None:
        return "none"
    return value.__class__.__name__.lower()


def _is_mutable_value(value):
    if isinstance(
        value,
        (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp),
    ):
        return True
    if isinstance(value, ast.Call):
        return _call_path(value.func).split(".")[-1] in MUTABLE_CONSTRUCTORS
    return False


def _assignment_parts(statement):
    if isinstance(statement, ast.Assign):
        return [path for target in statement.targets for path in _target_paths(target)], statement.value
    if isinstance(statement, ast.AnnAssign):
        return _target_paths(statement.target), statement.value
    if isinstance(statement, ast.AugAssign):
        return _target_paths(statement.target), statement.value
    return [], None


def _definition_usage(node):
    calls = set()
    references = set()
    globals_declared = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            path = _call_path(child.func)
            if path:
                calls.add(path)
        elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            references.add(child.id)
        elif isinstance(child, ast.Global):
            globals_declared.update(child.names)
    parameters = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        arguments = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
        if node.args.vararg is not None:
            arguments.append(node.args.vararg)
        if node.args.kwarg is not None:
            arguments.append(node.args.kwarg)
        parameters = [argument.arg for argument in arguments]
    return {
        "calls": sorted(calls),
        "references": sorted(references),
        "globals_declared": sorted(globals_declared),
        "parameters": parameters,
    }


def _platform_signals(usage):
    references = set(usage["references"])
    calls = usage["calls"]
    result = []
    for signal, roots in PLATFORM_NAMES.items():
        if references.intersection(roots) or any(call.split(".")[0] in roots for call in calls):
            result.append(signal)
    if set(usage["parameters"]).intersection(DOCUMENT_PARAMETER_NAMES):
        result.append("document_parameter")
    return sorted(result)


def _responsibility_signals(name, usage, platform_signals):
    lowered = name.lower()
    result = {
        responsibility
        for responsibility, keywords in RESPONSIBILITY_KEYWORDS.items()
        if any(keyword in lowered for keyword in keywords)
    }
    if "qt" in platform_signals:
        result.add("ui")
    if "freecad" in platform_signals or "document_parameter" in platform_signals:
        result.add("freecad_adapter")
    if re.search(r"_v\d+(?:_|$)", lowered):
        result.add("compatibility")
    return sorted(result or {"unclassified"})


def _relative_path(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def analyse_source(
    path,
    label,
    candidates=DEFAULT_CANDIDATES,
    dependency_depth=2,
    caller_depth=4,
):
    path = pathlib.Path(path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    scoped_statements = list(_module_scope(tree.body))

    definitions = []
    contexts = {id(statement): context for statement, context in scoped_statements}
    for statement, context in scoped_statements:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        usage = _definition_usage(statement)
        platform = _platform_signals(usage)
        definitions.append(
            {
                "key": "{}@{}".format(statement.name, statement.lineno),
                "name": statement.name,
                "kind": "class" if isinstance(statement, ast.ClassDef) else "function",
                "line": statement.lineno,
                "end_line": statement.end_lineno,
                "line_count": statement.end_lineno - statement.lineno + 1,
                "context": list(context),
                "calls": usage["calls"],
                "references": usage["references"],
                "globals_declared": usage["globals_declared"],
                "parameters": usage["parameters"],
                "platform_signals": platform,
                "responsibility_signals": _responsibility_signals(statement.name, usage, platform),
            }
        )
    definitions.sort(key=lambda item: (item["line"], item["name"]))

    definitions_by_name = {}
    definitions_by_key = {}
    for record in definitions:
        definitions_by_name.setdefault(record["name"], []).append(record)
        definitions_by_key[record["key"]] = record
    for records in definitions_by_name.values():
        for index, record in enumerate(records, 1):
            record["occurrence"] = index
            record["occurrence_count"] = len(records)
            record["active"] = index == len(records)

    imports = []
    assignments = []
    module_calls = []
    for statement, context in scoped_statements:
        if isinstance(statement, ast.Import):
            imports.append(
                {
                    "line": statement.lineno,
                    "context": list(context),
                    "module": "",
                    "names": [alias.name for alias in statement.names],
                }
            )
        elif isinstance(statement, ast.ImportFrom):
            imports.append(
                {
                    "line": statement.lineno,
                    "context": list(context),
                    "module": statement.module or "",
                    "names": [alias.name for alias in statement.names],
                }
            )
        targets, value = _assignment_parts(statement)
        if targets:
            value_path = _call_path(value) if isinstance(value, (ast.Name, ast.Attribute)) else ""
            value_calls = []
            if value is not None:
                value_calls = sorted(
                    {
                        _call_path(child.func)
                        for child in ast.walk(value)
                        if isinstance(child, ast.Call) and _call_path(child.func)
                    }
                )
            assignments.append(
                {
                    "line": statement.lineno,
                    "context": list(contexts.get(id(statement), context)),
                    "targets": targets,
                    "value_kind": _value_kind(value),
                    "value_path": value_path,
                    "value_calls": value_calls,
                    "mutable_value": _is_mutable_value(value),
                }
            )
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            module_calls.append(
                {
                    "line": statement.lineno,
                    "context": list(context),
                    "call": _call_path(statement.value.func),
                }
            )

    active_by_name = {name: records[-1] for name, records in definitions_by_name.items()}
    aliases = []
    patches = []
    for assignment in assignments:
        for target in assignment["targets"]:
            source_path = assignment["value_path"]
            if "." in target:
                patches.append(
                    {
                        "line": assignment["line"],
                        "target": target,
                        "source": source_path,
                    }
                )
            elif source_path:
                source_key = ""
                if "." not in source_path and source_path in definitions_by_name:
                    earlier = [
                        record
                        for record in definitions_by_name[source_path]
                        if record["line"] < assignment["line"]
                    ]
                    if earlier:
                        source_key = earlier[-1]["key"]
                elif "." in source_path and source_path.split(".", 1)[0] in definitions_by_name:
                    source_key = source_path
                if source_key:
                    aliases.append(
                        {
                            "line": assignment["line"],
                            "target": target,
                            "source": source_path,
                            "source_key": source_key,
                        }
                    )

    alias_by_name = {alias["target"]: alias for alias in aliases}

    def resolve_bare_call(name):
        alias = alias_by_name.get(name)
        if alias is not None and alias["source_key"] in definitions_by_key:
            return alias["source_key"]
        record = active_by_name.get(name)
        return record["key"] if record is not None else ""

    edges = {}
    for record in definitions:
        targets = set()
        for call in record["calls"]:
            if "." not in call:
                resolved = resolve_bare_call(call)
                if resolved:
                    targets.add(resolved)
        edges[record["key"]] = sorted(targets, key=lambda key: definitions_by_key[key]["line"])

    live_keys = {record["key"] for record in active_by_name.values()}
    live_keys.update(
        alias["source_key"] for alias in aliases if alias["source_key"] in definitions_by_key
    )
    reverse_edges = {}
    for caller_key in live_keys:
        for target_key in edges.get(caller_key, ()):
            reverse_edges.setdefault(target_key, set()).add(caller_key)
    candidate_reports = []
    for candidate_name, root_names in candidates:
        root_keys = [active_by_name[name]["key"] for name in root_names if name in active_by_name]
        missing_roots = [name for name in root_names if name not in active_by_name]
        depths = {key: 0 for key in root_keys}
        frontier = list(root_keys)
        for depth in range(1, dependency_depth + 1):
            next_frontier = []
            for key in frontier:
                for dependency in edges.get(key, ()):
                    if dependency not in depths:
                        depths[dependency] = depth
                        next_frontier.append(dependency)
            frontier = next_frontier
        closure = sorted(depths, key=lambda key: definitions_by_key[key]["line"])
        direct_callers = sorted(
            [
                key
                for key in live_keys
                if key not in root_keys and set(edges.get(key, ())).intersection(root_keys)
            ],
            key=lambda key: definitions_by_key[key]["line"],
        )
        caller_depths = {}
        caller_frontier = list(root_keys)
        for depth in range(1, caller_depth + 1):
            next_frontier = []
            for key in caller_frontier:
                for caller_key in reverse_edges.get(key, ()):
                    if caller_key in root_keys or caller_key in caller_depths:
                        continue
                    caller_depths[caller_key] = depth
                    next_frontier.append(caller_key)
            caller_frontier = next_frontier
        caller_closure = sorted(caller_depths, key=lambda key: definitions_by_key[key]["line"])
        candidate_reports.append(
            {
                "name": candidate_name,
                "dependency_depth": dependency_depth,
                "roots": [
                    {
                        "name": definitions_by_key[key]["name"],
                        "line": definitions_by_key[key]["line"],
                        "occurrence_count": definitions_by_key[key]["occurrence_count"],
                    }
                    for key in root_keys
                ],
                "missing_roots": missing_roots,
                "closure": [
                    {
                        "name": definitions_by_key[key]["name"],
                        "line": definitions_by_key[key]["line"],
                        "depth": depths[key],
                    }
                    for key in closure
                ],
                "closure_definition_count": len(closure),
                "closure_source_lines": sum(definitions_by_key[key]["line_count"] for key in closure),
                "direct_callers": [
                    {
                        "name": definitions_by_key[key]["name"],
                        "line": definitions_by_key[key]["line"],
                    }
                    for key in direct_callers
                ],
                "caller_depth": caller_depth,
                "caller_closure": [
                    {
                        "name": definitions_by_key[key]["name"],
                        "line": definitions_by_key[key]["line"],
                        "depth": caller_depths[key],
                    }
                    for key in caller_closure
                ],
                "caller_closure_definition_count": len(caller_closure),
                "platform_signals": sorted(
                    {
                        signal
                        for key in closure
                        for signal in definitions_by_key[key]["platform_signals"]
                    }
                ),
                "responsibility_signals": sorted(
                    {
                        signal
                        for key in closure
                        for signal in definitions_by_key[key]["responsibility_signals"]
                    }
                ),
                "duplicate_definition_names": sorted(
                    {
                        definitions_by_key[key]["name"]
                        for key in closure
                        if definitions_by_key[key]["occurrence_count"] > 1
                    }
                ),
                "captured_alias_calls": sorted(
                    {
                        call
                        for key in closure
                        for call in definitions_by_key[key]["calls"]
                        if call in alias_by_name
                    }
                ),
            }
        )

    mutable_bindings = sorted(
        {
            target
            for assignment in assignments
            if assignment["mutable_value"]
            for target in assignment["targets"]
            if "." not in target
        }
    )
    global_users = {}
    mutable_users = {}
    for record in definitions:
        for name in record["globals_declared"]:
            global_users.setdefault(name, []).append(record["key"])
        for name in set(record["references"]).intersection(mutable_bindings):
            mutable_users.setdefault(name, []).append(record["key"])

    duplicate_definitions = []
    for name, records in sorted(definitions_by_name.items()):
        if len(records) < 2:
            continue
        duplicate_definitions.append(
            {
                "name": name,
                "occurrences": [
                    {"kind": record["kind"], "line": record["line"], "end_line": record["end_line"]}
                    for record in records
                ],
                "active_line": records[-1]["line"],
                "captured_aliases": [
                    alias["target"]
                    for alias in aliases
                    if alias["source_key"] in {record["key"] for record in records[:-1]}
                ],
            }
        )

    duplicate_functions = [
        item for item in duplicate_definitions if item["occurrences"][0]["kind"] == "function"
    ]
    duplicate_classes = [
        item for item in duplicate_definitions if item["occurrences"][0]["kind"] == "class"
    ]

    return {
        "schema_version": 1,
        "label": label,
        "source": {
            "path": _relative_path(path),
            "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "bytes": len(source.encode("utf-8")),
            "newline_count": source.count("\n"),
            "logical_lines": len(source.splitlines()),
        },
        "summary": {
            "top_level_function_occurrences": sum(record["kind"] == "function" for record in definitions),
            "top_level_class_occurrences": sum(record["kind"] == "class" for record in definitions),
            "unique_definition_names": len(definitions_by_name),
            "duplicate_definition_names": len(duplicate_definitions),
            "additional_shadowing_occurrences": sum(len(item["occurrences"]) - 1 for item in duplicate_definitions),
            "duplicate_function_names": len(duplicate_functions),
            "additional_function_shadowing_occurrences": sum(
                len(item["occurrences"]) - 1 for item in duplicate_functions
            ),
            "duplicate_class_names": len(duplicate_classes),
            "additional_class_shadowing_occurrences": sum(
                len(item["occurrences"]) - 1 for item in duplicate_classes
            ),
            "captured_callable_aliases": len(aliases),
            "module_attribute_patches": len(patches),
            "module_expression_calls": len(module_calls),
            "mutable_module_bindings": len(mutable_bindings),
            "global_statement_bindings": len(global_users),
        },
        "imports": sorted(imports, key=lambda item: (item["line"], item["module"])),
        "definitions": [
            {
                "key": record["key"],
                "name": record["name"],
                "kind": record["kind"],
                "line": record["line"],
                "end_line": record["end_line"],
                "active": record["active"],
                "occurrence": record["occurrence"],
                "occurrence_count": record["occurrence_count"],
                "globals_declared": record["globals_declared"],
                "platform_signals": record["platform_signals"],
                "responsibility_signals": record["responsibility_signals"],
            }
            for record in definitions
        ],
        "call_edges": {
            key: edges[key]
            for key in sorted(live_keys, key=lambda item: definitions_by_key[item]["line"])
        },
        "duplicate_definitions": duplicate_definitions,
        "captured_callable_aliases": aliases,
        "module_attribute_patches": patches,
        "module_expression_calls": module_calls,
        "mutable_module_state": [
            {
                "name": name,
                "referenced_by": sorted(mutable_users.get(name, ())),
                "declared_global_by": sorted(global_users.get(name, ())),
            }
            for name in sorted(set(mutable_bindings).union(global_users))
        ],
        "responsibility_signal_counts": {
            signal: sum(signal in record["responsibility_signals"] for record in definitions)
            for signal in sorted(
                {signal for record in definitions for signal in record["responsibility_signals"]}
            )
        },
        "platform_signal_counts": {
            signal: sum(signal in record["platform_signals"] for record in definitions)
            for signal in sorted({signal for record in definitions for signal in record["platform_signals"]})
        },
        "candidates": candidate_reports,
    }


def _parse_mapping(value, separator):
    if "=" not in value:
        raise argparse.ArgumentTypeError("Expected LABEL={}VALUE".format(separator))
    label, payload = value.split("=", 1)
    if not label.strip() or not payload.strip():
        raise argparse.ArgumentTypeError("Both label and value are required")
    return label.strip(), payload.strip()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--macro",
        action="append",
        type=lambda value: _parse_mapping(value, ""),
        metavar="LABEL=PATH",
        help="Macro to inspect; may be repeated. Defaults to B14 and B15.",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        type=lambda value: _parse_mapping(value, ""),
        metavar="LABEL=FUNCTION[,FUNCTION...]",
        help="Candidate root functions; may be repeated.",
    )
    parser.add_argument("--dependency-depth", type=int, default=2)
    parser.add_argument("--caller-depth", type=int, default=4)
    parser.add_argument("--compact", action="store_true", help="Emit compact rather than indented JSON.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.dependency_depth < 0 or args.caller_depth < 0:
        raise SystemExit("--dependency-depth and --caller-depth must be zero or greater")
    macro_specs = args.macro or list(DEFAULT_MACROS)
    candidate_specs = args.candidate or [
        (name, ",".join(functions)) for name, functions in DEFAULT_CANDIDATES
    ]
    candidates = [
        (name, tuple(function.strip() for function in payload.split(",") if function.strip()))
        for name, payload in candidate_specs
    ]
    result = {
        "schema_version": 1,
        "dependency_depth": args.dependency_depth,
        "caller_depth": args.caller_depth,
        "macros": [
            analyse_source(
                pathlib.Path(path) if pathlib.Path(path).is_absolute() else PROJECT_ROOT / path,
                label,
                candidates,
                args.dependency_depth,
                args.caller_depth,
            )
            for label, path in macro_specs
        ],
    }
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))


if __name__ == "__main__":
    main()
