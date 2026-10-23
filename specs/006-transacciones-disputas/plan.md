# Implementation Plan: Transacciones y disputas: `consultar_transacciones` e `iniciar_disputa`

**Branch**: `006-transacciones-disputas` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-transacciones-disputas/spec.md` (issue #6)

## Summary

Las dos herramientas de transacciones del core, sobre la convención del #5:

- **Reglas de política en un solo lugar** (`repositorio.py`): métodos de `Politica`
  (`requiere_analista(monto)` y `cubre(transaccion, hoy)`) que usan el core ahora y el hook
  del umbral del #9 después, para que la regla no se escriba dos veces. El repositorio
  guarda su `hoy` y ofrece `tarjetas_de(cliente_id, ultimos4)`.
- **Registro de disputas** (`contexto.py`): `RegistroDisputas` en el `Contexto`, con casos
  `CASO-NNNN` en memoria y como máximo uno por transacción.
- **Herramientas** (`transacciones.py`): funciones puras `consultar_transacciones` e
  `iniciar_disputa` sobre el `Contexto`, y `registrar(servidor, contexto)` con descripciones,
  fallas inyectables y parámetros `Texto`.
- **Ajustes heredados del #5** (US5).

Decisiones en [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: `mcp[cli]` 1.30.0 y `pydantic`, ya declarados; `datetime` y `re`
de la biblioteca estándar. Sin dependencias nuevas.

**Storage**: los JSON del #4 sin cambios; los casos de disputa viven en memoria del proceso

**Testing**: `pytest`, tests junto a cada módulo, con "hoy" fijo; funciones puras con un
`Contexto` armado en el test y `list_tools`/`call_tool` para el registro

**Target Platform**: Windows, Linux y macOS; servidor por stdio

**Project Type**: servidor MCP dentro del proyecto `uv`

**Performance Goals**: el arranque sigue por debajo de 5 s (test existente)

**Constraints**:
- El monto de una disputa sale siempre del repositorio (regla 2); la herramienta no tiene
  parámetro de monto.
- Ninguna respuesta revela si una tarjeta pertenece a otro cliente (FR-005).
- Errores solo con `exito()` y `error()`; parámetros `Texto` (rule de MCP).

**Scale/Scope**: 1 módulo nuevo con su test; cambios en `repositorio.py`, `contexto.py`,
`errores.py`, `servidor.py`, `identificacion.py` y sus tests; spec del #5

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. Reglas de negocio | Regla 2: el core rechaza montos sobre $500.000 (inclusivo) tomando el monto de sus datos. Regla 5: el core rechaza lo que la política no cubre con un código propio que indica escalar. Regla 1: ambas herramientas requieren identidad; el core no la controla (sin sesiones) y la garantiza el hook del #9, que recibe lo necesario (cliente en `consultar_transacciones`, titular derivable de la transacción en `iniciar_disputa`). | ✅ |
| II. Garantías deterministas | Regla 2: el monto del argumento es **imposible por diseño** (no hay parámetro) y el umbral se verifica en el servidor como segunda defensa del hook del #9; ambos usan `Politica.requiere_analista`. Regla 5: **imposible por diseño** que se abra una disputa fuera de política (error de negocio no reintentable). La obligación de escalar después queda para el hook `Stop` (#10). | ✅ |
| III. Datos ficticios | Sin datos nuevos; tests con los datos ficticios o copias en `tmp_path`; respuestas sin datos de cliente ni tarjeta completa. | ✅ |
| IV. Spec-first | Spec aprobada (commit `6953d95`); plan y tareas antes de `src/`. | ✅ |
| V. Contrato de herramientas | Consulta sin resultados = `exito([])`; errores con tipo y código; parámetros `Texto` para que cualquier argumento responda con el contrato; descripciones según US4. | ✅ |
| VI. Tests junto al código | `test_transacciones.py` junto al módulo; tests de repositorio, contexto, servidor e identificación ampliados. | ✅ |
| VII. Simplicidad | Una sola fuente para las reglas de política; registro en memoria; sin dependencias. | ✅ |

**Resultado**: todos los gates pasan. **Re-evaluación tras la fase 1**: sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/006-transacciones-disputas/
├── spec.md · plan.md · research.md · data-model.md · quickstart.md
├── contracts/
│   ├── consultar_transacciones.md
│   ├── iniciar_disputa.md
│   ├── politica-y-registro.md
│   └── heredados-005.md
├── checklists/requirements.md
└── tasks.md                     # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
src/core_bancario_mcp/
├── repositorio.py               # mod: self.hoy, tarjetas_de, Politica.requiere_analista/cubre
├── test_repositorio.py          # mod: tests de política y tarjetas_de; "posición" calculada
├── contexto.py                  # mod: Caso y RegistroDisputas en el Contexto
├── test_contexto.py             # mod: tests del registro
├── errores.py                   # mod: FUERA_DE_POLITICA, REQUIERE_ANALISTA, DISPUTA_EXISTENTE
├── transacciones.py             # nuevo: consultar_transacciones, iniciar_disputa, registrar
├── test_transacciones.py        # nuevo
├── servidor.py                  # mod: registra también transacciones
├── test_servidor.py             # mod: 4 herramientas; call_tool de tipo incorrecto en verificar
├── identificacion.py            # mod: verificar_identidad recorta espacios
└── test_identificacion.py       # mod: casos con espacios
specs/005-identificacion-clientes/spec.md   # mod: Status Approved
```

**Structure Decision**: un módulo por grupo de herramientas con su `registrar`; las reglas de
política viven en `Politica` porque el hook del #9 importa el repositorio y no el servidor
([research.md R1 y R5](research.md)).

## Orden de implementación

1. **Heredados del #5** (US5): independientes y pequeños; primero para dejar la base limpia.
2. **Repositorio y política**: `hoy`, `tarjetas_de`, `requiere_analista` y `cubre`, con tests.
3. **Registro de disputas** en el `Contexto`, con tests.
4. **Consulta** (US1): tests y `consultar_transacciones`.
5. **Disputa** (US2 y US3): tests y `iniciar_disputa` con el orden de evaluación.
6. **Registro y descripciones** (US4): `registrar`, servidor con 4 herramientas, tests por
   `list_tools`/`call_tool` y stdio.
7. **Verificación**: sesión nueva con `core-bancario` (quickstart), y luego `/abrir-pr`.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La regla del umbral se duplica entre core y hook y diverge | Una sola implementación en `Politica.requiere_analista`, que el hook del #9 reutilizará (R5). |
| `date.fromisoformat` acepta formatos que no son año-mes-día (`20261023`, semanas ISO) | Patrón `[0-9]{4}-[0-9]{2}-[0-9]{2}` antes de convertir (R2, verificado). |
| Los casos de disputa se pierden al reiniciar el core | Aceptado en la spec (demo); se declara en la descripción del PR. |
| Un test de rango depende del reloj real | Todo cálculo usa `repositorio.hoy`, inyectado en los tests. |

## Complexity Tracking

Sin violaciones de la constitución; no aplica.
