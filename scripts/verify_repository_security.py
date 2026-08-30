#!/usr/bin/env python3
"""Aplica reglas de seguridad versionadas a los archivos rastreados por Git."""

from __future__ import annotations

import ast
from fnmatch import fnmatch
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "config" / "security-rules.json"


def _tracked_files(root: Path) -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=root, stderr=subprocess.STDOUT
    )
    return [root / item.decode() for item in output.split(b"\0") if item]


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def verify(root: Path = ROOT, rules_path: Path | None = None) -> dict[str, int]:
    """Rechaza secretos conocidos, ejecución dinámica y ``shell=True`` no autorizado."""
    rules_file = rules_path or root / RULES.relative_to(ROOT)
    rules = json.loads(rules_file.read_text(encoding="utf-8"))
    patterns = {name: re.compile(value.encode()) for name, value in rules["secret_patterns"].items()}
    excluded = tuple(rules["excluded_paths"])
    allowed_shell = set(rules["allowed_shell_true"])
    findings: list[str] = []
    scanned = 0
    python_files = 0
    for path in _tracked_files(root):
        relative = path.relative_to(root).as_posix()
        if any(fnmatch(relative, pattern) for pattern in excluded):
            continue
        data = path.read_bytes()
        scanned += 1
        for name, pattern in patterns.items():
            if pattern.search(data):
                findings.append(f"{relative}: secreto potencial ({name})")
        if path.suffix != ".py":
            continue
        python_files += 1
        tree = ast.parse(data, filename=relative)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name in {"eval", "exec"}:
                findings.append(f"{relative}:{node.lineno}: ejecución dinámica ({name})")
            shell_true = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
            if shell_true and relative not in allowed_shell:
                findings.append(f"{relative}:{node.lineno}: subprocess con shell=True")
    if findings:
        raise ValueError("Hallazgos de seguridad:\n" + "\n".join(findings))
    return {"tracked_files_scanned": scanned, "python_files_analyzed": python_files}


def main() -> None:
    result = verify()
    print(
        f"Seguridad del checkout correcta: {result['tracked_files_scanned']} archivos, "
        f"{result['python_files_analyzed']} módulos Python"
    )


if __name__ == "__main__":
    main()
