# Data Model: Automatización del ciclo en GitHub

No hay datos de negocio. Las entidades son las del ciclo de un ticket. Todas viven en GitHub
o en git.

## Ticket (issue de GitHub)

- **Campos usados**:
  - `number`, `title`, `body`, `state` (open o closed).
  - Ítem del Project con `Status`.
  - La sección "**Depende de**" del cuerpo: una lista de `#N` o `—`.
- **Validación**:
  - Elegible para `siguiente-ticket` si `Status = Todo`, `state = open` y todas sus
    dependencias están cerradas.
  - Si el número indicado está cerrado, no se trabaja.
- **Transiciones de estado** (campo `Status` del Project):

  | De | A | Quién |
  |---|---|---|
  | *Todo* | *In Progress* | `siguiente-ticket` |
  | *In Progress* | *In Review* | `/abrir-pr` |
  | *In Review* | *Done* | Regla integrada "Item closed", al fusionar el PR con `Closes #N` |

  Ninguna otra regla del Project mueve el estado: "Pull request linked to issue" está
  desactivada.

## Rama de ticket

- **Formato**: `NNN-slug`.
  - `NNN`: el siguiente número libre en `specs/`, con 3 dígitos.
  - `slug`: 2 a 4 palabras del título, en minúsculas, sin tildes y separadas por guiones.
- **Relación**: 1 rama ↔ 1 carpeta `specs/NNN-slug/` ↔ 1 issue (`Issue: #N` en `spec.md`).
- **Validación**: `/abrir-pr` se niega a correr si la rama no sigue el formato o si su
  `spec.md` no enlaza un issue.

## Hallazgo de revisión

- **Campos**: `severidad` (`BLOQUEANTE` o `NO BLOQUEANTE`), `archivo`, `línea`,
  `descripción`, `requisito` (FR-xxx o principio de la constitución, si aplica).
- **Regla**: un solo `BLOQUEANTE` detiene `/abrir-pr`.
- **Formato**: ver [contracts/revisor-codigo.md](contracts/revisor-codigo.md).

## Comentario de avance

- **Tipos**: `inicio` y `pr`.
- **Identificación**: cada uno empieza con un marcador fijo. Sirve para la idempotencia
  (R7).
- **Plantillas**: ver [contracts/comentarios.md](contracts/comentarios.md).
