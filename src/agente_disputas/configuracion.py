"""Opciones del agente: solo las herramientas del core bancario, nada del entorno.

La limitación de herramientas es una garantía por configuración (principio II): el agente no
tiene herramientas propias de Claude Code, no pide permisos y no carga settings ni servidores
MCP del disco. Hasta que el issue #9 agregue los hooks de identidad verificada y umbral, solo
se habilitan las herramientas que la constitución exime de la regla 1; las que operan sobre
productos quedan deshabilitadas, así la regla 1 se cumple por diseño. La clave de API no
pasa por aquí: el SDK la hereda del entorno, y ``validar_credencial`` solo comprueba que exista.
"""

import sys
from collections.abc import Mapping

from claude_agent_sdk import ClaudeAgentOptions

from agente_disputas.prompts import PROMPT_SISTEMA

SERVIDOR = "core-bancario"
HERRAMIENTAS = (
    "buscar_cliente",
    "verificar_identidad",
    "consultar_transacciones",
    "iniciar_disputa",
    "bloquear_tarjeta",
    "escalar_a_analista",
)
# Exentas de identidad verificada (regla 1). El #9 habilita las demás junto con sus hooks.
HERRAMIENTAS_HABILITADAS = (
    "buscar_cliente",
    "verificar_identidad",
    "escalar_a_analista",
)
VARIABLE_CREDENCIAL = "ANTHROPIC_API_KEY"
VARIABLE_MODELO = "ANDINO_MODELO"
VARIABLE_FALLAS = "CORE_BANCARIO_FALLAS"
MODELO_POR_OMISION = "claude-sonnet-5-5"
# Salvaguarda (FR-006): el ciclo termina por la razón de parada del modelo; este máximo solo
# evita que un fallo se convierta en un ciclo sin fin. No es el mecanismo de control.
MAXIMO_PASOS_POR_TURNO = 25


class CredencialFaltanteError(Exception):
    """Falta la clave de API; el agente no debe arrancar."""


def validar_credencial(entorno: Mapping[str, str]) -> None:
    if not entorno.get(VARIABLE_CREDENCIAL, "").strip():
        raise CredencialFaltanteError(
            f"Falta la variable de entorno {VARIABLE_CREDENCIAL} con la clave de API."
        )


def _nombre(herramienta: str) -> str:
    return f"mcp__{SERVIDOR}__{herramienta}"


def crear_opciones(entorno: Mapping[str, str]) -> ClaudeAgentOptions:
    servidor = {
        "type": "stdio",
        "command": sys.executable,
        "args": ["-m", "core_bancario_mcp"],
    }
    if VARIABLE_FALLAS in entorno:
        servidor["env"] = {VARIABLE_FALLAS: entorno[VARIABLE_FALLAS]}
    return ClaudeAgentOptions(
        tools=[],
        allowed_tools=[_nombre(n) for n in HERRAMIENTAS_HABILITADAS],
        disallowed_tools=[
            _nombre(n) for n in HERRAMIENTAS if n not in HERRAMIENTAS_HABILITADAS
        ],
        permission_mode="dontAsk",
        mcp_servers={SERVIDOR: servidor},
        strict_mcp_config=True,
        setting_sources=[],
        system_prompt=PROMPT_SISTEMA,
        model=entorno.get(VARIABLE_MODELO) or MODELO_POR_OMISION,
        max_turns=MAXIMO_PASOS_POR_TURNO,
    )
