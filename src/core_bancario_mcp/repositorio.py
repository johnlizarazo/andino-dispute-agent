"""Datos ficticios del core bancario: carga, validación y consulta.

Los datos viven en ``datos/*.json`` dentro del paquete. Las fechas de las transacciones se
guardan como días hacia atrás y se resuelven al cargar respecto de un ``hoy`` inyectable,
para que "ayer" sea siempre ayer y los tests sean deterministas.

El agente reutiliza este módulo (no el servidor) para consultar el monto real de una
transacción: monto y titular son inmutables, así que no importa que corran en procesos
distintos.
"""

import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from importlib import resources
from pathlib import Path

PATRON_DOCUMENTO = re.compile(r"^CC-FIC-\d{4}$")
PATRON_ULTIMOS4 = re.compile(r"^\d{4}$")


class DatosInvalidosError(Exception):
    """Los datos del core están ausentes o mal formados; el core no debe arrancar."""


@dataclass(frozen=True)
class Cliente:
    id: str
    nombre: str
    documento: str
    dato_verificacion: str


@dataclass(frozen=True)
class Tarjeta:
    id: str
    cliente_id: str
    ultimos4: str
    estado: str


@dataclass(frozen=True)
class Transaccion:
    id: str
    tarjeta_id: str
    cliente_id: str
    fecha: date
    monto: int
    comercio: str
    pais: str
    estado: str


@dataclass(frozen=True)
class Politica:
    dias_maximos_disputa_exterior: int
    dias_maximos_disputa_nacional: int
    umbral_disputa_automatica: int


CAMPOS = {
    "clientes.json": {"id", "nombre", "documento", "dato_verificacion"},
    "tarjetas.json": {"id", "cliente_id", "ultimos4", "estado"},
    "transacciones.json": {
        "id",
        "tarjeta_id",
        "dias_atras",
        "monto",
        "comercio",
        "pais",
        "estado",
    },
    "politicas.json": {
        "dias_maximos_disputa_exterior",
        "dias_maximos_disputa_nacional",
        "umbral_disputa_automatica",
    },
}


def _leer(carpeta, archivo: str):
    try:
        return json.loads((carpeta / archivo).read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise DatosInvalidosError(f"{archivo}: no existe") from e
    except json.JSONDecodeError as e:
        raise DatosInvalidosError(f"{archivo}: JSON inválido ({e.msg})") from e


def _campos(archivo: str, registro: dict) -> None:
    esperados = CAMPOS[archivo]
    faltan, sobran = esperados - registro.keys(), registro.keys() - esperados
    if faltan or sobran:
        detalle = f"faltan {sorted(faltan)}" if faltan else f"sobran {sorted(sobran)}"
        raise DatosInvalidosError(f"{archivo} {registro.get('id', '?')}: {detalle}")


def _por_id(archivo: str, registros: list[dict]) -> dict[str, dict]:
    resultado = {}
    for registro in registros:
        _campos(archivo, registro)
        if registro["id"] in resultado:
            raise DatosInvalidosError(f"{archivo}: id duplicado {registro['id']}")
        resultado[registro["id"]] = registro
    return resultado


class Repositorio:
    def __init__(self, hoy: date | None = None, carpeta: Path | None = None):
        hoy = hoy or date.today()
        origen = carpeta or resources.files("core_bancario_mcp") / "datos"

        clientes = _por_id("clientes.json", _leer(origen, "clientes.json"))
        tarjetas = _por_id("tarjetas.json", _leer(origen, "tarjetas.json"))
        transacciones = _por_id(
            "transacciones.json", _leer(origen, "transacciones.json")
        )
        politica = _leer(origen, "politicas.json")
        _campos("politicas.json", politica)

        for c in clientes.values():
            if not PATRON_DOCUMENTO.match(c["documento"]):
                raise DatosInvalidosError(
                    f"clientes.json {c['id']}: documento fuera del formato CC-FIC-NNNN"
                )
        for t in tarjetas.values():
            if not PATRON_ULTIMOS4.match(t["ultimos4"]):
                raise DatosInvalidosError(
                    f"tarjetas.json {t['id']}: ultimos4 debe tener exactamente 4 dígitos"
                )
            if t["cliente_id"] not in clientes:
                raise DatosInvalidosError(
                    f"tarjetas.json {t['id']}: cliente inexistente {t['cliente_id']}"
                )
        for x in transacciones.values():
            if x["tarjeta_id"] not in tarjetas:
                raise DatosInvalidosError(
                    f"transacciones.json {x['id']}: tarjeta inexistente {x['tarjeta_id']}"
                )
            if x["monto"] <= 0:
                raise DatosInvalidosError(
                    f"transacciones.json {x['id']}: monto debe ser positivo"
                )
            if x["dias_atras"] < 0:
                raise DatosInvalidosError(
                    f"transacciones.json {x['id']}: dias_atras no puede ser negativo"
                )

        self.clientes = {k: Cliente(**v) for k, v in clientes.items()}
        self.tarjetas = {k: Tarjeta(**v) for k, v in tarjetas.items()}
        self.transacciones = {
            k: Transaccion(
                id=v["id"],
                tarjeta_id=v["tarjeta_id"],
                cliente_id=tarjetas[v["tarjeta_id"]]["cliente_id"],
                fecha=hoy - timedelta(days=v["dias_atras"]),
                monto=v["monto"],
                comercio=v["comercio"],
                pais=v["pais"],
                estado=v["estado"],
            )
            for k, v in transacciones.items()
        }
        self.politica = Politica(**politica)
