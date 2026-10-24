import asyncio
import json

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKError,
    CLINotFoundError,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from agente_disputas.cli import (
    AVISO_ESCALAMIENTO_PENDIENTE,
    AVISO_FALLA_SERVICIO,
    AVISO_SESION,
    SIN_TEXTO,
)
from agente_disputas.controles import BLOQUEAR, Controles, EstadoSesion
from agente_disputas.eventos import Evento
from agente_disputas.sesion import AVISO_ARRANQUE, AVISO_SIN_CORE, SesionChat
from core_bancario_mcp.errores import exito
from core_bancario_mcp.repositorio import Repositorio

MODELO = "modelo-de-prueba"
ENTORNO = {"ANTHROPIC_API_KEY": "clave-ficticia"}


def _resultado(**cambios) -> ResultMessage:
    base = {
        "subtype": "success",
        "duration_ms": 1,
        "duration_api_ms": 1,
        "is_error": False,
        "num_turns": 1,
        "session_id": "sesion-de-prueba",
    }
    return ResultMessage(**{**base, **cambios})


def _texto(texto: str) -> AssistantMessage:
    return AssistantMessage(content=[TextBlock(text=texto)], model=MODELO)


def _bloqueo() -> list:
    datos = {"ultimos4": "4821", "estado": "bloqueada", "ya_estaba_bloqueada": False}
    entrada = {"cliente_id": "CLI-001", "ultimos4": "4821", "motivo": "Sospecha"}
    return [
        AssistantMessage(
            content=[ToolUseBlock(id="u1", name=BLOQUEAR, input=entrada)],
            model=MODELO,
        ),
        UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id="u1",
                    content=[{"type": "text", "text": json.dumps(exito(datos))}],
                )
            ]
        ),
        _texto("Listo, tu tarjeta quedó bloqueada."),
        _resultado(),
    ]


class ClienteFalso:
    """Imita ``ClaudeSDKClient``: contexto, ``query``, ``receive_response`` y estado MCP."""

    def __init__(self, turnos=(), estado_core="connected", falla_al_entrar=None):
        self.turnos = list(turnos)
        self.estado_core = estado_core
        self.falla_al_entrar = falla_al_entrar
        self.enviados: list[str] = []
        self.tareas: set = set()
        self.cerrado = False
        self.opciones = None

    def __call__(self, options):
        self.opciones = options
        return self

    async def __aenter__(self):
        self.tareas.add(asyncio.current_task())
        if self.falla_al_entrar:
            raise self.falla_al_entrar
        return self

    async def __aexit__(self, *_):
        self.tareas.add(asyncio.current_task())
        self.cerrado = True

    async def get_mcp_status(self):
        return {"mcpServers": [{"name": "core-bancario", "status": self.estado_core}]}

    async def query(self, texto):
        self.tareas.add(asyncio.current_task())
        self.enviados.append(texto)

    async def receive_response(self):
        self.tareas.add(asyncio.current_task())
        turno = self.turnos.pop(0)
        if isinstance(turno, Exception):
            raise turno
        for mensaje in turno:
            await asyncio.sleep(0)
            yield mensaje


def _controles() -> Controles:
    repositorio = Repositorio()
    return Controles(repositorio.obtener_transaccion, repositorio.politica)


def _sesion(cliente: ClienteFalso, entorno=ENTORNO, controles=None) -> SesionChat:
    return SesionChat(
        entorno, fabrica_cliente=cliente, controles=controles or _controles()
    )


def _correr(corrutina):
    return asyncio.run(corrutina)


class Registro:
    def __init__(self):
        self.vistos: list = []

    async def __call__(self, evento: Evento):
        self.vistos.append(evento)


# --- iniciar ---


def test_sin_credencial_avisa_y_no_crea_el_cliente():
    cliente = ClienteFalso()

    async def probar():
        sesion = _sesion(cliente, entorno={})
        aviso = await sesion.iniciar()
        await sesion.cerrar()
        return aviso

    aviso = _correr(probar())
    assert "ANTHROPIC_API_KEY" in aviso
    assert cliente.opciones is None


def test_core_que_no_conecta_avisa():
    cliente = ClienteFalso(estado_core="failed")

    async def probar():
        sesion = _sesion(cliente)
        aviso = await sesion.iniciar()
        respuesta = await sesion.turno("hola", Registro())
        await sesion.cerrar()
        return aviso, respuesta

    aviso, respuesta = _correr(probar())
    assert aviso == AVISO_SIN_CORE
    assert respuesta == AVISO_SIN_CORE
    assert cliente.enviados == []
    assert cliente.cerrado


def test_falla_al_arrancar_el_agente_avisa_sin_traza():
    cliente = ClienteFalso(falla_al_entrar=CLINotFoundError("sin motor"))

    async def probar():
        sesion = _sesion(cliente)
        return await sesion.iniciar()

    assert _correr(probar()) == AVISO_ARRANQUE


def test_core_conectado_queda_lista_con_los_controles_de_la_sesion():
    cliente = ClienteFalso()
    controles = _controles()

    async def probar():
        sesion = _sesion(cliente, controles=controles)
        aviso = await sesion.iniciar()
        await sesion.cerrar()
        return aviso

    assert _correr(probar()) is None
    assert cliente.opciones.hooks["Stop"][0].hooks[0].__self__ is controles


# --- turno ---


def test_turno_entrega_los_eventos_antes_de_la_respuesta():
    cliente = ClienteFalso([_bloqueo()])
    orden: list = []

    async def al_evento(evento):
        orden.append(evento.tipo)

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        respuesta = await sesion.turno("bloquea mi tarjeta", al_evento)
        orden.append("respuesta")
        await sesion.cerrar()
        return respuesta

    assert _correr(probar()) == "Listo, tu tarjeta quedó bloqueada."
    assert orden == ["bloqueo", "respuesta"]
    assert cliente.enviados == ["bloquea mi tarjeta"]


def test_turno_sin_texto_y_turno_que_no_completa():
    cliente = ClienteFalso(
        [[_resultado()], [_resultado(is_error=True, api_error_status=529)]]
    )

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        respuestas = [
            await sesion.turno("uno", Registro()),
            await sesion.turno("dos", Registro()),
        ]
        await sesion.cerrar()
        return respuestas

    assert _correr(probar()) == [SIN_TEXTO, AVISO_FALLA_SERVICIO]


def test_escalamiento_pendiente_agrega_el_aviso_de_la_interfaz():
    controles = _controles()
    controles.estado.pendientes["TRX-002"] = "umbral"
    cliente = ClienteFalso([[_texto("Te ayudo."), _resultado()]])

    async def probar():
        sesion = _sesion(cliente, controles=controles)
        await sesion.iniciar()
        respuesta = await sesion.turno("hola", Registro())
        await sesion.cerrar()
        return respuesta

    respuesta = _correr(probar())
    assert respuesta.startswith("Te ayudo.")
    assert respuesta.endswith(AVISO_ESCALAMIENTO_PENDIENTE)


def test_sesion_perdida_avisa_y_no_atiende_mas():
    cliente = ClienteFalso([ClaudeSDKError("se cayó"), [_resultado()]])

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        respuestas = [
            await sesion.turno("uno", Registro()),
            await sesion.turno("dos", Registro()),
        ]
        await sesion.cerrar()
        return respuestas

    assert _correr(probar()) == [AVISO_SESION, AVISO_SESION]
    assert cliente.enviados == ["uno"]


def test_un_error_inesperado_no_deja_el_turno_esperando():
    cliente = ClienteFalso([RuntimeError("inesperado")])

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        respuesta = await asyncio.wait_for(sesion.turno("uno", Registro()), 5)
        await sesion.cerrar()
        return respuesta

    assert _correr(probar()) == AVISO_SESION


def test_turnos_concurrentes_se_atienden_en_orden():
    cliente = ClienteFalso(
        [[_texto("primero"), _resultado()], [_texto("segundo"), _resultado()]]
    )

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        respuestas = await asyncio.gather(
            sesion.turno("a", Registro()), sesion.turno("b", Registro())
        )
        await sesion.cerrar()
        return respuestas

    assert _correr(probar()) == ["primero", "segundo"]
    assert cliente.enviados == ["a", "b"]


def test_el_cliente_solo_se_usa_desde_una_tarea():
    cliente = ClienteFalso([_bloqueo(), [_resultado()]])

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        await asyncio.create_task(sesion.turno("uno", Registro()))
        await asyncio.create_task(sesion.turno("dos", Registro()))
        await sesion.cerrar()

    _correr(probar())
    assert len(cliente.tareas) == 1


def test_cada_sesion_tiene_su_propio_estado():
    primera = SesionChat(ENTORNO, fabrica_cliente=ClienteFalso())
    segunda = SesionChat(ENTORNO, fabrica_cliente=ClienteFalso())
    assert primera.controles is not segunda.controles
    primera.controles.estado.cliente_verificado = "CLI-001"
    assert segunda.controles.estado == EstadoSesion()


def test_cerrar_libera_el_cliente_y_es_idempotente():
    cliente = ClienteFalso()

    async def probar():
        sesion = _sesion(cliente)
        await sesion.iniciar()
        await sesion.cerrar()
        await sesion.cerrar()
        return await sesion.turno("hola", Registro())

    assert _correr(probar()) == AVISO_SESION
    assert cliente.cerrado


def test_cerrar_sin_iniciar_no_falla():
    _correr(_sesion(ClienteFalso()).cerrar())
