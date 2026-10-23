# Implementation Plan: Identificación: `buscar_cliente` y `verificar_identidad`

**Branch**: `005-identificacion-clientes` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-identificacion-clientes/spec.md` (issue #5)

## Summary

Las dos primeras herramientas de negocio de `core-bancario`, sobre unos cimientos más firmes:

- **Contexto explícito** (`contexto.py`): un objeto `Contexto` con el repositorio, el
  inyector de fallas y el control de intentos. `crear_servidor` lo construye y lo pasa al
  registrar las herramientas; desaparecen los atributos agregados al vuelo a `FastMCP`.
- **Herramientas de identificación** (`identificacion.py`): funciones puras
  `buscar_cliente(contexto, ...)` y `verificar_identidad(contexto, ...)` más
  `registrar(servidor, contexto)`, que las publica con sus descripciones y la inyección de
  fallas.
- **Control de intentos fallidos**: 3 fallos consecutivos por cliente bloquean la
  verificación mientras el proceso siga vivo; un éxito reinicia el contador.
- **Endurecimiento** de `repositorio.py` (tipos, estado, país, dígitos ASCII) y de
  `fallas.py` (ASCII, signos, repetidas).

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `mcp[cli]` 1.30.0 (`FastMCP`) y `pydantic` (`WithJsonSchema`,
ya instalado con `mcp`), declarados; `unicodedata`,
`hmac` y `re` de la biblioteca estándar. Sin dependencias nuevas.

**Storage**: los JSON del issue #4 (sin cambios de datos); el contador de intentos vive en
memoria del proceso del servidor

**Testing**: `pytest`, tests junto a cada módulo; las herramientas se prueban como
funciones puras con un `Contexto` armado en el test, y por `call_tool`/`list_tools` del
servidor para el registro y las descripciones

**Target Platform**: Windows, Linux y macOS; Claude Code y el agente lanzan el servidor por
stdio

**Project Type**: servidor MCP dentro del proyecto `uv`

**Performance Goals**: el arranque sigue por debajo de 5 s (test existente)

**Constraints**:
- Ninguna respuesta de búsqueda incluye documento ni dato de verificación (SC-003).
- Errores solo con `exito()` y `error()`; `reintentable` derivado del tipo.
- Hook `exigir_spec`: nada en `src/` sin spec, plan y tareas.

**Scale/Scope**: 2 módulos nuevos con sus tests, cambios en `servidor.py`, `errores.py`,
`repositorio.py`, `fallas.py` y sus tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | `buscar_cliente` y `verificar_identidad` son las herramientas exentas de la regla 1; la verificación es la fuente de verdad que usará el hook del #9. Ninguna opera sobre productos. | ✅ |
| II. Garantías deterministas | Nivel declarado por regla: no elegir entre coincidencias es **imposible por diseño** (la búsqueda solo devuelve listas y nunca un "cliente elegido"); no revelar datos de otros es imposible por diseño (la coincidencia solo tiene id y nombre); el límite de intentos lo **garantiza el servidor**; "buscar no verifica" se **orienta** con la descripción y lo hará cumplir el hook del #9. | ✅ |
| III. Datos ficticios | Sin datos nuevos; documento validado contra `CC-FIC-[0-9]{4}` también en la entrada de la búsqueda; tests con los datos ficticios del #4 o generados en `tmp_path`. | ✅ |
| IV. Spec-first | Spec aprobada (commit `aa0426a`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | Ambas herramientas responden con `exito()`/`error()`; búsqueda vacía = `exito([])`; descripciones según US3. Los parámetros usan el tipo `Texto` (R5): incluso un tipo JSON incorrecto llega a la herramienta y se responde con el contrato. | ✅ |
| VI. Tests junto al código | `test_identificacion.py` y `test_contexto.py` al lado de sus módulos; tests de repositorio y fallas ampliados. | ✅ |
| VII. Simplicidad | Cierre sobre un `Contexto` en lugar de `lifespan`; sin sesiones en el core; sin dependencias. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/005-identificacion-clientes/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── buscar_cliente.md
│   ├── verificar_identidad.md
│   ├── contexto-servidor.md
│   └── cimientos.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/core_bancario_mcp/
├── contexto.py                  # nuevo: Contexto e IntentosVerificacion
├── test_contexto.py             # nuevo
├── identificacion.py            # nuevo: buscar_cliente, verificar_identidad, registrar
├── test_identificacion.py       # nuevo
├── errores.py                   # mod: códigos VERIFICACION_FALLIDA e INTENTOS_AGOTADOS
├── servidor.py                  # mod: arma el Contexto y registra las herramientas
├── test_servidor.py             # mod: lista exactamente las 2 herramientas (también por stdio)
├── repositorio.py               # mod: tipos, estado, país, [0-9], dato_verificacion
├── test_repositorio.py          # mod: casos de tipos incorrectos
├── fallas.py                    # mod: ASCII, signos, repetidas, nombre de operación
└── test_fallas.py               # mod: casos nuevos
```

**Structure Decision**: un módulo por responsabilidad. Las herramientas de cada issue
(#5 identificación, #6 transacciones, #7 disputas y bloqueo) viven en su propio módulo con
una función `registrar(servidor, contexto)`; `servidor.py` solo las ensambla
([research.md R1](research.md)).

## Orden de implementación

1. **Cimientos** (US4): tests y endurecimiento de `repositorio.py` y `fallas.py`.
2. **Contexto** (US4, FR-016): `contexto.py` con `IntentosVerificacion`, y `servidor.py`
   sin atributos dinámicos.
3. **Búsqueda** (US1): tests y `buscar_cliente`.
4. **Verificación** (US2): tests y `verificar_identidad` con el límite de intentos.
5. **Registro y descripciones** (US3): `registrar`, fallas inyectables, tests por
   `list_tools`/`call_tool` y por stdio.
6. **Verificación manual**: sesión nueva con `core-bancario` conectado (quickstart), y
   luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Un fragmento de documento en tests dispara `bloquear_pii` | Solo `CC-FIC-NNNN` y entradas inválidas sin forma de documento real (letras, longitudes cortas). |
| El contador de intentos se comparte entre conversaciones del mismo proceso | Es intencional (protege al cliente, no a la sesión); se reinicia con el proceso. Límite declarado en R3. |
| Errores de tipo JSON fuera del contrato | Tipo `Texto` con esquema de texto y validación en la herramienta (R5, ajuste C1). |
| Romper el test de arranque al registrar herramientas | El test por stdio pasa a esperar las 2 herramientas. |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
