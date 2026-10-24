import json

from claude_agent_sdk import (
    AssistantMessage,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from registro import Llamada, armar_registro

from agente_disputas.ciclo import COMPLETADO, ResultadoTurno
from agente_disputas.controles import EstadoSesion, Negacion
from core_bancario_mcp.errores import TipoError, error, exito

MODELO = "modelo-de-prueba"
PREFIJO = "mcp__core-bancario__"
RESULTADO = ResultadoTurno(COMPLETADO, "Listo.", (), None)


def _uso(uso: str, herramienta: str, argumentos=None, padre=None) -> AssistantMessage:
    bloque = ToolUseBlock(id=uso, name=herramienta, input=argumentos or {})
    return AssistantMessage(content=[bloque], model=MODELO, parent_tool_use_id=padre)


def _resultado(uso: str, contrato, padre=None) -> UserMessage:
    contenido = (
        [{"type": "text", "text": json.dumps(contrato)}]
        if isinstance(contrato, dict)
        else contrato
    )
    bloque = ToolResultBlock(tool_use_id=uso, content=contenido)
    return UserMessage(content=[bloque], parent_tool_use_id=padre)


def _armar(mensajes, estado=None, inicio=0):
    return armar_registro(mensajes, estado or EstadoSesion(), inicio, RESULTADO)


def test_llamadas_en_orden_con_nombre_corto_argumentos_y_respuesta():
    registro = _armar(
        [
            _uso("a", PREFIJO + "buscar_cliente", {"documento": "CC-FIC-0001"}),
            _resultado("a", exito([{"cliente_id": "CLI-001"}])),
            _uso("b", "Agent", {"subagent_type": "analista-transacciones"}),
            _resultado("b", "texto libre"),
        ]
    )
    assert [ll.herramienta for ll in registro.llamadas] == ["buscar_cliente", "Agent"]
    primera = registro.llamadas[0]
    assert primera.argumentos == {"documento": "CC-FIC-0001"}
    assert primera.respuesta == exito([{"cliente_id": "CLI-001"}])
    assert primera.ok and primera.codigo is None
    assert registro.llamadas[1].respuesta is None


def test_error_del_core_y_llamada_sin_resultado():
    falla = error(TipoError.NEGOCIO, "FUERA_DE_POLITICA", "No cubierto.")
    registro = _armar(
        [
            _uso("a", PREFIJO + "iniciar_disputa", {"transaccion_id": "TRX-006"}),
            _resultado("a", falla),
            _uso("b", PREFIJO + "bloquear_tarjeta"),
        ]
    )
    disputa, bloqueo = registro.llamadas
    assert not disputa.ok and disputa.codigo == "FUERA_DE_POLITICA"
    assert bloqueo.respuesta is None and not bloqueo.ok and bloqueo.codigo is None


def test_negaciones_solo_del_turno():
    estado = EstadoSesion(
        negaciones=[
            Negacion(PREFIJO + "iniciar_disputa", "SIN_IDENTIDAD", "viejo"),
            Negacion(PREFIJO + "iniciar_disputa", "REQUIERE_ANALISTA", "a"),
        ]
    )
    registro = _armar(
        [
            _uso("viejo", PREFIJO + "iniciar_disputa"),
            _uso("a", PREFIJO + "iniciar_disputa"),
            _resultado("a", "Razón para el modelo"),
        ],
        estado,
        inicio=1,
    )
    assert [ll.negada for ll in registro.llamadas] == [None, "REQUIERE_ANALISTA"]


def test_las_llamadas_del_subagente_se_excluyen():
    registro = _armar(
        [
            _uso("a", "Agent"),
            _uso("s", PREFIJO + "consultar_transacciones", padre="a"),
            _resultado("s", exito({"transacciones": []}), padre="a"),
            _resultado("a", "análisis"),
        ]
    )
    assert [ll.herramienta for ll in registro.llamadas] == ["Agent"]


def test_pendientes_estado_y_texto():
    estado = EstadoSesion(pendientes={"TRX-002": "umbral"})
    registro = _armar([], estado)
    estado.pendientes.clear()
    assert registro.pendientes == {"TRX-002": "umbral"}
    assert registro.estado == COMPLETADO
    assert registro.texto == "Listo."
    assert registro.primera() is None


def test_consultas_de_primera_y_escalamientos():
    ok = exito({"escalamiento_id": "ESC-1", "causa": "umbral"})
    registro = _armar(
        [
            _uso("a", PREFIJO + "escalar_a_analista", {"causa": "umbral"}),
            _resultado("a", ok),
            _uso("b", PREFIJO + "escalar_a_analista", {"causa": "umbral"}),
            _resultado("b", error(TipoError.TRANSITORIO, "FALLA_TRANSITORIA", "x")),
            _uso("c", PREFIJO + "escalar_a_analista", {"causa": "otra"}),
            _resultado("c", ok),
        ]
    )
    assert registro.primera().herramienta == "escalar_a_analista"
    assert len(registro.de("escalar_a_analista")) == 3
    assert registro.de("iniciar_disputa") == []
    assert [ll.argumentos["causa"] for ll in registro.escalamientos("umbral")] == [
        "umbral"
    ]


def test_llamada_es_inmutable():
    llamada = Llamada("buscar_cliente", {}, None, None)
    try:
        llamada.negada = "X"
    except AttributeError:
        return
    raise AssertionError("Llamada debería ser inmutable")
