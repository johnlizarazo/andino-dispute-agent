# Agente de disputas de Banco Andino

Banco Andino es un banco **ficticio** y todos los datos de esta demostración son ficticios.

El agente atiende disputas de transacciones y contracargos: identifica al cliente, verifica su
identidad, revisa sus cobros, inicia disputas, bloquea tarjetas y escala a un analista cuando
hace falta. Si quieres hablar con una persona, solo pídelo.

## Cómo leer la conversación

Además de los mensajes del **Agente**, verás mensajes de **Evento**: muestran lo que realmente
ocurrió en el sistema del banco, no lo que dice el agente.

- ✅ **Éxito**: la operación se realizó (identidad verificada, tarjeta bloqueada, disputa
  iniciada, caso escalado a un analista, análisis de transacciones realizado).
- ⛔ **Negado**: un control del banco impidió la operación (por ejemplo, identidad sin
  verificar o un monto que requiere un analista).
- ⚠️ **Falla**: la operación no se pudo completar y no se da por hecha.
