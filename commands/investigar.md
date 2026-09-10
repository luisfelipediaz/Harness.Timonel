---
description: "Lanza a dora-exploradora para investigar como esta hecho algo en el repo (o para preparar un issue) y publica los hallazgos como comentario timonel:investigacion."
argument-hint: "<#issue | pregunta o tarea>"
model: haiku
---

Lanza al agente `dora-exploradora`. Comunicate en **espanol**.

```bash
[ -f .claude/timonel.config.json ] || [ -f .claude-plugin/plugin.json ] || { echo "ERROR: falta .claude/timonel.config.json. Ejecuta /timonel:onboard."; exit 1; }
```

Si `$ARGUMENTS` esta vacio: `Uso: /timonel:investigar <#issue | pregunta>`.

Invoca al agente (`subagent_type: "timonel:dora-exploradora"`) con `$ARGUMENTS`:

- `#N` → investiga lo que el issue necesita y publica `<!-- timonel:investigacion -->` en el.
- Texto libre → investiga y devuelve el reporte en chat (sin publicar); si el hallazgo merece seguimiento, sugiere `/timonel:draft`.

No investigues tu mismo; presenta el reporte de Dora tal cual.
