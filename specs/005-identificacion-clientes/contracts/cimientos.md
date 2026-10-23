# Contrato: cimientos heredados del #4

Fundamento en [research.md R7](../research.md). Amplía los contratos
[repositorio](../../004-datos-errores-fallas/contracts/repositorio.md) y
[fallas](../../004-datos-errores-fallas/contracts/fallas.md) del #4.

## Repositorio (`DatosInvalidosError`, mensaje con archivo y registro)

| Caso | Ejemplo |
|---|---|
| Archivo que no es lista (u objeto, para políticas) | `clientes.json` con un objeto |
| Registro que no es objeto | un número dentro de la lista |
| Texto esperado y llega otro tipo | `documento: 1`, `ultimos4: 4821` |
| Entero esperado y llega otro tipo | `monto: 1.5`, `monto: true`, `dias_atras: "1"` |
| Estado de tarjeta fuera de {activa, bloqueada} | `estado: "perdida"` |
| País que no es `^[A-Z]{2}$` | `pais: "COL"` |
| `dato_verificacion` que no es `^[0-9]{4}$` | `"19x7"` |
| Dígitos no ASCII en patrones | `ultimos4` con dígitos arábigo-índicos |

## Fallas (`ConfiguracionFallasError`)

| Caso | Ejemplo |
|---|---|
| Dígitos no ASCII | `op:٣` |
| Signos | `op:+1`, `op:--1` |
| Operación repetida | `op:1,op:2` |
| Operación fuera de `^[a-z0-9_]+$` | `Op Mal:1` |

Los casos válidos del #4 siguen funcionando igual.
