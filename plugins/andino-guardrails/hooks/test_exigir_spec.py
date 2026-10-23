"""Tests de exigir_spec: cada test crea un repositorio git temporal."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("exigir_spec.py")


def _repo(tmp_path: Path, rama: str) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", rama], cwd=tmp_path, check=True)
    return tmp_path


def _correr(repo: Path, ruta_relativa: str, entrada: str | None = None):
    evento = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(repo / ruta_relativa)},
    }
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=(entrada if entrada is not None else json.dumps(evento)).encode("utf-8"),
        capture_output=True,
        check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)},
    )


def _artefactos(repo: Path, rama: str, nombres: tuple[str, ...]) -> None:
    carpeta = repo / "specs" / rama
    carpeta.mkdir(parents=True)
    for nombre in nombres:
        (carpeta / nombre).write_text("# x\n", encoding="utf-8")


def test_fuera_de_src_se_permite(tmp_path):
    repo = _repo(tmp_path, "main")
    assert _correr(repo, "docs/notas.md").returncode == 0


def test_src_en_main_se_bloquea(tmp_path):
    repo = _repo(tmp_path, "main")
    r = _correr(repo, "src/paquete/modulo.py")
    assert r.returncode == 2
    assert "NNN-slug" in r.stderr.decode("utf-8")


def test_src_sin_carpeta_de_spec_se_bloquea_y_nombra_faltantes(tmp_path):
    repo = _repo(tmp_path, "004-algo")
    r = _correr(repo, "src/paquete/modulo.py")
    assert r.returncode == 2
    error = r.stderr.decode("utf-8")
    for nombre in ("spec.md", "plan.md", "tasks.md"):
        assert nombre in error


def test_src_con_solo_spec_se_bloquea(tmp_path):
    repo = _repo(tmp_path, "004-algo")
    _artefactos(repo, "004-algo", ("spec.md",))
    r = _correr(repo, "src/paquete/modulo.py")
    assert r.returncode == 2
    assert "plan.md" in r.stderr.decode("utf-8")


@pytest.mark.parametrize("ruta", ["src/paquete/modulo.py", "src/nuevo.py"])
def test_src_con_los_tres_artefactos_se_permite(tmp_path, ruta):
    repo = _repo(tmp_path, "004-algo")
    _artefactos(repo, "004-algo", ("spec.md", "plan.md", "tasks.md"))
    assert _correr(repo, ruta).returncode == 0


def test_notebook_bajo_src_sin_artefactos_se_bloquea(tmp_path):
    repo = _repo(tmp_path, "main")
    evento = {
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": str(repo / "src" / "analisis.ipynb")},
    }
    r = _correr(repo, "", entrada=json.dumps(evento))
    assert r.returncode == 2


def test_src_en_mayusculas_tambien_se_controla(tmp_path):
    repo = _repo(tmp_path, "main")
    assert _correr(repo, "SRC/paquete/modulo.py").returncode == 2


def test_json_invalido_falla_cerrado(tmp_path):
    repo = _repo(tmp_path, "004-algo")
    assert _correr(repo, "src/x.py", entrada="no es json").returncode == 2
