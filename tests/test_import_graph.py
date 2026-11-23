# -*- coding: utf-8 -*-
"""
test_import_graph.py
Author: Group12A2 DSW Team
Purpose: Guard the package layout: the src package graph must stay acyclic and
         no library module may import a script.
Module: tests
"""
import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"


def _module_name(path: Path) -> str:
    relative = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _project_imports(path: Path) -> set[str]:
    """Return the project modules imported by one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    project = set()
    for name in names:
        if name == "src" or name.startswith("src.") or name.startswith("scripts"):
            project.add(name)
    return project


def _resolve(name: str, known: set[str]) -> set[str]:
    """Map an import statement onto the modules it actually loads."""
    if name in known:
        return {name}
    parent = name.rsplit(".", 1)[0] if "." in name else name
    if parent in known:
        return {parent}
    return set()


@pytest.fixture(scope="module")
def graph() -> dict[str, set[str]]:
    modules = {_module_name(path) for path in SRC.rglob("*.py")}
    edges: dict[str, set[str]] = {module: set() for module in modules}
    for path in SRC.rglob("*.py"):
        module = _module_name(path)
        for imported in _project_imports(path):
            edges[module] |= _resolve(imported, modules)
    return edges


def test_src_does_not_import_scripts(graph):
    offenders = {
        module: sorted(target for target in targets if target.startswith("scripts"))
        for module, targets in graph.items()
        if any(target.startswith("scripts") for target in targets)
    }
    assert not offenders, f"library modules must not import scripts: {offenders}"


def test_src_graph_is_acyclic(graph):
    state: dict[str, int] = {}

    def visit(module: str, trail: tuple[str, ...]) -> None:
        if state.get(module) == 2:
            return
        if state.get(module) == 1:
            cycle = " -> ".join(trail + (module,))
            raise AssertionError(f"circular import: {cycle}")
        state[module] = 1
        for target in sorted(graph.get(module, set())):
            visit(target, trail + (module,))
        state[module] = 2

    for module in sorted(graph):
        visit(module, ())


def test_reporting_layers_only_depend_downwards(graph):
    """Reporting may use evaluation/models/config, never the reverse."""
    for module, targets in graph.items():
        if not module.startswith("src.reporting"):
            continue
        for target in targets:
            assert target.split(".")[:2] != ["src", "scripts"], f"{module} -> {target}"
