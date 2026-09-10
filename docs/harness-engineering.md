# Harness engineering — principios, patrones y checklist

Referencia que consume `harness-auditor` (issue #10, 2026-09-10). Sintetiza literatura primaria y de practicantes; cada afirmacion lleva su fuente. El articulo de OpenAI se reconstruyo desde fuentes secundarias (403 al fetch directo).

## 1. Que es un harness

- OpenAI, *Harness engineering* (feb 2026, https://openai.com/index/harness-engineering/): harness = "the full environment of scaffolding, constraints, and feedback loops" alrededor del agente (estructura de repo, CI, linters, docs, tools). Escribir codigo a mano es un *failure mode*: senala una capacidad faltante del harness. El humano pasa a ser disenador del entorno. El conocimiento vive en el repo (`docs/` como system of record), no en Slack ni en cabezas. Contexto = recurso escaso: los manuales monoliticos fallan; el agente deja de seguir reglas y hace pattern matching.
- Bockeler, martinfowler.com (abr 2026, https://martinfowler.com/articles/harness-engineering.html): harness = todo salvo el modelo. Doble proposito: subir la probabilidad de acertar a la primera (**guias**, feedforward: AGENTS.md, docs, scaffolds) + loop que se autocorrige (**sensores**, feedback: linters, tests, revisores). Elementos **computacionales** (deterministas, baratos) antes que **inferenciales** (LLM-as-judge). Anti-patron: solo-feedback ("repite los mismos errores") o solo-feedforward ("codifica reglas pero nunca sabe si funcionaron"). Pregunta clave: *si los sensores nunca disparan, ¿es calidad o ceguera?*
- Anthropic, *Building effective agents* (dic 2024, https://www.anthropic.com/engineering/building-effective-agents): workflows (rutas predefinidas) vs agentes; patrones prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer. Simplicidad, transparencia, interfaz agente-computador documentada y testeada, guardrails y condiciones de parada.
- Anthropic, *Effective harnesses for long-running agents* (nov 2025, https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): cada sesion arranca sin memoria → initializer (progress file, feature list pass/fail, commit inicial) + coding agent que avanza **una feature a la vez** y deja el entorno limpio. Verificacion E2E como usuario, no solo unit tests. Git como memoria y rollback. Fallos: declarar "listo" sin verificar, perder contexto por progreso no documentado, romper lo existente.
- Anthropic, *Harness design for long-running application development* (mar 2026, https://www.anthropic.com/engineering/harness-design-long-running-apps): roles planner / generator / evaluator con rubrica explicita; *sprint contracts* (acordar "done" antes de codificar); resets completos de contexto con artefactos en archivos. "Every component in a harness encodes an assumption about what the model can't do on its own" → podar el harness cuando el modelo mejora.
- Claude Code docs (https://code.claude.com/docs/en/): CLAUDE.md siempre-on (<200 lineas, mapa no manual), `.claude/rules/` por path, skills (progressive disclosure), subagentes (aislamiento de contexto, `memory:`), hooks (deterministas: "an instruction in CLAUDE.md is a request, not a guarantee"), plugins. Disparadores: error repetido 2 veces → CLAUDE.md; prompt repetido → skill; procedimiento pegado 3 veces → skill; debe pasar siempre → hook; segundo repo → plugin. Evaluacion: `/skill-doctor`, `claude plugin eval`.
- Practicantes: Osmani (https://addyosmani.com/blog/agent-harness-engineering/) — *the ratchet*: cada fallo se convierte en regla permanente; anti-patrones AGENTS.md inflado y autoevaluacion sin verificador independiente. HumanLayer (https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) — "engineer a solution such that the agent never makes that mistake again"; subagentes como context firewall; no disenar el harness antes de observar fallos reales. Every, *Compound engineering* (https://every.to/chain-of-thought/compound-engineering-how-every-codes-with-agents) — "each feature should make the next feature easier to build"; loop Plan/Work/Review/Compound; los aprendizajes se escriben donde el proximo agente los lee. LangChain (https://www.langchain.com/blog/the-anatomy-of-an-agent-harness). Faros (https://www.faros.ai/blog/harness-engineering) — capas: orquestacion de tools, verificacion, contexto/memoria, guardrails, observabilidad; metricas por etapa. Galster et al., arXiv 2602.14690 — en 2.853 repos los context files suelen ser el unico mecanismo.

## 2. Catalogo de patrones

| Patron | Fuente |
| --- | --- |
| CLAUDE.md corto como mapa hacia `docs/` | OpenAI; Claude Code |
| `docs/` como system of record (design docs, planes, specs, referencias) | OpenAI |
| Linters / tests estructurales que codifican arquitectura y cuyo error dice como arreglarlo | OpenAI; Bockeler |
| Garbage collection: agentes que detectan drift codigo↔docs y abren PRs chicos | OpenAI |
| Observabilidad para el agente (logs, metricas, DOM) | OpenAI |
| Hooks deterministas (lint post-edit, bloquear comandos, audit log) | Claude Code; Bockeler |
| Guias vs sensores; computacional antes que inferencial | Bockeler |
| Feature list + progress file + git como memoria; una feature a la vez | Anthropic 2025 |
| Planner / generator / evaluator con rubrica y sprint contract | Anthropic 2026 |
| Verificacion E2E como usuario (browser) | Anthropic |
| Subagentes como context firewall; revisores paralelos | HumanLayer; Every |
| Progressive disclosure via skills | Claude Code |
| Ratchet / compound: la retro convierte fallos en reglas, los reviews en guidelines | Osmani; Every |
| Evals de skills (`/skill-doctor`, `evals.json`, A/B) | Claude Code |
| Plugins / harness templates por stack | Claude Code; Bockeler |
| Verificacion silenciosa (solo errores al contexto) | HumanLayer |

## 3. Anti-patrones

AGENTS.md enciclopedico ("graveyard of stale rules"); agentfiles generados por LLM sin poda; guardrails como prompt en vez de hook; solo-feedback o solo-feedforward; autoevaluacion sin evaluador independiente; declarar victoria sin verificar; one-shot de problemas grandes; instalar MCPs/skills "por si acaso"; correr toda la suite en cada sesion; disenar el harness antes de ver fallos; correcciones en el chat que no se persisten.

## 4. Checklist de madurez (15 preguntas)

1. ¿CLAUDE.md < 200 lineas y funciona como mapa? ¿Ultima poda?
2. ¿El conocimiento arquitectonico vive en artefactos versionados y referenciados?
3. ¿Las reglas arquitectonicas estan en linters/tests que corren en CI y cuyo error explica la correccion?
4. ¿Los guardrails duros ("nunca X") estan en hooks/permisos o solo en prompts?
5. ¿Hay al menos un sensor computacional por cada guia importante? ¿Alguna regla nunca se verifico?
6. ¿Cuantas veces disparan los sensores? Si nunca: ¿calidad o ceguera?
7. ¿El agente puede verificar E2E como usuario sin humano en el medio?
8. ¿Hay mecanismo formal para que cada fallo/review se convierta en regla, skill o test (ratchet)? ¿Cuantos se convirtieron el ultimo mes?
9. ¿Hay memoria entre sesiones en artefactos y el agente la lee al arrancar (reanudar)?
10. ¿"Hecho" se define antes de codificar y lo evalua un agente distinto del que genero?
11. ¿Se usan subagentes para aislar exploracion ruidosa y skills para conocimiento on-demand?
12. ¿Hay garbage collection periodica de docs, plantillas y reglas (drift, contradicciones)?
13. ¿Se miden skills/plugins (uso, costo, evals) y se eliminan los no usados?
14. ¿Cuanto se escribe a mano? ¿Cada caso se trata como gap del harness?
15. Metricas de salida: PRs por persona/dia, exito al primer intento, costo por PR, supervivencia a 30 dias, fatiga del revisor.
