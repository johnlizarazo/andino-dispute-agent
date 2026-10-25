"""Los seis casos de prueba obligatorios: esta suite es su única dueña (#13).

Cada test conversa con el agente real (requiere ANTHROPIC_API_KEY) y comprueba el registro de
operaciones del turno, no la redacción de la respuesta (contrato en
``specs/013-suite-casos-obligatorios/contracts/casos.md``). Los mensajes vienen de
``casos.py`` y no aparecen en el prompt de sistema (``test_mensajes.py``).
"""

import os

import pytest
from casos import mensaje
from registro import Registro, conversar

from agente_disputas.configuracion import VARIABLE_FALLAS
from core_bancario_mcp.bloqueo_escalamiento import lista_de_ids
from core_bancario_mcp.errores import Codigo

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        reason="requiere ANTHROPIC_API_KEY",
    ),
]

SOBRE_PRODUCTOS = ("consultar_transacciones", "iniciar_disputa", "bloquear_tarjeta")
CODIGOS_DEL_CORE = [v for k, v in vars(Codigo).items() if k.isupper()]


def _transaccion(llamada) -> str | None:
    valor = llamada.argumentos.get("transaccion_id")
    return valor.strip() if isinstance(valor, str) else None


def _disputas_abiertas(registro: Registro, transaccion_id: str) -> list:
    return [
        ll
        for ll in registro.de("iniciar_disputa")
        if ll.ok and _transaccion(ll) == transaccion_id
    ]


def _escala_con(registro: Registro, causa: str, transaccion_id: str) -> bool:
    return any(
        transaccion_id in (lista_de_ids(ll.argumentos.get("transacciones")) or [])
        for ll in registro.escalamientos(causa)
    )


def _completado(registro: Registro) -> None:
    assert registro.estado == "completado", registro.resumen()


def test_caso_1_mensaje_de_ejemplo():
    registro = conversar(mensaje("mensaje_de_ejemplo"))
    detalle = registro.resumen()
    _completado(registro)
    assert any(
        ll.ok and ll.argumentos.get("cliente_id", "").strip() == "CLI-001"
        for ll in registro.de("verificar_identidad")
    ), detalle
    assert _disputas_abiertas(registro, "TRX-001"), detalle
    assert any(
        ll.ok and ll.argumentos.get("ultimos4", "").strip() == "4821"
        for ll in registro.de("bloquear_tarjeta")
    ), detalle
    # El cobro sobre el umbral nunca se abre: se niega o no se intenta (research R3).
    assert _disputas_abiertas(registro, "TRX-002") == [], detalle
    assert _escala_con(registro, "umbral", "TRX-002"), detalle
    assert registro.pendientes == {}, detalle


def test_caso_2_persona():
    registro = conversar(mensaje("persona"))
    primera = registro.primera()
    _completado(registro)
    assert primera is not None, registro.resumen()
    assert primera.herramienta == "escalar_a_analista", registro.resumen()
    assert primera.ok, registro.resumen()
    assert primera.argumentos.get("causa") == "persona_solicitada", registro.resumen()


def test_caso_3_homonimos():
    registro = conversar(mensaje("homonimos"))
    detalle = registro.resumen()
    _completado(registro)
    assert registro.de("buscar_cliente"), detalle
    assert registro.de("verificar_identidad") == [], detalle
    for herramienta in SOBRE_PRODUCTOS:
        assert not any(ll.ok for ll in registro.de(herramienta)), detalle
    for ll in registro.llamadas:
        if ll.herramienta in SOBRE_PRODUCTOS:
            assert ll.argumentos.get("cliente_id") not in ("CLI-002", "CLI-003"), (
                detalle
            )


def test_caso_4_sin_identidad():
    registro = conversar(mensaje("sin_identidad"))
    detalle = registro.resumen()
    _completado(registro)
    disputas = registro.de("iniciar_disputa")
    assert not any(ll.ok for ll in disputas), detalle
    assert all(ll.negada == "SIN_IDENTIDAD" for ll in disputas), detalle


def test_caso_5_falla_transitoria():
    pasajera = conversar(
        mensaje("falla_transitoria"),
        {**os.environ, VARIABLE_FALLAS: "buscar_cliente:1"},
    )
    busquedas = pasajera.de("buscar_cliente")
    _completado(pasajera)
    assert len(busquedas) >= 2, pasajera.resumen()
    assert busquedas[-1].ok, pasajera.resumen()

    persistente = conversar(
        mensaje("falla_transitoria"),
        {**os.environ, VARIABLE_FALLAS: "buscar_cliente:5"},
    )
    busquedas = persistente.de("buscar_cliente")
    _completado(persistente)
    assert 1 <= len(busquedas) <= 3, persistente.resumen()
    assert not any(ll.ok for ll in busquedas), persistente.resumen()

    # Única comprobación sobre el texto: ningún código de error del core (FR-003).
    for registro in (pasajera, persistente):
        for codigo in CODIGOS_DEL_CORE:
            assert codigo not in registro.texto, registro.texto


def test_caso_6_fuera_de_politica():
    registro = conversar(mensaje("fuera_de_politica"))
    detalle = registro.resumen()
    _completado(registro)
    disputas = [
        ll for ll in registro.de("iniciar_disputa") if _transaccion(ll) == "TRX-006"
    ]
    assert not any(ll.ok for ll in disputas), detalle
    # Se intenta a lo sumo una vez y, si se intenta, el core la rechaza por política.
    assert len(disputas) <= 1, detalle
    assert all(ll.codigo == "FUERA_DE_POLITICA" for ll in disputas), detalle
    assert _escala_con(registro, "fuera_de_politica", "TRX-006"), detalle
    assert registro.pendientes == {}, detalle
