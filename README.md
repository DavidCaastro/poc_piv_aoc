# PIV/OAC — Marco de Configuración Operativa v3.1

> **Rama:** `agent-configs` | **Tipo:** Directive
> Esta rama contiene exclusivamente la configuración del sistema de agentes. No contiene código de aplicación.
> El código producido por este marco vive en las ramas artifact (`main`, `staging`, `feature/*`).

---

## ¿Qué es PIV/OAC?

**PIV** (Paradigma de Intencionalidad Verificable) + **OAC** (Orquestación Atómica de Contexto) es un marco operativo para desarrollo guiado por agentes de IA que resuelve tres problemas estructurales del uso convencional de LLMs en ingeniería de software:

| Problema convencional | Solución PIV/OAC |
|---|---|
| El agente genera código sin validar la intención real | Toda acción se valida contra una especificación documentada antes de ejecutarse |
| Un solo agente satura su ventana de contexto con todo el repo | Cada agente recibe solo el contexto mínimo necesario para su tarea (lazy loading) |
| La seguridad y auditoría son pasos finales opcionales | SecurityAgent, AuditAgent y CoherenceAgent corren desde el inicio con capacidad de veto pre-código |
| Las decisiones técnicas se pierden entre sesiones | El sistema Engram persiste las decisiones para que el agente no empiece desde cero |

---

## Arquitectura del Sistema

Jerarquía de tres niveles. Cada nivel tiene scope, responsabilidades y modelo de IA diferente.

```
┌──────────────────────────────────────────────────────────────────┐
│                    MASTER ORCHESTRATOR (Nivel 0)                  │
│  Recibe objetivo → construye DAG → presenta al usuario → delega  │
│  Nunca escribe código. Nunca lee archivos de implementación.      │
└──────────────────────────┬───────────────────────────────────────┘
                           │ crea entorno de control
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐  ┌────────────┐  ┌─────────────────┐
   │  SECURITY  │  │   AUDIT    │  │   COHERENCE     │
   │   AGENT    │  │   AGENT    │  │     AGENT       │
   │ Veto sobre │  │Trazabilidad│  │ Consistencia    │
   │ planes y   │  │y veracidad │  │ entre expertos  │
   │ código     │  │            │  │ paralelos       │
   └────────────┘  └────────────┘  └─────────────────┘
                           │
                           │ crea agentes de ejecución
                           ▼
                   DOMAIN ORCHESTRATORS (Nivel 1)
                   Uno por dominio del DAG
                           │
                           ▼
                   SPECIALIST AGENTS (Nivel 2)
                   N expertos por tarea, en subramas aisladas
```

---

## El Entorno de Control — Gate Bloqueante

Ninguna línea de código se escribe sin pasar este gate. Los tres agentes de control revisan **en paralelo** el plan de cada tarea:

```
Domain Orchestrator genera plan
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
Security    Audit   Coherence
patrones  trazabil  viabilidad
seguros    idad    ejecución
    │         │    paralela
    └─────────┼─────────┘
              │
   ¿Los tres aprueban?
              │
   NO ────────┴──────── SÍ
   │                     │
   ▼                     ▼
Plan revisado      Crear worktrees
→ repetir gate     y expertos
```

- **SecurityAgent (Opus):** verifica patrones de seguridad, ausencia de secretos, RF cubiertos. Tiene veto.
- **AuditAgent (Sonnet):** verifica trazabilidad a RF, coherencia de scope y arquitectura correcta.
- **CoherenceAgent (Sonnet):** detecta conflictos entre expertos paralelos (semánticos y técnicos de git). Fuerza acuerdos antes de que los expertos escriban código.

---

## Tipología de Ramas

El repositorio distingue dos tipos de rama con propósitos y ciclos de vida distintos:

### Rama Directive
Contiene las directivas que gobiernan el comportamiento del sistema de agentes. No produce artefactos ejecutables. No recibe merges desde ramas artifact. Versiona independientemente el marco operativo.

| Rama | Propósito |
|---|---|
| `agent-configs` | Marco PIV/OAC: CLAUDE.md, skills, registry, engram, protocolos de gates |

### Ramas Artifact
Contienen los artefactos producidos por el sistema de agentes. Su ciclo de vida está gobernado por las directivas de la rama directive.

| Rama | Subtipo | Propósito |
|---|---|---|
| `main` | delivery | Producción. Solo recibe merges desde `staging` con confirmación humana explícita |
| `staging` | integration | Pre-producción. Integración de todas las tareas. Gate final antes de `main` |
| `feature/<tarea>` | execution | Rama de tarea. Integra el trabajo de los expertos de esa tarea |
| `feature/<tarea>/<experto>` | execution | Subrama de experto. Aislamiento atómico de cada especialista |

---

## Flujo de Ramas Artifact (Tres Niveles)

```
[directive]  agent-configs  ← gobierna el proceso, no participa en el flujo de merge

[artifact]   main           ← delivery. Confirmación humana explícita requerida.
             └── staging    ← integration. Gate final Security + Audit + humano.
                 └── feature/<tarea>              ← execution
                     ├── feature/<tarea>/experto-1  ← execution (paralela)
                     └── feature/<tarea>/experto-2  ← execution (paralela)
```

**Merge en tres gates:**
```
feature/<tarea>/experto-N  [execution]
    │  GATE 1: CoherenceAgent autoriza
    ▼
feature/<tarea>            [execution]
    │  GATE 2: Security + Audit aprueban
    ▼
staging                    [integration]
    │  GATE 3: revisión humana + Security + Audit
    ▼
main                       [delivery] ← solo con confirmación humana explícita
```

---

## Clasificación de Tareas

Antes de actuar, toda tarea se clasifica en uno de dos niveles:

### Nivel 1 — Micro-tarea
Se cumplen **todos** los criterios: ≤ 2 archivos afectados, sin arquitectura nueva, RF documentado, riesgo bajo.
**Protocolo:** Ejecución directa. Sin orquestación. Zero-Trust y lazy loading aplican igual.

### Nivel 2 — Feature / POC / Objetivo complejo
Cualquiera de: archivos nuevos, ≥ 3 archivos, arquitectura nueva, RF nuevo o ambiguo, impacto en seguridad.
**Protocolo:** Orquestación completa con DAG, entorno de control, gates bloqueantes y merge en tres niveles.

**Escalado automático:** Nivel 1 que crece en scope → escala a Nivel 2 con notificación al usuario.

---

## Asignación Dinámica de Modelo

La capacidad se asigna por dimensión de razonamiento, no por jerarquía fija:

| Condición | Modelo |
|---|---|
| Alta ambigüedad / alto riesgo / múltiples trade-offs / construcción de DAG | claude-opus-4-6 |
| Planificación estructurada / coordinación / generación con patrones | claude-sonnet-4-6 |
| Transformaciones mecánicas / lookups / formateo / validación clara | claude-haiku-4-5 |

Cualquier agente puede solicitar escalado si detecta que su tarea supera su capacidad asignada.

---

## Gestión de Contexto por Abstracción (Lazy Loading)

- **Master Orchestrator:** Solo objetivos, DAG y estado de entorno. No lee código.
- **Domain Orchestrators:** Solo spec de su dominio + skill relevante de `/skills/`.
- **Specialist Agents:** Solo scope de su subrama + outputs necesarios de dependencias.
- **CoherenceAgent:** Solo diffs entre subramas, no el código completo de cada experto.

---

## Sistema Engram — Memoria Persistente

Resuelve la "amnesia agéntica": pérdida de decisiones técnicas entre sesiones.

- **Escritura exclusiva:** Solo AuditAgent escribe en `engram/session_learning.md`.
- **Lectura libre:** Cualquier agente puede consultarlo al inicio de una tarea.
- **Contenido:** Decisiones técnicas, patrones reutilizables, resultado de gates, observaciones para la próxima sesión.
- **No contiene:** Ningún valor del vault, ninguna credencial, ningún dato sensible.

---

## Principios Zero-Trust (todos los agentes, siempre)

1. **Vault restringido:** Ningún agente lee `security_vault.md` sin instrucción humana explícita en el turno activo
2. **Credenciales solo vía MCP:** Nunca en la ventana de contexto de ningún agente
3. **Veto de SecurityAgent:** Detiene cualquier plan o acción que represente un riesgo
4. **Anti Prompt Injection:** Veto automático + notificación al usuario
5. **Logs limpios:** AuditAgent verifica que ningún valor sensible aparezca en los logs

---

## Estructura de Archivos

```
agent-configs/
│
├── CLAUDE.md                         ← Instrucciones operativas cargadas automáticamente
│                                        por Claude Code en cada sesión (entrypoint)
│
├── agent.md                          ← Marco operativo completo PIV/OAC v3.1
│
├── project_spec.md                   ← Fuente de verdad activa (RF + DAG)
│                                        Actualmente: Mini Platform API v1.0
│
├── security_vault.md                 ← Acceso restringido (Zero-Trust)
│
├── skills/
│   ├── orchestration.md             ← Construcción de DAG (Master Orchestrator)
│   ├── layered-architecture.md      ← Arquitectura por capas (Domain Orchestrators)
│   ├── backend-security.md          ← Seguridad FastAPI + JWT + BCrypt
│   ├── api-design.md                ← Contratos de API
│   └── testing.md                   ← Tests pytest + httpx
│
├── registry/
│   ├── orchestrator.md              ← Master Orchestrator: protocolo + gates
│   ├── security_auditor.md          ← SecurityAgent + AuditAgent: protocolos
│   ├── coherence_agent.md           ← CoherenceAgent: monitoreo + conflictos
│   └── agent_taxonomy.md            ← Catálogo completo: ciclo de vida, modelos
│
├── engram/
│   └── session_learning.md          ← Memoria persistente (escritura: AuditAgent)
│
├── logs_veracidad/                   ← Generados por AuditAgent al cierre de objetivo
│   ├── acciones_realizadas.txt      ← Registro cronológico de acciones por agente
│   ├── uso_contexto.txt             ← Eficiencia de contexto y tokens
│   └── verificacion_intentos.txt    ← RF verificados contra código entregado
│
└── worktrees/                        ← Temporal, no versionado (.gitignore)
```

---

## Flujo Completo de un Objetivo Nivel 2

```
1. Usuario entrega objetivo
         │
2. Master Orchestrator (Opus)
   └── Lee project_spec.md → valida RF
   └── Construye DAG de dependencias
   └── Presenta DAG al usuario → espera confirmación
         │
3. Crear entorno de control (tras confirmación)
   ├── SecurityAgent (Opus)    — persistente
   ├── AuditAgent (Sonnet)     — persistente
   └── CoherenceAgent (Sonnet) — persistente
         │
4. Por cada tarea en orden del DAG:
   Domain Orchestrator → diseña plan → somete al gate
         │
5. Gate bloqueante (los 3 deben aprobar)
   RECHAZADO → revisar plan → repetir gate
   APROBADO  → crear worktrees y expertos
         │
6. Expertos trabajan en subramas aisladas
   CoherenceAgent monitoriza diffs continuamente
         │
7. Gate 1 (CoherenceAgent) → merge expertos → feature/<tarea>
   Gate 2 (Security + Audit) → merge feature/<tarea> → staging
         │
8. Gate 3 (humano + Security + Audit)
   Solo con confirmación humana → merge staging → main
         │
9. Cierre
   AuditAgent genera 3 logs en /logs_veracidad/
   AuditAgent + CoherenceAgent actualizan engram/
```

---

## Resultado de la POC activa

La especificación activa (`project_spec.md`) ejecutó la construcción de la **Mini Platform API** en la rama `main`:

| Métrica | Resultado |
|---|---|
| Tests | 35 passed, 0 failed |
| Cobertura | 96% (mínimo requerido: 80%) |
| Secretos en código | 0 |
| Gates ejecutados | 14 / 14 aprobados |
| RF cumplidos | RF-01 a RF-10 — todos |
| Archivos entregados | 60 archivos, 2.295 líneas |

El proceso completo está trazado en `gates/` (28 archivos de revisión) y `logs_veracidad/` (3 logs de auditoría).

---

## Separación Directive / Artifact

| | Rama directive (`agent-configs`) | Ramas artifact (`main`, `staging`, `feature/*`) |
|---|---|---|
| **Contiene** | CLAUDE.md, skills, registry, engram, project_spec.md | src/, tests/, docs/, gates/, logs_veracidad/ |
| **Produce** | Nada ejecutable — solo directivas | Código, tests, documentación, trazabilidad |
| **Recibe merges de** | Nunca desde artifact | Desde la rama artifact inmediatamente inferior |
| **Versionado** | Independiente del ciclo de entrega | Sigue el flujo execution → integration → delivery |
| **Quién la modifica** | El operador humano del marco | Los agentes bajo protocolo PIV/OAC |
