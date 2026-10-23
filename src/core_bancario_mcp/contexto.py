"""Estado que comparten las herramientas del core, pasado de forma explícita.

``crear_servidor`` arma un ``Contexto`` (repositorio, fallas, intentos, disputas, bloqueos y
escalamientos) y se lo entrega a ``registrar(servidor, contexto)`` de cada módulo de
herramientas. Así las herramientas no dependen de atributos agregados al vuelo a ``FastMCP``
y los tests las prueban como funciones puras. Todo el estado mutable vive en memoria del
proceso: al reiniciar el core se vuelve a los datos iniciales.
"""

from dataclasses import dataclass, field

from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Repositorio, Tarjeta, Transaccion


class IntentosVerificacion:
    """Fallos consecutivos de verificación por cliente, en memoria del proceso.

    Protege al cliente, no a una conversación: tras ``MAXIMO`` fallos su verificación queda
    bloqueada mientras el core siga en marcha. Un éxito antes del límite reinicia la cuenta.
    """

    MAXIMO = 3

    def __init__(self):
        self._fallos: dict[str, int] = {}

    def agotados(self, cliente_id: str) -> bool:
        return self._fallos.get(cliente_id, 0) >= self.MAXIMO

    def registrar_fallo(self, cliente_id: str) -> None:
        self._fallos[cliente_id] = self._fallos.get(cliente_id, 0) + 1

    def reiniciar(self, cliente_id: str) -> None:
        self._fallos.pop(cliente_id, None)


@dataclass(frozen=True)
class Caso:
    id: str
    transaccion_id: str
    monto: int
    motivo: str
    estado: str


class RegistroDisputas:
    """Casos de disputa abiertos, en memoria del proceso: como máximo uno por transacción."""

    def __init__(self):
        self._casos: dict[str, Caso] = {}
        self._ultimo = 0

    def caso_de(self, transaccion_id: str) -> Caso | None:
        return self._casos.get(transaccion_id)

    def abrir(self, transaccion: Transaccion, motivo: str) -> Caso:
        """Abre el siguiente ``CASO-NNNN`` con el monto del core, nunca uno recibido."""
        if transaccion.id in self._casos:
            raise ValueError(f"{transaccion.id} ya tiene un caso de disputa")
        self._ultimo += 1
        caso = Caso(
            id=f"CASO-{self._ultimo:04d}",
            transaccion_id=transaccion.id,
            monto=transaccion.monto,
            motivo=motivo,
            estado="abierta",
        )
        self._casos[transaccion.id] = caso
        return caso


class RegistroBloqueos:
    """Bloqueos hechos en la sesión; el estado inicial de la tarjeta sigue en los datos."""

    def __init__(self):
        self._motivos: dict[str, str] = {}

    def estado_de(self, tarjeta: Tarjeta) -> str:
        if tarjeta.estado == "bloqueada" or tarjeta.id in self._motivos:
            return "bloqueada"
        return "activa"

    def bloquear(self, tarjeta: Tarjeta, motivo: str) -> bool:
        """Bloquea de inmediato (regla 3) y dice si ya estaba bloqueada. Nunca desbloquea."""
        ya_estaba = self.estado_de(tarjeta) == "bloqueada"
        self._motivos.setdefault(tarjeta.id, motivo)
        return ya_estaba


@dataclass(frozen=True)
class DetalleTransaccion:
    transaccion_id: str
    fecha: str
    monto: int
    comercio: str
    caso_disputa: str | None


@dataclass(frozen=True)
class Escalamiento:
    """Resumen para el analista; al agente solo se le devuelve id, causa, estado y conteo."""

    id: str
    causa: str
    cliente_id: str | None
    cliente_nombre: str | None
    transacciones: tuple[DetalleTransaccion, ...]
    total: int
    acciones_realizadas: str
    accion_recomendada: str
    estado: str


class RegistroEscalamientos:
    """Escalamientos pendientes de analista, con numeración propia ``ESC-NNNN``."""

    def __init__(self):
        self._escalamientos: list[Escalamiento] = []
        self._ultimo = 0

    def registrar(
        self,
        causa: str,
        cliente_id: str | None,
        cliente_nombre: str | None,
        transacciones: tuple[DetalleTransaccion, ...],
        acciones_realizadas: str,
        accion_recomendada: str,
    ) -> Escalamiento:
        self._ultimo += 1
        escalamiento = Escalamiento(
            id=f"ESC-{self._ultimo:04d}",
            causa=causa,
            cliente_id=cliente_id,
            cliente_nombre=cliente_nombre,
            transacciones=transacciones,
            total=sum(t.monto for t in transacciones),
            acciones_realizadas=acciones_realizadas,
            accion_recomendada=accion_recomendada,
            estado="pendiente_analista",
        )
        self._escalamientos.append(escalamiento)
        return escalamiento

    def todos(self) -> list[Escalamiento]:
        """Para los tests y la vista del analista (el agente no lee esta memoria)."""
        return list(self._escalamientos)


@dataclass
class Contexto:
    repositorio: Repositorio
    inyector: InyectorFallas
    intentos: IntentosVerificacion = field(default_factory=IntentosVerificacion)
    disputas: RegistroDisputas = field(default_factory=RegistroDisputas)
    bloqueos: RegistroBloqueos = field(default_factory=RegistroBloqueos)
    escalamientos: RegistroEscalamientos = field(default_factory=RegistroEscalamientos)
