---

description: "Lista de tareas del issue #6: Transacciones y disputas"
---

# Tasks: Transacciones y disputas: `consultar_transacciones` e `iniciar_disputa`

**Input**: documentos de diseño en `specs/006-transacciones-disputas/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec los pide ("tests por cada camino"). En cada módulo el test se escribe
**antes** que el código, vive en la misma carpeta (rule `tests.md`) y se ve fallar antes de
implementar, salvo los de confirmación de cobertura existente (T004), que pueden pasar desde
el inicio. Los tests usan un "hoy" fijo (`date(2026, 10, 23)` salvo que se indique otro) y
solo datos ficticios.

**Organization**: en el orden del plan: US5 (heredados) → fundamentos (política y registro) →
US1 → US2 → US3 → US4, luego verificación en sesión nueva y cierre. El hook `formatear`
elimina imports sin uso entre ediciones: agregar el import en la misma edición que su uso.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US5).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: sin preparación; dependencias, datos y servidor existen desde el #4 y el #5.

---

## Phase 2: User Story 5 - Ajustes heredados de la revisión del #5 (Priority: P5, primero por el plan)

**Goal**: FR-016 ([contracts/heredados-005.md](contracts/heredados-005.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_repositorio.py src/core_bancario_mcp/test_identificacion.py src/core_bancario_mcp/test_servidor.py`.

- [X] T001 [P] [US5] (a) En `src/core_bancario_mcp/test_repositorio.py`, cambiar el caso "registro que no es objeto" de `test_tipos_y_valores_incorrectos_impiden_cargar` para que la posición esperada se calcule con `len(d)` antes del `append` (p. ej. un test propio que lea `tarjetas.json` de la copia, haga `posicion = len(d)` y espere `f"posición {posicion}"`), sin el literal "posición 5"
- [X] T002 [P] [US5] (b) Agregar a `src/core_bancario_mcp/test_identificacion.py`, **antes** de cambiar el módulo, un test donde `verificar_identidad` con `cliente_id=" CLI-001 "` y el dato correcto rodeado de espacios (leído del repositorio) verifica, y otro donde un dato distinto tras recortar sigue siendo permiso `VERIFICACION_FALLIDA`; verlos fallar
- [X] T003 [US5] (b) En `src/core_bancario_mcp/identificacion.py`, recortar con `strip()` los extremos de `cliente_id` y `dato_verificacion` antes de buscar y comparar (la comparación con `hmac.compare_digest` sigue exacta tras recortar). Agregar una nota al final de R6 en `specs/005-identificacion-clientes/research.md` ("Ajuste del #6: se recortan los espacios de los extremos, como en `buscar_cliente`")
- [X] T004 [P] [US5] (c) En `src/core_bancario_mcp/test_servidor.py`, agregar un test por `call_tool("verificar_identidad", {"cliente_id": "CLI-001", "dato_verificacion": 1987})` que responda `PARAMETRO_INVALIDO` con el contrato (sin `isError`); debería pasar ya (se confirma la cobertura)
- [X] T005 [P] [US5] (d) Cambiar `**Status**: Draft` por `**Status**: Approved` en `specs/005-identificacion-clientes/spec.md`. Dejar verdes los tests y hacer commit `fix(#6): ajustes heredados de la revisión del #5`

---

## Phase 3: Foundational - Política, repositorio y registro de disputas

**Purpose**: bloquea a US1–US3 ([contracts/politica-y-registro.md](contracts/politica-y-registro.md)).

- [X] T006 [P] Agregar a `src/core_bancario_mcp/test_repositorio.py`, **antes** de tocar el módulo, y verlos fallar:
  - `Repositorio(hoy=d).hoy == d`.
  - `politica.requiere_analista(500000)` es `False` y `requiere_analista(500001)` es `True` ("`monto > umbral_disputa_automatica`").
  - `politica.cubre(...)` en los cuatro bordes con transacciones construidas en el test: exterior (`pais="US"`) con 90 días → `True` y 91 → `False`; nacional (`pais="CO"`) con 120 → `True` y 121 → `False`.
  - `tarjetas_de("CLI-001", "4821")` devuelve la tarjeta TAR-001; `tarjetas_de("CLI-002", "4821")` y `tarjetas_de("CLI-999", "4821")` devuelven `[]`.
- [X] T007 Implementar en `src/core_bancario_mcp/repositorio.py`: `self.hoy`; métodos `requiere_analista(monto)` y `cubre(transaccion, hoy)` en `Politica` (`CO` nacional con `dias_maximos_disputa_nacional`, cualquier otro país con `dias_maximos_disputa_exterior`, límites inclusivos, antigüedad `(hoy - fecha).days`); y `tarjetas_de(cliente_id, ultimos4)`. Actualizar el docstring del módulo (el hook del #9 reutiliza `Politica`). Dejar verdes los tests y hacer commit `feat(#6): reglas de política y tarjetas del cliente en el repositorio`
- [X] T008 [P] Agregar a `src/core_bancario_mcp/test_contexto.py`, **antes** de tocar el módulo, y verlos fallar: `abrir` asigna `CASO-0001` y luego `CASO-0002`; `caso_de` es `None` antes y el caso después; el caso copia `monto` de la transacción y su `estado` es `"abierta"`; abrir dos veces la misma transacción lanza `ValueError`; cada `Contexto` tiene su propio `disputas`
- [X] T009 Implementar en `src/core_bancario_mcp/contexto.py` la dataclass inmutable `Caso` (`id`, `transaccion_id`, `monto`, `motivo`, `estado`), `RegistroDisputas` (`caso_de`, `abrir`) y el campo `disputas: RegistroDisputas = field(default_factory=RegistroDisputas)` en `Contexto`. Dejar verdes los tests y hacer commit `feat(#6): registro de disputas en el contexto`

---

## Phase 4: User Story 1 - Ver los cobros de una tarjeta en un rango de fechas (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-005 ([contracts/consultar_transacciones.md](contracts/consultar_transacciones.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_transacciones.py -k consultar`.

- [X] T010 [US1] Escribir `src/core_bancario_mcp/test_transacciones.py` (nuevo), **antes** que el módulo, con una fixture `contexto` (`Repositorio(hoy=HOY)`, `InyectorFallas(None)`) y los tests de consulta del contrato; verlos fallar:
  - CLI-001, `4821`, rango ayer–ayer → TRX-001 y TRX-002, parametrizado con 3 "hoy" (fin de año, fin de febrero, fin de mes).
  - Sin rango → cobros de hoy y los 29 días anteriores ("`fecha_desde = fecha_hasta − 29 días`", ajuste A1); con datos en `tmp_path`, un cobro de hace 29 días entra y uno de hace 30 no; en orden "fecha descendente y, a igual fecha, `transaccion_id` ascendente".
  - Solo `fecha_desde` o solo `fecha_hasta` → se completa la otra.
  - Rango sin cobros → `{"ok": True, "datos": []}`.
  - Tarjeta bloqueada: CLI-004 con `9012` y un rango que incluya hace 15 días → TRX-007 (ajuste U1).
  - Validación `PARAMETRO_INVALIDO`: `20261023`, `2026-W43-5`, `2026-02-30`, desde > hasta, hasta = mañana, rango de 366 días, fecha numérica, `ultimos4` `48a1`, `cliente_id` vacío o numérico.
  - `NO_ENCONTRADO` con el **mismo mensaje** para CLI-002 con `4821` y para CLI-999 con `4821`.
  - Cada cobro tiene exactamente las claves `transaccion_id`, `fecha`, `monto`, `comercio`, `pais`, `caso_disputa`; `fecha` en `AAAA-MM-DD`; `caso_disputa` es `None` sin caso y el id del caso tras abrir uno con `contexto.disputas.abrir(...)`.
- [X] T011 [US1] Implementar `consultar_transacciones(contexto, cliente_id=None, ultimos4=None, fecha_desde=None, fecha_hasta=None)` en `src/core_bancario_mcp/transacciones.py` según [research.md R2 y R4](research.md): tipos `str` o `None`; textos recortados; fechas con "`^[0-9]{4}-[0-9]{2}-[0-9]{2}$`" (`fullmatch`) y luego `date.fromisoformat` (un `ValueError` es `PARAMETRO_INVALIDO`); "desde ≤ hasta ≤ hoy, como máximo 365 días" con `contexto.repositorio.hoy`; `tarjetas_de` vacío → `NO_ENCONTRADO` ("No hay una tarjeta terminada en NNNN para ese cliente"); errores solo con `errores.error()`. Dejar verdes los tests y hacer commit `feat(#6): consultar_transacciones`

---

## Phase 5: User Story 2 - Abrir una disputa dentro de la política y del umbral (Priority: P2)

**Goal**: FR-006 a FR-008, FR-012 y FR-013 ([contracts/iniciar_disputa.md](contracts/iniciar_disputa.md)).

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_transacciones.py -k disputa`.

- [X] T012 [US2] Agregar a `src/core_bancario_mcp/test_transacciones.py`, **antes** de implementar, y verlos fallar:
  - TRX-001 con un motivo → `{"caso_id": "CASO-0001", "transaccion_id": "TRX-001", "monto": 180000, "estado": "abierta"}`; otra disputa válida después → `CASO-0002`.
  - TRX-004 ($500.000) → se abre; TRX-007 (tarjeta bloqueada) → se abre.
  - TRX-001 dos veces → negocio `DISPUTA_EXISTENTE` no reintentable con `CASO-0001` en el mensaje.
  - `TRX-999` → validación `NO_ENCONTRADO`; motivo vacío, de solo espacios, de 501 caracteres o numérico, y `transaccion_id` ausente → validación `PARAMETRO_INVALIDO`.
- [X] T013 [US2] Agregar a `Codigo` en `src/core_bancario_mcp/errores.py` `DISPUTA_EXISTENTE`, `FUERA_DE_POLITICA` y `REQUIERE_ANALISTA`, e implementar `iniciar_disputa(contexto, transaccion_id=None, motivo=None)` en `src/core_bancario_mcp/transacciones.py` con los pasos 2 a 4 y 7 del orden de [research.md R3](research.md) (motivo "texto no vacío, hasta 500 caracteres", recortado). El monto del caso sale de `contexto.repositorio.obtener_transaccion(...)`. Dejar verdes los tests y hacer commit `feat(#6): iniciar_disputa`

---

## Phase 6: User Story 3 - Rechazar lo que la política o el umbral no permiten (Priority: P3)

**Goal**: FR-009 a FR-011.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_transacciones.py -k "politica or umbral"`.

- [X] T014 [US3] Agregar a `src/core_bancario_mcp/test_transacciones.py`, **antes** de implementar, y verlos fallar:
  - TRX-006 (exterior, 120 días) → negocio `FUERA_DE_POLITICA` no reintentable; el mensaje contiene "analista".
  - TRX-002 ($1.250.000) → negocio `REQUIERE_ANALISTA` no reintentable; el mensaje contiene "analista"; después, `consultar_transacciones` muestra TRX-002 con `caso_disputa` `None` y `contexto.disputas.caso_de("TRX-002")` es `None`.
  - Bordes con datos copiados a `tmp_path` (editando `dias_atras` y `monto` de transacciones existentes): exterior de 90 días → se abre y de 91 → `FUERA_DE_POLITICA`; nacional de 120 → se abre y de 121 → `FUERA_DE_POLITICA`.
  - Fuera de política **y** sobre el umbral a la vez (datos en `tmp_path`) → `FUERA_DE_POLITICA`.
- [X] T015 [US3] Completar `iniciar_disputa` en `src/core_bancario_mcp/transacciones.py` con los pasos 5 y 6 de [research.md R3](research.md) usando `politica.cubre(transaccion, repositorio.hoy)` y `politica.requiere_analista(transaccion.monto)`; mensajes con la antigüedad y el límite, o con el umbral, y la indicación de escalar a un analista. Dejar verdes los tests y hacer commit `feat(#6): rechazo por política y por umbral en iniciar_disputa`

---

## Phase 7: User Story 4 - Descripciones y robustez (Priority: P4)

**Goal**: FR-014 y FR-015.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_servidor.py src/core_bancario_mcp/test_transacciones.py`.

- [X] T016 [US4] Actualizar `src/core_bancario_mcp/test_servidor.py` **antes** de registrar y verlo fallar: `HERRAMIENTAS` pasa a las 4 (`buscar_cliente`, `consultar_transacciones`, `iniciar_disputa`, `verificar_identidad`) en `list_tools` y en el arranque por stdio; la descripción de `consultar_transacciones` menciona "identidad verificada" y "titular"; la de `iniciar_disputa` menciona que el monto lo toma el core, `FUERA_DE_POLITICA`, `REQUIERE_ANALISTA` y "no reintentes"; un `call_tool("iniciar_disputa", {"transaccion_id": 1, "motivo": "x"})` responde `PARAMETRO_INVALIDO` con el contrato
- [X] T017 [US4] Agregar a `src/core_bancario_mcp/test_transacciones.py` tests de fallas a través de `registrar` sobre un `FastMCP` de prueba: con `consultar_transacciones:1` la primera llamada es transitoria reintentable y la segunda responde; con `iniciar_disputa:1` la falla no abre caso (`caso_de` sigue `None`) y el reintento lo abre
- [X] T018 [US4] Implementar `registrar(servidor, contexto)` en `src/core_bancario_mcp/transacciones.py` con las descripciones de los contratos, `con_fallas` por nombre y parámetros del tipo `Texto` importado de `identificacion` con `None` por omisión; en `src/core_bancario_mcp/servidor.py`, llamar también a `transacciones.registrar` sobre el mismo `Contexto` y actualizar el docstring. Dejar verdes los tests y hacer commit `feat(#6): herramientas de transacciones registradas en core-bancario`

---

## Phase 8: Verificación en sesión nueva

**Purpose**: Claude Code carga las herramientas de `core-bancario` al iniciar. **Requiere
reiniciar la app.**

- [X] T019 Ejecutar `uv run pytest` completo y `uv run --no-sync ruff check src` en verde ([quickstart.md §1](quickstart.md))
- [X] T020 En una sesión nueva, ejecutar la tabla de [quickstart.md §2](quickstart.md) (9 pasos) con las herramientas de `core-bancario` y comprobar cada resultado esperado
- [X] T021 Pasar `bloquear_pii.py --diff` sobre un archivo con `git diff --unified=0 main...HEAD` sin hallazgos ([quickstart.md §3](quickstart.md))

---

## Phase 9: Cierre con `/abrir-pr`

- [X] T022 Verificar `uv run pytest` en verde y el árbol limpio
- [X] T023 Marcar T001 a T023 en `specs/006-transacciones-disputas/tasks.md` y hacer commit. T024 y T025 ocurren después del último commit y se marcan en la rama del issue siguiente
- [ ] T024 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #6`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T025 Después del merge, hecho por el desarrollador: verificar que el #6 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **US5 (T001–T005)**: primero; independiente del resto. T001, T002/T003, T004 y T005 tocan
  archivos distintos.
- **Fundamentos (T006–T009)**: después de US5 (T001 y T006 tocan el mismo archivo de test).
  T006/T007 (repositorio) y T008/T009 (contexto) son independientes entre sí.
- **US1 (T010–T011)**: después de T007 y T009.
- **US2 (T012–T013)**: después de US1 (mismo módulo y mismo archivo de tests).
- **US3 (T014–T015)**: después de US2 (completa la misma función).
- **US4 (T016–T018)**: después de US3 (registra ambas herramientas).
- **Verificación (T019–T021)**: requiere reiniciar la sesión con todo lo anterior hecho.
- **Cierre (T022–T025)**: requiere la verificación en verde.

### Parallel Opportunities

- T001, T002, T004 y T005 (archivos distintos).
- T006 y T008, y luego T007 y T009.

## Parallel Example: Fundamentos

```text
Task: "T006 Tests de política y tarjetas_de en src/core_bancario_mcp/test_repositorio.py"
Task: "T008 Tests del registro de disputas en src/core_bancario_mcp/test_contexto.py"
```

## Implementation Strategy

### MVP

Fundamentos + US1: con la política en el repositorio y `consultar_transacciones` ya se cubre
el primer paso del mensaje de ejemplo.

### Incremental Delivery

Un commit por paso con el test escrito antes. Las herramientas se publican en el servidor
solo en US4, cuando ambas están completas; la verificación ocurre en una sesión nueva y el
cierre con `/abrir-pr`, que incluye las dos revisiones.
