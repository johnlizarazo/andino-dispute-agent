---

description: "Lista de tareas del issue #14: Plugin, marketplace y DECISIONES.md"
---

# Tasks: Plugin, marketplace y DECISIONES.md

**Input**: documentos de diseño en `specs/014-plugin-marketplace-decisiones/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: el script de entrega es lo que no debe fallar, así que su test determinista va
**antes** del script, junto a él, y se ve fallar. Los valores con forma de credencial y los
números que pasan Luhn se arman en tiempo de ejecución, nunca como literales (principio III;
el hook `bloquear_pii` los bloquearía). No se toca `src/`.

**Organization**: US3 (script) → US2 (`DECISIONES.md`) → US1 (README del plugin e
instalación) → US4 (visibilidad) → cierre. El script va primero porque es la única pieza
con código y test. Herramienta Bash: no escribir con scripts texto que lleve barras
invertidas; usar Write/Edit.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivo distinto, sin dependencias pendientes).
- **[Story]**: historia de usuario de la spec (US1 a US4).

---

## Phase 1: Setup

- [X] T001 Agregar `dist/` a `.gitignore`, `"scripts"` a `testpaths` en `pyproject.toml` y `"scripts/**/test_*.py"` a los `paths` de `.claude/rules/tests.md` (ajuste C1: misma convención de tests en todas las carpetas, principio VI). `uv run pytest` sigue en verde

---

## Phase 2: User Story 3 - Armar la entrega con un script (Priority: P2)

**Goal**: FR-007 a FR-011 ([contracts/armar-entrega.md](contracts/armar-entrega.md), research R4, R5).

**Independent Test**: `uv run pytest scripts/test_armar_entrega.py`.

- [X] T002 [US3] Escribir `scripts/test_armar_entrega.py`, **antes** del script, con un repositorio git temporal en `tmp_path` (`git init`, usuario y correo locales, un commit con `README.md`, `src/modulo.py` y `.env.example`; sin versionar: `.env`, `.venv/lib.py`, `src/__pycache__/x.pyc`, `.pytest_cache/`, `notas-locales.txt`). Casos: (a) `armar(raiz, salida)` crea el `.zip` con los versionados y entradas bajo `.git/`, sin `.env`, `.venv/`, cachés ni `notas-locales.txt`, y con `.env.example`; (b) un archivo versionado que coincide con una exclusión del modelo ("`.venv/`, `.env*` salvo `.env.example`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`, `*.egg-info/`, `dist/`, `build/`, `.chainlit/`, `.files/`, `CLAUDE.local.md`, `.claude/settings.local.json`") tampoco entra; (c) un token de GitHub armado en tiempo de ejecución (`"gh" + "p_" + "A" * 36`) en un archivo versionado da un hallazgo con tipo `github` y la ruta, sin el valor en ningún mensaje, código 1 y sin `.zip`; (d) el mismo token en un commit anterior que luego se borró da un hallazgo con `commit <sha corto>`; (e) lo mismo para `anthropic` (`"sk-" + "ant-" + …`), `aws` y `clave_privada`; (f) textos parecidos que no son credenciales (`ghp_` corto, `sk-ant-` sin cuerpo) no dan hallazgos; (g) con un límite inyectado menor que el tamaño, código 1, mensaje con el tamaño y sin `.zip`; con un umbral de aviso inyectado, código 0 y el aviso; (h) fuera de un repositorio git, código 1 con mensaje claro; (i) `main(["--salida", ruta])` devuelve 0 y escribe en esa ruta. Verlo fallar
- [X] T003 [US3] Escribir `scripts/armar_entrega.py` (docstring: arma el `.zip` de entrega con los archivos versionados y `.git`; verifica credenciales y tamaño; solo biblioteca estándar; uso `uv run --no-project python scripts/armar_entrega.py [--salida RUTA]`): `EXCLUSIONES`, `PATRONES` de credenciales (github `gh[pousr]_[A-Za-z0-9]{36,}` y `github_pat_[A-Za-z0-9_]{50,}`, anthropic `sk-ant-[A-Za-z0-9_-]{20,}`, aws `AKIA[0-9A-Z]{16}`, clave_privada `-----BEGIN [A-Z ]*PRIVATE KEY-----`), `Hallazgo` (`tipo`, `ubicacion`; "Nunca guarda ni muestra el valor encontrado"), `buscar_credenciales(raiz)` sobre los archivos versionados (texto, ignorando binarios) y sobre `git log -p --all`, `armar(raiz, salida, limite=50 MB, aviso=40 MB)` que escribe en un temporal y solo lo renombra si pasa, y `main(argv)`. Dejar verde. Commit `feat(#14): script de entrega`
- [X] T004 [US3] Correr `uv run --no-project python scripts/armar_entrega.py` sobre este repositorio y anotar aquí el tamaño, la cantidad de archivos y cuánto tardó (ajuste L1, SC-005: menos de 1 minuto). Debe dar **cero hallazgos** sobre este repositorio (ajuste L2: sin falsos positivos con los ejemplos y patrones documentados en los propios artefactos); si da alguno, ajustar el patrón y el test antes de seguir; abrir el `.zip` y confirmar `.git/` presente y `.venv/`, `.env`, `.chainlit/` y `.claude/launch.json` ausentes. Resultado (2026-10-26): código 0, `dist/entrega-andino-dispute-agent.zip` de 33.6 MB con 350 archivos, en 1.8 s (SC-005); **cero hallazgos** en los archivos versionados y en todo el historial (L2). El `.zip` tiene `.git/`, `.env.example` y el video, y no tiene `.venv/`, `.env`, `.chainlit/`, `.claude/launch.json`, `dist/` ni `__pycache__`

---

## Phase 3: User Story 2 - DECISIONES.md (Priority: P1)

**Goal**: FR-005, FR-006, SC-002 (research R3).

**Independent Test**: quickstart paso 3.

- [X] T005 [P] [US2] Escribir `DECISIONES.md` en la raíz, de máximo unas 900 palabras: un párrafo de criterio (lo que no puede fallar va en hooks; lo que necesita juicio, en un subagente aislado; lo que es contexto, en reglas o memoria; principio II); la tabla **Ecosistema de Claude Code** con columnas Necesidad, Mecanismo, Dónde, Alternativa descartada y Origen, y filas para memoria del proyecto (`CLAUDE.md` + constitución), memoria personal, reglas por ruta, skill `siguiente-ticket`, comando `/abrir-pr`, subagente `revisor-codigo`, hooks `bloquear_pii`, `exigir_spec` y `formatear`, auditor y skill de cumplimiento en el plugin, permisos sobre `.env*`, servidores MCP (`.mcp.json`), plugin y marketplace, CI (`guardrails.yml`) y paso a *Done*; y la tabla **Reglas de negocio** (regla, nivel, dónde). Cada alternativa y cada origen salen de los `research.md` existentes (001 R1–R5, 002 R1–R8, 003 R1–R11, 008–011), sin contradecirlos; el Origen es un enlace relativo al `research.md`. Contar las palabras con el comando del quickstart y anotarlo aquí. Commit `docs(#14): DECISIONES.md`. Resultado (2026-10-26): 778 palabras; todos los enlaces a `research.md` existen; el origen de la memoria del proyecto es la constitución (Governance), no un `research.md`

---

## Phase 4: User Story 1 - Instalar los guardrails en otro repositorio (Priority: P1)

**Goal**: FR-001 a FR-004, SC-001 (research R1, R2).

**Independent Test**: quickstart paso 4.

- [X] T006 [P] [US1] Actualizar `plugins/andino-guardrails/README.md`: instalación con `/plugin marketplace add johnlizarazo/andino-dispute-agent` y `/plugin install andino-guardrails@banco-andino` (antes de la alternativa por `settings.json`, que se conserva); advertencia de que `exigir_spec` bloquea escrituras bajo `src/` sin `specs/<rama>/` y de que el auditor espera una constitución en `.specify/memory/constitution.md`; cómo deshabilitar el plugin (`/plugin disable andino-guardrails@banco-andino` o `enabledPlugins` en `false`); quitar la frase "La prueba de instalación en otro repositorio y su documentación completa son del issue #14". Commit `docs(#14): instalación del plugin desde otro repositorio`
- [X] T007 [US1] Verificación manual (la hace el desarrollador; el plugin ya está en `main` desde el #3): en una carpeta nueva fuera del repositorio, `git init`, abrir Claude Code, ejecutar los dos comandos y comprobar que `/plugin` lo muestra habilitado, que `/agents` lista el auditor del plugin, que existe `/andino-guardrails:revisar-cumplimiento` y que el hook bloquea dos casos de prueba: un número de tarjeta con forma real y un número de documento real junto a "cédula" (ajuste L3). Anotar aquí el resultado (SC-001). Resultado (2026-10-26): el desarrollador confirmó que la prueba en un repositorio vacío fue correcta: el plugin se instaló con los dos comandos desde GitHub y se cumplieron las comprobaciones de la tarea

---

## Phase 5: User Story 4 - Acceso sin pedir permiso (Priority: P2)

**Goal**: FR-012, SC-004 (research R6).

- [X] T008 [US4] Comprobar sin token `GET https://api.github.com/repos/johnlizarazo/andino-dispute-agent` (`"private": false`) y pedir al desarrollador que abra el Project en una ventana privada del navegador (si es privado, que lo cambie a público). Anotar aquí el resultado. Resultado (2026-10-26): la API sin token responde 200 con `"private": false`; la página del Project sin sesión responde 200 con el título "MVP Agente de disputas · GitHub" (no es la página de inicio de sesión), así que el Project es público. No hizo falta la ventana privada

---

## Phase 6: Cierre

- [X] T009 Actualizar `README.md`: enlace a `DECISIONES.md` en la cabecera y una sección **Entrega** con el comando del script, qué incluye y excluye, y los límites (50 MB, sin credenciales). Commit `docs(#14): README con la entrega y DECISIONES.md`
- [X] T010 Verificación final: `uv run pytest` en verde, `uv run ruff check src tests scripts plugins` y `uv run ruff format --check src tests scripts plugins` limpios, el script vuelve a pasar tras los últimos cambios, y T004, T005, T007 y T008 anotados. Luego `/abrir-pr`. Resultado (2026-10-26): 674 passed; ruff limpio; el script vuelve a dar código 0 (33.6 MB, 374 archivos, sin hallazgos); T004, T005, T007 y T008 anotados. Límite: el script solo se corrió en Windows; en Linux lo cubren sus tests, que corren en el CI (Ubuntu)

---

## Dependencies & Execution Order

- **T001** antes de T002 (`testpaths`).
- **T002 → T003 → T004**.
- **T005**, **T006** y **T008** no dependen del script: se pueden hacer en paralelo con la fase 2.
- **T007** depende solo de que el desarrollador tenga Claude Code abierto en una carpeta vacía; puede ir en cualquier momento.
- **T009** después de T003 (documenta el script).
- **T010** al final; el script se vuelve a correr porque `DECISIONES.md` y los README cambian el contenido del `.zip`.

## Parallel Example

```text
T005 (DECISIONES.md) en paralelo con T006 (README del plugin) y con T002–T003 (script).
```

## Implementation Strategy

- **MVP**: T001–T004 (la entrega se puede armar y verificar) y T005 (`DECISIONES.md`).
- Lo manual (T007, T008) se pide al desarrollador temprano para no bloquear el cierre.
