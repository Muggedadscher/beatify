#!/usr/bin/env python3
"""Static intra-package import verification for custom_components/beatify.

Resolves BOTH relative (from .x import Y) and absolute
(from custom_components.beatify.x import Y) intra-package imports and checks
every imported name is actually defined in the target module. Modules with a
lazy __getattr__ (PEP 562) are tolerated EXCEPT for CONSTANT-style
(UPPER_SNAKE) and dunder names, which are never lazily generated in this
codebase — that exact gap shipped a boot-blocking ENGINE_VERSION import once.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "beatify"


def names_in(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text("utf-8"))
    except (OSError, SyntaxError):
        return set()
    out: set[str] = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                out.add((a.asname or a.name).split(".")[0])
    return out


def module_file(base: Path, dotted: str) -> Path | None:
    p = base
    parts = [x for x in dotted.split(".") if x]
    for part in parts:
        p = p / part
    if p.with_suffix(".py").exists():
        return p.with_suffix(".py")
    if (p / "__init__.py").exists():
        return p / "__init__.py"
    return None


def main() -> int:
    bad = 0
    for py in sorted(ROOT.rglob("*.py")):
        try:
            tree = ast.parse(py.read_text("utf-8"))
        except SyntaxError as err:
            print(f"SYNTAX: {py}: {err}")
            bad += 1
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level > 0:
                base = py.parent
                for _ in range(node.level - 1):
                    base = base.parent
                target = module_file(base, node.module or "")
            elif node.module and node.module.startswith("custom_components.beatify"):
                rel = node.module[len("custom_components.beatify") :].lstrip(".")
                target = module_file(ROOT, rel) if rel else ROOT / "__init__.py"
            else:
                continue
            if target is None:
                continue
            defined = names_in(target)
            lazy = "__getattr__" in defined
            for a in node.names:
                if a.name == "*" or a.name in defined:
                    continue
                # `from package import submodule` is valid when the submodule
                # file exists next to the package __init__.
                if target.name == "__init__.py" and (
                    (target.parent / f"{a.name}.py").exists()
                    or (target.parent / a.name / "__init__.py").exists()
                ):
                    continue
                looks_constant = a.name.isupper() or (
                    a.name.startswith("__") and a.name.endswith("__")
                )
                if lazy and not looks_constant:
                    continue
                rel = py.relative_to(ROOT.parent.parent)
                print(f"MISSING: {rel}: from {node.module or '.'} import {a.name}")
                bad += 1
    print("IMPORT GRAPH OK" if not bad else f"{bad} broken import(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
