# Contrato: skill `siguiente-ticket`

Archivo: `.claude/skills/siguiente-ticket/SKILL.md`. Fundamento en
[research.md R1, R2, R5, R6 y R7](../research.md).

## Frontmatter

```yaml
name: siguiente-ticket
description: Toma el siguiente issue del Project (o el indicado), lo mueve a In Progress,
  comenta el inicio, crea la rama NNN-slug y genera su spec con speckit-specify. Se detiene
  en la spec para revisión humana.
argument-hint: "[número de issue opcional]"
allowed-tools:
  - mcp__github__projects_list
  - mcp__github__projects_write
  - mcp__github__issue_read
  - mcp__github__add_issue_comment
  - Bash(git status *)
  - Bash(git checkout -b *)
```

Sin `context: fork`: la spec debe quedar en la sesión para el punto de control.

## Entradas

- `$ARGUMENTS`: vacío, o un número de issue (con o sin `#`).

## Pasos obligatorios, en orden

1. **Árbol limpio**: `git status --porcelain` vacío y rama actual `main`. Si no se cumple,
   detenerse y explicar.
2. **Elegir el issue**:
   - **Con argumento:** ese issue. Si está cerrado, detenerse. Si ya está en *In Progress*,
     pedir confirmación.
   - **Sin argumento:** listar los ítems del Project 1 con `Status`, filtrar `Todo`, ordenar
     por número y tomar el primero cuya sección "Depende de" tenga todos sus issues
     cerrados. Informar cuál y por qué se saltaron los anteriores.
   - **Sin elegibles:** informar y detenerse sin cambios.
3. **Mover a *In Progress***: `projects_write` con `update_project_item`, resolviendo el
   ítem por número de issue. Si ya está en ese estado, omitir. Si el ítem no existe,
   agregarlo con `add_project_item` antes.
4. **Rama**:
   - Calcular `NNN` como el siguiente número libre en `specs/` y el `slug` desde el título.
   - Si la rama ya existe y su `spec.md` enlaza este issue, reutilizarla; si no, detenerse.
   - Si no existe, `git checkout -b NNN-slug`.
5. **Comentario de inicio**: si no existe ya un comentario que empiece con el marcador de
   inicio, publicarlo con la plantilla de [comentarios.md](comentarios.md).
6. **Spec**: invocar la skill `speckit-specify` pasándole `Issue: #N (url)`, la rama, el
   título y el cuerpo del issue.
7. **Parar**: presentar la ruta de la spec y pedir revisión. **No** ejecutar
   `speckit-plan`, `speckit-tasks` ni `speckit-implement`.

## Salidas observables

- **En GitHub:** el issue está en *In Progress* y tiene un comentario de inicio.
- **En git:** existe la rama `NNN-slug` y `specs/NNN-slug/spec.md` contiene `Issue: #N`.
- **En la sesión:** un mensaje final con la spec y la pregunta de revisión.
