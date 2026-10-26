import subprocess
import zipfile
from pathlib import Path

import pytest
from armar_entrega import armar, main

# Valores con forma de credencial armados en tiempo de ejecución, nunca como literales.
TOKEN_GITHUB = "gh" + "p_" + "A" * 36
TOKEN_ANTHROPIC = "sk-" + "ant-" + "a" * 30
CLAVE_AWS = "AK" + "IA" + "B" * 16
CLAVE_PRIVADA = "-----BEGIN " + "RSA PRIVATE KEY-----"


def _git(raiz: Path, *argumentos: str) -> str:
    resultado = subprocess.run(
        ["git", *argumentos], cwd=raiz, check=True, capture_output=True, text=True
    )
    return resultado.stdout.strip()


def _escribir(raiz: Path, ruta: str, texto: str = "contenido\n") -> None:
    archivo = raiz / ruta
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(texto, encoding="utf-8")


def _commit(raiz: Path, mensaje: str = "cambio") -> None:
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", mensaje)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "prueba@example.invalid")
    _git(raiz, "config", "user.name", "Prueba")
    _git(raiz, "config", "core.autocrlf", "false")
    for ruta in ("README.md", "src/modulo.py", ".env.example"):
        _escribir(raiz, ruta)
    _commit(raiz, "inicio")
    # Sin versionar: nada de esto puede entrar a la entrega.
    for ruta in (
        ".env",
        ".venv/lib.py",
        "src/__pycache__/x.pyc",
        ".pytest_cache/v",
        "notas-locales.txt",
    ):
        _escribir(raiz, ruta)
    return raiz


def _nombres(zip_ruta: Path) -> set[str]:
    with zipfile.ZipFile(zip_ruta) as archivo:
        return set(archivo.namelist())


def test_incluye_lo_versionado_y_git_y_excluye_lo_local(repo, tmp_path):
    salida = tmp_path / "entrega.zip"
    resultado = armar(repo, salida)
    assert resultado.ok, resultado.mensajes
    nombres = _nombres(salida)
    assert {"README.md", "src/modulo.py", ".env.example"} <= nombres
    assert any(n.startswith(".git/") for n in nombres)
    for local in (".env", ".venv/lib.py", "src/__pycache__/x.pyc", "notas-locales.txt"):
        assert local not in nombres
    assert not any(n.startswith(".pytest_cache/") for n in nombres)
    assert resultado.archivos == len(nombres)
    assert resultado.bytes == salida.stat().st_size


@pytest.mark.parametrize(
    "ruta",
    [
        "node_modules/paquete.js",
        "dist/viejo.zip",
        "build/salida.txt",
        "paquete.egg-info/PKG-INFO",
        ".chainlit/config.toml",
        ".files/subido.txt",
        "CLAUDE.local.md",
        ".claude/settings.local.json",
        ".env.produccion",
        ".ruff_cache/x",
    ],
)
def test_las_exclusiones_aplican_aunque_esten_versionadas(repo, tmp_path, ruta):
    _escribir(repo, ruta)
    _git(repo, "add", "-f", ruta)
    _git(repo, "commit", "-q", "-m", "versionado por error")
    salida = tmp_path / "entrega.zip"
    assert armar(repo, salida).ok
    assert ruta not in _nombres(salida)


def _sin_valor(resultado, valor: str) -> None:
    texto = " ".join(resultado.mensajes) + " ".join(
        f"{h.tipo} {h.ubicacion}" for h in resultado.hallazgos
    )
    assert valor not in texto


@pytest.mark.parametrize(
    ("valor", "tipo"),
    [
        (TOKEN_GITHUB, "github"),
        (TOKEN_ANTHROPIC, "anthropic"),
        (CLAVE_AWS, "aws"),
        (CLAVE_PRIVADA, "clave_privada"),
    ],
)
def test_una_credencial_versionada_impide_la_entrega(repo, tmp_path, valor, tipo):
    _escribir(repo, "config/claves.txt", f"clave = {valor}\n")
    _commit(repo)
    salida = tmp_path / "entrega.zip"
    resultado = armar(repo, salida)
    assert not resultado.ok
    assert any(
        h.tipo == tipo and h.ubicacion == "config/claves.txt"
        for h in resultado.hallazgos
    )
    _sin_valor(resultado, valor)
    assert not salida.exists()


def test_una_credencial_borrada_sigue_en_el_historial(repo, tmp_path):
    _escribir(repo, "viejo.txt", f"token: {TOKEN_GITHUB}\n")
    _commit(repo, "con token")
    sha = _git(repo, "rev-parse", "--short", "HEAD")
    (repo / "viejo.txt").unlink()
    _commit(repo, "borra el token")
    salida = tmp_path / "entrega.zip"
    resultado = armar(repo, salida)
    assert not resultado.ok
    assert any(
        h.tipo == "github"
        and h.ubicacion.startswith("commit ")
        and sha.startswith(h.ubicacion.split()[1][:7])
        for h in resultado.hallazgos
    ), resultado.hallazgos
    _sin_valor(resultado, TOKEN_GITHUB)
    assert not salida.exists()


def test_textos_parecidos_no_son_credenciales(repo, tmp_path):
    _escribir(
        repo,
        "docs.md",
        "Prefijos que se buscan: ghp_, github_pat_, sk-ant- y bloques PRIVATE KEY.\n"
        + "gh"
        + "p_corto\n"
        + "sk-"
        + "ant-\n",
    )
    _commit(repo)
    resultado = armar(repo, tmp_path / "entrega.zip")
    assert resultado.ok, resultado.hallazgos
    assert resultado.hallazgos == []


def test_supera_el_limite_falla_y_no_deja_zip(repo, tmp_path):
    salida = tmp_path / "entrega.zip"
    resultado = armar(repo, salida, limite=10)
    assert not resultado.ok
    assert any("MB" in m for m in resultado.mensajes)
    assert not salida.exists()


def test_cerca_del_limite_avisa_pero_entrega(repo, tmp_path):
    salida = tmp_path / "entrega.zip"
    resultado = armar(repo, salida, aviso=10)
    assert resultado.ok
    assert any("aviso" in m.lower() for m in resultado.mensajes)
    assert salida.exists()


def test_fuera_de_un_repositorio_git(tmp_path):
    vacio = tmp_path / "sin-git"
    vacio.mkdir()
    resultado = armar(vacio, tmp_path / "entrega.zip")
    assert not resultado.ok
    assert any("git" in m for m in resultado.mensajes)


def test_main_con_salida(repo, tmp_path, monkeypatch):
    salida = tmp_path / "otra" / "entrega.zip"
    monkeypatch.chdir(repo)
    assert main(["--salida", str(salida)]) == 0
    assert salida.exists()


def test_main_devuelve_1_si_falla(repo, tmp_path, monkeypatch):
    _escribir(repo, "claves.txt", TOKEN_ANTHROPIC)
    _commit(repo)
    monkeypatch.chdir(repo)
    assert main(["--salida", str(tmp_path / "entrega.zip")]) == 1
