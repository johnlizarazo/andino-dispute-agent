import asyncio
import sys
from dataclasses import replace

import pytest

from agente_disputas.analista import HERRAMIENTA_DELEGAR, NOMBRE, definir_analista
from agente_disputas.configuracion import (
    HERRAMIENTAS,
    CredencialFaltanteError,
    crear_opciones,
    validar_credencial,
)
from agente_disputas.controles import Controles
from agente_disputas.prompts import PROMPT_SISTEMA
from core_bancario_mcp.repositorio import Repositorio

CLAVE_FICTICIA = "clave-de-prueba"
ENTORNO = {"ANTHROPIC_API_KEY": CLAVE_FICTICIA}


def test_herramientas_son_las_seis_del_core():
    assert set(HERRAMIENTAS) == {
        "buscar_cliente",
        "verificar_identidad",
        "consultar_transacciones",
        "iniciar_disputa",
        "bloquear_tarjeta",
        "escalar_a_analista",
    }


def test_sin_settings_del_entorno_ni_permisos_interactivos():
    opciones = crear_opciones(ENTORNO)
    assert opciones.permission_mode == "dontAsk"
    assert opciones.strict_mcp_config is True
    assert opciones.setting_sources == []


PRODUCTOS = (
    "mcp__core-bancario__consultar_transacciones",
    "mcp__core-bancario__iniciar_disputa",
    "mcp__core-bancario__bloquear_tarjeta",
)
VERIFICAR = "mcp__core-bancario__verificar_identidad"
DISPUTA_SIN_VERIFICAR = {
    "hook_event_name": "PreToolUse",
    "tool_name": "mcp__core-bancario__iniciar_disputa",
    "tool_input": {"transaccion_id": "TRX-001", "motivo": "No lo reconozco"},
}


def test_se_habilitan_las_seis_del_core_y_solo_la_delegacion():
    opciones = crear_opciones(ENTORNO)
    assert opciones.allowed_tools == [
        f"mcp__core-bancario__{nombre}" for nombre in HERRAMIENTAS
    ] + [HERRAMIENTA_DELEGAR]
    assert opciones.tools == [HERRAMIENTA_DELEGAR]
    assert opciones.disallowed_tools == []


def test_unico_subagente_es_el_analista_de_transacciones():
    opciones = crear_opciones(ENTORNO)
    assert list(opciones.agents) == [NOMBRE]
    assert opciones.agents[NOMBRE] == definir_analista(Repositorio().politica)


def test_sin_datos_del_core_no_hay_subagente_ni_delegacion():
    opciones = crear_opciones(ENTORNO, controles=Controles(lambda _: None, None))
    assert not opciones.agents
    assert opciones.tools == []
    assert HERRAMIENTA_DELEGAR not in opciones.allowed_tools


def _antes_de_productos(opciones):
    (antes,) = [
        m for m in opciones.hooks["PreToolUse"] if m.matcher == "|".join(PRODUCTOS)
    ]
    return antes


def test_hooks_por_nombre_completo_de_cada_herramienta():
    hooks = crear_opciones(ENTORNO).hooks
    assert set(hooks) == {"PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit"}
    assert [m.matcher for m in hooks["PreToolUse"]] == [
        "|".join(PRODUCTOS),
        "Agent|Task",
    ]
    assert [m.matcher for m in hooks["PostToolUse"]] == [
        VERIFICAR,
        "mcp__core-bancario__iniciar_disputa",
        "mcp__core-bancario__escalar_a_analista",
    ]


def test_stop_y_mensaje_nuevo_aplican_a_todo_el_turno():
    hooks = crear_opciones(ENTORNO).hooks
    for evento in ("Stop", "UserPromptSubmit"):
        (matcher,) = hooks[evento]
        assert matcher.matcher is None


def test_las_exentas_no_tienen_control_previo():
    # Regla 1: buscar, verificar y escalar nunca se niegan por identidad.
    for matcher in crear_opciones(ENTORNO).hooks["PreToolUse"]:
        for exenta in ("buscar_cliente", "verificar_identidad", "escalar_a_analista"):
            assert exenta not in matcher.matcher


def test_sin_prompt_de_sistema_la_disputa_sin_verificar_se_niega():
    opciones = replace(crear_opciones(ENTORNO), system_prompt=None)
    (callback,) = _antes_de_productos(opciones).hooks
    salida = asyncio.run(callback(DISPUTA_SIN_VERIFICAR, "uso-1", {"signal": None}))
    assert salida["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_cada_conversacion_tiene_su_propio_estado():
    primera, segunda = crear_opciones(ENTORNO), crear_opciones(ENTORNO)
    (callback,) = primera.hooks["PreToolUse"][0].hooks
    asyncio.run(callback(DISPUTA_SIN_VERIFICAR, "uso-1", {"signal": None}))
    estado_primera = primera.hooks["PreToolUse"][0].hooks[0].__self__.estado
    estado_segunda = segunda.hooks["PreToolUse"][0].hooks[0].__self__.estado
    assert len(estado_primera.negaciones) == 1
    assert estado_segunda.negaciones == []


def test_acepta_controles_inyectados():
    controles = Controles.desde_entorno(ENTORNO)
    opciones = crear_opciones(ENTORNO, controles=controles)
    (callback,) = opciones.hooks["PreToolUse"][0].hooks
    asyncio.run(callback(DISPUTA_SIN_VERIFICAR, "uso-1", {"signal": None}))
    assert [n.codigo for n in controles.estado.negaciones] == ["SIN_IDENTIDAD"]


def test_max_turns_es_la_salvaguarda():
    assert crear_opciones(ENTORNO).max_turns == 25


def test_unico_servidor_es_el_core_por_stdio_con_el_mismo_python():
    servidores = crear_opciones(ENTORNO).mcp_servers
    assert list(servidores) == ["core-bancario"]
    core = servidores["core-bancario"]
    assert core["type"] == "stdio"
    assert core["command"] == sys.executable
    assert core["args"] == ["-m", "core_bancario_mcp"]


def test_fallas_se_pasan_al_core_solo_si_estan_definidas():
    sin_fallas = crear_opciones(ENTORNO).mcp_servers["core-bancario"]
    assert "CORE_BANCARIO_FALLAS" not in sin_fallas.get("env", {})
    con_fallas = crear_opciones({**ENTORNO, "CORE_BANCARIO_FALLAS": "buscar_cliente:1"})
    env = con_fallas.mcp_servers["core-bancario"]["env"]
    assert env["CORE_BANCARIO_FALLAS"] == "buscar_cliente:1"


def test_modelo_por_omision_y_configurable():
    assert crear_opciones(ENTORNO).model == "claude-sonnet-5-5"
    opciones = crear_opciones({**ENTORNO, "ANDINO_MODELO": "claude-opus-5-5"})
    assert opciones.model == "claude-opus-5-5"


def test_prompt_de_sistema_es_el_versionado():
    assert crear_opciones(ENTORNO).system_prompt == PROMPT_SISTEMA


def test_la_clave_no_se_copia_a_las_opciones():
    assert CLAVE_FICTICIA not in repr(crear_opciones(ENTORNO))


@pytest.mark.parametrize("entorno", [{}, {"ANTHROPIC_API_KEY": "   "}])
def test_credencial_faltante_nombra_la_variable(entorno):
    with pytest.raises(CredencialFaltanteError, match="ANTHROPIC_API_KEY"):
        validar_credencial(entorno)


def test_credencial_presente_no_lanza():
    validar_credencial(ENTORNO)


def test_mensaje_de_error_nunca_incluye_un_valor():
    with pytest.raises(CredencialFaltanteError) as error:
        validar_credencial({"ANTHROPIC_API_KEY": "   ", "OTRA": CLAVE_FICTICIA})
    assert CLAVE_FICTICIA not in str(error.value)
