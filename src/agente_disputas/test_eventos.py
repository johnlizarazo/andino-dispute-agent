import json

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from agente_disputas.analista import HERRAMIENTA_DELEGAR
from agente_disputas.controles import (
    BLOQUEAR,
    CONSULTAR,
    DISPUTAR,
    ESCALAR,
    VERIFICAR,
    EstadoSesion,
    Negacion,
)
from agente_disputas.eventos import (
    EXITO,
    FALLA,
    NEGADO,
    Evento,
    LectorEventos,
    formatear_evento,
)
from core_bancario_mcp.bloqueo_escalamiento import CAUSAS
from core_bancario_mcp.errores import TipoError, error, exito

BUSCAR = "mcp__core-bancario__buscar_cliente"
MODELO = "modelo-de-prueba"
ARGUMENTOS = {
    VERIFICAR: {"cliente_id": "CLI-001", "dato_verificacion": "0000"},
    BLOQUEAR: {"cliente_id": "CLI-001", "ultimos4": "4821", "motivo": "Sospecha"},
    DISPUTAR: {"transaccion_id": "TRX-001", "motivo": "No la reconozco"},
    ESCALAR: {"causa": "umbral", "transacciones": ["TRX-002"]},
    CONSULTAR: {"cliente_id": "CLI-001", "ultimos4": "4821"},
    BUSCAR: {"documento": "CC-FIC-0001"},
    HERRAMIENTA_DELEGAR: {"subagent_type": "analista-transacciones", "prompt": "..."},
}


def _llamada(herramienta: str, uso: str = "uso-1", padre=None) -> AssistantMessage:
    bloque = ToolUseBlock(id=uso, name=herramienta, input=ARGUMENTOS[herramienta])
    return AssistantMessage(content=[bloque], model=MODELO, parent_tool_use_id=padre)


def _resultado(contenido, uso: str = "uso-1", is_error=None, padre=None):
    bloque = ToolResultBlock(tool_use_id=uso, content=contenido, is_error=is_error)
    return UserMessage(content=[bloque], parent_tool_use_id=padre)


def _del_core(respuesta: dict) -> list:
    """Forma en que el SDK entrega la respuesta de una herramienta MCP (T001)."""
    return [{"type": "text", "text": json.dumps(respuesta)}]


def _eventos(herramienta, contenido, estado=None, is_error=None) -> list[Evento]:
    lector = LectorEventos(estado or EstadoSesion())
    eventos = lector.leer(_llamada(herramienta))
    eventos += lector.leer(_resultado(contenido, is_error=is_error))
    return eventos + lector.cerrar()


def _uno(herramienta, contenido, **extra) -> Evento:
    eventos = _eventos(herramienta, contenido, **extra)
    assert len(eventos) == 1
    return eventos[0]


def _error(codigo: str, tipo=TipoError.NEGOCIO) -> list:
    return _del_core(error(tipo, codigo, "Mensaje técnico del core."))


# --- una prueba por fila del contrato ---


def test_identidad_verificada():
    evento = _uno(
        VERIFICAR, _del_core(exito({"cliente_id": "CLI-001", "verificado": True}))
    )
    assert (evento.tipo, evento.resultado) == ("identidad", EXITO)
    assert evento.titulo == "Identidad verificada"
    assert "CLI-001" in evento.detalle


@pytest.mark.parametrize("codigo", ["VERIFICACION_FALLIDA", "INTENTOS_AGOTADOS"])
def test_identidad_no_verificada(codigo):
    evento = _uno(VERIFICAR, _error(codigo, TipoError.PERMISO))
    assert (evento.tipo, evento.resultado) == ("identidad", FALLA)
    assert evento.titulo == "No se pudo verificar la identidad"
    assert evento.detalle


def test_tarjeta_bloqueada():
    datos = {"ultimos4": "4821", "estado": "bloqueada", "ya_estaba_bloqueada": False}
    evento = _uno(BLOQUEAR, _del_core(exito(datos)))
    assert (evento.tipo, evento.resultado) == ("bloqueo", EXITO)
    assert evento.titulo == "Tarjeta bloqueada"
    assert evento.detalle == "•••• 4821"


def test_tarjeta_que_ya_estaba_bloqueada():
    datos = {"ultimos4": "4821", "estado": "bloqueada", "ya_estaba_bloqueada": True}
    evento = _uno(BLOQUEAR, _del_core(exito(datos)))
    assert "•••• 4821" in evento.detalle
    assert "ya estaba bloqueada" in evento.detalle


def test_disputa_iniciada_con_el_monto_del_core():
    datos = {
        "caso_id": "DSP-001",
        "transaccion_id": "TRX-001",
        "monto": 180000,
        "estado": "abierta",
    }
    evento = _uno(DISPUTAR, _del_core(exito(datos)))
    assert (evento.tipo, evento.resultado) == ("disputa", EXITO)
    assert evento.titulo == "Disputa iniciada"
    for parte in ("DSP-001", "TRX-001", "$180.000"):
        assert parte in evento.detalle


@pytest.mark.parametrize(
    ("codigo", "titulo"),
    [
        ("FUERA_DE_POLITICA", "Disputa fuera de la política del banco"),
        ("REQUIERE_ANALISTA", "Disputa por encima del umbral"),
    ],
)
def test_disputa_rechazada_por_el_core(codigo, titulo):
    evento = _uno(DISPUTAR, _error(codigo))
    assert (evento.tipo, evento.resultado) == ("rechazo_politica", NEGADO)
    assert evento.titulo == titulo
    assert "TRX-001" in evento.detalle
    assert "requiere un analista" in evento.detalle


MOTIVOS = {
    "persona_solicitada": "el cliente pidió hablar con una persona",
    "umbral": "el monto supera el umbral de disputa automática",
    "fuera_de_politica": "el caso está fuera de la política del banco",
    "intentos_agotados": "se agotaron los intentos de verificación",
    "otra": "otro motivo",
}


def test_hay_motivo_de_negocio_para_cada_causa_del_core():
    assert set(MOTIVOS) == set(CAUSAS)


@pytest.mark.parametrize("causa", CAUSAS)
def test_caso_escalado_con_cada_causa_en_lenguaje_de_negocio(causa):
    datos = {
        "escalamiento_id": "ESC-001",
        "causa": causa,
        "estado": "pendiente",
        "cantidad_transacciones": 1,
    }
    evento = _uno(ESCALAR, _del_core(exito(datos)))
    assert (evento.tipo, evento.resultado) == ("escalamiento", EXITO)
    assert evento.titulo == "Caso escalado a un analista"
    assert "ESC-001" in evento.detalle
    assert MOTIVOS[causa] in evento.detalle


def test_analisis_del_subagente_con_texto_libre():
    evento = _uno(HERRAMIENTA_DELEGAR, [{"type": "text", "text": "<analisis>…"}])
    assert (evento.tipo, evento.resultado) == ("analisis", EXITO)
    assert evento.titulo == "Análisis de transacciones realizado"


def test_analisis_del_subagente_con_error():
    evento = _uno(HERRAMIENTA_DELEGAR, "falló", is_error=True)
    assert (evento.tipo, evento.resultado) == ("falla", FALLA)
    assert evento.titulo == "No se pudo completar: Análisis de transacciones"


@pytest.mark.parametrize(
    ("herramienta", "datos"), [(CONSULTAR, {"transacciones": []}), (BUSCAR, [])]
)
def test_lecturas_exitosas_no_producen_evento(herramienta, datos):
    assert _eventos(herramienta, _del_core(exito(datos))) == []


@pytest.mark.parametrize(
    ("tipo", "detalle"),
    [
        (TipoError.TRANSITORIO, "error temporal del sistema"),
        (TipoError.VALIDACION, "datos inválidos"),
    ],
)
@pytest.mark.parametrize("herramienta", [BLOQUEAR, DISPUTAR, ESCALAR, CONSULTAR])
def test_falla_del_core(herramienta, tipo, detalle):
    evento = _uno(herramienta, _error("FALLA_TRANSITORIA", tipo))
    assert (evento.tipo, evento.resultado) == ("falla", FALLA)
    assert evento.titulo.startswith("No se pudo completar: ")
    assert detalle in evento.detalle


# --- negaciones ---


def _negado(herramienta: str, codigo: str, uso: str = "uso-1") -> EstadoSesion:
    return EstadoSesion(negaciones=[Negacion(herramienta, codigo, uso)])


@pytest.mark.parametrize(
    ("codigo", "razon"),
    [
        ("SIN_IDENTIDAD", "la identidad del cliente no está verificada"),
        ("CLIENTE_DISTINTO", "el producto no es del cliente verificado"),
        ("REQUIERE_ANALISTA", "supera el umbral de disputa automática"),
        ("FALLA_CONTROL", "no se pudo confirmar la operación"),
        ("CODIGO_NUEVO", "no se pudo confirmar la operación"),
    ],
)
def test_negacion_con_resultado_usa_la_razon_de_negocio(codigo, razon):
    lector = LectorEventos(EstadoSesion())
    lector.leer(_llamada(BLOQUEAR))
    lector.estado.negaciones.append(Negacion(BLOQUEAR, codigo, "uso-1"))
    eventos = lector.leer(_resultado("Razón para el modelo", is_error=True))
    [evento] = eventos + lector.cerrar()
    assert (evento.tipo, evento.resultado) == ("negacion", NEGADO)
    assert evento.titulo == "Operación negada por un control del banco"
    assert evento.detalle.startswith("Bloqueo de tarjeta: ")
    assert razon in evento.detalle


def test_negacion_sin_resultado_aparece_al_cerrar():
    lector = LectorEventos(EstadoSesion())
    assert lector.leer(_llamada(DISPUTAR)) == []
    lector.estado.negaciones.append(Negacion(DISPUTAR, "REQUIERE_ANALISTA", "uso-1"))
    [evento] = lector.cerrar()
    assert (evento.tipo, evento.resultado) == ("negacion", NEGADO)
    assert evento.detalle.startswith("Disputa: ")


def test_negacion_de_la_delegacion():
    lector = LectorEventos(EstadoSesion())
    lector.leer(_llamada(HERRAMIENTA_DELEGAR))
    lector.estado.negaciones.append(
        Negacion(HERRAMIENTA_DELEGAR, "CONTEXTO_INCOMPLETO", "uso-1")
    )
    [evento] = lector.leer(_resultado("Falta el bloque", is_error=True))
    assert evento.resultado == NEGADO
    assert "Análisis de transacciones" in evento.detalle
    assert "no cumplió las condiciones" in evento.detalle


def test_consulta_del_subagente_negada():
    lector = LectorEventos(EstadoSesion())
    lector.leer(_llamada(CONSULTAR, "uso-9", padre="uso-1"))
    lector.estado.negaciones.append(Negacion(CONSULTAR, "CLIENTE_DISTINTO", "uso-9"))
    [evento] = lector.leer(_resultado("negada", "uso-9", True, padre="uso-1"))
    assert evento.resultado == NEGADO
    assert evento.detalle.startswith("Consulta de transacciones: ")


def test_negaciones_de_turnos_anteriores_no_cuentan():
    estado = _negado(BLOQUEAR, "SIN_IDENTIDAD")
    datos = {"ultimos4": "4821", "estado": "bloqueada", "ya_estaba_bloqueada": False}
    evento = _uno(BLOQUEAR, _del_core(exito(datos)), estado=estado)
    assert evento.resultado == EXITO


# --- robustez ---


@pytest.mark.parametrize(
    "contenido",
    [None, "texto que no es JSON", [{"type": "text", "text": "{}"}], {"ok": "sí"}],
)
@pytest.mark.parametrize("herramienta", [VERIFICAR, BLOQUEAR, DISPUTAR, ESCALAR])
def test_respuesta_ilegible_es_falla(herramienta, contenido):
    evento = _uno(herramienta, contenido)
    assert evento.resultado == FALLA


def test_llamada_sin_resultado_ni_negacion_es_falla_al_cerrar():
    lector = LectorEventos(EstadoSesion())
    lector.leer(_llamada(BLOQUEAR))
    [evento] = lector.cerrar()
    assert (evento.tipo, evento.resultado) == ("falla", FALLA)
    assert evento.titulo == "No se pudo completar: Bloqueo de tarjeta"


def test_eventos_en_el_orden_de_los_resultados_y_uno_por_llamada():
    lector = LectorEventos(EstadoSesion())
    verificado = exito({"cliente_id": "CLI-001", "verificado": True})
    bloqueo = exito(
        {"ultimos4": "4821", "estado": "bloqueada", "ya_estaba_bloqueada": False}
    )
    llamadas = AssistantMessage(
        content=[
            TextBlock(text="Reviso."),
            ToolUseBlock(id="a", name=VERIFICAR, input=ARGUMENTOS[VERIFICAR]),
            ToolUseBlock(id="b", name=BLOQUEAR, input=ARGUMENTOS[BLOQUEAR]),
        ],
        model=MODELO,
    )
    resultados = UserMessage(
        content=[
            ToolResultBlock(tool_use_id="a", content=_del_core(verificado)),
            ToolResultBlock(tool_use_id="b", content=_del_core(bloqueo)),
        ]
    )
    eventos = lector.leer(llamadas) + lector.leer(resultados)
    eventos += lector.leer(resultados)  # un resultado repetido no duplica eventos
    eventos += lector.cerrar() + lector.cerrar()
    assert [e.tipo for e in eventos] == ["identidad", "bloqueo"]


def test_mensajes_sin_herramientas_no_producen_eventos():
    lector = LectorEventos(EstadoSesion())
    texto = AssistantMessage(content=[TextBlock(text="Hola")], model=MODELO)
    assert lector.leer(texto) == []
    assert lector.leer(UserMessage(content="hola")) == []
    assert lector.leer(object()) == []


# --- lenguaje de negocio (FR-008) ---


def _todos_los_eventos() -> list[Evento]:
    datos_ok = {
        VERIFICAR: {"cliente_id": "CLI-001", "verificado": True},
        BLOQUEAR: {
            "ultimos4": "4821",
            "estado": "bloqueada",
            "ya_estaba_bloqueada": True,
        },
        DISPUTAR: {
            "caso_id": "DSP-1",
            "transaccion_id": "TRX-001",
            "monto": 1,
            "estado": "x",
        },
        ESCALAR: {"escalamiento_id": "E-1", "causa": "otra", "estado": "x"},
    }
    eventos = []
    for herramienta, datos in datos_ok.items():
        eventos += _eventos(herramienta, _del_core(exito(datos)))
        eventos += _eventos(
            herramienta, _error("FALLA_TRANSITORIA", TipoError.TRANSITORIO)
        )
        eventos += _eventos(herramienta, None)
    for codigo in ("FUERA_DE_POLITICA", "REQUIERE_ANALISTA", "VERIFICACION_FALLIDA"):
        eventos += _eventos(DISPUTAR, _error(codigo))
        eventos += _eventos(VERIFICAR, _error(codigo))
    for codigo in ("SIN_IDENTIDAD", "CONTEXTO_INCOMPLETO", "TRANSACCION_NO_CONFIRMADA"):
        eventos += _eventos(BLOQUEAR, "x", estado=_negado(BLOQUEAR, codigo))
    return eventos


def test_ningun_evento_expone_detalles_tecnicos():
    prohibidos = ("mcp__", "core-bancario", "_", "{", "ok", "Mensaje técnico")
    for evento in _todos_los_eventos():
        for texto in (evento.titulo, evento.detalle):
            for prohibido in prohibidos:
                assert prohibido not in texto, (prohibido, evento)


def test_solo_hay_exito_con_ok_verdadero():
    for herramienta in (VERIFICAR, BLOQUEAR, DISPUTAR, ESCALAR):
        for contenido in (
            _error("FALLA_TRANSITORIA"),
            None,
            "x",
            _del_core({"ok": False}),
        ):
            assert all(e.resultado != EXITO for e in _eventos(herramienta, contenido))


# --- formato para la interfaz ---


@pytest.mark.parametrize(
    ("resultado", "prefijo"), [(EXITO, "✅"), (NEGADO, "⛔"), (FALLA, "⚠️")]
)
def test_formato_del_evento(resultado, prefijo):
    evento = Evento("bloqueo", resultado, "Tarjeta bloqueada", "•••• 4821")
    assert formatear_evento(evento) == f"{prefijo} Tarjeta bloqueada\n•••• 4821"


def test_formato_sin_detalle():
    evento = Evento("analisis", EXITO, "Análisis de transacciones realizado", "")
    assert formatear_evento(evento) == "✅ Análisis de transacciones realizado"
