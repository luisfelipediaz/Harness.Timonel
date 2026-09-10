---
description: "Audita la madurez del harness (del consumidor o del propio plugin) con harness-auditor y persiste el resultado como issue harness-audit comparado con el anterior."
argument-hint: "[consumidor | plugin] [area]"
model: haiku
---

Lanza al agente `harness-auditor`. Comunicate en **espanol**.

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

Invoca al agente (`subagent_type: "timonel:harness-auditor"`) con `$ARGUMENTS` como alcance (`consumidor` por defecto si hay `timonel.config.json`; `plugin` si estas en el repo de Timonel). Un `area` opcional (ej. `retro`, `planificacion`, `CI`) acota el inventario.

No audites tu mismo. Presenta el score, los 3 gaps principales y la pregunta final del agente.
