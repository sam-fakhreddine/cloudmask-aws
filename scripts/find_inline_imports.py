#!/usr/bin/env python3
"""Find all non-top-level imports in Python files."""

import ast
from pathlib import Path
from typing import NamedTuple


class ImportInfo(NamedTuple):
    file: str
    line: int
    module: str
    context: str


def find_non_toplevel_imports(file_path: Path, base_path: Path) -> list[ImportInfo]:
    """Find imports that are not at module top level."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return []

    imports = []

    def visit_node(node, context="module"):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            new_context = f"function:{node.name}"
            for child in ast.iter_child_nodes(node):
                visit_node(child, new_context)
        elif isinstance(node, ast.ClassDef):
            new_context = f"class:{node.name}"
            for child in ast.iter_child_nodes(node):
                visit_node(child, new_context)
        elif isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
            new_context = f"{context}>{type(node).__name__.lower()}"
            for child in ast.iter_child_nodes(node):
                visit_node(child, new_context)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if context != "module":
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(
                            ImportInfo(
                                file=str(file_path.relative_to(base_path)),
                                line=node.lineno,
                                module=alias.name,
                                context=context,
                            )
                        )
                else:  # ImportFrom
                    module = node.module or ""
                    for alias in node.names:
                        full_name = f"{module}.{alias.name}" if module else alias.name
                        imports.append(
                            ImportInfo(
                                file=str(file_path.relative_to(base_path)),
                                line=node.lineno,
                                module=full_name,
                                context=context,
                            )
                        )
        else:
            for child in ast.iter_child_nodes(node):
                visit_node(child, context)

    for node in tree.body:
        visit_node(node)

    return imports


def main():
    base_path = Path.cwd()
    src_dir = base_path / "src/cloudmask"
    tests_dir = base_path / "tests"
    examples_dir = base_path / "examples"

    all_imports = []

    for directory in [src_dir, tests_dir, examples_dir]:
        if directory.exists():
            for py_file in directory.rglob("*.py"):
                imports = find_non_toplevel_imports(py_file, base_path)
                all_imports.extend(imports)

    if not all_imports:
        print("✓ No non-top-level imports found!")
        return

    print(f"Found {len(all_imports)} non-top-level imports:\n")

    # Group by file
    by_file = {}
    for imp in all_imports:
        if imp.file not in by_file:
            by_file[imp.file] = []
        by_file[imp.file].append(imp)

    for file_path in sorted(by_file.keys()):
        print(f"\n{file_path}:")
        for imp in sorted(by_file[file_path], key=lambda x: x.line):
            print(f"  Line {imp.line:4d}: {imp.module:40s} [{imp.context}]")


if __name__ == "__main__":
    main()
