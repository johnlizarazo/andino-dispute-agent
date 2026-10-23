# Contrato: ajustes heredados del #7

Fundamento en [research.md R7](../research.md). Son los no bloqueantes de las revisiones del
PR #21.

| Ajuste | Archivo | Comportamiento esperado | Test |
|---|---|---|---|
| (a) Un solo error | `src/core_bancario_mcp/bloqueo_escalamiento.py` | transacción inexistente o de otro cliente → `NO_ENCONTRADO` con el mismo mensaje | `TRX-999` y `TRX-004` con CLI-001 dan respuestas idénticas |
| (b) Test faltante | `src/core_bancario_mcp/test_bloqueo_escalamiento.py` | `persona_solicitada` sin cliente y con `["TRX-001"]` → éxito con `cantidad_transacciones` 1 | nuevo |
| (c) Legibilidad | `src/core_bancario_mcp/bloqueo_escalamiento.py` | `CAUSAS_SIN_CLIENTE` en una línea con el comentario arriba | — |
| (d) Plan del #7 | `specs/007-bloqueo-escalamiento/plan.md` | sin mención a cambios en `errores.py` | — |
