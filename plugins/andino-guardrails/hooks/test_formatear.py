"""Tests de formatear: ejecutan ruff del proyecto sobre archivos temporales."""

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("formatear.py")
PROYECTO = Path(__file__).resolve().parents[3]


def _correr(archivo: Path):
    evento = {"tool_name": "Write", "tool_input": {"file_path": str(archivo)}}
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(evento).encode("utf-8"),
        capture_output=True,
        check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(PROYECTO)},
    )


def test_python_mal_formateado_queda_formateado(tmp_path):
    archivo = tmp_path / "modulo.py"
    archivo.write_text("x=[1,2,\n 3]\ndef f( a ):\n  return a\n", encoding="utf-8")
    r = _correr(archivo)
    assert r.returncode == 0, r.stderr.decode("utf-8")
    assert (
        archivo.read_text(encoding="utf-8")
        == "x = [1, 2, 3]\n\n\ndef f(a):\n    return a\n"
    )


def test_archivo_que_no_es_python_no_se_toca(tmp_path):
    archivo = tmp_path / "notas.md"
    contenido = "x=[1,2,\n 3]\n"
    archivo.write_text(contenido, encoding="utf-8")
    assert _correr(archivo).returncode == 0
    assert archivo.read_text(encoding="utf-8") == contenido


def test_problema_no_corregible_se_reporta_con_salida_2(tmp_path):
    archivo = tmp_path / "roto.py"
    archivo.write_text("def f():\n    return nombre_indefinido\n", encoding="utf-8")
    r = _correr(archivo)
    assert r.returncode == 2
    assert "F821" in r.stderr.decode("utf-8")


def test_archivo_inexistente_se_permite(tmp_path):
    assert _correr(tmp_path / "no_existe.py").returncode == 0


def test_json_invalido_sale_con_2_y_mensaje_de_error_interno():
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=b"no es json",
        capture_output=True,
        check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(PROYECTO)},
    )
    assert r.returncode == 2
    assert "error interno" in r.stderr.decode("utf-8")
