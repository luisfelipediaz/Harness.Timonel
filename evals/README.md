# Evals del plugin

Casos de `claude plugin eval` (issue #32), uno por agente/skill: `evals/<agente-o-skill>/<caso>/prompt.md` + `graders/*.md`. `prompt.md` lleva frontmatter (`name`, `tags`, `runs`, `max_turns`) y su body es el prompt; cada grader es un `.md` con frontmatter `type: regex|llm|tool_used|file_exists|tool_order|baseline` (`regex`: `pattern`, `flags`, `match`, `target`; `llm`: el body es la rúbrica, score 0..1). No se usan campos no confirmados por `claude plugin eval --help` (p. ej. `weight`): si el esquema real los acepta, agregarlos solo en el frontmatter de los graders.

- `user-story-planner/hu-cumple-dor/`: la HU que devuelve el planner cumple el DoR (TIM-ADR-0003).
- `code-review/tres-violaciones-warning/`: el skill `code-review` detecta `any`, `*ngIf` y un tipo espejo como WARNING, sin inventar CRITICO.

## Correr los evals

Desde la raíz del plugin:

```bash
claude plugin eval . --no-publish
claude plugin eval . --no-publish --case 'code-review/*' --runs 1 --threshold 0.8 --json evals/results/ultimo.json
```

**Estado**: `claude plugin eval` está en early access; en esta máquina devuelve `plugin eval is currently in early access` (exit 1). Si eso pasa, los casos quedan listos para correr cuando se habilite.

## DoR del caso del planner

El grader `llm`/`regex` no valida el DoR completo; para eso, pasa el último mensaje del caso a:

```bash
python3 scripts/eval_dor.py respuesta.md
```
