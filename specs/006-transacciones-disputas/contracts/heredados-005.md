# Contrato: ajustes heredados del #5

Fundamento en [research.md R6](../research.md). Son los no bloqueantes de `revisor-codigo` en
el PR #19.

| Ajuste | Archivo | Comportamiento esperado | Test |
|---|---|---|---|
| (a) Posición calculada | `src/core_bancario_mcp/test_repositorio.py` | el caso "registro que no es objeto" usa `len(d)` como posición esperada | el test sigue pasando si se agregan tarjetas a los datos |
| (b) Espacios en verificación | `src/core_bancario_mcp/identificacion.py` | `verificar_identidad` recorta los extremos de `cliente_id` y `dato_verificacion`; la comparación sigue exacta | `" CLI-001 "` con `" 1987 "` (dato leído del repositorio) verifica; un dato distinto tras recortar sigue fallando |
| (c) Tipo incorrecto por protocolo | `src/core_bancario_mcp/test_servidor.py` | `call_tool("verificar_identidad", ...)` con `dato_verificacion` numérico | responde `PARAMETRO_INVALIDO` con el contrato |
| (d) Estado de la spec | `specs/005-identificacion-clientes/spec.md` | `**Status**: Approved` | — |

Además, la nota de (b) se agrega a `specs/005-identificacion-clientes/research.md` R6 para que
el cambio quede trazado.
