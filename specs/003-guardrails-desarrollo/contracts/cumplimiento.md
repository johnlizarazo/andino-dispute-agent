# Contrato: auditor, skill y `/abrir-pr`

Fundamento en [research.md R9, R10 y R11](../research.md).

## `plugins/andino-guardrails/agents/auditor-cumplimiento.md`

```yaml
name: auditor-cumplimiento
description: Auditor de cumplimiento de solo lectura. Verifica que la constitución del
  proyecto (reglas de negocio, garantías deterministas y datos ficticios) esté implementada
  como se especificó, y corre los tests deterministas. Úsalo antes de abrir un PR.
tools: Read, Grep, Glob, Bash
```

`permissionMode` no se declara porque los agentes de plugins lo ignoran.

**Cuerpo:**

1. Leer `.specify/memory/constitution.md` y la spec de la rama.
2. **Principio I**: para cada regla de negocio, buscar dónde se implementa (hooks del SDK,
   servidor MCP). Si no hay código aplicable todavía, marcarla "NO APLICA". Si hay código y
   la regla no se cumple, es bloqueante.
3. **Principio II**: las reglas 1 y 2 deben tener un hook `PreToolUse` que falle cerrado; si
   dependen solo del prompt, es bloqueante.
4. **Principio III**: ningún dato con forma real ni credencial.
5. Correr `uv run pytest`, que nunca ejecuta `e2e`. Un fallo es bloqueante.
6. No editar nada ni ejecutar otros comandos que `uv run pytest`, `git diff` y `git log`.
7. Responder con el formato del [data-model](../data-model.md#veredicto-de-cumplimiento).

## `plugins/andino-guardrails/skills/revisar-cumplimiento/SKILL.md`

```yaml
name: revisar-cumplimiento
description: Revisión de cumplimiento de la constitución sobre la rama actual, en un
  contexto aislado con el auditor de cumplimiento. Devuelve APROBADO o BLOQUEADO.
argument-hint: "[ruta o módulo opcional]"
context: fork
agent: andino-guardrails:auditor-cumplimiento
background: false
allowed-tools: Read, Grep, Glob, Bash(uv run pytest *)
```

El cuerpo es un prompt autocontenido: la rama actual, la base `main`, el alcance
(`$ARGUMENTS` o todo el diff) y lo que debe auditar, porque no ve la conversación.

**Fallback (R10)**: si `agent:` no acepta el nombre con espacio de nombres, usar
`agent: general-purpose` y copiar en la skill las instrucciones del auditor.

## Cambio en `.claude/commands/abrir-pr.md`

Paso **2b** nuevo, después del 2:

> Invoca la skill `andino-guardrails:revisar-cumplimiento`. Si su respuesta empieza con
> `VEREDICTO: BLOQUEADO`, muestra los bloqueantes y **detente sin publicar nada**.

En la plantilla del comentario de avance, la sección "Revisión independiente" incluye también
el veredicto de cumplimiento.
