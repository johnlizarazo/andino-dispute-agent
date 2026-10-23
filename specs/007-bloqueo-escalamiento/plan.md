# Implementation Plan: Bloqueo y escalamiento: `bloquear_tarjeta` y `escalar_a_analista`

**Branch**: `007-bloqueo-escalamiento` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-bloqueo-escalamiento/spec.md` (issue #7)

## Summary

Las dos últimas herramientas del core, con la misma convención del #5 y el #6:

- **Registros en el Contexto** (`contexto.py`): `RegistroBloqueos` (estado efectivo de cada
  tarjeta: dato inicial + bloqueos de la sesión) y `RegistroEscalamientos` (`ESC-NNNN` con
  contador propio).
- **Herramientas** (`bloqueo_escalamiento.py`): funciones puras `bloquear_tarjeta` y
  `escalar_a_analista` sobre el `Contexto`, y `registrar(servidor, contexto)`.
- **Tipo `ListaTexto`** para la lista de transacciones: el esquema publica `array` de
  `string`, pero cualquier valor llega a la herramienta y se valida con el contrato.
- **Ajustes heredados del #6**: fecha de solo espacios = omitida, contador propio de casos y
  `Politica.limite_dias`.

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `mcp[cli]` 1.30.0 y `pydantic` (`WithJsonSchema`), ya declarados;
`json` de la biblioteca estándar. Sin dependencias nuevas.

**Storage**: los JSON del #4 sin cambios; bloqueos y escalamientos en memoria del proceso

**Testing**: `pytest`, tests junto a cada módulo, con "hoy" fijo; funciones puras con un
`Contexto` armado en el test y `list_tools`/`call_tool` para el registro

**Target Platform**: Windows, Linux y macOS; servidor por stdio

**Project Type**: servidor MCP dentro del proyecto `uv`

**Performance Goals**: el arranque sigue por debajo de 5 s (test existente)

**Constraints**:
- `bloquear_tarjeta` no tiene ningún parámetro ni paso de aprobación (regla 3).
- Los montos del escalamiento salen del repositorio; no hay parámetro de monto (regla 2).
- Ninguna respuesta revela si una tarjeta es de otro cliente.

**Scale/Scope**: 1 módulo nuevo con su test; cambios en `contexto.py`, `errores.py`,
`repositorio.py`, `transacciones.py`, `identificacion.py` (tipo `ListaTexto`), `servidor.py`,
la rule de MCP y sus tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Regla 3: bloqueo inmediato sin aprobación. Regla 1: `bloquear_tarjeta` exige identidad (la garantiza el hook del #9, que recibe el `cliente_id`); `escalar_a_analista` está exenta. Regla 4: "persona solicitada" se acepta sin cliente ni transacciones. Regla 2: montos del core en el resumen. | ✅ |
| II. Garantías deterministas | Declaradas en la spec (Assumptions): sin aprobación intermedia y montos del core, **imposibles por diseño**; identidad antes de bloquear, **hook** del #9; reconocer el pedido de persona, **instrucción + test** (#10, #13); no cerrar con escalamiento pendiente, **hook `Stop`** del #10 (la causa en lista cerrada se lo permite). | ✅ |
| III. Datos ficticios | Sin datos nuevos; tests con datos ficticios o copias en `tmp_path`; los resúmenes solo contienen ids, nombres ficticios y montos del core. | ✅ |
| IV. Spec-first | Spec aprobada (commit `ea5f641`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | `exito()`/`error()`; parámetros `Texto` y `ListaTexto` para que cualquier argumento responda con el contrato; descripciones según US3. | ✅ |
| VI. Tests junto al código | `test_bloqueo_escalamiento.py` junto al módulo; tests de contexto, repositorio, transacciones y servidor ampliados. | ✅ |
| VII. Simplicidad | Registros en memoria como en el #5 y el #6; un tipo nuevo solo para la lista; sin dependencias. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/007-bloqueo-escalamiento/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── bloquear_tarjeta.md
│   ├── escalar_a_analista.md
│   ├── registros-y-servidor.md
│   └── heredados-006.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/core_bancario_mcp/
├── contexto.py                  # mod: RegistroBloqueos, Escalamiento, RegistroEscalamientos; contador de casos
├── test_contexto.py             # mod
├── repositorio.py               # mod: Politica.limite_dias
├── test_repositorio.py          # mod
├── errores.py                   # sin cambios (usa PARAMETRO_INVALIDO y NO_ENCONTRADO)
├── identificacion.py            # mod: tipo ListaTexto junto a Texto
├── transacciones.py             # mod: fechas de solo espacios = omitidas; usa limite_dias
├── test_transacciones.py        # mod
├── bloqueo_escalamiento.py      # nuevo: bloquear_tarjeta, escalar_a_analista, registrar
├── test_bloqueo_escalamiento.py # nuevo
├── servidor.py                  # mod: registra también bloqueo_escalamiento
└── test_servidor.py             # mod: 6 herramientas
.claude/rules/herramientas-mcp.md  # mod: ListaTexto para listas
```

**Structure Decision**: un módulo por grupo de herramientas con su `registrar`
([research.md R1](research.md)).

## Orden de implementación

1. **Heredados del #6** (US4).
2. **Registros** de bloqueos y escalamientos en el `Contexto`, con tests.
3. **Bloqueo** (US1): tests y `bloquear_tarjeta`.
4. **Escalamiento** (US2): tests y `escalar_a_analista` con la validación por causa.
5. **Registro y descripciones** (US3): `ListaTexto`, `registrar`, servidor con 6 herramientas,
   tests por `list_tools`/`call_tool` y stdio; rule de MCP.
6. **Verificación**: sesión nueva con `core-bancario` (quickstart), y luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Un cliente MCP envía la lista como texto JSON (`"[\"TRX-002\"]"`) | La herramienta acepta una lista o un texto que sea una lista JSON de textos; cualquier otra cosa es `PARAMETRO_INVALIDO` (R3). Se comprueba en la sesión nueva. |
| El estado "bloqueada" de la sesión se pierde al reiniciar | Aceptado en la spec (demo); se declara en el PR. |
| El hook `Stop` del #10 necesita saber qué escalamientos hubo | La causa en lista cerrada y la respuesta estructurada se lo permiten; el registro queda en el core. |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
