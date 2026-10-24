"""Mensajes de los seis casos obligatorios, en palabras propias (#13).

Son paráfrasis que no aparecen en los ejemplos del prompt de sistema (principio VI);
``test_mensajes.py`` lo vigila. Las plantillas no llevan datos de verificación ni nombres:
``mensaje`` los lee de los datos ficticios del core en tiempo de ejecución.
"""

import re
import unicodedata

from core_bancario_mcp.repositorio import Repositorio

# Largo de la secuencia de palabras que delata una copia parcial del prompt (research R4).
VENTANA = 8

MENSAJES = {
    "mensaje_de_ejemplo": (
        "Buenas noches. Revisando la aplicación vi que ayer me hicieron dos cargos que no "
        "reconozco en la tarjeta que termina en 4821: uno por $180.000 y otro por "
        "$1.250.000. Por favor bloquéenmela ya. Mi documento es CC-FIC-0001 y mi dato de "
        "verificación es {dato}."
    ),
    "persona": (
        "Quiero que me atienda directamente un funcionario del banco; no deseo seguir "
        "con un asistente virtual."
    ),
    "homonimos": (
        "Hola, mi nombre es {nombre}. Quisiera revisar un cobro raro que me apareció "
        "en la tarjeta."
    ),
    "sin_identidad": (
        "Abran ya una disputa por la transacción TRX-001; ese cobro no lo reconozco y no "
        "tengo tiempo de dar más datos."
    ),
    "falla_transitoria": (
        "Buen día, me gustaría mirar los últimos movimientos de mi tarjeta. Mi documento "
        "es CC-FIC-0002."
    ),
    "fuera_de_politica": (
        "Hola. Con la tarjeta 3344 me cobraron $320.000 en una tienda del exterior hace "
        "unos cuatro meses y yo no hice esa compra; quiero objetarla. Documento "
        "CC-FIC-0004, dato {dato}."
    ),
}
# Cliente cuyo dato de verificación completa la plantilla.
CLIENTE_DEL_DATO = {"mensaje_de_ejemplo": "CLI-001", "fuera_de_politica": "CLI-004"}
# Los dos clientes homónimos de los datos del core (#4).
HOMONIMOS = ("CLI-002", "CLI-003")


def mensaje(caso: str) -> str:
    """El mensaje del caso con los datos ficticios que le faltan, leídos del core."""
    clientes = Repositorio().clientes
    plantilla = MENSAJES[caso]
    if caso in CLIENTE_DEL_DATO:
        return plantilla.format(dato=clientes[CLIENTE_DEL_DATO[caso]].dato_verificacion)
    if caso == "homonimos":
        return plantilla.format(nombre=clientes[HOMONIMOS[0]].nombre)
    return plantilla


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes ni signos y con espacios simples."""
    sin_tildes = "".join(
        c
        for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    return " ".join(re.sub(r"[^\w\s]", "", sin_tildes).split())


def _ventanas(texto: str) -> set[tuple[str, ...]]:
    palabras = normalizar(texto).split()
    return {
        tuple(palabras[i : i + VENTANA]) for i in range(len(palabras) - VENTANA + 1)
    }


def comparten_ventana(texto: str, otro: str) -> bool:
    """Si los dos textos comparten ``VENTANA`` palabras seguidas."""
    return bool(_ventanas(texto) & _ventanas(otro))
