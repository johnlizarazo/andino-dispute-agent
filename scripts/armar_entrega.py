"""Arma el .zip de entrega con los archivos versionados y el directorio .git (#14).

Uso: ``uv run --no-project python scripts/armar_entrega.py [--salida RUTA]``, desde la raíz
del repositorio. Solo entra lo que lista ``git ls-files`` (lo no versionado nunca se
entrega) más ``.git``; además se aplican exclusiones defensivas por si algo local quedó
versionado. Antes de comprimir busca credenciales en los archivos versionados y en todo el
historial, y nunca muestra el valor encontrado. Escribe primero en un temporal y solo lo
deja si pasa todas las verificaciones: con hallazgos o con 50 MB o más, no queda ningún
.zip. Solo usa la biblioteca estándar, como los hooks del plugin.
"""

import argparse
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

SALIDA_POR_OMISION = Path("dist") / "entrega-andino-dispute-agent.zip"
LIMITE = 50 * 1000 * 1000
AVISO = 40 * 1000 * 1000

CARPETAS_EXCLUIDAS = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".chainlit",
    ".files",
}
ARCHIVOS_EXCLUIDOS = {"CLAUDE.local.md", ".claude/settings.local.json"}
PATRONES = {
    "github": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,}"),
    "anthropic": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "aws": re.compile(r"AKIA[0-9A-Z]{16}"),
    "clave_privada": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


@dataclass(frozen=True)
class Hallazgo:
    """Nunca guarda ni muestra el valor encontrado: solo su tipo y dónde está."""

    tipo: str
    ubicacion: str


@dataclass
class Resultado:
    ok: bool
    bytes: int = 0
    archivos: int = 0
    hallazgos: list[Hallazgo] = field(default_factory=list)
    mensajes: list[str] = field(default_factory=list)


def excluido(ruta: str) -> bool:
    partes = PurePosixPath(ruta).parts
    nombre = partes[-1]
    if ruta in ARCHIVOS_EXCLUIDOS:
        return True
    if nombre.startswith(".env") and nombre != ".env.example":
        return True
    return any(p in CARPETAS_EXCLUIDAS or p.endswith(".egg-info") for p in partes[:-1])


def _git(raiz: Path, *argumentos: str) -> bytes:
    return subprocess.run(
        ["git", *argumentos], cwd=raiz, check=True, capture_output=True
    ).stdout


def archivos_versionados(raiz: Path) -> list[str]:
    salida = _git(raiz, "ls-files", "-z").decode("utf-8")
    rutas = [r for r in salida.split("\0") if r]
    return [r for r in rutas if not excluido(r) and (raiz / r).is_file()]


def _tipos(texto: str) -> list[str]:
    return [tipo for tipo, patron in PATRONES.items() if patron.search(texto)]


def buscar_credenciales(raiz: Path, rutas: list[str]) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    for ruta in rutas:
        contenido = (raiz / ruta).read_bytes()
        if b"\0" in contenido[:8000]:
            continue  # binario
        for tipo in _tipos(contenido.decode("utf-8", errors="replace")):
            hallazgos.append(Hallazgo(tipo, ruta))
    # .git entra completo: su config puede llevar un token en la URL del remoto.
    configuracion = raiz / ".git" / "config"
    if configuracion.is_file():
        texto = configuracion.read_text(encoding="utf-8", errors="replace")
        hallazgos += [Hallazgo(tipo, ".git/config") for tipo in _tipos(texto)]
    historial = _git(raiz, "log", "-p", "--all", "--format=commit %H")
    commit = None
    for linea in historial.decode("utf-8", errors="replace").splitlines():
        if linea.startswith("commit ") and len(linea.split()) == 2:
            commit = linea.split()[1][:7]
            continue
        for tipo in _tipos(linea):
            hallazgo = Hallazgo(tipo, f"commit {commit}")
            if hallazgo not in hallazgos:
                hallazgos.append(hallazgo)
    return hallazgos


def _megas(cantidad: int) -> str:
    return f"{cantidad / 1000 / 1000:.1f} MB"


def _comprimir(raiz: Path, rutas: list[str], destino: Path) -> int:
    archivos = 0
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zip_salida:
        for ruta in rutas:
            zip_salida.write(raiz / ruta, ruta)
            archivos += 1
        for carpeta, _, nombres in os.walk(raiz / ".git"):
            for nombre in nombres:
                completo = Path(carpeta) / nombre
                zip_salida.write(completo, completo.relative_to(raiz).as_posix())
                archivos += 1
    return archivos


def armar(
    raiz: Path, salida: Path, limite: int = LIMITE, aviso: int = AVISO
) -> Resultado:
    raiz = Path(raiz)
    if not (raiz / ".git").exists():
        return Resultado(
            False, mensajes=[f"{raiz} no es la raíz de un repositorio git."]
        )
    salida = Path(salida)
    # Una entrega de una corrida anterior no puede quedar como válida si esta falla.
    salida.unlink(missing_ok=True)
    rutas = archivos_versionados(raiz)
    hallazgos = buscar_credenciales(raiz, rutas)
    if hallazgos:
        mensajes = ["Se encontraron posibles credenciales; no se armó la entrega:"] + [
            f"- {h.tipo} en {h.ubicacion}" for h in hallazgos
        ]
        return Resultado(False, hallazgos=hallazgos, mensajes=mensajes)

    salida.parent.mkdir(parents=True, exist_ok=True)
    temporal = salida.with_name(salida.name + ".tmp")
    try:
        archivos = _comprimir(raiz, rutas, temporal)
        tamano = temporal.stat().st_size
        if tamano >= limite:
            temporal.unlink()
            mensaje = (
                f"La entrega pesa {_megas(tamano)} y el límite es {_megas(limite)}; "
                "no se armó."
            )
            return Resultado(False, bytes=tamano, archivos=archivos, mensajes=[mensaje])
        temporal.replace(salida)
    finally:
        temporal.unlink(missing_ok=True)

    mensajes = [f"Entrega lista: {salida} ({_megas(tamano)}, {archivos} archivos)."]
    if tamano > aviso:
        mensajes.append(
            f"Aviso: supera {_megas(aviso)}; se acerca al límite de {_megas(limite)}."
        )
    return Resultado(True, bytes=tamano, archivos=archivos, mensajes=mensajes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Arma el .zip de entrega del proyecto."
    )
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_OMISION)
    argumentos = parser.parse_args(argv)
    resultado = armar(Path.cwd(), argumentos.salida)
    for mensaje in resultado.mensajes:
        print(mensaje, file=sys.stdout if resultado.ok else sys.stderr)
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    sys.exit(main())
