# SKILL: Orchestration — Construcción de Grafo de Dependencias y Composición de Equipo
> Skill de carga perezosa. Cargar SOLO por el Master Orchestrator al inicio de una tarea Nivel 2.

## Contexto de Aplicación
- **Agente:** Master Orchestrator
- **Cuándo:** Al recibir un objetivo para descomponerlo antes de crear ningún agente
- **Output esperado:** DAG de tareas + composición del equipo + confirmación del usuario

---

## Patrón 1: Descomposición del Objetivo en Tareas

El objetivo se descompone siguiendo estas dimensiones de análisis:

```
1. DIMENSIÓN DE DATOS
   ¿El objetivo requiere acceso, diseño o modificación de esquemas de BD?
   → TAREA: data-layer

2. DIMENSIÓN DE LÓGICA DE NEGOCIO
   ¿El objetivo requiere lógica de dominio, validaciones, cálculos, servicios?
   → TAREA: domain-layer

3. DIMENSIÓN DE INTERFAZ
   ¿El objetivo expone endpoints, schemas de entrada/salida, contratos de API?
   → TAREA: transport-layer

4. DIMENSIÓN DE VERIFICACIÓN
   ¿El objetivo requiere tests unitarios, de integración o de contrato?
   → TAREA: tests

5. DIMENSIÓN DE DOCUMENTACIÓN
   ¿Hay decisiones técnicas que deben persistirse en el engram?
   → TAREA: docs (temporal, paralela)
```

Cada dimensión presente en el objetivo genera una tarea en el grafo.

---

## Patrón 2: Determinación de Dependencias (Secuencial vs Paralela)

```python
# Reglas de dependencia entre dimensiones estándar:

DEPENDENCIAS = {
    "data-layer":      [],                    # Sin deps → PARALELA
    "domain-layer":    [],                    # Sin deps → PARALELA
    "transport-layer": ["domain-layer"],      # Necesita contratos del dominio → SECUENCIAL
    "tests":           ["transport-layer"],   # Necesita código implementado → SECUENCIAL
    "docs":            ["data-layer",
                        "domain-layer"],      # Puede documentar desde que hay diseño → PARALELA con tests
}

# Una tarea es PARALELA si su lista de deps está vacía o todas sus deps ya completaron.
# Una tarea es SECUENCIAL si tiene deps que aún no han completado.
```

**Regla de paralelismo:** Dos tareas pueden ejecutarse en paralelo si ninguna depende del output de la otra, independientemente de su posición en el grafo.

---

## Patrón 3: Determinación de Número de Expertos por Tarea

```
Factores que justifican ≥ 2 expertos en una tarea:

FACTOR 1 — Alta complejidad de diseño
  La tarea tiene múltiples enfoques arquitectónicos válidos y se beneficia
  de explorarlos en paralelo para elegir el mejor.
  Ejemplo: domain-layer con lógica de negocio no trivial.

FACTOR 2 — Riesgo arquitectónico
  Una decisión incorrecta en esta tarea tendría impacto en cascada.
  Dos perspectivas paralelas reducen el riesgo de error.
  Ejemplo: diseño del esquema de BD si no es straightforward.

FACTOR 3 — Volumen que justifica paralelismo
  La tarea tiene subtareas independientes dentro de ella que pueden
  distribuirse entre expertos sin generar conflictos.
  Ejemplo: tests con suite de unit tests + suite de integration tests.

Si ningún factor aplica → 1 experto es suficiente.
```

---

## Patrón 4: Formato del Grafo de Dependencias (DAG)

```markdown
## Grafo de Dependencias — [nombre del objetivo]

| ID | Tarea | Tipo | Expertos | Depende de | Justificación expertos |
|---|---|---|---|---|---|
| T-01 | data-layer | PARALELA | 1 | — | Esquema simple y claro |
| T-02 | domain-layer | PARALELA | 2 | — | Lógica auth compleja, vale explorar 2 enfoques |
| T-03 | transport-layer | SECUENCIAL | 1 | T-02 | Straightforward una vez definido el dominio |
| T-04 | tests | SECUENCIAL | 2 | T-03 | Unit tests + integration tests en paralelo |
| T-05 | docs | PARALELA | 1 | T-01, T-02 | Temporal, documenta decisiones de diseño |

### Orden de ejecución:
FASE 1 (paralelas): T-01, T-02, T-05
FASE 2 (desbloquea al completar T-02): T-03
FASE 3 (desbloquea al completar T-03): T-04
```

---

## Patrón 5: Composición del Entorno de Control

```markdown
## Entorno de Control — [nombre del objetivo]

### Mínimos obligatorios
- SecurityAgent     (Opus)   — gate de seguridad, veto
- AuditAgent        (Sonnet) — trazabilidad, logs, engram
- CoherenceAgent    (Sonnet) — consistencia entre expertos paralelos

### Criterios para superagentes adicionales
Si el objetivo involucra...          Añadir...
────────────────────────────────────────────────────────
Alto volumen de datos / queries      PerformanceAgent (Sonnet)
Múltiples servicios externos         IntegrationAgent (Sonnet)
Requisitos regulatorios (GDPR, etc.) ComplianceAgent (Opus)
Infraestructura / deploy             InfraAgent (Sonnet)
```

---

## Patrón 6: Presentación al Usuario para Confirmación

```
## Propuesta de equipo para: [objetivo]

### Grafo de tareas
[tabla DAG]

### Fases de ejecución
FASE 1 (paralelas): [lista]
FASE 2: [lista] — inicia al completar [deps]
...

### Entorno de control
[lista de superagentes con roles]

### Domain Orchestrators a crear
[lista por dominio]

### Specialist Agents planificados
[lista por tarea, incluyendo número de expertos y subramas]

---
¿Confirmas este plan o quieres ajustar algún elemento?
```

El Master Orchestrator NO crea ningún agente ni worktree hasta recibir confirmación.

---

## Patrón 7: Gestión del Estado del Grafo durante Ejecución

```
Estado por tarea:
  BLOQUEADA      → tiene dependencias sin completar
  LISTA          → dependencias completadas, esperando activación
  EN_EJECUCIÓN   → Domain Orchestrator y expertos activos
  GATE_PENDIENTE → esperando aprobación del entorno de control
  COMPLETADA     → código en rama de tarea, gate aprobado

Transiciones:
  BLOQUEADA → LISTA        cuando todas sus deps pasan a COMPLETADA
  LISTA → EN_EJECUCIÓN     cuando Master activa el Domain Orchestrator
  EN_EJECUCIÓN → GATE_PENDIENTE  cuando expertos reportan completado
  GATE_PENDIENTE → COMPLETADA    cuando Security + Audit aprueban
  GATE_PENDIENTE → EN_EJECUCIÓN  cuando gate rechaza (revisión y retry)
```
