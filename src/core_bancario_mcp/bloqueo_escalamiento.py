"""Herramientas de bloqueo y escalamiento: ``bloquear_tarjeta`` y ``escalar_a_analista``.

El bloqueo es inmediato y no tiene paso de aprobación (regla 3). El escalamiento no exige
identidad verificada, así que su respuesta no expone datos de productos: el resumen completo
queda registrado para el analista. Las funciones son puras sobre un ``Contexto``.
"""

from core_bancario_mcp.contexto import Contexto
from core_bancario_mcp.errores import Codigo, TipoError, error, exito
from core_bancario_mcp.repositorio import PATRON_CUATRO_DIGITOS
from core_bancario_mcp.transacciones import tarjeta_no_encontrada

LARGO_MAXIMO_MOTIVO = 500


def _invalido(mensaje: str) -> dict:
    return error(TipoError.VALIDACION, Codigo.PARAMETRO_INVALIDO, mensaje)


def bloquear_tarjeta(
    contexto: Contexto, cliente_id=None, ultimos4=None, motivo=None
) -> dict:
    for campo, valor in (
        ("cliente_id", cliente_id),
        ("ultimos4", ultimos4),
        ("motivo", motivo),
    ):
        if not isinstance(valor, str) or not valor.strip():
            return _invalido(f"{campo} es obligatorio y debe ser texto")
    cliente_id, ultimos4, motivo = cliente_id.strip(), ultimos4.strip(), motivo.strip()
    if not PATRON_CUATRO_DIGITOS.fullmatch(ultimos4):
        return _invalido("ultimos4 debe tener exactamente 4 dígitos")
    if len(motivo) > LARGO_MAXIMO_MOTIVO:
        return _invalido(f"motivo no puede superar {LARGO_MAXIMO_MOTIVO} caracteres")

    tarjetas = contexto.repositorio.tarjetas_de(cliente_id, ultimos4)
    if not tarjetas:
        return tarjeta_no_encontrada(ultimos4)
    ya_estaban = [contexto.bloqueos.bloquear(t, motivo) for t in tarjetas]
    return exito(
        {
            "ultimos4": ultimos4,
            "estado": "bloqueada",
            "ya_estaba_bloqueada": all(ya_estaban),
        }
    )
