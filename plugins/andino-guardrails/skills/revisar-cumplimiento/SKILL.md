---
name: revisar-cumplimiento
description: Revisión de cumplimiento de la constitución sobre la rama actual, en un contexto aislado con el auditor de cumplimiento. Devuelve APROBADO o BLOQUEADO. Úsala antes de abrir un PR.
argument-hint: "[ruta o módulo opcional]"
context: fork
agent: andino-guardrails:auditor-cumplimiento
background: false
allowed-tools: Read, Grep, Glob, Bash(uv run pytest *)
---

Audita el cumplimiento de la constitución del proyecto en la rama actual de git, comparada
con la base `main`.

- **Alcance**: $ARGUMENTS. Si está vacío, audita todo el diff de la rama (`git diff
  main...HEAD`) y el código que implementa las reglas de negocio.
- **Constitución**: `.specify/memory/constitution.md`. Audita los principios I (reglas de
  negocio), II (garantías deterministas) y III (datos ficticios y credenciales).
- **Spec de la rama**: `specs/<rama>/spec.md`, si existe.
- **Tests**: ejecuta `uv run pytest` (solo deterministas; nunca `e2e`).

Las reglas sin código aplicable todavía van en NO APLICA, no como incumplimiento. Responde
exactamente con el formato de veredicto de tus instrucciones: `VEREDICTO: APROBADO |
BLOQUEADO`, BLOQUEANTES, NO BLOQUEANTES, NO APLICA y TESTS.
