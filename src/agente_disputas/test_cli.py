import asyncio

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    CLIJSONDecodeError,
    CLINotFoundError,
    ResultMessage,
    TextBlock,
)

from agente_disputas import cli

MODELO = "claude-sonnet-5-5"


def _turno(texto: str = "", **resultado) -> list:
    base = {
        "subtype": "success",
        "duration_ms": 1,
        "duration_api_ms": 1,
        "is_error": False,
        "num_turns": 1,
        "session_id": "sesion-de-prueba",
    }
    mensajes = []
    if texto:
        mensajes.append(
            AssistantMessage(
                content=[TextBlock(text=texto)], model=MODELO, stop_reason="end_turn"
            )
        )
    mensajes.append(ResultMessage(**{**base, **resultado}))
    return mensajes


class ClienteFalso:
    """Imita ``query`` y ``receive_response`` de ``ClaudeSDKClient`` con turnos preparados."""

    def __init__(self, *turnos: list):
        self._turnos = list(turnos)
        self.enviados: list[str] = []

    async def query(self, texto: str) -> None:
        self.enviados.append(texto)

    async def receive_response(self):
        for mensaje in self._turnos.pop(0):
            yield mensaje


def _entrada(*lineas):
    """``leer`` que devuelve las líneas y luego simula el fin de la entrada."""
    pendientes = list(lineas)

    def leer() -> str:
        if not pendientes:
            raise EOFError
        linea = pendientes.pop(0)
        if isinstance(linea, BaseException):
            raise linea
        return linea

    return leer


def _conversar(cliente, *lineas) -> tuple[int, list[str]]:
    salida: list[str] = []
    codigo = asyncio.run(cli.conversar(cliente, _entrada(*lineas), salida.append))
    return codigo, salida


def test_dos_mensajes_dan_dos_respuestas_en_orden():
    cliente = ClienteFalso(_turno("Primera respuesta"), _turno("Segunda respuesta"))
    codigo, salida = _conversar(cliente, "hola", "sigo aquí")
    assert codigo == 0
    assert cliente.enviados == ["hola", "sigo aquí"]
    texto = "\n".join(salida)
    assert texto.index("Primera respuesta") < texto.index("Segunda respuesta")


def test_linea_vacia_no_se_envia():
    cliente = ClienteFalso(_turno("Respuesta"))
    _conversar(cliente, "   ", "", "hola")
    assert cliente.enviados == ["hola"]


@pytest.mark.parametrize("lineas", [("/salir",), ()])
def test_salir_o_fin_de_entrada_terminan_con_cero(lineas):
    cliente = ClienteFalso()
    codigo, _ = _conversar(cliente, *lineas)
    assert codigo == 0
    assert cliente.enviados == []


def test_ctrl_c_termina_con_despedida_sin_traza():
    codigo, salida = _conversar(ClienteFalso(), KeyboardInterrupt())
    assert codigo == 0
    assert salida
    assert "Traceback" not in "\n".join(salida)


@pytest.mark.parametrize(
    ("resultado", "aviso"),
    [
        ({"subtype": "error_max_turns"}, cli.AVISO_SALVAGUARDA),
        ({"is_error": True, "api_error_status": 529}, cli.AVISO_FALLA_SERVICIO),
        ({"subtype": "error_during_execution", "is_error": True}, cli.AVISO_ERROR),
    ],
)
def test_avisos_sin_datos_tecnicos_y_el_bucle_sigue(resultado, aviso):
    cliente = ClienteFalso(_turno(**resultado), _turno("Sigo atendiéndote"))
    codigo, salida = _conversar(cliente, "uno", "dos")
    texto = "\n".join(salida)
    assert codigo == 0
    assert aviso in texto
    assert "529" not in texto
    assert "error_" not in texto
    assert "Sigo atendiéndote" in texto


def test_main_sin_credencial_nombra_la_variable(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert cli.main() == 1
    salida = capsys.readouterr()
    assert "ANTHROPIC_API_KEY" in salida.out + salida.err
    assert "Traceback" not in salida.out + salida.err


# --- arranque: espera del core ---


class ClienteConEstados:
    """Imita ``get_mcp_status`` y el uso como contexto asíncrono de ``ClaudeSDKClient``."""

    def __init__(self, *estados: str, **_):
        self._estados = list(estados)

    async def get_mcp_status(self) -> dict:
        estado = self._estados.pop(0) if len(self._estados) > 1 else self._estados[0]
        return {"mcpServers": [{"name": "core-bancario", "status": estado}]}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


@pytest.fixture
def sin_espera(monkeypatch):
    async def no_esperar(_segundos):
        return None

    monkeypatch.setattr(cli.asyncio, "sleep", no_esperar)


def test_espera_mientras_el_core_esta_pendiente(sin_espera):
    cliente = ClienteConEstados("pending", "pending", "connected")
    assert asyncio.run(cli._esperar_core(cliente)) == "connected"


def test_core_que_falla_se_informa_sin_esperar_mas(sin_espera):
    cliente = ClienteConEstados("failed")
    assert asyncio.run(cli._esperar_core(cliente)) == "failed"


def test_core_que_nunca_arranca_agota_la_espera(sin_espera):
    cliente = ClienteConEstados("pending")
    assert asyncio.run(cli._esperar_core(cliente)) == "pending"


def test_core_no_conectado_termina_con_uno(monkeypatch, sin_espera, capsys):
    monkeypatch.setattr(cli, "ClaudeSDKClient", lambda **_: ClienteConEstados("failed"))
    codigo = asyncio.run(cli._ejecutar({"ANTHROPIC_API_KEY": "clave-de-prueba"}))
    salida = capsys.readouterr()
    assert codigo == 1
    assert "core bancario no arrancó" in salida.err
    assert "clave-de-prueba" not in salida.out + salida.err


def test_cualquier_error_del_sdk_al_arrancar_termina_sin_traza(monkeypatch, capsys):
    class ClienteQueFalla:
        def __init__(self, **_):
            pass

        async def __aenter__(self):
            raise CLIJSONDecodeError("línea inválida", ValueError("x"))

        async def __aexit__(self, *_):
            return False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(cli, "ClaudeSDKClient", ClienteQueFalla)
    assert cli.main() == 1
    salida = capsys.readouterr()
    assert "Traceback" not in salida.out + salida.err
    assert "clave-de-prueba" not in salida.out + salida.err


def _main_con_falla(monkeypatch, excepcion: BaseException) -> int:
    async def ejecutar_que_falla(_entorno):
        raise excepcion

    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(cli, "_ejecutar", ejecutar_que_falla)
    return cli.main()


def test_main_con_ctrl_c_al_arrancar_se_despide_con_cero(monkeypatch, capsys):
    assert _main_con_falla(monkeypatch, KeyboardInterrupt()) == 0
    salida = capsys.readouterr()
    assert cli.DESPEDIDA in salida.out
    assert "Traceback" not in salida.out + salida.err


def test_main_sin_motor_del_agente_termina_con_uno(monkeypatch, capsys):
    assert _main_con_falla(monkeypatch, CLINotFoundError("sin motor")) == 1
    salida = capsys.readouterr()
    assert "motor del agente" in salida.err
    assert "Traceback" not in salida.out + salida.err
