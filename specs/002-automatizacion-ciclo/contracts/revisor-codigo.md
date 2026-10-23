# Contrato: subagente `revisor-codigo`

Archivo: `.claude/agents/revisor-codigo.md`. Fundamento en [research.md R1 y R3](../research.md).

## Frontmatter

```yaml
name: revisor-codigo
description: Revisor independiente de solo lectura. Compara el diff de la rama de un ticket
  contra su spec y reporta hallazgos bloqueantes y no bloqueantes. Úsalo antes de abrir un PR.
tools: Read, Grep, Glob, Bash
permissionMode: dontAsk
```

## Restricción de Bash (declarativa)

En `.claude/settings.json`:

```json
"permissions": {
  "allow": ["Bash(git diff *)", "Bash(git log *)", "Bash(git show *)"]
}
```

Con `dontAsk`, cualquier otro comando se niega sin preguntar.

**Fallback (R3)**: si la verificación muestra que `dontAsk` no se comporta así, se agrega un
hook `PreToolUse` con matcher `Bash` en el frontmatter, que solo deje pasar esos tres
comandos.

## Entrada (mensaje de delegación)

- La rama y su base (`main`).
- La ruta de `specs/NNN-slug/` (spec, plan, tareas y contratos).

El revisor no recibe la conversación: todo lo que necesita está en esos archivos y en el
diff.

## Qué revisa

1. Que cada cambio del diff responda a un requisito o tarea de la spec, y que no falten
   requisitos marcados como hechos en `tasks.md`.
2. Que los archivos coincidan con sus contratos, si existen.
3. Que se cumplan los principios III (credenciales y datos) y VI (tests junto al código) de
   la constitución. Los principios I y II quedan para `revisar-cumplimiento` (issue #3).

## Salida (formato fijo)

```text
VEREDICTO: APROBADO | BLOQUEADO

BLOQUEANTES:
- <archivo>:<línea> — <descripción> (<FR-xxx o principio>)

NO BLOQUEANTES:
- <archivo>:<línea> — <descripción>

REQUISITOS SIN EVIDENCIA EN EL REPO:
- <FR-xxx> — <motivo>
```

`VEREDICTO: BLOQUEADO` si y solo si hay al menos un bloqueante. El revisor no edita nada.
