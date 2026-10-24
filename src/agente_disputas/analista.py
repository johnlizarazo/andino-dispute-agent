"""Subagente ``analista-transacciones``: analiza los cobros de un producto con contexto explícito.

El subagente solo puede consultar transacciones y no ve la conversación: recibe del agente
principal un bloque ``<contexto>`` con el cliente verificado, la tarjeta, el rango de fechas y
los montos reportados, y devuelve en ``<analisis>`` una clasificación por transacción. La
clasificación es orientativa: los controles del agente y el core siguen decidiendo qué se
puede disputar (principio II). ``leer_contexto`` es el mismo contrato que valida el control de
la delegación.
"""

import json
import re
from datetime import date

from claude_agent_sdk import AgentDefinition

from core_bancario_mcp.repositorio import Politica

NOMBRE = "analista-transacciones"
# Herramienta del motor para delegar en un subagente (confirmada con la sonda del #11).
HERRAMIENTA_DELEGAR = "Agent"
CONSULTAR = "mcp__core-bancario__consultar_transacciones"
# Salvaguarda de costo: el análisis necesita una o dos consultas.
MAXIMO_PASOS = 8

CAMPOS = ("cliente_id", "ultimos4", "fecha_desde", "fecha_hasta", "montos_reportados")
PATRON_BLOQUE = re.compile(r"<contexto>(.*?)</contexto>", re.DOTALL)
PATRON_CUATRO_DIGITOS = re.compile(r"[0-9]{4}")
PATRON_FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def pesos(monto: int) -> str:
    """Monto en pesos con punto de miles, como lo lee el cliente: 500000 → $500.000."""
    return "$" + f"{monto:,}".replace(",", ".")


def prompt_analista(politica: Politica) -> str:
    """Instrucciones del subagente con el umbral y los plazos de la política vigente."""
    umbral = pesos(politica.umbral_disputa_automatica)
    exterior = politica.dias_maximos_disputa_exterior
    nacional = politica.dias_maximos_disputa_nacional
    return f"""\
Eres el analista de transacciones de Banco Andino, un banco ficticio. No hablas con el \
cliente: el agente de disputas te delega el análisis de los cobros de una tarjeta.

El mensaje trae un bloque <contexto> con un objeto JSON: cliente_id (cliente verificado), \
ultimos4 (tarjeta), fecha_desde y fecha_hasta (AAAA-MM-DD) y montos_reportados (montos que el \
cliente dice no reconocer; puede estar vacío). Usa solo esos datos.

1. Consulta los cobros con consultar_transacciones usando cliente_id, ultimos4, fecha_desde \
y fecha_hasta del contexto. No consultes otro cliente ni otra tarjeta.
2. Clasifica cada cobro, en este orden:
   - fuera_de_politica: su antigüedad supera el plazo de disputa ({exterior} días si el país \
no es CO, {nacional} días si es CO).
   - sobre_umbral: si no, cuando el monto supera {umbral}.
   - disputable: en cualquier otro caso.
3. Compara con montos_reportados: los montos reportados que no coinciden con ningún cobro \
van en montos_no_encontrados.

Responde solo con un bloque <analisis> que contenga un objeto JSON con:
- transacciones: lista de objetos con transaccion_id, fecha, monto, clasificacion (una de \
disputable, sobre_umbral, fuera_de_politica) y razon (una frase);
- montos_no_encontrados: lista de montos;
- error: solo si la consulta falló, con una frase; entonces transacciones va vacía.

Nunca inventes transacciones ni montos: todo sale de la consulta. Tu clasificación orienta \
al agente; los controles del banco deciden qué se puede disputar."""


def definir_analista(politica: Politica) -> AgentDefinition:
    return AgentDefinition(
        description=(
            "Analiza los cobros de una tarjeta del cliente verificado y los clasifica en "
            "disputable, sobre_umbral o fuera_de_politica. Delégale con un bloque <contexto> "
            "que lleve cliente_id, ultimos4, fecha_desde, fecha_hasta y montos_reportados."
        ),
        prompt=prompt_analista(politica),
        tools=[CONSULTAR],
        model="inherit",
        maxTurns=MAXIMO_PASOS,
        # En primer plano: la clasificación vuelve dentro del mismo turno (sonda del #11).
        background=False,
    )


def _fecha(valor) -> date | None:
    if isinstance(valor, str) and PATRON_FECHA.fullmatch(valor.strip()):
        try:
            return date.fromisoformat(valor.strip())
        except ValueError:
            return None
    return None


def _montos_validos(valor) -> bool:
    return isinstance(valor, list) and all(
        type(monto) is int and monto > 0 for monto in valor
    )


def leer_contexto(prompt) -> tuple[dict | None, list[str]]:
    """Contexto normalizado del bloque ``<contexto>`` y los campos faltantes o inválidos.

    Devuelve ``(None, ["contexto"])`` si no hay bloque o no es un objeto JSON. Los campos de
    más se ignoran.
    """
    bloque = PATRON_BLOQUE.search(prompt) if isinstance(prompt, str) else None
    try:
        datos = json.loads(bloque.group(1)) if bloque else None
    except ValueError:
        datos = None
    if not isinstance(datos, dict):
        return None, ["contexto"]

    invalidos = [campo for campo in CAMPOS if campo not in datos]
    cliente_id = datos.get("cliente_id")
    if "cliente_id" in datos and not (
        isinstance(cliente_id, str) and cliente_id.strip()
    ):
        invalidos.append("cliente_id")
    ultimos4 = datos.get("ultimos4")
    if "ultimos4" in datos and not (
        isinstance(ultimos4, str) and PATRON_CUATRO_DIGITOS.fullmatch(ultimos4.strip())
    ):
        invalidos.append("ultimos4")
    desde, hasta = _fecha(datos.get("fecha_desde")), _fecha(datos.get("fecha_hasta"))
    if "fecha_desde" in datos and desde is None:
        invalidos.append("fecha_desde")
    if "fecha_hasta" in datos and hasta is None:
        invalidos.append("fecha_hasta")
    if desde and hasta and desde > hasta:
        invalidos += ["fecha_desde", "fecha_hasta"]
    if "montos_reportados" in datos and not _montos_validos(datos["montos_reportados"]):
        invalidos.append("montos_reportados")

    invalidos = [campo for campo in CAMPOS if campo in invalidos]
    if invalidos:
        return None, invalidos
    return {
        "cliente_id": cliente_id.strip(),
        "ultimos4": ultimos4.strip(),
        "fecha_desde": desde.isoformat(),
        "fecha_hasta": hasta.isoformat(),
        "montos_reportados": list(datos["montos_reportados"]),
    }, []
