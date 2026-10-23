# Contrato: ajustes heredados del #6

Fundamento en [research.md R6](../research.md). Son los no bloqueantes 1 a 3 de
`revisor-codigo` en el PR #20.

| Ajuste | Archivo | Comportamiento esperado | Test |
|---|---|---|---|
| (a) Fechas vacías | `src/core_bancario_mcp/transacciones.py` | `""` y `"   "` en `fecha_desde` o `fecha_hasta` se tratan como omitidas | ambas devuelven lo mismo que sin fecha |
| (b) Contador de casos | `src/core_bancario_mcp/contexto.py` | `RegistroDisputas` numera con un contador propio | ids secuenciales sin depender de `len` (test existente sigue verde; nuevo test de que el contador no se basa en la cantidad de casos guardados) |
| (c) Límite único | `src/core_bancario_mcp/repositorio.py`, `transacciones.py` | `Politica.limite_dias(transaccion)`: 120 si `CO`, 90 si no; `cubre` y el mensaje de `FUERA_DE_POLITICA` lo usan | `limite_dias` para `CO` y `US`; `transacciones.py` deja de comparar `pais == "CO"` |
