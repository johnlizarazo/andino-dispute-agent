---

description: "Lista de tareas del issue #4: Datos ficticios, contrato de errores e inyección de fallas"
---

# Tasks: Datos ficticios, contrato de errores e inyección de fallas

**Input**: documentos de diseño en `specs/004-datos-errores-fallas/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec los pide ("tests junto al código"). En cada módulo el test se escribe
**antes** que el código y vive en la misma carpeta (rule `tests.md`). Los tests usan un "hoy"
fijo y nunca contienen literales con forma real.

**Organization**: en el orden del plan: US1 → US2 → US4 → US3 → US5 → US6, luego
verificación y cierre. Los hooks del plugin están activos: `exigir_spec` permite escribir en
`src/` porque spec, plan y tareas ya existen, y `bloquear_pii` revisa cada archivo de datos.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US6).

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Crear la carpeta `src/core_bancario_mcp/datos/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: no hay prerrequisitos adicionales. El contrato de errores (US1) es la base de
fallas y servidor, y va primero.

---

## Phase 3: User Story 1 - Errores que el agente entiende sin interpretar texto (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-005.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_errores.py`.

- [X] T002 [US1] Escribir `src/core_bancario_mcp/test_errores.py` **antes** que el módulo, con los tests de [contracts/errores.md](contracts/errores.md):
  - `exito` con un dict, una lista y una lista vacía.
  - La forma completa del error para cada `TipoError`, con "`reintentable` verdadero solo en `transitorio`".
  - Que un tipo inválido lanza una excepción.
- [X] T003 [US1] Implementar `src/core_bancario_mcp/errores.py` según [contracts/errores.md](contracts/errores.md): `TipoError` (`StrEnum`), `Codigo` y las funciones `exito` y `error`, con `reintentable` derivado del tipo
- [X] T004 [US1] Dejar verdes los tests y hacer commit `feat(#4): contrato de errores del core bancario`

---

## Phase 4: User Story 2 - Datos ficticios que reproducen los casos obligatorios (Priority: P2)

**Goal**: FR-006 a FR-012.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_repositorio.py` y
[quickstart.md §2](quickstart.md).

- [X] T005 [P] [US2] Crear `src/core_bancario_mcp/datos/clientes.json` con exactamente los 4 clientes de [contracts/datos.md](contracts/datos.md); documentos "`^CC-FIC-\d{4}$`"
- [X] T006 [P] [US2] Crear `src/core_bancario_mcp/datos/tarjetas.json` con exactamente las 5 tarjetas del contrato; "`ultimos4` exactamente 4 dígitos", con `estado` en `activa` o `bloqueada`
- [X] T007 [P] [US2] Crear `src/core_bancario_mcp/datos/transacciones.json` con exactamente las 7 transacciones del contrato: `dias_atras` entero ≥ 0, `monto` entero > 0, `pais` de 2 letras y `estado: "aplicada"`
- [X] T008 [P] [US2] Crear `src/core_bancario_mcp/datos/politicas.json` exactamente como en el contrato
- [X] T009 [US2] Escribir `src/core_bancario_mcp/test_repositorio.py` **antes** que el módulo, con los tests de [contracts/repositorio.md](contracts/repositorio.md):
  - Fechas con `hoy = 2027-01-01` y con `hoy = 2026-03-01`.
  - La tarjeta `4821` con sus dos cobros de ayer.
  - Los homónimos.
  - El cobro en el exterior con más de 90 días.
  - El cobro de 500000 y la tarjeta bloqueada.
  - Un test por cada regla de validación, con JSON mal formados escritos en `tmp_path`.
- [X] T010 [US2] Implementar `src/core_bancario_mcp/repositorio.py` según [contracts/repositorio.md](contracts/repositorio.md): dataclasses inmutables, `DatosInvalidosError`, carga con `importlib.resources` o la `carpeta` indicada, validación completa y fechas con `hoy` inyectable. **No** implementar todavía `obtener_transaccion`: es de T013, para que su test (T012) falle primero
- [X] T011 [US2] Dejar verdes los tests y hacer commit `feat(#4): datos ficticios y repositorio del core`

---

## Phase 5: User Story 4 - Consulta de transacciones reutilizable (Priority: P4)

**Goal**: FR-017 y FR-018.

**Independent Test**: los tests de consulta en `test_repositorio.py`.

- [X] T012 [US4] Agregar a `src/core_bancario_mcp/test_repositorio.py` los tests de `obtener_transaccion`:
  - `TRX-002` devuelve monto 1250000, cliente `CLI-001` y la fecha de ayer.
  - Un id inexistente devuelve `None`.
  - El monto de cada transacción coincide con el JSON (SC-006).
- [X] T013 [US4] Comprobar que los tests de T012 fallan, implementar `Repositorio.obtener_transaccion` en `src/core_bancario_mcp/repositorio.py`, dejarlos verdes y hacer commit `feat(#4): consulta de transacción por id`

---

## Phase 6: User Story 3 - Fallas transitorias reproducibles (Priority: P3)

**Goal**: FR-013 a FR-016.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_fallas.py`.

- [X] T014 [US3] Escribir `src/core_bancario_mcp/test_fallas.py` **antes** que el módulo, con los tests de [contracts/fallas.md](contracts/fallas.md):
  - `"op:2"` devuelve `True`, `True` y `False`.
  - Sin configuración, nunca falla.
  - Dos operaciones son independientes.
  - Las configuraciones inválidas lanzan la excepción.
  - El decorador devuelve el error transitorio sin ejecutar la función y después la ejecuta.
- [X] T015 [US3] Implementar `src/core_bancario_mcp/fallas.py` según [contracts/fallas.md](contracts/fallas.md): `InyectorFallas`, `ConfiguracionFallasError`, `desde_entorno` y el decorador `con_fallas`
- [X] T016 [US3] Dejar verdes los tests y hacer commit `feat(#4): inyección de fallas transitorias`

---

## Phase 7: User Story 5 - Servidor ejecutable y registrado (Priority: P5)

**Goal**: FR-019 y FR-020.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_servidor.py` y
[quickstart.md §3 y §4](quickstart.md).

- [X] T017 [US5] Escribir `src/core_bancario_mcp/test_servidor.py` **antes** que el servidor, con los tests de [contracts/servidor.md](contracts/servidor.md):
  - `crear_servidor()` se llama `core-bancario` y no tiene herramientas.
  - El arranque real por stdio con el cliente de `mcp`, con un límite de 10 s, responde en menos de 5 s. El objetivo de 5 s (SC-005) se mide; el límite de 10 s da margen al arranque en frío del runner de CI.
  - Con `CORE_BANCARIO_FALLAS="op:0"`, sale con código 1.
- [X] T018 [US5] Implementar `src/core_bancario_mcp/servidor.py` (`crear_servidor`) y `src/core_bancario_mcp/__main__.py` según [contracts/servidor.md](contracts/servidor.md)
- [X] T019 [US5] Agregar el servidor `core-bancario` a `.mcp.json` exactamente como en el contrato, sin tocar `github`
- [X] T020 [US5] Ejecutar `uv run pytest` completo en verde. Ejecutar `uv build` y listar el wheel para confirmar que incluye los 4 archivos de `core_bancario_mcp/datos/`; si faltan, declararlos en `[tool.uv.build-backend]` de `pyproject.toml` y repetir. Borrar `dist/` y hacer commit `feat(#4): servidor core-bancario registrado en .mcp.json`

---

## Phase 8: User Story 6 - Ajustes heredados de los guardrails (Priority: P6)

**Goal**: FR-021 a FR-023.

- [X] T021 [P] [US6] En `.claude/rules/herramientas-mcp.md`, mantener la regla de reintento y agregar que la deriva `errores.error()` a partir del tipo (contrato del issue #4)
- [X] T022 [US6] En `plugins/andino-guardrails/hooks/test_bloquear_pii.py`, agregar:
  - Un test con una tarjeta válida de 15 dígitos agrupada en 4-6-5, generada al correr.
  - Un test del modo `--diff` donde se borra un archivo con una tarjeta generada (`+++ /dev/null` y líneas `-`): no debe reportar hallazgos.
- [X] T023 [US6] En `plugins/andino-guardrails/hooks/bloquear_pii.py`, hacer que el modo `--diff` ignore las líneas cuando el destino es `/dev/null`. Es una defensa explícita: git solo produce líneas `-` en un archivo borrado y esas ya se ignoraban, así que el test de T022 probablemente ya pasa (se documenta en el commit). Dejar verdes los tests y hacer commit `fix(#4): ajustes heredados de guardrails (4-6-5, /dev/null, rule de MCP)`

---

## Phase 9: Verificación en sesión nueva

**Purpose**: Claude Code carga los servidores de `.mcp.json` al iniciar. **Requiere
reiniciar la app** y, si lo pide, aprobar el nuevo servidor del proyecto.

- [ ] T024 [US5] En `/mcp`, comprobar que `core-bancario` y `github` aparecen conectados y que `core-bancario` lista 0 herramientas ([quickstart.md §4](quickstart.md))
- [ ] T025 [US2] Ejecutar [quickstart.md §2 y §3](quickstart.md): los dos cobros de ayer de la tarjeta 4821 y la salida con código 1 ante una configuración de fallas inválida
- [ ] T026 Pasar `bloquear_pii.py --diff` sobre `git diff --unified=0 main...HEAD` sin hallazgos ([quickstart.md §5](quickstart.md))

---

## Phase 10: Cierre con `/abrir-pr`

- [ ] T027 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T028 Marcar T001 a T028 en `specs/004-datos-errores-fallas/tasks.md` y hacer commit. T029 y T030 ocurren después del último commit y se marcan en la rama del issue siguiente
- [ ] T029 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO` (el principio III ahora tiene datos reales que auditar), PR con `Closes #4`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T030 Después del merge, hecho por el desarrollador: verificar que el #4 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **T001** → **US1 (T002–T004)**: errores primero, porque fallas y servidor lo usan.
- **US2 (T005–T011)**: después de US1. Los JSON (T005–T008) se pueden escribir en paralelo,
  antes de los tests del repositorio.
- **US4 (T012–T013)**: después de US2 (mismo módulo).
- **US3 (T014–T016)**: después de US1 (usa `errores`).
- **US5 (T017–T020)**: después de US2 y US3 (el servidor usa repositorio e inyector).
- **US6 (T021–T023)**: independiente; se puede hacer en cualquier momento.
- **Verificación (T024–T026)**: requiere reiniciar la sesión con todo lo anterior hecho.
- **Cierre (T027–T030)**: requiere la verificación en verde.

### Parallel Opportunities

- T005, T006, T007 y T008 (cuatro archivos JSON).
- US3 en paralelo con US2 y US4, una vez hecho US1.
- T021 en paralelo con cualquier fase.

## Parallel Example: User Story 2

```text
Task: "T005 Crear src/core_bancario_mcp/datos/clientes.json"
Task: "T006 Crear src/core_bancario_mcp/datos/tarjetas.json"
Task: "T007 Crear src/core_bancario_mcp/datos/transacciones.json"
Task: "T008 Crear src/core_bancario_mcp/datos/politicas.json"
```

## Implementation Strategy

### MVP

US1 (contrato de errores): toda herramienta de los issues #5 a #7 depende de él.

### Incremental Delivery

Un commit por historia, siempre con el test escrito antes. La verificación ocurre en una
sesión nueva con el servidor conectado, y el cierre se hace con `/abrir-pr`, que incluye
las dos revisiones.
