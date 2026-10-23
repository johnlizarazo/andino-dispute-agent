"""Estado que comparten las herramientas del core, pasado de forma explícita.

``crear_servidor`` arma un ``Contexto`` (repositorio, fallas, intentos y disputas) y se lo
entrega a ``registrar(servidor, contexto)`` de cada módulo de herramientas. Así las
herramientas no dependen de atributos agregados al vuelo a ``FastMCP`` y los tests las
prueban como funciones puras.
"""

from dataclasses import dataclass, field

from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Repositorio, Transaccion


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

    def caso_de(self, transaccion_id: str) -> Caso | None:
        return self._casos.get(transaccion_id)

    def abrir(self, transaccion: Transaccion, motivo: str) -> Caso:
        """Abre el siguiente ``CASO-NNNN`` con el monto del core, nunca uno recibido."""
        if transaccion.id in self._casos:
            raise ValueError(f"{transaccion.id} ya tiene un caso de disputa")
        caso = Caso(
            id=f"CASO-{len(self._casos) + 1:04d}",
            transaccion_id=transaccion.id,
            monto=transaccion.monto,
            motivo=motivo,
            estado="abierta",
        )
        self._casos[transaccion.id] = caso
        return caso


@dataclass
class Contexto:
    repositorio: Repositorio
    inyector: InyectorFallas
    intentos: IntentosVerificacion = field(default_factory=IntentosVerificacion)
    disputas: RegistroDisputas = field(default_factory=RegistroDisputas)
