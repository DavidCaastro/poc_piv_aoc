# ESPECIFICACIÓN TÉCNICA: POC LOGIN SEGURO PIV/OAC v1.0

## 1. Intención General del Sistema
Desarrollar un endpoint de autenticación robusto que valide credenciales de usuario y devuelva un token JWT, implementado bajo un flujo multiagente que garantice la trazabilidad y eficiencia del contexto.

## 2. Requerimientos Funcionales (Contrato de Intención)
- **RF-01 (Autenticación):** El sistema debe recibir email y contraseña mediante un endpoint `POST /login`.
- **RF-02 (Seguridad):** Las contraseñas deben ser comparadas utilizando hasheo **BCrypt** (No texto plano).
- **RF-03 (Autorización):** Si las credenciales son válidas, devolver un token **JWT** con expiración de 1 hora.
- **RF-04 (Manejo de Errores):** Devolver error HTTP 401 si las credenciales fallan, con mensajes que no revelen información sensible.

## 3. Stack Tecnológico y Restricciones Técnicas
- **Lenguaje/Framework:** Python 3.10 + FastAPI.
- **Base de Datos:** Simulación de PostgreSQL conectada exclusivamente vía **Model Context Protocol (MCP)** para evitar la exposición de credenciales en el código.
- **Arquitectura:** **Arquitectura por Capas** obligatoria (Transporte, Dominio, Datos) para asegurar el desacoplamiento.
- **Estructuras de Datos:** El agente debe justificar en el código el uso de **Dict (Hashmap)** para la caché de tokens revocados, indexada por `jti` (JWT ID). Justificación: el lookup por clave string es O(1) en un dict. Una lista/array sería O(n) para búsqueda por valor, inaceptable bajo carga.

## 4. Gestión de Eficiencia y Orquestación (OAC)
- **Aislamiento:** La implementación se realiza en worktrees independientes por experto (`./worktrees/<tarea>/<experto>/`). El código fluye por tres ramas antes de llegar a producción: `feature/<tarea>` → `staging` → `main`.
- **Carga de Skills:** El orquestador debe invocar la habilidad `/skills/backend-security.md` para aplicar los patrones de seguridad definidos.
- **Model Orchestration:** Usar modelos de razonamiento (ej. Opus) para la fase de planificación y modelos rápidos (ej. Sonnet) para la generación de código atómico.

## 5. Protocolo de Auto-Comprobación (Definición de Hecho)
La POC se considerará exitosa solo si el **AuditAgent** (definido en `/registry/security_auditor.md`) genera los siguientes reportes en la carpeta `/logs_veracidad/`:

1.  **`acciones_realizadas.txt`:** Registro paso a paso de las herramientas MCP invocadas y comandos de terminal ejecutados durante el flujo SDD.
2.  **`uso_contexto.txt`:** Reporte detallado indicando la capacidad de la ventana de contexto utilizada y el ahorro de tokens logrado mediante el uso de Skills y Worktrees.
3.  **`verificacion_intentos.txt`:** Documento de veracidad que compare el código final contra los requerimientos RF-01 a RF-04, confirmando la ausencia de secretos (Zero-Trust).

## 7. Descomposición de Tareas (DAG para el Master Orchestrator)

Tareas esperadas para esta POC, en orden de ejecución:

| ID | Tarea | Tipo | Expertos | Depende de |
|---|---|---|---|---|
| T-01 | data-layer | PARALELA | 1 | — |
| T-02 | domain-layer | PARALELA | 2 | — |
| T-03 | transport-layer | SECUENCIAL | 1 | T-02 |
| T-04 | tests | SECUENCIAL | 2 | T-03 |
| T-05 | docs | PARALELA | 1 | T-01, T-02 |

**Fases de ejecución:**
- FASE 1 (paralelas): T-01, T-02, T-05
- FASE 2 (desbloquea al completar T-02): T-03
- FASE 3 (desbloquea al completar T-03): T-04

**Skills por tarea:**
- T-01 `data-layer`: `skills/layered-architecture.md`
- T-02 `domain-layer`: `skills/layered-architecture.md` + `skills/backend-security.md`
- T-03 `transport-layer`: `skills/layered-architecture.md` + `skills/api-design.md`
- T-04 `tests`: `skills/testing.md`
- T-05 `docs`: ninguna (DocGenerator temporal)

---

## 6. Persistencia (Engram)
Cualquier decisión técnica tomada durante la resolución de esta POC (ej. elección de algoritmos de hasheo) debe persistirse en `/engram/session_learning.md` para evitar la amnesia agéntica en futuras sesiones.
