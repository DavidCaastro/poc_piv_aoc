# Mini Platform API — Auth + RBAC + Rate Limiting + Audit Trail

> **Rama:** `main` | Construido bajo el marco **PIV/OAC v3.1**
> La configuración del sistema de agentes que construyó este proyecto vive en la rama `agent-configs`.

---

## Qué es este proyecto

Una plataforma API autocontenida con autenticación JWT, control de acceso basado en roles (RBAC), rate limiting in-memory y audit trail inmutable. Desarrollada como prueba de concepto del marco **PIV/OAC**: un sistema multi-agente con gates de seguridad, auditoría y coherencia activos en todo momento.

No requiere conexiones externas. Todos los datos son in-memory. Verificable por cualquier usuario con acceso al repositorio ejecutando `pytest`.

---

## Cómo ejecutar

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Arrancar el servidor

```bash
uvicorn src.main:app --reload
```

API disponible en `http://127.0.0.1:8000`

### 3. Documentación interactiva

```
http://127.0.0.1:8000/docs
```

### 4. Ejecutar los tests

```bash
pip install -r requirements-test.txt
pytest tests/ -v --cov=src --cov-report=term-missing
```

Resultado esperado: **35 passed, 96% coverage.**

---

## Usuarios de prueba

| Email | Password | Rol |
|---|---|---|
| `admin@test.com` | `Admin123!` | ADMIN |
| `editor@test.com` | `Editor123!` | EDITOR |
| `viewer@test.com` | `Viewer123!` | VIEWER |

---

## Endpoints

### Autenticación

| Método | Endpoint | Descripción | Acceso |
|---|---|---|---|
| POST | `/auth/login` | Login — devuelve access_token (1h) + refresh_token (24h) | Público |
| POST | `/auth/refresh` | Renueva access_token con refresh_token válido | Público |
| POST | `/auth/logout` | Revoca el token activo | Autenticado |

### Recursos

| Método | Endpoint | Descripción | Rol mínimo |
|---|---|---|---|
| GET | `/resources` | Listar recursos | VIEWER |
| POST | `/resources` | Crear recurso | EDITOR |
| PUT | `/resources/{id}` | Actualizar recurso | EDITOR |
| DELETE | `/resources/{id}` | Eliminar recurso | ADMIN |

### Administración

| Método | Endpoint | Descripción | Rol mínimo |
|---|---|---|---|
| GET | `/admin/audit-log` | Ver log de auditoría completo | ADMIN |

---

## Flujo básico

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@test.com","password":"Viewer123!"}'

# 2. Usar el access_token en requests protegidos
curl http://127.0.0.1:8000/resources \
  -H "Authorization: Bearer <access_token>"

# 3. Intentar una acción sin permisos suficientes (→ 403)
curl -X DELETE http://127.0.0.1:8000/resources/1 \
  -H "Authorization: Bearer <access_token_del_viewer>"
```

---

## Arquitectura

Capas con flujo unidireccional estricto:

```
TRANSPORTE   src/transport/   FastAPI routers, middleware chain (auth → RBAC → rate limit)
     ↓
DOMINIO      src/domain/      auth_service, rbac_engine, rate_limiter
     ↓
DATOS        src/data/        In-memory store (users, resources, tokens revocados, audit log)
```

El middleware chain sigue el orden de seguridad correcto verificado por SecurityAgent: **auth → RBAC → rate limiting**.

---

## Stack

| Componente | Tecnología |
|---|---|
| Framework | FastAPI |
| Lenguaje | Python 3.10 |
| Autenticación | JWT (python-jose) + BCrypt (cost 12) |
| Almacenamiento | In-memory (dict / list) |
| Tests | pytest + httpx + pytest-cov |

---

## Requerimientos funcionales verificados

| RF | Descripción | Test |
|---|---|---|
| RF-01 | `POST /auth/login` → access_token (1h) + refresh_token (24h) | `test_auth.py:12` |
| RF-02 | `POST /auth/refresh` con refresh_token válido | `test_auth.py:51` |
| RF-03 | `POST /auth/logout` revoca token (dict O(1) por jti) | `test_auth.py:85` |
| RF-04 | BCrypt cost 12, timing-safe comparison siempre | `test_auth.py:33` |
| RF-05 | RBAC: ADMIN > EDITOR > VIEWER con matriz de permisos explícita | `test_rbac.py` |
| RF-06 | 5 endpoints con permisos diferenciados | `test_resources.py` |
| RF-07 | Rate limiting sliding window (VIEWER 10, EDITOR 30, ADMIN 100 req/min) | `test_rate_limit.py` |
| RF-08 | Audit trail inmutable in-memory por request autenticado | `test_resources.py:78` |
| RF-09 | Errores genéricos 401/403/429 sin revelar información sensible | `test_auth.py:44` |
| RF-10 | ≥ 80% cobertura + 5 escenarios de seguridad obligatorios | 96% / 5 de 5 |

### Escenarios de seguridad obligatorios (RF-10)

| Escenario | Test | HTTP |
|---|---|---|
| VIEWER intentando endpoint de ADMIN | `test_rbac.py:14` | 403 |
| Token revocado intentando acceder | `test_auth.py:85` | 401 |
| VIEWER superando 10 req/min | `test_rate_limit.py:12` | 429 |
| Refresh con token inválido | `test_auth.py:57` | 401 |
| EDITOR intentando DELETE | `test_rbac.py:39` | 403 |

---

## Principios de seguridad aplicados

### Autenticación y tokens
- **Zero-Trust:** `JWT_SECRET_KEY` solo vía variable de entorno — la app falla al arrancar si no está definida
- **Timing-safe:** `verify_password()` se ejecuta aunque el usuario no exista (anti-enumeración)
- **Mensajes genéricos:** El sistema no distingue entre usuario inexistente y contraseña incorrecta
- **Revocación O(1):** Caché de tokens revocados como `dict[jti → exp]` — purga automática de entradas expiradas
- **Revocación de refresh en logout:** El refresh token puede enviarse en el body de `/auth/logout` para ser invalidado simultáneamente con el access token
- **`iat` claim:** Todos los JWT incluyen issued-at para auditoría y detección de tokens antedatados

### Control de acceso
- **RBAC + ownership:** Las comprobaciones de rol y de autoría son independientes — un EDITOR solo puede editar sus propios recursos aunque su rol permita la operación
- **Orden de middleware verificado:** auth → RBAC → rate limiting, documentado en `gates/transport-layer/security_review.md`

### Rate limiting
- **Por usuario autenticado:** Sliding window 60 s (VIEWER 10, EDITOR 30, ADMIN 100 req/min) — RF-07
- **Por IP en login:** Sliding window 15 min, máximo 10 intentos — protección contra fuerza bruta en endpoint público

### Hardening de inputs
- **Límites en campos de texto:** `title` ≤ 200 chars, `description` ≤ 5 000 chars (previene crecimiento ilimitado de memoria)
- **Límite en contraseña:** ≤ 128 chars (BCrypt trunca a 72 bytes — el límite evita overhead de hashing de entradas masivas)
- **`extra = "forbid"`** en todos los modelos de request — campos no declarados son rechazados con 422

### Headers HTTP
- `X-Content-Type-Options: nosniff` — previene MIME sniffing
- `X-Frame-Options: DENY` — previene clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 0` — desactiva el filtro legacy (CSP es el mecanismo correcto)

### Audit trail
- Los intentos de login fallidos se registran en el audit log (`event: login_failed`) junto con IP y timestamp

---

## Cómo se construyó: el marco PIV/OAC

El desarrollo siguió un protocolo de orquestación multi-agente definido en la rama `agent-configs`:

1. **Spec primero:** Ningún agente escribió código sin RF documentado en `project_spec.md`
2. **DAG de dependencias:** Master Orchestrator construyó el grafo de 7 tareas y 5 fases antes de crear cualquier agente de ejecución
3. **Entorno de control:** SecurityAgent + AuditAgent + CoherenceAgent activos antes que cualquier experto
4. **Gate bloqueante:** Cada plan pasó revisión de los 3 agentes de control antes de que existiera cualquier worktree — 14/14 gates documentados en `gates/`
5. **Conflicto resuelto en diseño:** CoherenceAgent forzó acuerdo del schema JWT entre auth-service y rbac-engine antes de que cualquiera de los dos escribiera código
6. **Verificación final:** AuditAgent generó 3 logs en `logs_veracidad/` que mapean cada RF contra el código entregado

---

## Trazabilidad del proceso

```
gates/              ← 28 archivos de revisión (plan + security + audit + coherence por tarea)
logs_veracidad/     ← 3 logs de auditoría generados por AuditAgent
engram/             ← Decisiones técnicas persistidas entre sesiones
```

---

## Estructura del repositorio

```
├── README.md
├── requirements.txt
├── requirements-test.txt
├── src/
│   ├── main.py
│   ├── schemas/          ← Pydantic models (Role, TokenPayload, UserInDB, Resource...)
│   ├── data/             ← In-memory store + seed users
│   ├── domain/           ← auth_service, rbac_engine, rate_limiter
│   └── transport/        ← dependencies, auth_router, resources_router, admin_router
├── tests/                ← 35 tests (conftest, auth, rbac, rate_limit, resources)
├── docs/                 ← API reference
├── gates/                ← Reviews de seguridad, auditoría y coherencia por tarea
├── logs_veracidad/       ← Logs de auditoría del AuditAgent
└── engram/               ← Memoria persistente entre sesiones
```

---

## Rama `agent-configs`

Contiene el marco operativo PIV/OAC v3.1 que orquestó este proyecto: instrucciones para Claude Code (`CLAUDE.md`), definición de agentes, skills, registry, protocolos de gates y memoria persistente (engram).
