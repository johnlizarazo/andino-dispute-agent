"""Opciones del agente: solo las herramientas del core bancario, nada del entorno.

La limitación de herramientas es una garantía por configuración (principio II): el agente no
tiene herramientas propias de Claude Code salvo la de delegar en ``analista-transacciones``
(issue #11), no pide permisos y no carga settings ni servidores MCP del disco. Las reglas 1 y 2 las garantizan los hooks de ``controles`` (issue #9), que se
registran aquí con un estado nuevo por conversación y no dependen del prompt. La clave de API
no pasa por aquí: el SDK la hereda del entorno, y ``validar_credencial`` solo comprueba que
exista.
"""

import sys
from collections.abc import Mapping

from claude_agent_sdk import ClaudeAgentOptions

from agente_disputas.analista import HERRAMIENTA_DELEGAR, definir_analista
from agente_disputas.analista import NOMBRE as NOMBRE_ANALISTA
from agente_disputas.controles import Controles
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


def crear_opciones(
    entorno: Mapping[str, str], controles: Controles | None = None
) -> ClaudeAgentOptions:
    if controles is None:
        controles = Controles.desde_entorno(entorno)
    servidor = {
        "type": "stdio",
        "command": sys.executable,
        "args": ["-m", "core_bancario_mcp"],
    }
    if VARIABLE_FALLAS in entorno:
        servidor["env"] = {VARIABLE_FALLAS: entorno[VARIABLE_FALLAS]}
    # El subagente necesita la política para sus instrucciones; sin datos del core no se
    # registra ni él ni la herramienta de delegación (falla cerrada).
    delegar = [HERRAMIENTA_DELEGAR] if controles.politica is not None else []
    agentes = (
        {NOMBRE_ANALISTA: definir_analista(controles.politica)} if delegar else None
    )
    return ClaudeAgentOptions(
        tools=delegar,
        allowed_tools=[_nombre(n) for n in HERRAMIENTAS] + delegar,
        disallowed_tools=[],
        agents=agentes,
        hooks=controles.hooks(),
        permission_mode="dontAsk",
        mcp_servers={SERVIDOR: servidor},
        strict_mcp_config=True,
        setting_sources=[],
        system_prompt=PROMPT_SISTEMA,
        model=entorno.get(VARIABLE_MODELO) or MODELO_POR_OMISION,
        max_turns=MAXIMO_PASOS_POR_TURNO,
    )
