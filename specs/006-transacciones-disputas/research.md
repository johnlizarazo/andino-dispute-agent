# Research: Transacciones y disputas (issue #6)

Verificado en el entorno del proyecto (Python 3.14, `mcp` 1.30.0).

## R1. Módulo y estado (FR-008, FR-012)

- **Decision**: `transacciones.py` con funciones puras `consultar_transacciones(contexto, ...)`
  e `iniciar_disputa(contexto, ...)` y `registrar(servidor, contexto)`, igual que
  `identificacion.py`. Los casos viven en `RegistroDisputas`, un campo nuevo del `Contexto`
  (`disputas`, con `default_factory`), con:
  - `caso_de(transaccion_id) -> Caso | None`
  - `abrir(transaccion, motivo) -> Caso`: asigna `CASO-NNNN` secuencial (desde `CASO-0001`),
    estado `abierta`; lanza `ValueError` si ya hay caso (la herramienta lo evita antes).
- **Rationale**: misma convención que el #5 (rule de MCP); el registro es estado mutable del
  core, como los intentos, y se prueba aislado.
- **Alternatives considered**: guardar el caso en la `Transaccion` (es inmutable y la comparte
  el hook del #9 en otro proceso); persistir en disco (nada que ganar en la demo).

## R2. Fechas y rango (FR-002, FR-003, FR-009)

- **Decision**:
  - El `Repositorio` guarda `self.hoy` (hoy lo calcula y lo descarta). Todo cálculo de rango
    y antigüedad usa `contexto.repositorio.hoy`, nunca `date.today()`.
  - Formato: patrón `[0-9]{4}-[0-9]{2}-[0-9]{2}` con `fullmatch` y luego
    `date.fromisoformat`. Verificado: `fromisoformat` en 3.14 acepta también `20261023` y
    `2026-W43-5`, que no deben pasar; `2026-02-30` lo rechaza (fecha imposible → validación).
  - Omisión: `fecha_hasta = hoy`; `fecha_desde = fecha_hasta − 29 días` (30 días
    contando ambos extremos; ajuste A1 del análisis). Se completan por
    separado (se puede dar solo una).
  - Validación: desde ≤ hasta; hasta ≤ hoy; `(hasta − desde).days ≤ 365`.
  - Antigüedad del cobro: `(hoy − fecha).days`.
- **Rationale**: el "hoy" inyectable del #4 hace deterministas los tests y el mensaje de
  ejemplo ("ayer") en cualquier fecha.

## R3. Orden de evaluación de `iniciar_disputa` y códigos (FR-007 a FR-011)

- **Decision**, en este orden:
  1. Falla transitoria inyectada (antes de todo; no abre caso).
  2. Parámetros: `transaccion_id` y `motivo` textos no vacíos (tras recortar); motivo hasta
     500 caracteres → validación `PARAMETRO_INVALIDO`.
  3. Transacción inexistente → validación `NO_ENCONTRADO`.
  4. Caso existente → negocio `DISPUTA_EXISTENTE`, con el `caso_id` en el mensaje.
  5. Fuera de política → negocio `FUERA_DE_POLITICA` (mensaje con antigüedad y límite, e
     indicación de escalar).
  6. Sobre el umbral → negocio `REQUIERE_ANALISTA` (mensaje con el umbral e indicación de
     escalar).
  7. Abre el caso → `exito({caso_id, transaccion_id, monto, estado})`.
- **Rationale**: el caso existente va antes que política y umbral porque es la respuesta más
  útil (ya hay una referencia que dar). La política va antes que el umbral porque decide si
  el caso es disputable (FR-011).
- Códigos nuevos en `errores.Codigo`: `FUERA_DE_POLITICA`, `REQUIERE_ANALISTA`,
  `DISPUTA_EXISTENTE`.

## R4. Tarjeta del cliente sin revelar terceros (FR-001, FR-005)

- **Decision**: `Repositorio.tarjetas_de(cliente_id, ultimos4) -> list[Tarjeta]` devuelve las
  tarjetas de ese cliente con esos últimos 4. `consultar_transacciones` lista los cobros de
  todas ellas (normalmente una). Lista vacía → validación `NO_ENCONTRADO` con un mensaje
  único ("No hay una tarjeta terminada en NNNN para ese cliente"), tanto si el cliente no
  existe como si la tarjeta es de otro.
- **Rationale**: un mismo mensaje para ambos casos no permite sondear tarjetas ajenas. Los
  cobros no incluyen datos del cliente ni de la tarjeta (spec, Key Entities).
- Formato de `ultimos4`: el mismo patrón `[0-9]{4}` del repositorio.

## R5. Reutilización por el hook del #9 (regla 2)

- **Decision**: métodos de la dataclass `Politica`:
  - `requiere_analista(monto: int) -> bool`: `monto > umbral_disputa_automatica`.
  - `cubre(transaccion: Transaccion, hoy: date) -> bool`: antigüedad ≤ 90 si `pais != "CO"`,
    ≤ 120 si `pais == "CO"`.
- El hook del #9 hará `Repositorio().obtener_transaccion(id)` y
  `repositorio.politica.requiere_analista(transaccion.monto)`, sin pasar por el servidor ni
  por el monto del modelo.
- **Rationale**: una sola definición del umbral (inclusivo) para el core y el hook; cambiar
  `politicas.json` cambia ambos.
- **Alternatives considered**: duplicar la comparación en el hook (riesgo de divergencia, p.
  ej. `<` frente a `<=`, que ya se señaló como pendiente del #9).

## R6. Ajustes heredados del #5 (US5)

- **(a)** `test_repositorio.py`: el caso "registro que no es objeto" calcula la posición con
  `len(d)` antes del `append` (la pista pasa a construirse en el test).
- **(b)** `verificar_identidad` recorta espacios en los extremos de `cliente_id` y
  `dato_verificacion` antes de buscar y comparar; la comparación sigue exacta tras recortar.
  Se actualiza `research.md` R6 del #5 con una nota.
- **(c)** `test_servidor.py`: `call_tool("verificar_identidad", {"cliente_id": "CLI-001",
  "dato_verificacion": 1987})` responde `PARAMETRO_INVALIDO` con el contrato.
- **(d)** `specs/005-identificacion-clientes/spec.md`: `Status: Approved`.
