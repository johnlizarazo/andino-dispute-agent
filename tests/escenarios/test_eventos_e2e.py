"""Escenarios de los eventos de la interfaz: conversaciones reales por ``SesionChat`` (#12).

Llaman al modelo real (requieren ANTHROPIC_API_KEY). Los mensajes son distintos de los
ejemplos del prompt de sistema (principio VI). Los datos de verificación ficticios se leen de
los datos del core en tiempo de ejecución. Cada caso usa una sesión nueva.
"""

import asyncio
import os

import pytest

from agente_disputas.eventos import EXITO, NEGADO, Evento
from agente_disputas.sesion import SesionChat
from core_bancario_mcp.repositorio import Repositorio

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        reason="requiere ANTHROPIC_API_KEY",
    ),
]


def _dato(cliente_id: str) -> str:
    return Repositorio().clientes[cliente_id].dato_verificacion


def _registrar_en(eventos: list[Evento]):
    async def registrar(evento: Evento) -> None:
        eventos.append(evento)

    return registrar


def _conversar(*mensajes: str) -> list[list[Evento]]:
    """Eventos de cada turno, en orden, de una conversación nueva."""

    async def conversar() -> list[list[Evento]]:
        sesion = SesionChat(dict(os.environ))
        assert await sesion.iniciar() is None
        turnos = []
        try:
            for mensaje in mensajes:
                eventos: list[Evento] = []
                respuesta = await sesion.turno(mensaje, _registrar_en(eventos))
                assert respuesta.strip()
                turnos.append(eventos)
        finally:
            await sesion.cerrar()
        return turnos

    return asyncio.run(conversar())


def _sin_falsos_exitos(turnos: list[list[Evento]]) -> None:
    for evento in (e for turno in turnos for e in turno):
        assert evento.resultado in (EXITO, NEGADO, "falla")
        if evento.resultado == EXITO:
            assert evento.tipo != "negacion"


def test_bloqueo_muestra_identidad_y_tarjeta_bloqueada_en_orden():
    turnos = _conversar(
        "Me robaron la billetera esta mañana y adentro estaba la tarjeta que termina en "
        f"2468; necesito inhabilitarla. Mi cédula es CC-FIC-0003 y mi año es {_dato('CLI-003')}."
    )
    tipos = [(e.tipo, e.resultado) for e in turnos[-1]]
    assert ("identidad", EXITO) in tipos
    assert ("bloqueo", EXITO) in tipos
    assert tipos.index(("identidad", EXITO)) < tipos.index(("bloqueo", EXITO))
    bloqueo = next(e for e in turnos[-1] if e.tipo == "bloqueo")
    assert "2468" in bloqueo.detalle
    _sin_falsos_exitos(turnos)


def test_disputa_sobre_el_umbral_muestra_la_negacion_y_el_escalamiento():
    turnos = _conversar(
        "Revisando el extracto vi que ayer cargaron a mi tarjeta 4821 una compra de "
        "$1.250.000 en Electro Ficticio que no reconozco; quiero reclamarla. "
        f"Documento CC-FIC-0001, validación {_dato('CLI-001')}."
    )
    eventos = turnos[-1]
    negados = [
        i for i, e in enumerate(eventos) if e.tipo in ("negacion", "rechazo_politica")
    ]
    escalados = [
        i
        for i, e in enumerate(eventos)
        if (e.tipo, e.resultado) == ("escalamiento", EXITO)
    ]
    assert negados and escalados
    assert negados[0] < escalados[0]
    assert all(e.tipo != "disputa" for e in eventos)
    _sin_falsos_exitos(turnos)


def test_disputa_dentro_del_umbral_muestra_la_disputa_iniciada():
    turnos = _conversar(
        "Buenas. Ayer apareció en mi tarjeta 4821 un pago de $180.000 en Tienda Ficticia "
        "Uno que nunca autoricé y quiero objetarlo. Soy CC-FIC-0001 y mi dato es "
        f"{_dato('CLI-001')}."
    )
    disputas = [e for e in turnos[-1] if (e.tipo, e.resultado) == ("disputa", EXITO)]
    assert len(disputas) == 1
    assert "$180.000" in disputas[0].detalle
    _sin_falsos_exitos(turnos)


def test_pedir_una_persona_muestra_el_escalamiento():
    turnos = _conversar(
        "Esto no lo quiero resolver con una máquina. Pásenme por favor con alguien de "
        "carne y hueso del banco."
    )
    escalados = [
        e for e in turnos[-1] if (e.tipo, e.resultado) == ("escalamiento", EXITO)
    ]
    assert len(escalados) == 1
    assert "persona" in escalados[0].detalle
    _sin_falsos_exitos(turnos)
