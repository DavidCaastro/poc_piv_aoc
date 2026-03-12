# PERSISTENCIA DE MEMORIA — Sistema Engram PIV/OAC
> Este archivo es la memoria a largo plazo del agente. Se actualiza al finalizar cada sesión.
> RESTRICCIÓN: No incluir valores del security_vault.md. Solo decisiones técnicas y patrones.

---

## Sesión 2026-03-12 — Inicialización del Marco PIV/OAC

**Tarea:** Completar la infraestructura de configuración del marco operativo.

**Decisiones técnicas tomadas:**
- `CLAUDE.md` establecido como punto de entrada para Claude Code (cargado automáticamente en cada sesión).
- `skills/backend-security.md` creado con patrones para FastAPI + JWT + BCrypt.
- `registry/security_auditor.md` creado con protocolo de auditoría de 6 pasos.
- **Corrección de imprecisión conceptual:** La caché de tokens usa `dict` (hashmap), NO un array/lista. Razón: la operación de lookup es por clave string (token ID/jti), lo que requiere O(1) por clave. Un array es O(1) solo por índice numérico y O(n) para búsqueda por valor. Esta corrección se aplicó en `agent.md`, `project_spec.md` y en el patrón 4 de `skills/backend-security.md`.

**Patrones establecidos:**
- Arquitectura por Capas: Transporte → Dominio → Datos (flujo unidireccional).
- BCrypt con cost factor 12 como mínimo.
- JWT con campo `jti` para soporte de revocación.
- Mensaje de error 401 unificado para prevenir enumeración de usuarios.
- Timing-safe comparison: ejecutar `verify_password` incluso si el usuario no existe.

**Estructura de archivos confirmada:**
- `CLAUDE.md` → instrucciones operativas para Claude Code (cargar siempre)
- `agent.md` → marco extendido PIV/OAC (referencia, no cargar por defecto)
- `skills/` → carga perezosa por tarea
- `registry/` → definiciones de subagentes
- `worktrees/` → no versionado (en .gitignore)

**Resultado auditoría de sesión:** N/A (sesión de configuración, no de implementación)

**Observaciones para próxima sesión:**
- El worktree `./worktrees/poc-login` debe crearse antes de iniciar la implementación del endpoint.
- SECRET_KEY para JWT debe obtenerse vía MCP antes de cualquier prueba local.
- Cargar `skills/backend-security.md` como primer paso de la implementación.

---

## Sesión 2026-03-12 — Revisión y Mejoras del Marco PIV/OAC (v3.1)

**Tarea:** Aplicar 29 mejoras identificadas en segunda revisión de consistencia del marco.

**Decisiones técnicas y protocolos establecidos:**

- **Definición de "mismo plan":** Un plan revisado que no corrige el componente específico que originó el rechazo se considera el mismo plan. Reinicia el contador si corrige el componente rechazado. Registrado en `registry/orchestrator.md` Paso 6.
- **Gate timing sin ambigüedad:** Worktrees y expertos solo existen DESPUÉS de aprobación explícita del gate de los tres agentes de control. Añadido como restricción bloqueante explícita en CLAUDE.md FASE 4 y orchestrator.md.
- **Protocolo Domain Orchestrator sin plan:** Si el DO no puede producir un plan válido → escalar al Master → notificar usuario → estado BLOQUEADA_POR_DISEÑO. Evita bucles silenciosos de revisión sin salida.
- **Protocolo DAG insuficiente:** Si la spec no permite construir el DAG completo → listar preguntas específicas al usuario. Nunca asumir ni inventar información faltante. Registrado en orchestrator.md Paso 1 y orchestration.md Patrón 2.
- **Conflictos git técnicos:** CoherenceAgent ahora cubre dos tipos: semánticos (ya existía) y técnicos git (nuevos). Protocolo en `registry/coherence_agent.md`. Nunca descartar trabajo de un experto sin evaluación.
- **Registro de gate en tiempo real:** AuditAgent registra cada decisión de gate (no solo al cierre) con PLAN_VERSION incremental. Permite rastrear el historial de rechazos para aplicar correctamente la regla del "mismo plan".
- **Protocolo agente no responde:** 3 intentos fallidos → escalar a orquestador padre → si persiste: notificar usuario. Registrado en CLAUDE.md y agent_taxonomy.md.
- **Dimensiones de descomposición stack-agnostic:** Las 5 dimensiones en orchestration.md ahora son universales con nombres adaptables al stack. Añadidas dimensiones opcionales: INFRAESTRUCTURA e INTEGRACIÓN.

**Archivos actualizados:** agent.md (v3.1), CLAUDE.md, orchestrator.md, security_auditor.md, coherence_agent.md, agent_taxonomy.md, skills/orchestration.md

**Resultado:** 29 oportunidades de mejora identificadas. Aplicadas las críticas e importantes. Marco elevado a v3.1.
