# POC Login Seguro — PIV/OAC

> **Rama:** `main`
> Código de aplicación. La configuración del sistema de agentes vive en la rama `agent-configs`.

---

## ¿Qué es este proyecto?

Una prueba de concepto (POC) de un sistema de autenticación seguro desarrollado bajo el marco **PIV/OAC**: un paradigma de desarrollo donde una organización de agentes de IA colabora de forma estructurada, con gates de seguridad y auditoría activos en todo momento, para garantizar que cada decisión técnica sea intencional, trazable y verificable antes de convertirse en código.

El objetivo no es solo construir el endpoint. Es demostrar que un sistema multi-agente puede producir software seguro de forma reproducible, con menor riesgo de errores arquitectónicos y sin depender de la memoria o el criterio puntual de una sola sesión de IA.

---

## Qué construye este proyecto

Un endpoint de autenticación `POST /login` con las siguientes características:

- Recibe `email` y `password` vía HTTP
- Valida credenciales contra una base de datos usando hashing **BCrypt**
- Devuelve un token **JWT** con expiración de 1 hora si las credenciales son válidas
- Retorna HTTP 401 con mensaje genérico si fallan, sin revelar si el fallo fue el email o la contraseña
- Implementado en **Python 3.10 + FastAPI** bajo arquitectura por capas estricta

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework web | FastAPI |
| Lenguaje | Python 3.10 |
| Autenticación | JWT (python-jose) |
| Hashing | BCrypt |
| Base de datos | PostgreSQL (acceso vía MCP) |
| Gestión de secretos | Model Context Protocol (MCP) |
| Aislamiento de trabajo | Git Worktrees |

---

## Arquitectura de la aplicación

El código sigue una **arquitectura por capas** con flujo unidireccional estricto:

```
┌─────────────────────────────────┐
│         TRANSPORTE              │
│  Routers FastAPI, schemas       │
│  Validación de entrada (Pydantic)│
└────────────────┬────────────────┘
                 │ solo hacia abajo
┌────────────────▼────────────────┐
│           DOMINIO               │
│  Lógica de negocio pura         │
│  Servicio de autenticación      │
│  Caché de tokens (dict, O(1))   │
└────────────────┬────────────────┘
                 │ solo hacia abajo
┌────────────────▼────────────────┐
│            DATOS                │
│  Repositorio de usuarios        │
│  Acceso a BD exclusivamente     │
│  vía MCP (sin credenciales      │
│  en el código fuente)           │
└─────────────────────────────────┘
```

Ninguna capa puede comunicarse hacia arriba. Los secretos y credenciales nunca aparecen en el código fuente.

---

## Cómo se construyó: el marco PIV/OAC

El desarrollo no fue lineal. Siguió un protocolo de orquestación multi-agente definido en la rama `agent-configs`:

### 1. Especificación primero
Ningún agente escribió código sin que existiera un requerimiento funcional (RF) documentado en la especificación técnica del proyecto. La spec es la única fuente de verdad.

### 2. Equipo de agentes inferido automáticamente
El **Master Orchestrator** analizó el objetivo, identificó los dominios involucrados y compuso el equipo completo de agentes especializados antes de iniciar cualquier implementación.

### 3. Gates de seguridad y auditoría pre-código
Antes de que se escribiera cualquier línea de código, el plan de implementación pasó por dos agentes que corrieron en paralelo:

- **Security Agent:** verificó que el plan siguiera patrones de seguridad correctos, sin credenciales expuestas y con todos los requerimientos de seguridad cubiertos.
- **Audit Agent:** verificó la trazabilidad del plan a los requerimientos documentados y la coherencia arquitectónica.

Ambos debían aprobar. Un rechazo de cualquiera devolvía el plan para revisión.

### 4. Implementación aislada
El código se escribió en un worktree de Git independiente (`./worktrees/poc-login`) en su propia rama, sin contaminar ni `main` ni `agent-configs` durante el desarrollo.

### 5. Verificación final
Al cerrar la tarea, el Audit Agent generó logs de veracidad que documentan cada acción tomada, la eficiencia del contexto utilizado y la verificación explícita de cada requerimiento funcional contra el código entregado.

---

## Requerimientos funcionales verificados

| ID | Descripción | Estado |
|---|---|---|
| RF-01 | `POST /login` recibe email y contraseña | Verificado |
| RF-02 | Contraseñas validadas con BCrypt, nunca en texto plano | Verificado |
| RF-03 | JWT devuelto con expiración de 1 hora | Verificado |
| RF-04 | HTTP 401 con mensaje genérico ante credenciales inválidas | Verificado |

---

## Principios de seguridad aplicados

- **Zero-Trust en credenciales:** Ninguna credencial o secreto en el código fuente. Todo vía MCP.
- **Timing-safe comparison:** `bcrypt.checkpw()` se ejecuta incluso cuando el usuario no existe, para evitar ataques de temporización.
- **Mensaje de error unificado:** El sistema no distingue entre "usuario no existe" y "contraseña incorrecta" en la respuesta HTTP.
- **JWT con campo `jti`:** Soporte de revocación de tokens sin necesidad de estado en el servidor de aplicación.
- **Caché de tokens revocados con `dict`:** Lookup O(1) por clave de token ID, sin degradación bajo carga.

---

## Estructura del repositorio

```
main/
├── README.md          ← Este archivo
└── src/
    ├── transport/     ← Routers FastAPI, schemas de entrada/salida
    ├── domain/        ← Lógica de autenticación, caché de tokens
    └── data/          ← Repositorio de usuarios (acceso vía MCP)
```

---

## Rama `agent-configs`

Contiene toda la configuración del sistema de agentes que construyó este proyecto:
instrucciones operativas, definición de agentes, skills de seguridad, taxonomía,
protocolos de auditoría y memoria persistente entre sesiones.

Está intencionalmente aislada de `main` mediante `.gitignore` para mantener separada
la infraestructura de desarrollo de los artefactos de producción.
