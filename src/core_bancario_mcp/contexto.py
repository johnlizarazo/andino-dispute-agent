"""Estado que comparten las herramientas del core, pasado de forma explícita.

``crear_servidor`` arma un ``Contexto`` y se lo entrega a ``registrar(servidor, contexto)``
de cada módulo de herramientas. Así las herramientas no dependen de atributos agregados al
vuelo a ``FastMCP`` y los tests las prueban como funciones puras.
"""

from dataclasses import dataclass, field

from core_bancario_mcp.fallas import InyectorFallas
from core_bancario_mcp.repositorio import Repositorio


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


@dataclass
class Contexto:
    repositorio: Repositorio
    inyector: InyectorFallas
    intentos: IntentosVerificacion = field(default_factory=IntentosVerificacion)
