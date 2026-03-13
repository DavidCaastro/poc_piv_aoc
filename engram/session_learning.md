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

---

## Sesión 2026-03-13 — Auditoría de Seguridad Completa (SecurityAgent)

**Tarea:** Auditoría exhaustiva de seguridad sobre dos superficies: aplicación FastAPI (rama `main`) + marco operativo PIV/OAC (rama `agent-configs`).

**Hallazgos totales:** 32 (1 crítica, 8 alta, 12 media, 8 baja, 1 inconsistencia marco-implementación)
**Archivos analizados:** 23 (13 aplicación + 10 marco operativo)
**Categorías OWASP:** A01, A02, A03, A04, A05, A07, A09 + Prompt Injection + Token Security

### Fixes aplicados — Aplicación (rama main)

| ID | Severidad | Fix |
|---|---|---|
| VULN-001 | CRÍTICA | JWT_SECRET_KEY sin fallback — `os.environ["JWT_SECRET_KEY"]` lanza RuntimeError si no está definida |
| VULN-014 | BAJA | Añadido claim `iat` al JWT en `_create_token()` |
| VULN-005 | ALTA | Añadida `purge_expired_tokens()` llamada en cada `is_token_revoked()` |
| VULN-015 | MEDIA | Logout acepta `refresh_token` opcional y revoca ambos tokens |
| VULN-016 | ALTA | PUT /resources/{id} valida `owner_id == current_user.sub` para EDITOR |
| VULN-007 | ALTA | Rate limiting por IP en /auth/login (10 req/15min, sliding window) |
| VULN-012 | MEDIA | Intentos fallidos de login registrados en audit_log con `event: login_failed` |
| VULN-004 | MEDIA | Security headers middleware añadido en main.py |
| VULN-018/020 | BAJA | `max_length` en campos de recursos y password |
| VULN-023 | ALTA | `security_vault.md` añadido a `.gitignore` |

### Fixes aplicados — Marco operativo (rama agent-configs)

| ID | Severidad | Fix |
|---|---|---|
| VULN-028 | MEDIA | `skills/backend-security.md` ampliado con Patrones 7-12: RBAC, rate limiting, CORS, security headers, audit logging, in-memory purge |
| VULN-029 | MEDIA | `registry/coherence_agent.md` — añadido protocolo de escalado de conflictos de seguridad al SecurityAgent |
| VULN-027 | MEDIA | Checklist de seguridad actualizado para incluir `iat`, rate limiting por IP, ownership validation, CORS, security headers |

### Vulnerabilidades conocidas no resueltas (limitaciones estructurales del POC)

| ID | Razón de no resolución |
|---|---|
| VULN-021 | In-memory pierde estado al reiniciar — limitación inherente del POC, documentada |
| VULN-009/010 | Race conditions sin locks — requiere base de datos en producción |
| VULN-022 | Audit log mutable — en producción usar sistema de logs externo inmutable |
| VULN-011 | status_code en audit log siempre 200 — requiere middleware de respuesta, comentario de limitación añadido |
| VULN-024 | Zero-Trust sin enforcement técnico — requiere permisos de filesystem + vault externo |
| VULN-025 | Agent-configs sin firma digital — requiere branch protection rules en GitHub (configuración manual del repositorio) |
| VULN-003 | CORS no configurado — añadido patrón en skill; implementación requiere conocer dominios de producción |
| VULN-006 | Purga de rate_windows huérfanas — parcialmente cubierta por purge_rate_windows en skill |
| VULN-008 | Rate limiting en /auth/refresh — patrón añadido en skill; implementación pendiente |
| VULN-013 | verify_token sin expected_type — diseño funciona, mejora defensiva pendiente |
| VULN-019 | Sin paginación — fuera del scope del POC |
| VULN-031 | Límite de escalados de modelo — mejora operativa menor pendiente |
| VULN-032 | Prompt injection en templates de invocación — mejora estructural de los prompts pendiente |

### Patrones críticos para futuras implementaciones

1. **JWT_SECRET_KEY siempre sin fallback** — `os.environ["JWT_SECRET_KEY"]` en producción; conftest.py establece la variable antes de importar la app
2. **Todo endpoint público necesita rate limiting por IP** — no solo rate limiting por usuario autenticado
3. **RBAC verifica rol, ownership verifica pertenencia** — son validaciones independientes y ambas obligatorias
4. **Audit log registra TODOS los eventos**, incluidos fallos, con status_code real
5. **Todo dict in-memory con crecimiento ilimitado necesita purga periódica** — tokens revocados, rate windows
6. **security_vault.md y URLs de infraestructura NUNCA en el repositorio**
7. **CoherenceAgent escala al SecurityAgent cualquier conflicto que afecte a seguridad** — no resolver unilateralmente
8. **SCA obligatorio en toda auditoría** — `requirements.txt` es parte del scope; `pip audit` debe ejecutarse; `python-jose` tiene CVEs activos (CVE-2024-33664/33663), reemplazar por `PyJWT >= 2.8.0`

---

## Sesión 2026-03-13 — Gap detectado: SCA ausente en protocolo de auditoría

**Hallazgo:** El SecurityAgent no detectó la dependencia vulnerable `python-jose[cryptography]>=3.3.0` durante la auditoría de seguridad de la sesión anterior.

**Causa raíz:** El scope del audit estaba limitado a archivos `src/`. `requirements.txt` no fue cargado en contexto. El skill `backend-security.md` no tenía patrón de SCA ni checklist para dependencias de terceros.

**Correcciones aplicadas en agent-configs:**
- `skills/backend-security.md`: añadido **Patrón 13 — SCA** con criterios de evaluación, tabla de riesgo y checklist específico
- `skills/backend-security.md`: dependencia `python-jose` reemplazada por `PyJWT >= 2.8.0` en la sección "Dependencias Requeridas"
- `skills/backend-security.md`: checklist Pre-Deploy ampliado con dos ítems `[SCA]` como primeros puntos obligatorios
- `engram/session_learning.md`: patrón crítico #8 añadido

**Correcciones aplicadas en la aplicación (main/feature/auth-service):**
- `requirements.txt`: `python-jose[cryptography]>=3.3.0` → `PyJWT>=2.8.0` + `cryptography>=42.0.0`
- `src/domain/auth_service.py`: migración de API `jose` → `jwt` (PyJWT)

**Regla operativa para futuras sesiones:**
El SecurityAgent DEBE incluir `requirements.txt` y `requirements-test.txt` en el scope de TODA auditoría de seguridad, ejecutar `pip audit` como primer paso, y evaluar cada dependencia de terceros contra CVEs conocidos y actividad de mantenimiento.
