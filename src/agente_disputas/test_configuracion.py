import asyncio
import sys
from dataclasses import replace

import pytest

from agente_disputas.configuracion import (
    HERRAMIENTAS,
    CredencialFaltanteError,
    crear_opciones,
    validar_credencial,
)
from agente_disputas.controles import Controles
from agente_disputas.prompts import PROMPT_SISTEMA

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


def test_sin_herramientas_ni_settings_del_entorno_ni_permisos_interactivos():
    opciones = crear_opciones(ENTORNO)
    assert opciones.tools == []
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


def test_con_los_hooks_del_issue_9_se_habilitan_las_seis():
    opciones = crear_opciones(ENTORNO)
    assert opciones.allowed_tools == [
        f"mcp__core-bancario__{nombre}" for nombre in HERRAMIENTAS
    ]
    assert opciones.disallowed_tools == []


def test_hooks_por_nombre_completo_de_cada_herramienta():
    hooks = crear_opciones(ENTORNO).hooks
    (antes,) = hooks["PreToolUse"]
    (despues,) = hooks["PostToolUse"]
    assert antes.matcher == "|".join(PRODUCTOS)
    assert despues.matcher == VERIFICAR
    assert set(hooks) == {"PreToolUse", "PostToolUse"}


def test_las_exentas_no_tienen_hooks():
    hooks = crear_opciones(ENTORNO).hooks
    matchers = " ".join(m.matcher for lista in hooks.values() for m in lista)
    assert "buscar_cliente" not in matchers
    assert "escalar_a_analista" not in matchers


def test_sin_prompt_de_sistema_la_disputa_sin_verificar_se_niega():
    opciones = replace(crear_opciones(ENTORNO), system_prompt=None)
    (antes,) = opciones.hooks["PreToolUse"]
    (callback,) = antes.hooks
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
