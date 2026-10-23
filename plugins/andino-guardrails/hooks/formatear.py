"""Formatea archivos Python tras cada edición (hook PostToolUse).

Ejecuta ``ruff format`` y ``ruff check --fix`` con el entorno del proyecto. Si quedan
problemas que no se corrigen solos, sale con 2 para que Claude los vea; la edición ya
ocurrió y no se revierte. Si uv o ruff no están disponibles, avisa sin bloquear.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def _ruff(proyecto: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "--no-sync", "ruff", *args],
        check=False,
        cwd=proyecto,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main() -> int:
    try:
        return formatear()
    except Exception as error:  # noqa: BLE001 - un error siempre se reporta a Claude
        print(f"formatear: error interno: {type(error).__name__}", file=sys.stderr)
        return 2


def formatear() -> int:
    sys.stderr.reconfigure(encoding="utf-8")
    evento = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    archivo = Path((evento.get("tool_input") or {}).get("file_path", ""))
    if archivo.suffix != ".py" or not archivo.is_file():
        return 0
    proyecto = Path(os.environ.get("CLAUDE_PROJECT_DIR") or evento.get("cwd") or ".")
    try:
        _ruff(proyecto, "format", str(archivo))
        revision = _ruff(
            proyecto, "check", "--fix", "--output-format", "concise", str(archivo)
        )
    except FileNotFoundError:
        print(
            "formatear: uv no está disponible; el archivo no se formateó.",
            file=sys.stderr,
        )
        return 0
    if revision.returncode == 0:
        return 0
    salida = (revision.stdout + revision.stderr).strip()
    if "ruff" in salida.lower() and "not found" in salida.lower():
        print(
            "formatear: ruff no está instalado (uv sync); no se formateó.",
            file=sys.stderr,
        )
        return 0
    print(
        f"ruff encontró problemas que no se corrigen solos:\n{salida}", file=sys.stderr
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
