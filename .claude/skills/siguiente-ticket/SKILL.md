---
name: siguiente-ticket
description: Toma el siguiente issue del Project (o el indicado), lo mueve a In Progress, comenta el inicio, crea la rama NNN-slug y genera su spec con speckit-specify. Se detiene en la spec para revisión humana.
argument-hint: "[número de issue opcional]"
allowed-tools:
  - mcp__github__projects_list
  - mcp__github__projects_write
  - mcp__github__issue_read
  - mcp__github__add_issue_comment
  - Bash(git status *)
  - Bash(git checkout -b *)
---

Inicia un ticket siguiendo estos pasos **en orden**. Si un paso dice "detente", explica por
qué y no cambias nada más. Antes de cada acción visible, comprueba si ya está hecha y, si lo
está, omítela e infórmalo: un reintento nunca duplica movimientos ni comentarios.

Repositorio: `johnlizarazo/andino-dispute-agent`. Project: número 1 del usuario
`johnlizarazo`. Argumento: $ARGUMENTS

## 1. Árbol limpio

`git status --porcelain` debe estar vacío y la rama actual debe ser `main` (actualizada).
Si no, detente.

## 2. Elegir el issue

- **Con argumento** (un número, con o sin `#`): usa ese issue (`issue_read`). Si está
  cerrado, detente. Si ya está en *In Progress*, avisa y pide confirmación antes de seguir.
- **Sin argumento**: lista los ítems del Project con `projects_list`
  (`list_project_items`, `field_names: ["Status"]`, paginando hasta el final). Quédate con
  los issues abiertos en *Todo*, ordénalos por número y toma el primero cuya sección
  **Depende de** del cuerpo tenga todos sus `#N` cerrados (`—` significa sin dependencias).
  Di cuál elegiste y por qué saltaste los anteriores.
- **Sin elegibles**: infórmalo y detente.

## 3. Mover a *In Progress*

Con `projects_write` (`update_project_item`, resolviendo el ítem por `item_owner`,
`item_repo` e `issue_number`), pon `Status` en *In Progress*. Si ya está así, omítelo. Si el
issue no está en el Project, agrégalo antes con `add_project_item`.

## 4. Rama

- `NNN`: el siguiente número libre de 3 dígitos según las carpetas de `specs/`.
- `slug`: 2 a 4 palabras significativas del título, en minúsculas, sin tildes, unidas
  con guiones.
- Si ya existe una rama local que termina en el mismo `slug` y su `specs/<rama>/spec.md`
  enlaza este issue, cámbiate a ella. Si existe y enlaza otro issue, detente.
- Si no existe: `git checkout -b NNN-slug`.

## 5. Comentario de inicio

Lee los comentarios del issue (`issue_read`, `get_comments`). Si ninguno empieza con
`**Inicio del ticket.**`, publica con `add_issue_comment`:

```markdown
**Inicio del ticket.** Movido a *In Progress* por Claude Code (skill `siguiente-ticket`).

- Rama: `NNN-slug`
- Siguiente paso: revisión humana de `specs/NNN-slug/spec.md` (punto de control 1).
```

## 6. Spec

Invoca la skill `speckit-specify` con este insumo:

- `Issue: #N (https://github.com/johnlizarazo/andino-dispute-agent/issues/N)`.
- Rama y carpeta: `NNN-slug` / `specs/NNN-slug`.
- El título y el cuerpo completos del issue.
- Dos exigencias para la spec: el título debe ser exactamente
  `# Feature Specification: <título del issue>`, y debajo de **Created** debe ir la línea
  `**Issue**: #N (<url>)`. `/abrir-pr` depende de ambas. Redactarla en español.

## 7. Parar

Muestra la ruta de la spec y pide al desarrollador que la revise (punto de control 1).
**No** ejecutes `speckit-plan`, `speckit-tasks` ni `speckit-implement`.
