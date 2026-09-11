# Changelog

## 0.6.0 — en desarrollo

- El PR es la única vía de integración en ambos perfiles: `git.integracion: "merge"` queda deprecado e ignorado desde esta versión (ya no hay `git merge --no-ff` a `main`/rama base); la apertura del PR se adelanta a la nueva **Fase 6.5**, que corre tras el review (5.5) y la retro (6) pero **antes** del DoD (Fase 7), en vez de después; `flechodiezx` ya no cierra el issue en ninguna fase — `scripts/integracion.py` arma el cuerpo del PR con la keyword real `Closes #N` y es GitHub quien cierra el issue al mergear; `scripts/estado_historia.py` reordena la fase del PR antes del DoD (`6.5 PR/Integración`) y `plantilla-hu.md`/`TAREAS` quedan alineadas con ese orden; `_tabla_dod` devuelve "DoD pendiente" en vez de "Sin DoD publicado" cuando aún no hay marcador; label nuevo `estado:en-revision` para la ventana entre PR abierto y merge; `test_consistencia.py` suma invariantes que prohíben tanto las cadenas de integración directa (`git merge --no-ff` a la base) como `gh issue close` dentro del agente (#80)
- Hook `PreToolUse` hace cumplir la política de integración por PR de la épica #79 con criterio semántico, no posicional: `scripts/guard_integracion.py` (función pura `decidir(cmd, rama, bases)` + CLI sobre el JSON del hook) bloquea en rama base todo `git merge`/`git pull` salvo `--ff-only` contra el remoto de la propia base (`origin/main`, `@{u}`), juzga `push` por el destino del refspec y bloquea siempre `gh pr merge`; `hooks/hooks.json` suma el bloque nuevo y deja el guard de `push --force` INLINE para el perfil plugin (protección incondicional que no hereda el fail-open del script) y corrige el mensaje del guard de commits que aún citaba `git merge --no-ff` (derogado por #80); `tests/test_hooks_integracion.py` cubre ~26 casos en capa pura y en caja negra contra `hooks.json` (#82)

## 0.5.0 — 2026-09-10

Épica #26: el harness aplicado a sí mismo.

- Perfil `plugin` en `flechodiezx`: HUs `mod:plugin` se implementan con el flujo completo (investigación, contrato de cambio, sub-agente único con `implement-plugin-change`, consolidación con unittest/bash -n/jq, review, retro, DoD, merge `--no-ff`); el guard del plugin bloquea commits directos en `main` (#27)
- DoD estricto: el ítem 11 con `REQUIERE CAMBIOS`, `NO_GENERADO` o `SKIPPED` es FAILED CRITICO en `tipo:hu`/`tipo:hotfix` (sin degradación a "no crítico"); el ítem 9 (retro) es CRITICO en perfil plugin; `validar_marcador.py` rechaza `decision: DONE` con `Item 11 · veredicto: NO_GENERADO|SKIPPED` y, con `perfil: plugin`, exige la fila 9 en PASSED; `flechodiezx` y `flechodiezx-hotfix` reintentan review/retro una vez y pasan `perfil` a `verify-dod` (#28)
- Smoke E2E del harness: `scripts/smoke_harness.py [--repo] [--issues 27,28] [--events-log]` mide por HU la cobertura de los 6 marcadores, labels `review:*`/`retro:*`, issues derivados de `cosechar_retro.py`, commits `#N` y eventos de `.timonel/events.log`, e imprime la tabla "disparos por sensor/hook"; evidencia real sobre #27/#28 publicada en el issue (#29)
- Métricas de disparo: `scripts/metricas_flujo.py [--events-log]` agrega al issue "Métricas de flujo" las secciones "Ratchet" (issues derivados por retro: total, por HU origen, % de HUs cerradas con retro que generaron ≥1 issue, derivados en borrador/refinados/cerrados) y "Disparos de hooks" (eventos `[gh]` y `raiz-editada` de `.timonel/events.log`, `sin datos` si falta), reutilizando `contar_eventos`/`fila_hook` de `smoke_harness.py` y la nueva `timonel_gh.origen_retro`; `/timonel:insights` pasa `--events-log` cuando el log existe (#30)
- Fase 8 con PR: `git.integracion: "pr" | "merge"` en `timonel.config.json` (default `pr` en consumidores, `merge` en el propio plugin); `flechodiezx` cierra el issue en la Fase 8 tras integrar (ya no en la Fase 7): con `pr` hace `git push -u origin hu/N-slug`, arma el comando con el nuevo `scripts/integracion.py` (`tipo_remote` GitHub/Azure DevOps → `gh pr create` / `az repos pr create`, cuerpo con link al issue, contrato y tabla DoD), comenta la URL en el issue y marca la tarea nueva `- [ ] PR abierto` (`plantilla-hu.md`, fase `8 PR/Integración` en `estado_historia.py`; ausente = SKIPPED); `/timonel:onboard` genera `git.integracion` y TIM-ADR-0002 lo documenta; `test_consistencia` exige `TAREAS` == checklist de la plantilla (#31)
- Evals del plugin: `evals/<agente-o-skill>/<caso>/prompt.md` + `graders/*.md` para `claude plugin eval` (dir default `evals/`, formato confirmado por `--help`); dos casos: `user-story-planner/hu-cumple-dor` (la HU devuelta sin publicar cumple las 7 secciones, los 6 labels y el Gherkin del DoR; rúbrica `llm` TIM-ADR-0003) y `code-review/tres-violaciones-warning` (diff TypeScript con `any`, `*ngIf` y tipo espejo `GastoResponse` → 3 WARNING, 0 CRITICO, `APROBADO CON OBSERVACIONES`); sensor `scripts/eval_dor.py` reutiliza `dor_check.check()` sobre la respuesta del planner; `test_consistencia.EvalsTests` exige que cada caso cuelgue de un agente/skill existente, tenga graders con `type` conocido y que el fixture siga sembrando las 3 violaciones; `evals/results/` ignorado; README/CLAUDE.md documentan el comando. `claude plugin eval` está en early access y no se pudo ejecutar aquí: los casos quedan listos, el score por caso sigue sin verificar (#32)

## 0.4.1 — 2026-09-10

Corrige los defectos que la re-auditoría #24 encontró en los sensores de 0.4.0 (#25).

### Corregido

- `estado_historia.py`: un issue `CLOSED` o con `timonel:dod` devuelve `REANUDAR_EN: cerrar`; una historia nueva de `alcance:backend` ya no se confunde con "en curso" por las fases N/A.
- `contrato_check.py`: recorta query string y fragmento antes de comparar rutas (falsos FAILED en Organigrama).
- `validar_marcador.py` contrato `dod`: exige las 11 filas, la línea `Item 11 · veredicto:` y, con `decision: DONE`, las filas críticas 1, 2, 4, 8 y 11 en PASSED (el code review nunca es SKIPPED en `tipo:hu`/`hotfix`).
- Validador invocado también para `contrato-api` (flechodiezx), `investigacion` (dora-exploradora), `refinamiento` (backlog-refiner) y `harness-audit` (harness-auditor); `test_consistencia` exige un invocador por contrato y que cada script esté documentado en CLAUDE.md/README.
- CLAUDE.md: tabla de `scripts/`, `hooks/` y CI al día.

## 0.4.0 — 2026-09-10

Épica #12: cierra los gaps 1–9, 13, 14 y 15 de la auditoría #11 (score 4/10). El loop se cierra: cada fase produce un artefacto que la siguiente lee y verifica.

### Añadido

- **Ratchet** (#13): `scripts/cosechar_retro.py` convierte "Mejoras sugeridas" y "Harness engineering" de cada retro en issues `estado:borrador` (en el consumidor o en `timonel.repo`), idempotente, y anota "Issues derivados" en la retro. `generate-retro` lo ejecuta siempre.
- **CI** (#14): `.github/workflows/ci.yml` corre unittest, `bash -n`, `jq`, labels dry-run y, en PRs, exige `#issue` en cada commit. `tests/test_consistencia.py` detecta drift: agentes referenciados inexistentes, skills declarados inexistentes, marcadores sin documentar o sin contrato en el validador, versión ≠ CHANGELOG, labels documentados sin script.
- **Guardrails en hooks** (#15): en consumidores, `PreToolUse` bloquea `git commit` en ramas base (`git.baseBranches`, `git.protectBase`), bloquea `git push --force`, y en ramas `hu/N-*` exige `#N` en el mensaje; `PostToolUse` avisa y loguea cuando se edita `modelos.path`, `api.moduleFile` o un `routesFile`.
- **Reanudación** (#16): `scripts/estado_historia.py N` deduce la fase pendiente desde `## Tareas`, marcadores y rama local; `flechodiezx` y `flechodiezx-hotfix` arrancan con ella (Fase 0.5).
- **Validador de marcadores** (#17): `scripts/validar_marcador.py` con contrato por tipo (claves YAML, valores, secciones, tabla de hallazgos, coherencia criticos/warnings/bloquea_dod y estimado/real/precisión). Lo corren `code-review`, `generate-retro`, `verify-dod`, `consolidate-story` antes de publicar.
- **DoR único** (#18): `scripts/dor_check.py N [--para implementar]` implementa TIM-ADR-0003; lo usan `user-story-planner` (antes de `estado:listo`), `backlog-refiner`, `/timonel:implement`, `flechodiezx` y `flechodiezx-hotfix`.
- **Insights con lector** (#19): planner, refiner y Dora leen "Errores recurrentes" / "Calibración" de los issues `insights` al arrancar.
- **Contrato vs código** (#20): `scripts/contrato_check.py N` contrasta `timonel:contrato-api` con los `@Controller/@Get…` del consumidor; `code-review` pega la tabla en Ficha.
- **Aviso de versión** (#22): `SessionStart` compara la versión instalada con el último release (cache 1 día).
- **Métricas de flujo** (#23): `scripts/metricas_flujo.py [--publish]` (cobertura de artefactos, review a la primera, precisión, lead time, backlog por estado); `/timonel:insights` lo publica.

### Cambiado

- `code-review` (#21): las convenciones se leen del `CLAUDE.md` / `.claude/rules/` del consumidor; las de Bitákora pasan a `heuristics/angular/convenciones-bitakora.md`.
- Config del consumidor: `git.baseBranches`, `git.protectBase`, `timonel.repo` (TIM-ADR-0002).
- `generate-retro` y `code-review` reportan `RETRO_VALIDA` / `REVIEW_VALIDO`, `ISSUES_DERIVADOS`, `CONTRATO_CHECK`.

## 0.3.0 — 2026-09-10

Épica #4. Incorpora lo rescatable del harness de `Cosmos.BuildingBlocks` y formaliza la gobernanza del plugin.

### Añadido

- Agente **`dora-exploradora`** (#7) y skill `investigar`: investigación acotada del código y docs antes del contrato API; publica `<!-- timonel:investigacion -->` y reutiliza investigaciones previas del módulo. Nueva Fase 1.5 en `flechodiezx` (y ligera en `flechodiezx-hotfix`); comando `/timonel:investigar`.
- Agente **`harness-auditor`** (#8) y comando `/timonel:audit`: clasifica artefactos y transiciones del flujo en HARNESS / SEMI / AD-HOC, persiste issue `harness-audit` y compara con el anterior. Label `harness-audit`.
- Sección **Harness engineering** obligatoria en la retro (#9): patrón repetitivo, proceso manual 2+, contexto faltante, error prevenible.
- Regla de alcance en `implement-backend-story` / `implement-frontend-story` (#9): no tocar archivos fuera de la tarea.
- **Gobernanza** (#5, TIM-ADR-0005): todo cambio del plugin nace en un issue del repo; `.githooks/commit-msg` + `scripts/install-git-hooks.sh` y hook `PreToolUse` bloquean commits sin `#N`. Los comandos funcionan dentro del repo del plugin usando `gh repo view` como repo de issues.

### Cambiado

- Ejecutores renombrados (#6): `story-executor` → **`flechodiezx`**, `hotfix-executor` → **`flechodiezx-hotfix`**.

## 0.2.0 — 2026-09-10

### Añadido

- Skill `interrogame` (rescatado de `Bitakora.MonoRepo.Portal` rama `feature/fal/notificaciones`): entrevista exhaustiva una pregunta a la vez con respuesta recomendada, con bloques A–J para diseño de software.
- `sdd-planner` precarga `interrogame`, explora el código antes de preguntar y lee el skill `*-estructura` del consumidor si existe.
- Plantilla de SDD ampliada a 15 secciones fusionando el agente `sdd-specs` del Portal (RF con actor/precondición/flujo, RNF en tabla, archivos nuevos por capa, seguridad, plan de despliegue, criterios de aceptación, dudas abiertas con responsable).

### Notas

- `portal-estructura` no entra al plugin: es específico del Portal y se restauró en su `.claude/skills/`.

## 0.1.0 — 2026-09-09

Extracción del harness SDD de `Bitakora.MonoRepo.Portal/.claude` como plugin (TIM-ADR-0004).

### Añadido

- Plugin `timonel` con marketplace propio (`luisfelipediaz-harness`).
- Backlog en GitHub Issues: jerarquía `tipo:sdd → tipo:epica → tipo:hu` con sub-issues nativos, labels facetados, comentarios con marcador para contrato API, consolidación, review, retro, DoD y refinamiento (TIM-ADR-0001).
- Configuración del consumidor `.claude/timonel.config.json` y comando `/timonel:onboard` (TIM-ADR-0002).
- Definition of Ready por tipo de issue y validación en `/timonel:implement` y `/timonel:hotfix` (TIM-ADR-0003).
- Agente nuevo `sdd-planner`: SDD como issue, versionado en el mismo issue, derivación de épicas.
- Comandos `sdd`, `plan`, `refine`, `draft`, `implement`, `hotfix`, `backlog`, `insights`, `migrate`.
- Skill `github-issues` con plantillas (HU, hotfix, épica, SDD), formato de marcadores y esquema de labels.
- Scripts `retro_query`, `retro_distill`, `review_query`, `review_distill` leyendo de GitHub; `--publish` hace upsert de issues `insights`.
- `migrate_backlog.py`: importa `docs/user-stories` (incluidas `completadas.md`, tachadas y retros/reviews) de forma idempotente.
- `setup-github-labels.sh` idempotente con `--dry-run` y `--prune-defaults`.
- Heurísticas de código incluidas en el plugin (`heuristics/`).
- Tests `unittest` para parsers, destilado y migración.

### Cambiado respecto al harness original

- Agentes y skills parametrizados por config (sin `apps/client`, alias ni `app-routing.module.ts` hardcodeados; soporte para varias apps frontend).
- `HU-XXX` reemplazado por el número de issue; MoSCoW/SP/prioridad pasan a labels.
- DoD item 8: "marcada en BACKLOG" → "checklist `## Tareas` completo"; DoD `DONE` cierra el issue.
- `code-review`, `generate-retro`, `verify-dod`, `consolidate-story` publican en el issue en vez de escribir archivos.
