# Contrato: prompt v4 y descripción de `escalar_a_analista`

Fundamento en [research.md R6](../research.md).

## `src/agente_disputas/prompts.py`

- `VERSION_PROMPT = "4"`; ninguna línea de más de 95 caracteres (test del #9).
- Secciones nuevas:
  - **Cuándo escalar y cuándo no**: persona a pedido → `escalar_a_analista` de inmediato con
    causa `persona_solicitada`, sin buscar, verificar ni consultar antes (sin `cliente_id` si
    no se conoce); no escalar disputas bajo el umbral ni bloqueos; no escalar solo por
    molestia; "una persona" mencionada como autora del fraude no es un pedido.
  - **Varios asuntos**: separar, resolver cada uno y responder una sola vez con el resultado de
    cada asunto (número de caso, de escalamiento o estado del bloqueo).
  - Handoff completo en los escalamientos por umbral o política: causa, cliente,
    transacciones, acciones realizadas y acción recomendada.
- **`<ejemplos>` … `</ejemplos>`** con 4 ejemplos; cada uno tiene `Cliente:` y
  `Acción esperada:` (herramientas en orden y qué se responde):
  1. Pedido de persona en el primer mensaje.
  2. Mención de una persona que no es pedido ("una persona me clonó la tarjeta").
  3. Varios asuntos con un cobro bajo y otro sobre el umbral más un bloqueo.
  4. Cobro fuera de política escalado con `fuera_de_politica`.

## `src/core_bancario_mcp/bloqueo_escalamiento.py`

- `DESCRIPCION_ESCALAR` agrega cuándo **no** usarla: solo porque el cliente esté molesto, o
  cuando el caso se puede resolver (disputa bajo el umbral, bloqueo).

## Tests deterministas

En `src/agente_disputas/test_prompts.py`:

1. `VERSION_PROMPT == "4"`.
2. Hay un bloque `<ejemplos>…</ejemplos>` con entre 3 y 5 apariciones de `Acción esperada:`.
3. Separación (principio VI): dentro de `<ejemplos>` no aparece ningún `ultimos4` de
   `core_bancario_mcp/datos/tarjetas.json`, ningún monto de `transacciones.json` (con y sin
   separador de miles), ningún id `TRX-`/`CLI-`/`CC-FIC-` de los datos, ni ningún mensaje de
   cliente de `tests/escenarios/*.py` (se extraen las cadenas de los mensajes).
4. El prompt menciona `persona_solicitada`, `fuera_de_politica` y "molest".

En `src/core_bancario_mcp/test_bloqueo_escalamiento.py` (o `test_servidor.py`): la descripción
de `escalar_a_analista` menciona la persona a pedido y "molest".
