---

description: "Lista de tareas del issue #5: Identificación: buscar_cliente y verificar_identidad"
---

# Tasks: Identificación: `buscar_cliente` y `verificar_identidad`

**Input**: documentos de diseño en `specs/005-identificacion-clientes/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: la spec los pide (criterios de aceptación del issue). En cada módulo el test se
escribe **antes** que el código, vive en la misma carpeta (rule `tests.md`) y se ve fallar
antes de implementar. Solo datos ficticios: documentos `CC-FIC-NNNN`; las entradas
inválidas no tienen forma de documento ni de tarjeta reales.

**Organization**: en el orden de implementación del plan: US4 (cimientos y contexto) → US1 →
US2 → US3, luego verificación en sesión nueva y cierre. Los hooks del plugin están activos
(`exigir_spec`, `bloquear_pii`, `formatear`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: no hay preparación: dependencias, datos y servidor existen desde el #4.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: los cimientos de US4 bloquean a las herramientas y se hacen primero (fase 3).

---

## Phase 3: User Story 4 - Cimientos más robustos (Priority: P4, primero por el plan)

**Goal**: FR-014 a FR-016.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_repositorio.py src/core_bancario_mcp/test_fallas.py src/core_bancario_mcp/test_contexto.py`.

- [ ] T001 [P] [US4] Ampliar `src/core_bancario_mcp/test_repositorio.py` **antes** de tocar el módulo, con todos los casos de [contracts/cimientos.md](contracts/cimientos.md) como parametrización de `test_datos_invalidos_impiden_cargar` (o un test hermano) y verlos fallar:
  - Archivo que no es lista (`clientes.json` como objeto) y `politicas.json` que no es objeto.
  - Registro que no es objeto (un número en la lista).
  - Texto esperado con otro tipo: `documento: 1`, `ultimos4: 4821` (número).
  - Entero esperado con otro tipo: `monto: 1.5`, `monto: true`, `dias_atras: "1"`, y un campo de la política como texto.
  - `estado` de tarjeta `"perdida"` (válidos: "{`activa`, `bloqueada`}").
  - `pais: "COL"` (regla: "`^[A-Z]{2}$`").
  - `dato_verificacion: "19x7"` (regla: "`^[0-9]{4}$`").
  - `ultimos4` con 4 dígitos arábigo-índicos, construidos en el test con `chr(0x0660 + n)`.
  - Cada caso espera `DatosInvalidosError` con el archivo y el id (o la posición) del registro en el mensaje.
- [ ] T002 [US4] Endurecer `src/core_bancario_mcp/repositorio.py` según [research.md R7](research.md): validar que cada archivo es lista de objetos (políticas, un objeto); tipos por campo (textos no vacíos para ids, nombre, comercio y estados; enteros que sean `int` y no `bool` para `monto`, `dias_atras` y la política); `estado` de tarjeta en {`activa`, `bloqueada`}; `pais` `^[A-Z]{2}$`; `dato_verificacion` `^[0-9]{4}$`; cambiar los patrones a `[0-9]`. Mantener los mensajes existentes y dejar verdes los tests nuevos y los del #4
- [ ] T003 [P] [US4] Ampliar `src/core_bancario_mcp/test_fallas.py` **antes** de tocar el módulo con los casos de [contracts/cimientos.md](contracts/cimientos.md) y verlos fallar: `op:٣` (dígito construido con `chr(0x0663)`), `op:+1`, `op:--1`, `op:1,op:2` (repetida) y `Op Mal:1` (operación fuera de "`^[a-z0-9_]+$`"), todos con `ConfiguracionFallasError`; los casos válidos existentes siguen pasando
- [ ] T004 [US4] Endurecer `src/core_bancario_mcp/fallas.py`: operación `^[a-z0-9_]+$`, veces `^[0-9]+$` y `>= 1`, operación repetida rechazada; mensajes con `VARIABLE` y el fragmento. Dejar verdes los tests y hacer commit `fix(#5): validación estricta de datos y de configuración de fallas`
- [ ] T005 [P] [US4] Escribir `src/core_bancario_mcp/test_contexto.py` **antes** que el módulo, con las transiciones del [data-model.md](data-model.md): cliente nuevo no agotado; 3 fallos agotan (`MAXIMO = 3`); 2 fallos + `reiniciar` vuelven a 0; un cliente agotado sigue agotado; los fallos de un cliente no afectan a otro; `Contexto(repositorio, inyector)` crea un `IntentosVerificacion` propio por instancia
- [ ] T006 [US4] Implementar `src/core_bancario_mcp/contexto.py` según [contracts/contexto-servidor.md](contracts/contexto-servidor.md): `IntentosVerificacion` (`agotados`, `registrar_fallo`, `reiniciar`) y el dataclass `Contexto` con `field(default_factory=IntentosVerificacion)`. Dejar verdes los tests y hacer commit `feat(#5): contexto explícito del servidor con control de intentos`

---

## Phase 4: User Story 1 - Encontrar al cliente sin confundirlo con otro (Priority: P1) 🎯 MVP

**Goal**: FR-001 a FR-005.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_identificacion.py -k buscar`.

- [ ] T007 [US1] Escribir en `src/core_bancario_mcp/test_identificacion.py` (nuevo), **antes** que el módulo, los tests de búsqueda de [contracts/buscar_cliente.md](contracts/buscar_cliente.md), llamando a la función pura con un `Contexto` armado en una fixture (`Repositorio(hoy=date(2026, 10, 23))`, `InyectorFallas(None)`):
  - Documento `CC-FIC-0001` → 1 coincidencia (CLI-001); últimos 4 `4821` → CLI-001.
  - "Carlos Andrés Pérez", "carlos perez" y "CARLOS ANDRES PEREZ" → CLI-002 y CLI-003, en ese orden.
  - "an" no encuentra a nadie (palabras completas, no subcadenas); "Pérez," con puntuación encuentra a los dos homónimos (ajuste U1).
  - Documento `CC-FIC-0099` → `{"ok": True, "datos": []}`.
  - Ninguna coincidencia de ninguna búsqueda tiene claves distintas de `cliente_id` y `nombre`.
  - Validación `PARAMETRO_INVALIDO` no reintentable: sin criterio, dos criterios, texto vacío o de solo espacios como único criterio, documento `CC-0001`, últimos 4 `48a1` y `482`, últimos 4 como número (`4821`) y como lista (ajuste C1), nombre `"a"` y nombre de 101 caracteres.
  - Últimos 4 compartidos: datos copiados a `tmp_path` con una tarjeta extra `4821` de CLI-004 → CLI-001 y CLI-004, sin repetir.
- [ ] T008 [US1] Implementar `buscar_cliente(contexto, documento=None, nombre=None, ultimos4=None)` en `src/core_bancario_mcp/identificacion.py` según [research.md R4](research.md): todo valor que no sea `None` debe ser `str` (si no, `PARAMETRO_INVALIDO`); exactamente un criterio no vacío ni de solo espacios; documento "`^CC-FIC-[0-9]{4}$`" tras `strip()`; nombre con "2+ letras tras normalizar, hasta 100 caracteres", normalizado con NFKD sin marcas combinantes y `casefold()`, palabras extraídas con `re.findall(r"\w+")`, coincidencia por palabras completas; últimos 4 "`^[0-9]{4}$`"; resultado `exito([...])` ordenado por `cliente_id`, solo `cliente_id` y `nombre`. Errores solo con `errores.error()`. Dejar verdes los tests y hacer commit `feat(#5): buscar_cliente`

---

## Phase 5: User Story 2 - Verificar la identidad con un dato adicional (Priority: P2)

**Goal**: FR-006 a FR-010.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_identificacion.py -k verificar`.

- [ ] T009 [US2] Agregar a `src/core_bancario_mcp/test_identificacion.py`, **antes** de implementar, los tests de [contracts/verificar_identidad.md](contracts/verificar_identidad.md), leyendo el dato correcto del repositorio (no como literal en el test):
  - Dato correcto → `{"cliente_id": ..., "verificado": True}`.
  - Dato incorrecto → permiso `VERIFICACION_FALLIDA` no reintentable, y el mensaje no contiene el dato correcto.
  - Cliente `CLI-999` → validación `NO_ENCONTRADO`; parámetro ausente, vacío o que no es texto (`dato_verificacion` como número) → validación `PARAMETRO_INVALIDO`.
  - 3 fallos → el cuarto intento con el dato correcto es negocio `INTENTOS_AGOTADOS` no reintentable.
  - 2 fallos + éxito → hacen falta 3 fallos más para agotar.
  - Los fallos de CLI-001 no afectan a CLI-002; un cliente inexistente no suma intentos.
- [ ] T010 [US2] Agregar a `Codigo` en `src/core_bancario_mcp/errores.py` los códigos `VERIFICACION_FALLIDA` e `INTENTOS_AGOTADOS`, e implementar `verificar_identidad(contexto, cliente_id=None, dato_verificacion=None)` (parámetro con el nombre del campo de los datos, ajuste I1) en `src/core_bancario_mcp/identificacion.py` con el orden de evaluación del contrato (parámetros → cliente existe → agotados → `hmac.compare_digest` exacto; éxito reinicia, fallo suma). El mensaje de `INTENTOS_AGOTADOS` indica escalar a un analista. Dejar verdes los tests y hacer commit `feat(#5): verificar_identidad con límite de intentos`

---

## Phase 6: User Story 3 - Descripciones que guían al agente (Priority: P3)

**Goal**: FR-011 a FR-013 y el cierre de FR-016.

**Independent Test**: `uv run pytest src/core_bancario_mcp/test_servidor.py src/core_bancario_mcp/test_identificacion.py`.

- [ ] T011 [US3] Actualizar `src/core_bancario_mcp/test_servidor.py` **antes** de registrar las herramientas y verlo fallar:
  - `list_tools` de `crear_servidor()` devuelve exactamente `buscar_cliente` y `verificar_identidad` (reemplaza el test de lista vacía).
  - La descripción de `buscar_cliente` dice que no verifica identidad y que con varias coincidencias se pide otro identificador sin elegir; la de `verificar_identidad`, que va después de una única coincidencia y que un fallo no se reintenta con un dato inventado (aserciones sobre frases clave, sin mayúsculas).
  - `call_tool("buscar_cliente", {"nombre": "carlos perez"})` devuelve un JSON con `ok: true` y 2 coincidencias.
  - El servidor no tiene atributos `repositorio` ni `inyector` agregados.
  - El arranque real por stdio lista las 2 herramientas en menos de 5 s.
- [ ] T012 [US3] Agregar a `src/core_bancario_mcp/test_identificacion.py` los tests de fallas inyectadas a través de `registrar` sobre un `FastMCP` de prueba: con `InyectorFallas("buscar_cliente:1")` la primera llamada es transitoria reintentable y la segunda responde; con `verificar_identidad:1` la falla no cambia el contador de intentos
- [ ] T013 [US3] Implementar `registrar(servidor, contexto)` en `src/core_bancario_mcp/identificacion.py`: publica ambas herramientas con `@servidor.tool(name=..., description=...)` sobre `con_fallas(contexto.inyector, "<nombre>")`, con parámetros del tipo `Texto = Annotated[object, WithJsonSchema({"type": "string"})]` y valor por defecto `None` ([research.md R5](research.md), ajuste C1) y las descripciones de los contratos. Agregar a `test_servidor.py` un test por `call_tool` con `ultimos4` numérico que responda `PARAMETRO_INVALIDO` con el contrato (no `isError`), y otro que confirme que el esquema publicado declara los parámetros como `string`. Cambiar `src/core_bancario_mcp/servidor.py` para construir el `Contexto` y llamar a `registrar`, sin atributos dinámicos, y actualizar su docstring. Dejar verdes los tests y hacer commit `feat(#5): herramientas de identificación registradas en core-bancario`
- [ ] T014 [P] [US3] En `.claude/rules/herramientas-mcp.md`, agregar que cada módulo de herramientas expone `registrar(servidor, contexto)`, recibe el estado por `Contexto` (nunca atributos en `FastMCP`) y declara sus parámetros con el tipo `Texto` (esquema de texto, validación en la herramienta) para que ausencias, formatos y tipos JSON incorrectos se respondan con el contrato. Commit `docs(#5): convención de registro de herramientas en la rule de MCP`

---

## Phase 7: Verificación en sesión nueva

**Purpose**: Claude Code carga las herramientas de `core-bancario` al iniciar. **Requiere
reiniciar la app.**

- [ ] T015 Ejecutar `uv run pytest` completo y `uv run --no-sync ruff check src` en verde ([quickstart.md §1](quickstart.md))
- [ ] T016 En una sesión nueva, ejecutar la tabla de [quickstart.md §2](quickstart.md) con las herramientas de `core-bancario` (7 pasos) y comprobar cada resultado esperado
- [ ] T017 Ejecutar [quickstart.md §3](quickstart.md) (operación repetida en `CORE_BANCARIO_FALLAS`, variante Bash o PowerShell): mensaje claro y código 1, sin traza
- [ ] T018 Pasar `bloquear_pii.py --diff` sobre `git diff --unified=0 main...HEAD` sin hallazgos

---

## Phase 8: Cierre con `/abrir-pr`

- [ ] T019 Verificar `uv run pytest` en verde y el árbol limpio
- [ ] T020 Marcar T001 a T020 en `specs/005-identificacion-clientes/tasks.md` y hacer commit. T021 y T022 ocurren después del último commit y se marcan en la rama del issue siguiente
- [ ] T021 El desarrollador ejecuta `/abrir-pr` y aprueba el push y el PR. Esperado: revisión de código `APROBADO`, cumplimiento `APROBADO`, PR con `Closes #5`, CI `guardrails` en verde, issue en *In Review* y comentario de avance
- [ ] T022 Después del merge, hecho por el desarrollador: verificar que el #5 queda cerrado y en *Done*

---

## Dependencies & Execution Order

- **US4 (T001–T006)**: primero. T001/T002 (repositorio), T003/T004 (fallas) y T005/T006
  (contexto) son tres pares independientes entre sí.
- **US1 (T007–T008)**: después de T002 (repositorio endurecido) y T006 (contexto).
- **US2 (T009–T010)**: después de US1 (mismo módulo y mismo archivo de tests).
- **US3 (T011–T013)**: después de US2 (registra ambas herramientas); T014 en cualquier
  momento.
- **Verificación (T015–T018)**: requiere reiniciar la sesión con todo lo anterior hecho.
- **Cierre (T019–T022)**: requiere la verificación en verde.

### Parallel Opportunities

- T001, T003 y T005 (tres archivos de test distintos), y luego sus implementaciones.
- T014 en paralelo con cualquier fase.

## Parallel Example: User Story 4

```text
Task: "T001 Ampliar src/core_bancario_mcp/test_repositorio.py"
Task: "T003 Ampliar src/core_bancario_mcp/test_fallas.py"
Task: "T005 Escribir src/core_bancario_mcp/test_contexto.py"
```

## Implementation Strategy

### MVP

US4 + US1: con los cimientos y `buscar_cliente` ya se cubre el caso obligatorio de dos
clientes con el mismo nombre.

### Incremental Delivery

Un commit por paso con el test escrito antes. Las herramientas se publican en el servidor
solo en US3, cuando ambas existen; la verificación ocurre en una sesión nueva y el cierre
con `/abrir-pr`, que incluye las dos revisiones.
