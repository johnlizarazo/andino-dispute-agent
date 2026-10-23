import asyncio

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from agente_disputas.ciclo import ResultadoTurno, estado_core, procesar_turno

MODELO = "claude-sonnet-5-5"
BUSCAR = "mcp__core-bancario__buscar_cliente"


def _resultado(**campos) -> ResultMessage:
    base = {
        "subtype": "success",
        "duration_ms": 10,
        "duration_api_ms": 8,
        "is_error": False,
        "num_turns": 2,
        "session_id": "sesion-de-prueba",
        "stop_reason": "end_turn",
    }
    return ResultMessage(**{**base, **campos})


def _pide_herramienta(texto: str = "") -> AssistantMessage:
    contenido = [TextBlock(text=texto)] if texto else []
    contenido.append(ToolUseBlock(id="uso-1", name=BUSCAR, input={"nombre": "x"}))
    return AssistantMessage(content=contenido, model=MODELO, stop_reason="tool_use")


def _resultado_herramienta() -> UserMessage:
    return UserMessage(
        content=[ToolResultBlock(tool_use_id="uso-1", content='{"ok": true}')]
    )


def _responde(texto: str) -> AssistantMessage:
    return AssistantMessage(
        content=[TextBlock(text=texto)], model=MODELO, stop_reason="end_turn"
    )


def _procesar(*mensajes) -> ResultadoTurno:
    async def flujo():
        for mensaje in mensajes:
            yield mensaje

    return asyncio.run(procesar_turno(flujo()))


def test_turno_con_herramienta_termina_por_fin_de_turno():
    resultado = _procesar(
        _pide_herramienta(),
        _resultado_herramienta(),
        _responde("Encontré tu registro."),
        _resultado(),
    )
    assert resultado.estado == "completado"
    assert resultado.texto == "Encontré tu registro."
    assert resultado.herramientas == (BUSCAR,)
    assert resultado.detalle is None


@pytest.mark.parametrize(
    "campos",
    [{"subtype": "error_max_turns"}, {"terminal_reason": "max_turns"}],
)
def test_maximo_de_pasos_es_salvaguarda(campos):
    resultado = _procesar(_pide_herramienta(), _resultado(**campos))
    assert resultado.estado == "salvaguarda"


@pytest.mark.parametrize("estado_http", [429, 500, 503, 529])
def test_saturacion_o_falla_del_servicio_es_temporal(estado_http):
    resultado = _procesar(_resultado(is_error=True, api_error_status=estado_http))
    assert resultado.estado == "falla_servicio"
    assert str(estado_http) in resultado.detalle


@pytest.mark.parametrize("estado_http", [400, 401, 403])
def test_errores_de_la_peticion_o_la_clave_no_son_temporales(estado_http):
    # Reintentar no los arregla: no se le dice al cliente que escriba de nuevo.
    resultado = _procesar(_resultado(is_error=True, api_error_status=estado_http))
    assert resultado.estado == "error"


def test_otro_error_es_error():
    resultado = _procesar(_resultado(subtype="error_during_execution", is_error=True))
    assert resultado.estado == "error"


def test_flujo_sin_resultado_es_error():
    assert _procesar(_responde("Hola")).estado == "error"


@pytest.mark.parametrize("palabra", ["listo", "fin", "terminé"])
def test_palabras_del_modelo_no_cierran_el_turno(palabra):
    resultado = _procesar(
        _pide_herramienta(texto=palabra),
        _resultado_herramienta(),
        _responde("Ya revisé tu caso."),
        _resultado(),
    )
    assert resultado.estado == "completado"
    assert resultado.herramientas == (BUSCAR,)
    assert resultado.texto.endswith("Ya revisé tu caso.")


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [("connected", "connected"), ("failed", "failed"), ("pending", "pending")],
)
def test_estado_core_lee_el_estado_del_servidor(estado, esperado):
    respuesta = {
        "mcpServers": [
            {"name": "otro", "status": "connected"},
            {"name": "core-bancario", "status": estado},
        ]
    }
    assert estado_core(respuesta) == esperado


def test_estado_core_ausente():
    assert estado_core({"mcpServers": []}) == "ausente"
