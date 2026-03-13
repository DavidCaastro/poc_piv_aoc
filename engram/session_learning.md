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

---

## Sesión 2026-03-13 — Análisis de coherencia de tests y cobertura de gaps

**Tarea:** Identificar gaps entre implementación y tests, escribirlos, y corregir un false positive.

**Gaps encontrados (10) y resueltos:**

| Gap | Severidad | Test añadido |
|---|---|---|
| Login rate limit por IP | Mayor | `TestLogin::test_login_rate_limit_per_ip` |
| Failed login en audit log | Mayor | `TestLogin::test_failed_login_recorded_in_audit_log` |
| Ownership cross-user | Mayor | `TestResourceCRUD::test_editor_cannot_update_other_users_resource` |
| Validación de límites de input | Mayor | `TestInputValidation` (7 tests en `test_security.py`) |
| False positive audit trail | Mayor (fix) | `test_audit_log_contains_required_fields` — ahora filtra entries autenticadas y verifica valores non-null |
| Refresh token revocado en logout | Moderado | `TestLogout::test_logout_also_revokes_refresh_token` |
| Purga de tokens revocados expirados | Moderado | `TestTokenExpiry::test_purge_removes_expired_revoked_tokens` |
| Security headers | Moderado | `TestSecurityHeaders` (3 tests en `test_security.py`) |
| Admin rate limit exacto a 100 | Menor | `TestRateLimiting::test_admin_rate_limit_exceeded_at_100` |
| Token expirado | Menor | `TestTokenExpiry::test_expired_token_returns_401` |

**Bug de producción descubierto por los tests:**
`max_length=128` en `LoginRequest.password` causaba `ValueError: password cannot be longer than 72 bytes` en `bcrypt>=4.1.0` para contraseñas de 73-128 chars, resultando en un HTTP 500.
**Fix:** `max_length=128 → 72` en `src/schemas/users.py`. Regla: bcrypt>=4.1 lanza ValueError para inputs >72 bytes — el límite en el schema debe ser ≤ 72.

**Resultado final:** 35 → 55 tests passed, 93% coverage.

### Patrones de testing a aplicar en futuras implementaciones

1. **Verificar no solo presencia de campos sino sus valores** — un audit log entry con `user_id=None` pasa un test que solo verifique `field in entry`. Siempre verificar que los valores son significativos para el contexto del test.

2. **Cada fix de seguridad necesita su test negativo** — para cada vuln fix hay que añadir el test que demuestra el vector de ataque bloqueado:
   - VULN-006 (rate limit IP) → test que envía 11 requests y verifica 429
   - VULN-012 (failed login audit) → test que verifica entry con event=login_failed
   - VULN-015 (logout revoca refresh) → test que verifica refresh token inválido post-logout
   - VULN-016 (ownership) → test que verifica EDITOR no puede editar recurso ajeno
   - VULN-018/020 (input limits) → tests de boundary exacto (max, max+1, 0)

3. **Tests de boundary deben verificar ambos lados del límite:**
   - `len(field) = max_length` → debe aceptarse (201 o 422 indica bug)
   - `len(field) = max_length + 1` → debe rechazarse con 422
   - `len(field) = 0` si min_length=1 → debe rechazarse con 422

4. **Rate limit tests deben alcanzar el límite real**, no solo verificar que otro rol tiene límite más alto:
   - Incorrecto: "ADMIN hace 31 requests y todos pasan" (no verifica el límite real de 100)
   - Correcto: "ADMIN hace 100 requests (ok) + 1 más (429)"

5. **Tokens expirados deben crear manualmente** con `jwt.encode(..., exp=time.time()-3600)` — no depender del mock de tiempo ni de esperar que expire naturalmente.

6. **False positives de formato:** Si el schema del audit log puede tener variantes (entries de login fallido con `user_id=None` vs. entries autenticadas con `user_id` real), el test debe filtrar explícitamente el tipo de entry que quiere verificar.

7. **bcrypt>=4.1 no silencia passwords >72 bytes** — lanza `ValueError` causando HTTP 500. `max_length` en el schema debe ser ≤ 72.

8. **`new_test_file` vs. `existing_test_file`:** Crear `test_security.py` separado para tests de headers y validación de inputs. No sobre-cargar `test_auth.py` con concerns de transporte.

---

## Sesión 2026-03-13 — Implementación RF-11 a RF-17 (v2.0)

**Tarea:** Activar el proceso PIV/OAC completo con el informe de auditoría como fuente de verdad. Implementar los 7 RF nuevos derivados de la auditoría.

**Requerimientos implementados:**

| RF | Descripción | Archivos principales |
|---|---|---|
| RF-11 | Audit log registra 403 (rbac_denied) y 429 (rate_limit_exceeded) | `src/transport/dependencies.py` |
| RF-12 | `/auth/refresh` registra token_refreshed / token_refresh_failed | `src/transport/auth_router.py` |
| RF-13 | CI: ruff + pip-audit como gates bloqueantes | `.github/workflows/ci.yml`, `pyproject.toml` |
| RF-14 | `.dockerignore` excluye secretos y archivos del marco | `.dockerignore` |
| RF-15 | Test para actualización de `description` en PUT /resources | `tests/test_resources.py` |
| RF-16 | SECURITY.md con política de divulgación responsable | `SECURITY.md` |
| RF-17 | `.env.example` documentado con comentarios inline | `.env.example` |

**Resultado final:** 60 tests passed (era 55), 93% coverage. Ruff: 0 errores. pip-audit: 0 vulnerabilidades.

**Decisiones técnicas:**
- `pyproject.toml` configura ruff con `ignore = ["E501"]` — docstrings y comentarios no penalizan por longitud.
- F401 (unused imports) sí se enforcan — eliminado `import pytest` en varios test files y `from src.schemas.roles import Role` en `auth_service.py`.
- El audit log de `check_rbac` y `check_rate` escribe ANTES de lanzar la `HTTPException` — es la única forma de capturar el evento ya que el middleware de respuesta no está implementado.
- Para RF-12: el refresh token se decodifica con `options={"verify_exp": False}` en el bloque de fallo para poder registrar el `user_id` incluso cuando el token está expirado. Esto es solo para el audit log — la validación real ya falló antes.

**Patrones operativos para futuras sesiones:**
1. **Auditoría antes de implementación:** Un informe técnico exhaustivo (antes de escribir código) identifica gaps que los tests no cubrían y previene regresiones.
2. **Agents en background comparten working tree:** Cuando 3+ agentes trabajan en paralelo en el mismo directorio sin `isolation: "worktree"`, usar `git stash` antes de cambiar de rama y pop al regresar.
3. **Ruff F401 en CI:** Eliminar todos los `import pytest` en test files que no usan directamente fixtures de pytest (solo usan `client`, `admin_token`, etc. de conftest via DI). pytest no necesita ser importado explícitamente.
4. **project_spec.md como registro de versiones:** Mantener secciones v1.0/v2.0 separadas en el DAG para que el historial de evolución del producto sea trazable desde la spec.

**Archivos actualizados en agent-configs:** `project_spec.md` (v2.0), `README.md` (60 tests, RF-01 a RF-17), `engram/session_learning.md`

---

## Sesión 2026-03-13 — Auditoría de calificación objetiva + 6 fixes adicionales

**Tarea:** Generar calificación técnica objetiva 1-100 del repositorio y ejecutar todos los fixes derivados sin confirmación.

**Calificación:** 74.3/100 (pre-fix) → **79.8/100** (post-fix)
**Comparativa:** Senior junior — límite superior mid-level / MVP startup-ready

**6 fixes implementados:**

| Fix | Archivo | Descripción |
|---|---|---|
| deque(maxlen=10_000) | `src/data/store.py` | Circular buffer previene OOM en audit_log |
| Real status_code | `src/main.py`, `src/transport/dependencies.py` | `audit_log_middleware` captura el status_code real después del handler; check_rate ya no asume 200 |
| Exception handler | `src/main.py` | `@app.exception_handler(Exception)` devuelve 500 genérico, loguea internamente |
| HSTS header | `src/main.py` | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| Docker non-root | `Dockerfile` | `adduser appuser` + `USER appuser` |
| Docker HEALTHCHECK | `Dockerfile` | `HEALTHCHECK --interval=30s` vía urllib |
| CI coverage gate | `.github/workflows/ci.yml` | `--cov-fail-under=90` bloqueante |

**Resultado:** 61 tests (era 60), 93.48% coverage, gate 90% pasado, main.py 100% cubierto.

**Decisiones técnicas críticas:**

1. **`request.state.audit_entry` para status_code real:**
   - Antes: `check_rate` hacía `store.audit_log.append({...status_code: 200})` antes del handler → siempre 200
   - Ahora: `check_rate` pone `request.state.audit_entry = {sin status_code}` → `audit_log_middleware` en main.py lo completa con `response.status_code` real tras ejecutar el handler
   - Los eventos 403/429/401 siguen siendo append directo (correctos ya antes)

2. **deque vs. list para audit_log:**
   - `deque(maxlen=10_000)` es drop-in replacement para append y clear
   - El único cambio necesario: `admin_router.py` retorna `list(store.audit_log)` para serialización FastAPI
   - `deque.clear()` funciona in-place → `reset_store()` no necesita cambios

3. **@app.exception_handler(Exception) + TestClient:**
   - `raise_server_exceptions=True` en TestClient hace que el cliente re-lance excepciones incluso si el handler las captura
   - Solución: testear el handler directamente con `asyncio.run(unhandled_exception_handler(mock_request, exc))`
   - NO intentar provocar una excepción real vía HTTP en tests con el TestClient por defecto

4. **Orden de middlewares en FastAPI:**
   - Last registered = innermost (runs first on response)
   - `audit_log_middleware` registrado después de `security_headers` → es el más cercano al handler → ve `request.state` antes de que se limpie
   - `security_headers` registrado primero → envuelve todo → añade headers a todas las respuestas incluyendo el 500 del exception handler

**Informe de auditoría guardado:** `logs_veracidad/auditoria_tecnica_2026-03-13_v2.md`
