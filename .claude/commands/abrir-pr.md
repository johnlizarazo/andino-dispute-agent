---
description: Revisa la rama del ticket con revisor-codigo y, si no hay bloqueantes, publica la rama, crea el PR con Closes #N, mueve el issue a In Review y comenta el avance.
argument-hint: "[notas opcionales para el comentario]"
disable-model-invocation: true
allowed-tools:
  - mcp__github__issue_read
  - mcp__github__list_pull_requests
  - mcp__github__projects_write
  - mcp__github__add_issue_comment
  - Bash(git status *)
---

Abre el pull request del ticket actual siguiendo estos pasos **en orden**. Si un paso dice
"detente", explica por qué y no sigues con los demás. `git push` y la creación del PR no
están pre-aprobados a propósito: piden confirmación al desarrollador.

Repositorio: `johnlizarazo/andino-dispute-agent`. Project: número 1 del usuario
`johnlizarazo`. Notas del desarrollador: $ARGUMENTS

## 1. Precondiciones

- La rama actual sigue el patrón `NNN-slug` y no es `main`.
- `git status --porcelain` está vacío.
- Existe `specs/<rama>/spec.md` y contiene `**Issue**: #N`.
- El issue `#N` existe y está abierto (`issue_read`), y su título coincide con el título de
  la spec (`# Feature Specification: <título>`).

Si falla cualquiera, detente.

## 2. Revisión independiente

Delega en el subagente `revisor-codigo` con este mensaje: la rama, la base `main` y la
carpeta `specs/<rama>/`. No le pases nada de esta conversación. Si su respuesta empieza con
`VEREDICTO: BLOQUEADO`, muestra los bloqueantes y **detente sin publicar nada**.

## 3. Publicar la rama

`git push -u origin <rama>` (pide confirmación).

## 4. Pull request

Con `list_pull_requests` (`head: johnlizarazo:<rama>`, estado abierto), busca un PR existente.
Si lo hay, reutilízalo. Si no, créalo contra `main` (pide confirmación) con:

- **Título**: el del issue.
- **Cuerpo**: `Closes #N`, qué entrega, cómo se verificó, el resultado de la revisión
  (veredicto y no bloqueantes) y los límites conocidos. Termina con
  `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## 5. Estado

Con `projects_write` (`update_project_item`, resolviendo el ítem por `item_owner`,
`item_repo` e `issue_number`), mueve el issue a *In Review*. Si ya está ahí, omítelo.

## 6. Comentario de avance

Lee los comentarios del issue (`issue_read`, `get_comments`). Si ninguno empieza con
`**PR abierto: #<PR>.**`, publica uno con `add_issue_comment` usando esta plantilla:

```markdown
**PR abierto: #<PR>.** El issue pasa a *In Review*.

### Qué se especificó
<historias de usuario y número de requisitos, con enlace a spec.md en la rama>

### Qué se decidió
<decisiones principales, con enlace a research.md en la rama>

**Ajustes en los puntos de control**: <cambios pedidos en la revisión de spec, plan o
analyze, tomados de esta conversación y de los commits de la rama; o "Sin ajustes">

### Revisión independiente
<veredicto de revisor-codigo y conteo de no bloqueantes>

### Qué quedó pendiente
<lista, o "Nada">
```

Si las notas del desarrollador no están vacías, inclúyelas en la sección que corresponda.

## 7. Informe final

Muestra la URL del PR, el estado del issue y recuerda que el merge lo hace el desarrollador
y es la aprobación final. Al fusionar, el Project pasa el issue a *Done* solo.
