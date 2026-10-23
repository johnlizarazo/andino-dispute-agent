# Contrato: comentarios de avance

Fundamento en [research.md R7 y R9](../research.md). El marcador de la primera línea sirve
para detectar duplicados.

## Inicio (lo publica `siguiente-ticket`)

```markdown
**Inicio del ticket.** Movido a *In Progress* por Claude Code (skill `siguiente-ticket`).

- Rama: `NNN-slug`
- Siguiente paso: revisión humana de `specs/NNN-slug/spec.md` (punto de control 1).
```

## PR abierto (lo publica `/abrir-pr`)

```markdown
**PR abierto: #<PR>.** El issue pasa a *In Review*.

### Qué se especificó
<historias de usuario y número de requisitos, con enlace a spec.md en la rama>

### Qué se decidió
<decisiones principales, con enlace a research.md>

**Ajustes en los puntos de control**: <lista, o "Sin ajustes">

### Revisión independiente
<veredicto de revisor-codigo y conteo de no bloqueantes>

### Qué quedó pendiente
<lista, o "Nada">
```

Los enlaces apuntan a la rama del ticket. Al fusionar, el contenido queda igual en `main`.
