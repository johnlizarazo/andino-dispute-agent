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

PATRON_DOCUMENTO = re.compile(r"CC-FIC-[0-9]{4}")
PATRON_CUATRO_DIGITOS = re.compile(r"[0-9]{4}")
PATRON_PAIS = re.compile(r"[A-Z]{2}")
ESTADOS_TARJETA = {"activa", "bloqueada"}


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


# Campos exactos de cada archivo y su tipo: texto no vacío o entero (nunca bool ni float).
CAMPOS = {
    "clientes.json": {
        "id": str,
        "nombre": str,
        "documento": str,
        "dato_verificacion": str,
    },
    "tarjetas.json": {"id": str, "cliente_id": str, "ultimos4": str, "estado": str},
    "transacciones.json": {
        "id": str,
        "tarjeta_id": str,
        "dias_atras": int,
        "monto": int,
        "comercio": str,
        "pais": str,
        "estado": str,
    },
    "politicas.json": {
        "dias_maximos_disputa_exterior": int,
        "dias_maximos_disputa_nacional": int,
        "umbral_disputa_automatica": int,
    },
}


def _leer(carpeta, archivo: str):
    try:
        return json.loads((carpeta / archivo).read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise DatosInvalidosError(f"{archivo}: no existe") from e
    except json.JSONDecodeError as e:
        raise DatosInvalidosError(f"{archivo}: JSON inválido ({e.msg})") from e


def _campos(archivo: str, registro, posicion: int | None = None) -> None:
    donde = f"{archivo} posición {posicion}" if posicion is not None else archivo
    if not isinstance(registro, dict):
        raise DatosInvalidosError(f"{donde}: el registro no es un objeto")
    if isinstance(registro.get("id"), str):
        donde = f"{archivo} {registro['id']}"
    esperados = CAMPOS[archivo]
    faltan = esperados.keys() - registro.keys()
    sobran = registro.keys() - esperados.keys()
    if faltan or sobran:
        detalle = f"faltan {sorted(faltan)}" if faltan else f"sobran {sorted(sobran)}"
        raise DatosInvalidosError(f"{donde}: {detalle}")
    for campo, tipo in esperados.items():
        valor = registro[campo]
        if tipo is int and type(valor) is not int:
            raise DatosInvalidosError(f"{donde}: {campo} debe ser un entero")
        if tipo is str and not (isinstance(valor, str) and valor.strip()):
            raise DatosInvalidosError(f"{donde}: {campo} debe ser un texto no vacío")


def _por_id(archivo: str, registros) -> dict[str, dict]:
    if not isinstance(registros, list):
        raise DatosInvalidosError(f"{archivo}: debe ser una lista de registros")
    resultado = {}
    for posicion, registro in enumerate(registros):
        _campos(archivo, registro, posicion)
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
        if not isinstance(politica, dict):
            raise DatosInvalidosError("politicas.json: debe ser un objeto")
        _campos("politicas.json", politica)

        for c in clientes.values():
            if not PATRON_DOCUMENTO.fullmatch(c["documento"]):
                raise DatosInvalidosError(
                    f"clientes.json {c['id']}: documento fuera del formato CC-FIC-NNNN"
                )
            if not PATRON_CUATRO_DIGITOS.fullmatch(c["dato_verificacion"]):
                raise DatosInvalidosError(
                    f"clientes.json {c['id']}: dato_verificacion debe tener 4 dígitos"
                )
        for t in tarjetas.values():
            if not PATRON_CUATRO_DIGITOS.fullmatch(t["ultimos4"]):
                raise DatosInvalidosError(
                    f"tarjetas.json {t['id']}: ultimos4 debe tener exactamente 4 dígitos"
                )
            if t["estado"] not in ESTADOS_TARJETA:
                raise DatosInvalidosError(
                    f"tarjetas.json {t['id']}: estado debe ser activa o bloqueada"
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
            if not PATRON_PAIS.fullmatch(x["pais"]):
                raise DatosInvalidosError(
                    f"transacciones.json {x['id']}: pais debe ser un código de 2 letras"
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

    def obtener_transaccion(self, transaccion_id: str) -> Transaccion | None:
        """Transacción por id, o ``None`` si no existe (no es un error transitorio)."""
        return self.transacciones.get(transaccion_id)
