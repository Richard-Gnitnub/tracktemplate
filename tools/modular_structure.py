#!/usr/bin/env python3
"""Report and validate the modular package's deterministic import structure."""

import argparse
import ast
import json
import pathlib
import sys


SENTINEL = "TRACKTEMPLATE_MODULAR_STRUCTURE="
PACKAGE_NAME = "tracktemplate"
FORBIDDEN_DOMAIN_ROOTS = {
    "FreeCAD",
    "FreeCADGui",
    "Part",
    "PySide",
    "PySide2",
    "PySide6",
    "pivy",
}


def _module_name(package_root, path):
    relative = path.relative_to(package_root)
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join([PACKAGE_NAME] + parts)


def _layer(module):
    if module == PACKAGE_NAME:
        return "package"
    if module == PACKAGE_NAME + ".api":
        return "api"
    if module == PACKAGE_NAME + ".bootstrap":
        return "bootstrap"
    if module.startswith(PACKAGE_NAME + ".compatibility"):
        return "compatibility"
    if module.startswith(PACKAGE_NAME + ".domain"):
        return "domain"
    return "undeclared"


def _absolute_import(current_module, node, is_package):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if node.level == 0:
        return [node.module] if node.module else []

    current_parts = current_module.split(".")
    package_parts = current_parts if is_package else current_parts[:-1]
    remove = node.level - 1
    if remove:
        package_parts = package_parts[:-remove]
    if node.module:
        package_parts = package_parts + node.module.split(".")
        return [".".join(package_parts)]
    return [
        ".".join(package_parts + alias.name.split("."))
        for alias in node.names
    ]


def _literal_exports(tree):
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in targets
        ):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (TypeError, ValueError):
            return None
        if isinstance(value, (list, tuple)) and all(
            isinstance(item, str) for item in value
        ):
            return list(value)
        return None
    return []


def _definition_names(tree):
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def _warning_signals(module, tree):
    definitions = _definition_names(tree)
    warnings = []
    duplicated = sorted(
        name for name in set(definitions) if definitions.count(name) > 1
    )
    for name in duplicated:
        warnings.append(
            {"module": module, "kind": "duplicate-definition", "name": name}
        )

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            warnings.append(
                {
                    "module": module,
                    "kind": "import-time-call",
                    "line": node.lineno,
                }
            )
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Attribute) for target in targets):
            warnings.append(
                {
                    "module": module,
                    "kind": "import-time-attribute-patch",
                    "line": node.lineno,
                }
            )
        value = node.value
        if isinstance(value, (ast.Dict, ast.List, ast.Set, ast.Call)):
            names = [
                target.id for target in targets if isinstance(target, ast.Name)
            ]
            for name in names:
                warnings.append(
                    {
                        "module": module,
                        "kind": "mutable-or-constructed-module-state",
                        "name": name,
                        "line": node.lineno,
                    }
                )
    return warnings


def _cycles(edges):
    graph = {}
    for edge in edges:
        graph.setdefault(edge["from"], set()).add(edge["to"])
    found = set()

    def visit(node, stack, active):
        if node in active:
            start = stack.index(node)
            cycle = stack[start:] + [node]
            rotations = [
                tuple(cycle[index:-1] + cycle[:index] + [cycle[index]])
                for index in range(len(cycle) - 1)
            ]
            found.add(min(rotations))
            return
        active.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, ())):
            visit(target, stack, active)
        stack.pop()
        active.remove(node)

    for module in sorted(graph):
        visit(module, [], set())
    return [list(cycle) for cycle in sorted(found)]


def _edge_allowed(source_layer, target_layer):
    allowed = {
        "package": {"package"},
        "domain": {"domain"},
        "api": {"package", "domain"},
        "bootstrap": {"package", "api"},
        "compatibility": {"package", "api", "domain", "compatibility"},
    }
    return target_layer in allowed.get(source_layer, set())


def structure_report(repository_root):
    """Return a deterministic source/import report for the current foundation."""
    repository_root = pathlib.Path(repository_root).resolve()
    package_root = repository_root / PACKAGE_NAME
    paths = sorted(package_root.rglob("*.py"))
    modules = {}
    trees = {}
    all_warnings = []
    for path in paths:
        module = _module_name(package_root, path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        trees[module] = tree
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.extend(
                    _absolute_import(module, node, path.name == "__init__.py")
                )
        warnings = _warning_signals(module, tree)
        all_warnings.extend(warnings)
        modules[module] = {
            "path": path.relative_to(repository_root).as_posix(),
            "layer": _layer(module),
            "line_count": len(source.splitlines()),
            "definitions": _definition_names(tree),
            "imports": sorted(set(item for item in imports if item)),
            "public_exports": _literal_exports(tree),
            "warning_signals": warnings,
        }

    edges = []
    external = []
    domain_forbidden = []
    module_names = set(modules)
    for module, record in modules.items():
        for imported in record["imports"]:
            if imported == PACKAGE_NAME or imported.startswith(PACKAGE_NAME + "."):
                target = imported
                while target not in module_names and "." in target:
                    target = target.rsplit(".", 1)[0]
                if target in module_names:
                    edges.append({"from": module, "to": target})
            else:
                external.append({"from": module, "root": imported.split(".", 1)[0]})
                if record["layer"] == "domain":
                    root = imported.split(".", 1)[0]
                    if root in FORBIDDEN_DOMAIN_ROOTS or root not in sys.stdlib_module_names:
                        domain_forbidden.append(
                            {"module": module, "import_root": root}
                        )

    edges = sorted(edges, key=lambda item: (item["from"], item["to"]))
    prohibited = []
    for edge in edges:
        source_layer = modules[edge["from"]]["layer"]
        target_layer = modules[edge["to"]]["layer"]
        if not _edge_allowed(source_layer, target_layer):
            prohibited.append(
                {
                    "from": edge["from"],
                    "from_layer": source_layer,
                    "to": edge["to"],
                    "to_layer": target_layer,
                }
            )

    launcher_path = repository_root / "TrackTemplate.FCMacro"
    launcher_source = launcher_path.read_text(encoding="utf-8")
    launcher_tree = ast.parse(launcher_source, filename=str(launcher_path))
    return {
        "schema_version": 1,
        "package": PACKAGE_NAME,
        "modules": [modules[name] | {"module": name} for name in sorted(modules)],
        "import_edges": edges,
        "external_imports": sorted(
            external, key=lambda item: (item["from"], item["root"])
        ),
        "cycles": _cycles(edges),
        "prohibited_layer_edges": prohibited,
        "domain_forbidden_imports": sorted(
            domain_forbidden,
            key=lambda item: (item["module"], item["import_root"]),
        ),
        "warning_signals": sorted(
            all_warnings,
            key=lambda item: (
                item["module"],
                item["kind"],
                str(item.get("name", "")),
                int(item.get("line", 0)),
            ),
        ),
        "launcher": {
            "path": launcher_path.relative_to(repository_root).as_posix(),
            "line_count": len(launcher_source.splitlines()),
            "definitions": _definition_names(launcher_tree),
            "launch_calls": sum(
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "run_macro"
                for node in launcher_tree.body
            ),
        },
    }


def validate_report(report):
    """Return enforceable structural violations from a generated report."""
    errors = []
    modules = report.get("modules") or []
    if any(item.get("layer") == "undeclared" for item in modules):
        errors.append("the package contains an undeclared layer")
    if report.get("cycles"):
        errors.append("the package import graph contains a cycle")
    if report.get("prohibited_layer_edges"):
        errors.append("the package import graph contains a prohibited layer edge")
    if report.get("domain_forbidden_imports"):
        errors.append("the domain imports a platform or third-party dependency")
    if report.get("warning_signals"):
        errors.append("the package contains a structural warning signal")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[1],
    )
    arguments = parser.parse_args(argv)
    report = structure_report(arguments.root)
    print(
        SENTINEL + json.dumps(report, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return int(bool(validate_report(report)))


if __name__ == "__main__":
    raise SystemExit(main())
