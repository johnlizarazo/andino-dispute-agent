---

description: "Lista de tareas del issue #7: Bloqueo y escalamiento"
---

# Tasks: Bloqueo y escalamiento: `bloquear_tarjeta` y `escalar_a_analista`

**Input**: documentos de diseño en `specs/007-bloqueo-escalamiento/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec los pide ("tests de ambos"). En cada módulo el test se escribe **antes**
que el código, vive en la misma carpeta (rule `tests.md`) y se ve fallar antes de
implementar, salvo los de confirmación de cobertura existente, que pueden pasar desde el
inicio. Los tests usan un "hoy" fijo (`date(2026, 10, 23)`) y solo datos ficticios.

**Organization**: en el orden del plan: US4 (heredados del #6) → fundamentos (registros) →
US1 → US2 → US3, luego verificación en sesión nueva y cierre. El hook `formatear` elimina
imports sin uso entre ediciones: agregar el import en la misma edición que su uso.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: sin preparación; dependencias, datos y servidor existen desde el #4.

---

## Phase 2: User Story 4 - Ajustes heredados de la revisión del #6 (Priority: P4, primero por el plan)

**Goal**: FR-014 ([contracts/heredados-006.md](contracts/heredados-006.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_transacciones.py src/core_bancario_mcp/test_contexto.py src/core_bancario_mcp/test_repositorio.py`.

- [ ] T001 [P] [US4] (a) Agregar a `src/core_bancario_mcp/test_transacciones.py` un test parametrizado donde `fecha_desde` o `fecha_hasta` en `""` y en `"   "` devuelven lo mismo que sin fecha; verlo fallar con `"   "`. Después, en `src/core_bancario_mcp/transacciones.py`, recortar cada fecha **antes** de decidir si se omite (texto vacío tras recortar = omitida)
- [ ] T002 [P] [US4] (b) Agregar a `src/core_bancario_mcp/test_contexto.py` un test que fije el contador: tras abrir `CASO-0001` y `CASO-0002`, vaciar el diccionario interno de casos (simula casos cerrados en el futuro) y comprobar que el siguiente es `CASO-0003`; verlo fallar. Después, en `src/core_bancario_mcp/contexto.py`, numerar `RegistroDisputas` con un contador propio (`self._ultimo`) en lugar de `len(self._casos) + 1`
- [ ] T003 [US4] (c) Agregar a `src/core_bancario_mcp/test_repositorio.py` tests de `Politica.limite_dias`: 120 para una transacción `CO` y 90 para una `US`; verlos fallar. Después, en `src/core_bancario_mcp/repositorio.py`, implementar `limite_dias(transaccion)` y usarlo en `cubre`; en `src/core_bancario_mcp/transacciones.py`, construir el mensaje de `FUERA_DE_POLITICA` con `politica.limite_dias(transaccion)` (sin comparar `pais == "CO"` para el límite)
- [ ] T004 [US4] Dejar verdes todos los tests y hacer commit `fix(#7): ajustes heredados de la revisión del #6`

---

## Phase 3: Foundational - Registros de bloqueos y escalamientos

**Purpose**: bloquea a US1 y US2 ([contracts/registros-y-servidor.md](contracts/registros-y-servidor.md)).

- [ ] T005 Agregar a `src/core_bancario_mcp/test_contexto.py`, **antes** de tocar el módulo, y verlos fallar:
  - `RegistroBloqueos().estado_de(...)`: TAR-004 → `"bloqueada"` (dato inicial), TAR-001 → `"activa"`.
  - `bloquear(TAR-001, motivo)` devuelve `False` y después `estado_de` es `"bloqueada"`; un segundo `bloquear` devuelve `True`; `bloquear(TAR-004, ...)` devuelve `True`.
  - `RegistroEscalamientos().registrar(...)` con dos `DetalleTransaccion` asigna `ESC-0001` y luego `ESC-0002`, calcula `total` como la suma de montos, deja `estado` `"pendiente_analista"`, y `todos()` los devuelve en orden.
  - Cada `Contexto` tiene sus propios `bloqueos` y `escalamientos`.
- [ ] T006 Implementar en `src/core_bancario_mcp/contexto.py`: `RegistroBloqueos` (`estado_de`, `bloquear`; nunca desbloquea), las dataclasses inmutables `DetalleTransaccion` (`transaccion_id`, `fecha`, `monto`, `comercio`, `caso_disputa`) y `Escalamiento` (`id`, `causa`, `cliente_id`, `cliente_nombre`, `transacciones` como tupla de `DetalleTransaccion`, `total`, `acciones_realizadas`, `accion_recomendada`, `estado`) según [data-model.md](data-model.md), `RegistroEscalamientos` (`registrar`, `todos`, contador propio) y los campos `bloqueos` y `escalamientos` del `Contexto` con `default_factory`. Actualizar el docstring del módulo. Dejar verdes los tests y hacer commit `feat(#7): registros de bloqueos y escalamientos en el contexto`

---

## Phase 4: User Story 1 - Bloquear la tarjeta de inmediato (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-004 ([contracts/bloquear_tarjeta.md](contracts/bloquear_tarjeta.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_bloqueo_escalamiento.py -k bloquear`.

- [ ] T007 [US1] Escribir `src/core_bancario_mcp/test_bloqueo_escalamiento.py` (nuevo), **antes** que el módulo, con una fixture `contexto` y los tests de bloqueo del contrato; verlos fallar:
  - CLI-001 `4821` → `{"ultimos4": "4821", "estado": "bloqueada", "ya_estaba_bloqueada": False}` y `contexto.bloqueos.estado_de` de TAR-001 es `"bloqueada"`.
  - Repetir → éxito con `ya_estaba_bloqueada` `True`; CLI-004 `9012` → éxito con `ya_estaba_bloqueada` `True`.
  - CLI-002 `4821` y CLI-999 `4821` → `NO_ENCONTRADO` con el mismo mensaje.
  - `PARAMETRO_INVALIDO` sin bloquear nada: motivo vacío, de solo espacios, de 501 caracteres ("hasta 500 caracteres") o numérico; `ultimos4` `48a1`; `cliente_id` ausente.
  - Tras bloquear la 4821, `consultar_transacciones` y `iniciar_disputa` sobre sus cobros siguen funcionando.
- [ ] T008 [US1] Implementar `bloquear_tarjeta(contexto, cliente_id=None, ultimos4=None, motivo=None)` en `src/core_bancario_mcp/bloqueo_escalamiento.py` (nuevo) según [research.md R2](research.md): textos recortados, `ultimos4` con `PATRON_CUATRO_DIGITOS`, motivo hasta 500, `tarjetas_de` vacío → `NO_ENCONTRADO` con el mensaje de `consultar_transacciones`, bloquear todas las tarjetas devueltas y `ya_estaba_bloqueada` verdadero solo si todas lo estaban. Errores solo con `errores.error()`. Dejar verdes los tests y hacer commit `feat(#7): bloquear_tarjeta`

---

## Phase 5: User Story 2 - Escalar con un resumen que el analista pueda usar (Priority: P2)

**Goal**: FR-005 a FR-011 ([contracts/escalar_a_analista.md](contracts/escalar_a_analista.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_bloqueo_escalamiento.py -k escalar`.

- [ ] T009 [US2] Agregar a `src/core_bancario_mcp/test_bloqueo_escalamiento.py`, **antes** de implementar, los tests del contrato y verlos fallar:
  - `umbral`, CLI-001, `["TRX-002"]` → respuesta exactamente `{"escalamiento_id": "ESC-0001", "causa": "umbral", "estado": "pendiente_analista", "cantidad_transacciones": 1}` (ajuste C1: sin montos, fechas, comercios ni nombre); el registro (`contexto.escalamientos.todos()[0]`) tiene `cliente_nombre` del repositorio, un `DetalleTransaccion` con `monto` 1250000 y `caso_disputa` `None`, y `total` 1250000; un segundo → `ESC-0002`.
  - Ninguna respuesta de éxito contiene claves distintas de esas cuatro.
  - `persona_solicitada` solo con acciones y recomendación → éxito con `cantidad_transacciones` 0; el registro tiene `cliente_id` y `cliente_nombre` `None`.
  - `intentos_agotados` con CLI-004 y sin transacciones → éxito; sin cliente → `PARAMETRO_INVALIDO`.
  - Faltan `causa` y `accion_recomendada` → un solo `PARAMETRO_INVALIDO` cuyo mensaje nombra ambos.
  - Causa `urgente` → `PARAMETRO_INVALIDO` cuyo mensaje lista las 5 causas.
  - `umbral` y `fuera_de_politica` sin transacciones → `PARAMETRO_INVALIDO`.
  - `TRX-999` → `NO_ENCONTRADO`; `TRX-004` con CLI-001 → `PARAMETRO_INVALIDO`; CLI-999 → `NO_ENCONTRADO`.
  - `["TRX-002", "TRX-002"]` → `cantidad_transacciones` 1 y `total` 1250000 en el registro.
  - Transacción con disputa abierta (`contexto.disputas.abrir(...)`) → el registro guarda su `caso_disputa`.
  - `transacciones` como `'["TRX-002"]'` → aceptado; como `"TRX-002"`, `5`, `{"a": 1}` o `[1]` → `PARAMETRO_INVALIDO`.
  - Acciones de 1001 caracteres ("hasta 1000 caracteres") o recomendación de 501 ("hasta 500 caracteres") → `PARAMETRO_INVALIDO`.
  - Tras cada error, `contexto.escalamientos.todos()` sigue vacío.
- [ ] T010 [US2] Implementar `escalar_a_analista(contexto, causa=None, cliente_id=None, transacciones=None, acciones_realizadas=None, accion_recomendada=None)` en `src/core_bancario_mcp/bloqueo_escalamiento.py` con el orden de [research.md R4](research.md): registra el `Escalamiento` completo y responde al agente solo las cuatro claves de R5 (ajuste C1); causas válidas exactamente "`persona_solicitada`, `umbral`, `fuera_de_politica`, `intentos_agotados`, `otra`"; lista según R3 (lista de textos o texto con una lista JSON de textos; ids recortados y sin repetir, en orden). Dejar verdes los tests y hacer commit `feat(#7): escalar_a_analista con resumen estructurado`

---

## Phase 6: User Story 3 - Descripciones y robustez (Priority: P3)

**Goal**: FR-012 y FR-013.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_servidor.py src/core_bancario_mcp/test_bloqueo_escalamiento.py`.

- [ ] T011 [US3] Actualizar `src/core_bancario_mcp/test_servidor.py` **antes** de registrar y verlo fallar:
  - `HERRAMIENTAS` pasa a las 6 (`bloquear_tarjeta`, `buscar_cliente`, `consultar_transacciones`, `escalar_a_analista`, `iniciar_disputa`, `verificar_identidad`) en `list_tools` y en el arranque por stdio.
  - `test_parametros_se_publican_como_texto` admite que `transacciones` de `escalar_a_analista` se publique como `{"type": "array", "items": {"type": "string"}}` y exige `string` en todo lo demás.
  - La descripción de `bloquear_tarjeta` menciona "inmediato", "no requiere" aprobación de un analista e "identidad verificada"; la de `escalar_a_analista` menciona que no requiere identidad verificada, `persona_solicitada`, que el core completa los montos y las 5 causas.
  - `call_tool("bloquear_tarjeta", {"cliente_id": "CLI-001", "ultimos4": 4821, "motivo": "x"})` y `call_tool("escalar_a_analista", {"causa": "otra", "cliente_id": "CLI-001", "transacciones": 5, "acciones_realizadas": "x", "accion_recomendada": "y"})` responden `PARAMETRO_INVALIDO` con el contrato.
- [ ] T012 [US3] Agregar a `src/core_bancario_mcp/test_bloqueo_escalamiento.py` tests de fallas a través de `registrar` sobre un `FastMCP` de prueba: con `bloquear_tarjeta:1` la primera llamada es transitoria reintentable y la tarjeta sigue `"activa"`, y la segunda bloquea; con `escalar_a_analista:1` la falla no registra nada y el reintento sí
- [ ] T013 [US3] Agregar `ListaTexto = Annotated[object, WithJsonSchema({"type": "array", "items": {"type": "string"}})]` junto a `Texto` en `src/core_bancario_mcp/identificacion.py`; implementar `registrar(servidor, contexto)` en `src/core_bancario_mcp/bloqueo_escalamiento.py` con las descripciones de los contratos, `con_fallas` por nombre y parámetros `Texto`/`ListaTexto` con `None` por omisión; en `src/core_bancario_mcp/servidor.py`, llamar también a `bloqueo_escalamiento.registrar` sobre el mismo `Contexto` y actualizar el docstring. Dejar verdes los tests y hacer commit `feat(#7): herramientas de bloqueo y escalamiento registradas en core-bancario`
- [ ] T014 [P] [US3] En `.claude/rules/herramientas-mcp.md`, agregar que los parámetros de lista se declaran con `ListaTexto` (esquema `array` de `string`, validación en la herramienta, que acepta también una lista JSON en texto). Commit `docs(#7): ListaTexto en la rule de MCP`

---

## Phase 7: Verificación en sesión nueva

**Purpose**: Claude Code carga las herramientas de `core-bancario` al iniciar. **Requiere
reiniciar la app.**

- [ ] T015 Ejecutar `uv run pytest` completo y `uv run --no-sync ruff check src` en verde ([quickstart.md §1](quickstart.md))
- [ ] T016 En una sesión nueva, ejecutar la tabla de [quickstart.md §2](quickstart.md) (8 pasos) con las herramientas de `core-bancario`, anotando cómo envía Claude Code la lista de transacciones
- [ ] T017 Pasar `bloquear_pii.py --diff` sobre un archivo con `git diff --unified=0 main...HEAD` sin hallazgos ([quickstart.md §3](quickstart.md))

---

## Phase 8: Cierre con `/abrir-pr`

- [ ] T018 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T019 Marcar T001 a T019 en `specs/007-bloqueo-escalamiento/tasks.md` y hacer commit. T020 y T021 ocurren después del último commit y se marcan en la rama del issue siguiente
- [ ] T020 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #7`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T021 Después del merge, hecho por el desarrollador: verificar que el #7 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **US4 (T001–T004)**: primero. T001, T002 y T003 tocan archivos distintos (T001 y T003
  comparten `transacciones.py`: hacer T003 después de T001 si se trabaja en serie).
- **Fundamentos (T005–T006)**: después de US4 (T002 y T005 tocan `test_contexto.py` y
  `contexto.py`).
- **US1 (T007–T008)**: después de T006.
- **US2 (T009–T010)**: después de US1 (mismo módulo y mismo archivo de tests).
- **US3 (T011–T013)**: después de US2; T014 en cualquier momento.
- **Verificación (T015–T017)**: requiere reiniciar la sesión con todo lo anterior hecho.
- **Cierre (T018–T021)**: requiere la verificación en verde.

### Parallel Opportunities

- T002 y T003 (archivos distintos), y T001 con T002.
- T014 en paralelo con cualquier fase.

## Parallel Example: User Story 4

```text
Task: "T001 Fechas vacías en src/core_bancario_mcp/transacciones.py"
Task: "T002 Contador de casos en src/core_bancario_mcp/contexto.py"
```

## Implementation Strategy

### MVP

Fundamentos + US1: con el registro de bloqueos y `bloquear_tarjeta` se cubre la regla 3.

### Incremental Delivery

Un commit por paso con el test escrito antes. Las herramientas se publican en el servidor
solo en US3; la verificación ocurre en una sesión nueva y el cierre con `/abrir-pr`, que
incluye las dos revisiones.
