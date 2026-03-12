# REGISTRY: Taxonomía de Agentes PIV/OAC v3.0
> Referencia completa: tipos de agentes, ciclo de vida, modelo, estructura de ramas y criterios de creación/destrucción.

---

## Jerarquía

```
Nivel 0  →  Master Orchestrator
Nivel 1  →  Entorno de Control (Security + Audit + Coherence + extras)
             + Domain Orchestrators
Nivel 2  →  Specialist Agents (Expertos: N por tarea, paralelos en subramas)
```

---

## Estructura de Ramas por Tarea

```
main
└── feature/<tarea>                        ← creada por Domain Orchestrator
    ├── feature/<tarea>/<experto-1>        ← creada por Domain Orchestrator
    ├── feature/<tarea>/<experto-2>        ← creada por Domain Orchestrator (si aplica)
    └── feature/<tarea>/<experto-N>        ← tantas como expertos asigne el orquestador

Worktrees:
./worktrees/<tarea>/
./worktrees/<tarea>/<experto-1>/
./worktrees/<tarea>/<experto-2>/
```

**Flujo de merge:**
```
feature/<tarea>/<experto-N>  →(Coherence aprueba)→  feature/<tarea>
feature/<tarea>              →(Security+Audit aprueban)→  main
```

---

## Catálogo de Agentes

### Nivel 0 — Master Orchestrator

| Campo | Valor |
|---|---|
| Modelo | claude-opus-4-6 |
| Ciclo de vida | Persistente (toda la tarea Nivel 2) |
| Responsabilidad | Construir grafo de dependencias, determinar equipo, coordinar entorno de control |
| Crea | Entorno de control completo + Domain Orchestrators |
| Contexto que carga | `skills/orchestration.md` + `project_spec.md` (RF + stack) + estado del grafo |
| Ver definición | `registry/orchestrator.md` |

---

### Nivel 1 — Entorno de Control (Superagentes Permanentes)

#### SecurityAgent
| Campo | Valor |
|---|---|
| Modelo | claude-opus-4-6 |
| Ciclo de vida | Persistente (toda la tarea) |
| Responsabilidad | Gate de seguridad pre-código y post-implementación |
| Capacidad | Veto inmediato sobre cualquier plan o acción |
| Contexto | Plan/código a revisar + `skills/backend-security.md` |
| Ver definición | `registry/security_auditor.md` |

#### AuditAgent
| Campo | Valor |
|---|---|
| Modelo | claude-sonnet-4-6 |
| Ciclo de vida | Persistente (toda la tarea) |
| Responsabilidad | Trazabilidad a spec, veracidad, logs de cierre, engram |
| Escritura exclusiva | `engram/session_learning.md` y `/logs_veracidad/` |
| Contexto | Plan/código a auditar + `project_spec.md` |
| Ver definición | `registry/security_auditor.md` |

#### CoherenceAgent
| Campo | Valor |
|---|---|
| Modelo | claude-sonnet-4-6 |
| Ciclo de vida | Siempre creado con el entorno de control. Monitorización activa solo cuando hay ≥ 2 expertos paralelos en una tarea. |
| Responsabilidad | Detectar y resolver conflictos entre expertos paralelos en subramas |
| Capacidad | Veto sobre merge de subramas a rama de tarea |
| Contexto | Diffs entre subramas activas (no el código completo) |
| Contribuye al engram | Resumen de conflictos detectados y resoluciones aplicadas |

> Protocolo completo en `registry/coherence_agent.md`.

---

### Nivel 1 — Domain Orchestrators

#### BackendOrchestrator (ejemplo)
| Campo | Valor |
|---|---|
| Modelo | claude-sonnet-4-6 |
| Ciclo de vida | Persistente por dominio |
| Responsabilidad | Planificar dominio, crear rama de tarea, crear expertos y sus subramas |
| Contexto | `skills/layered-architecture.md` + `skills/backend-security.md` + RF del dominio + grafo |
| Crea | Rama `feature/<tarea>` + subramas `feature/<tarea>/<experto-N>` + worktrees |

*(El Master crea un Domain Orchestrator por cada dominio identificado en el grafo)*

---

### Nivel 2 — Specialist Agents (Expertos)

#### Persistentes (viven durante el dominio)

| Agente | Modelo | Cuándo se crea | Cuándo se destruye | Skill |
|---|---|---|---|---|
| DBArchitect | claude-sonnet-4-6 | Diseño de esquemas no trivial | Diseño completado y aprobado | `skills/layered-architecture.md` |
| APIDesigner | claude-sonnet-4-6 | Contratos de interfaz nuevos | Contratos definidos y aprobados | `skills/api-design.md` |

#### Temporales (una tarea atómica, se destruyen al reportar)

| Agente | Modelo | Tarea | Input | Output |
|---|---|---|---|---|
| CodeImplementer | claude-sonnet-4-6 / claude-haiku-4-5 | Implementar función/módulo | Spec atómica + `skills/layered-architecture.md` | Código |
| SchemaValidator | claude-haiku-4-5 | Validar schema o contrato | Schema + `skills/api-design.md` | VÁLIDO/INVÁLIDO |
| TestWriter | claude-sonnet-4-6 | Escribir tests para una unidad | Código + `skills/testing.md` | Tests |
| DocGenerator | claude-haiku-4-5 | Documentar una decisión | Decisión técnica | Entrada para engram |

*Haiku si la tarea es mecánica y clara. Sonnet si requiere razonamiento sobre patrones.*

---

## Reglas de Asignación Dinámica de Modelo

```
IF alta_ambigüedad OR alto_riesgo OR múltiples_trade-offs OR construcción_de_grafo:
    modelo = claude-opus-4-6

ELIF planificación_estructurada OR coordinación OR generación_con_patrones OR monitoreo:
    modelo = claude-sonnet-4-6

ELIF transformación_mecánica OR lookup OR formateo OR validación_clara:
    modelo = claude-haiku-4-5
```

**Escalado:** Cualquier agente puede solicitar reasignación de modelo si detecta que la tarea supera su capacidad. El orquestador padre decide.

---

## Reglas de Ciclo de Vida

### Creación
```
Master Orchestrator  →  crea Entorno de Control + Domain Orchestrators
Domain Orchestrators →  crean rama de tarea + subramas de expertos + Specialist Agents
Specialist Agents    →  no crean subagentes (no hay Nivel 3)
CoherenceAgent       →  creado por Master, monitoriza subramas creadas por Domain Orchestrators
```

### Destrucción
```
Temporales           →  auto-destrucción al reportar resultado
Persistentes Niv.2   →  destrucción cuando Domain Orchestrator cierra el dominio
Persistentes Niv.1   →  destrucción cuando Master Orchestrator cierra la tarea
CoherenceAgent       →  destrucción cuando todas las tareas con expertos paralelos cierran
Destrucción forzada  →  2 rechazos consecutivos del gate → Master notifica al usuario
```

### Comunicación entre agentes
- Los agentes NO comparten contexto directamente
- Comunicación por **mensajes estructurados**: output → input del siguiente
- Ningún agente recibe el contexto completo de otro, solo el resultado relevante para su tarea
- El CoherenceAgent recibe **diffs**, no código completo

---

## Protocolo de Escalado

| Evento | Acción |
|---|---|
| Agente detecta tarea > su capacidad | Notificar orquestador padre + solicitar reasignación |
| Security rechaza 2 veces el mismo plan | Escalar a usuario para decisión humana (ver definición de "mismo plan" en `registry/orchestrator.md`) |
| Coherence detecta conflicto crítico | Veto + escalar a Master + notificar usuario |
| Conflicto técnico git al hacer merge | CoherenceAgent evalúa + propone resolución. Nunca descartar trabajo sin evaluación. |
| Domain Orchestrator no puede producir plan válido | Escalar a Master → notificar usuario. Tarea: BLOQUEADA_POR_DISEÑO. |
| Master no puede construir DAG por spec insuficiente | Listar preguntas específicas al usuario. No crear agentes. |
| Agente no responde tras 3 intentos | Escalar a orquestador padre → si persiste: notificar usuario |
| Domain Orchestrator detecta RF no documentado | Escalar a Master → usuario |
| Tarea Nivel 1 crece en scope | Notificar al usuario ANTES de escalar → esperar confirmación → activar entorno de control |
| Prompt Injection detectado | Veto inmediato del entorno de control + notificar usuario |
| Tarea SECUENCIAL desbloqueada | Master activa su Domain Orchestrator automáticamente |
