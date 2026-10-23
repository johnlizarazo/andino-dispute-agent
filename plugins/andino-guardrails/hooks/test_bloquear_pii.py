"""Tests de bloquear_pii.

Ningún número con forma real aparece como literal: las tarjetas y los documentos se generan
al correr (principio III de la constitución).
"""

import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

import bloquear_pii
import pytest

SCRIPT = Path(__file__).with_name("bloquear_pii.py")
rng = random.Random(20261023)


def _digito_luhn(carga: str) -> str:
    total = 0
    for i, c in enumerate(reversed(carga)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def tarjeta_valida(longitud: int, separador: str = "") -> str:
    carga = str(rng.randint(1, 9)) + "".join(
        str(rng.randint(0, 9)) for _ in range(longitud - 2)
    )
    numero = carga + _digito_luhn(carga)
    if not separador:
        return numero
    return separador.join(numero[i : i + 4] for i in range(0, len(numero), 4))


def tarjeta_invalida(longitud: int) -> str:
    numero = tarjeta_valida(longitud)
    malo = str((int(numero[-1]) + 1) % 10)
    return numero[:-1] + malo


def documento(palabra: str, digitos: int, con_puntos: bool = False) -> str:
    numero = str(rng.randint(1, 9)) + "".join(
        str(rng.randint(0, 9)) for _ in range(digitos - 1)
    )
    if con_puntos:
        numero = f"{int(numero):,}".replace(",", ".")
    return f"{palabra} {numero}"


TARJETAS = [tarjeta_valida(n) for n in range(13, 20)] + [
    tarjeta_valida(n, sep) for n in (16, 16, 16, 19, 13, 15, 14) for sep in (" ", "-")
]

LEGITIMOS = [
    "180000",
    "1250000",
    "$1.250.000",
    "Disputa por 180000 y otra por 1250000",
    "CC-FIC-0001",
    "cliente CC-FIC-0042",
    "13 a 19 dígitos",
    "documento de identidad ficticio",
    "NIT pendiente de registro",
    "tarjeta terminada en 4821",
    "fecha 2026-10-23",
    "marca de tiempo 1729650000",
    hashlib.sha256(b"andino").hexdigest(),
    "uuid 3f2b8c1e-9a4d-4e2b-8f1a-2c3d4e5f6a7b",
    "monto 999999999999",
    "transacción 42",
    "+57 300 000 0000",
] + [tarjeta_invalida(n) for n in (13, 15, 16, 16, 19)]


@pytest.mark.parametrize("numero", TARJETAS)
def test_tarjetas_validas_se_detectan(numero):
    hallazgos = bloquear_pii.buscar_hallazgos(f"pago con {numero} ayer")
    assert [h["tipo"] for h in hallazgos] == ["tarjeta"]


def test_hay_al_menos_20_tarjetas_y_20_legitimos():
    assert len(TARJETAS) >= 20
    assert len(LEGITIMOS) >= 20


@pytest.mark.parametrize("texto", LEGITIMOS)
def test_casos_legitimos_no_se_detectan(texto):
    assert bloquear_pii.buscar_hallazgos(texto) == []


@pytest.mark.parametrize(
    "texto",
    [
        documento("CC", 8),
        documento("cédula:", 7, con_puntos=True),
        documento("documento", 10),
    ],
)
def test_documentos_se_detectan(texto):
    hallazgos = bloquear_pii.buscar_hallazgos(texto)
    assert [h["tipo"] for h in hallazgos] == ["documento"]


@pytest.mark.parametrize(
    "texto",
    [
        f"El cliente es {documento('CC', 8)}.",
        f"Su {documento('cédula', 7, con_puntos=True)}. Gracias",
        f"({documento('documento', 10)}).",
    ],
)
def test_documentos_seguidos_de_puntuacion_se_detectan(texto):
    hallazgos = bloquear_pii.buscar_hallazgos(texto)
    assert [h["tipo"] for h in hallazgos] == ["documento"]


def test_luhn_valido():
    numero = tarjeta_valida(16)
    assert bloquear_pii.luhn_valido(numero)
    assert not bloquear_pii.luhn_valido(tarjeta_invalida(16))


def test_la_muestra_no_contiene_el_numero_completo():
    numero = tarjeta_valida(16)
    (hallazgo,) = bloquear_pii.buscar_hallazgos(numero)
    assert numero not in hallazgo["muestra"]
    assert hallazgo["muestra"].endswith(numero[-4:])


def test_linea_del_hallazgo():
    texto = "linea uno\nlinea dos " + tarjeta_valida(16)
    (hallazgo,) = bloquear_pii.buscar_hallazgos(texto)
    assert hallazgo["linea"] == 2


@pytest.mark.parametrize(
    ("tool_name", "tool_input"),
    [
        ("Write", {"content": "A"}),
        ("Edit", {"old_string": "x", "new_string": "A"}),
        ("MultiEdit", {"edits": [{"old_string": "x", "new_string": "A"}]}),
        ("NotebookEdit", {"new_source": "A"}),
    ],
)
def test_textos_nuevos_por_herramienta(tool_name, tool_input):
    evento = {
        "tool_name": tool_name,
        "tool_input": {"file_path": "x.txt", **tool_input},
    }
    assert bloquear_pii.textos_nuevos(evento) == ["A"]


def _correr_hook(entrada: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=entrada.encode("utf-8"),
        capture_output=True,
        check=False,
    )


def test_hook_bloquea_tarjeta_con_salida_2():
    numero = tarjeta_valida(16, " ")
    evento = {
        "tool_name": "Write",
        "tool_input": {"file_path": "a.txt", "content": numero},
    }
    r = _correr_hook(json.dumps(evento))
    assert r.returncode == 2
    error = r.stderr.decode("utf-8")
    assert "tarjeta" in error
    assert numero not in error


def test_hook_permite_texto_limpio():
    evento = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "a.txt", "new_string": "1250000"},
    }
    r = _correr_hook(json.dumps(evento))
    assert r.returncode == 0
    assert r.stderr == b""


def test_hook_falla_cerrado_con_json_invalido():
    r = _correr_hook("esto no es json")
    assert r.returncode == 2


def _correr_diff(tmp_path: Path, contenido: str) -> subprocess.CompletedProcess:
    diff = tmp_path / "cambios.diff"
    diff.write_text(contenido, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--diff", str(diff)],
        capture_output=True,
        check=False,
    )


def test_diff_detecta_lineas_agregadas(tmp_path):
    numero = tarjeta_valida(16)
    contenido = f"+++ b/datos.txt\n@@ -0,0 +1 @@\n+pago {numero}\n"
    r = _correr_diff(tmp_path, contenido)
    assert r.returncode == 1
    assert "datos.txt" in r.stdout.decode("utf-8")
    assert numero not in r.stdout.decode("utf-8")


def test_diff_ignora_lineas_eliminadas(tmp_path):
    numero = tarjeta_valida(16)
    contenido = f"--- a/datos.txt\n+++ b/datos.txt\n@@ -1 +0,0 @@\n-pago {numero}\n"
    r = _correr_diff(tmp_path, contenido)
    assert r.returncode == 0
