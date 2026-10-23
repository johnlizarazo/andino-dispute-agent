# Contrato: comando `/abrir-pr`

Archivo: `.claude/commands/abrir-pr.md`. Fundamento en
[research.md R1, R4, R7 y R8](../research.md).

## Frontmatter

```yaml
description: Revisa la rama del ticket con revisor-codigo y, si no hay bloqueantes, publica
  la rama, crea el PR con Closes #N, mueve el issue a In Review y comenta el avance.
argument-hint: "[notas opcionales para el comentario]"
disable-model-invocation: true
allowed-tools:
  - mcp__github__issue_read
  - mcp__github__list_pull_requests
  - mcp__github__create_pull_request
  - mcp__github__projects_write
  - mcp__github__add_issue_comment
  - Bash(git status *)
  - Bash(git push *)
```

`disable-model-invocation: true` hace que solo el desarrollador pueda dispararlo (publica en
GitHub).

## Pasos obligatorios, en orden

1. **Precondiciones**:
   - La rama sigue el patrón `NNN-slug` y no es `main`.
   - El árbol está limpio.
   - Existe `specs/NNN-slug/spec.md` con `Issue: #N`.
   - El issue `#N` existe, está abierto y su título concuerda con la spec.

   Si falla cualquiera, detenerse y explicar.
2. **Revisión**: delegar en el subagente `revisor-codigo` con la rama y la carpeta de la
   spec. Si el veredicto es `BLOQUEADO`, mostrar los bloqueantes y **detenerse sin
   publicar**.
3. **Publicar la rama**: `git push -u origin NNN-slug`.
4. **PR**: si `list_pull_requests` ya muestra un PR abierto para la rama, reutilizarlo. Si
   no, crear uno contra `main`:
   - Título descriptivo del ticket.
   - Cuerpo con `Closes #N`, resumen, verificación, resultado de la revisión y límites.
5. **Estado**: mover el issue a *In Review*. Si ya lo está, omitir.
6. **Comentario de avance**: si no existe uno con el marcador de PR, publicarlo con la
   plantilla de [comentarios.md](comentarios.md), incluidos los ajustes de los puntos de
   control (y `$ARGUMENTS` si se pasaron notas).
7. **Informar**: URL del PR, estado del issue y recordatorio de que el merge es la
   aprobación final.

## Extensión prevista (issue #3)

Entre los pasos 2 y 3 se agregará la invocación de `revisar-cumplimiento`. Un bloqueante de
cumplimiento también detendrá el comando.
