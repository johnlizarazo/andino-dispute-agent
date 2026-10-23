"""Bloquea escrituras bajo src/ sin spec, plan y tareas del ticket (hook PreToolUse).

La rama actual debe seguir el patrón NNN-slug y tener specs/<rama>/{spec,plan,tasks}.md.
Fuera de src/ no interviene. Cualquier error interno sale con 2: el control falla cerrado.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PATRON_RAMA = re.compile(r"^\d{3}-[a-z0-9-]+$")
ARTEFACTOS = ("spec.md", "plan.md", "tasks.md")


def _rama(proyecto: Path) -> str:
    # symbolic-ref funciona también en una rama sin commits; rev-parse no.
    r = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"],
        check=False,
        cwd=proyecto,
        capture_output=True,
        text=True,
    )
    return r.stdout.strip()


def evaluar(evento: dict, proyecto: Path) -> str | None:
    """Devuelve el motivo del bloqueo, o None si la escritura se permite."""
    entrada = evento.get("tool_input") or {}
    # NotebookEdit envía la ruta en notebook_path, no en file_path.
    ruta = Path(entrada.get("file_path") or entrada.get("notebook_path") or "")
    if not ruta.is_absolute():
        ruta = proyecto / ruta
    try:
        relativa = ruta.resolve().relative_to(proyecto.resolve())
    except ValueError:
        return None  # fuera del proyecto
    # En Windows el sistema de archivos no distingue mayúsculas: SRC/ es src/.
    if not relativa.parts or relativa.parts[0].lower() != "src":
        return None

    rama = _rama(proyecto)
    if not PATRON_RAMA.match(rama):
        return (
            f"Bloqueado: escribir en src/ requiere una rama de ticket NNN-slug (rama actual: "
            f"'{rama or 'desconocida'}'). Inicia el ticket con /siguiente-ticket."
        )
    faltantes = [a for a in ARTEFACTOS if not (proyecto / "specs" / rama / a).is_file()]
    if faltantes:
        return (
            f"Bloqueado: spec-first. Faltan en specs/{rama}/: {', '.join(faltantes)}. "
            "Completa specify, plan y tasks antes de escribir código."
        )
    return None


def main() -> int:
    try:
        sys.stderr.reconfigure(encoding="utf-8")
        evento = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        proyecto = Path(
            os.environ.get("CLAUDE_PROJECT_DIR") or evento.get("cwd") or "."
        )
        motivo = evaluar(evento, proyecto)
    except Exception as error:  # noqa: BLE001 - fallo cerrado intencional
        print(
            f"exigir_spec: error interno, se bloquea por seguridad: {type(error).__name__}",
            file=sys.stderr,
        )
        return 2
    if motivo:
        print(motivo, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
