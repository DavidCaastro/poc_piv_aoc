# SKILL: Backend Security — FastAPI + JWT + BCrypt
> Skill de carga perezosa. Cargar SOLO cuando la tarea involucre autenticación, autorización o seguridad de endpoints.

## Contexto de Aplicación
- **Stack:** Python 3.10 + FastAPI
- **RF cubiertos:** RF-01, RF-02, RF-03, RF-04 (ver `project_spec.md`)
- **Arquitectura:** Capas — Transporte → Dominio → Datos

---

## Patrón 1: Estructura de Capas

> Estructura de carpetas, reglas de importación y patrones de implementación por capa en `skills/layered-architecture.md`.

Resumen: `transport/` → `domain/` → `data/`. Flujo unidireccional estricto. Nunca al revés.

---

## Patrón 2: Hashing de Contraseñas con BCrypt

```python
# domain/auth_service.py
import bcrypt

def hash_password(plain_password: str) -> str:
    """Genera hash BCrypt con salt automático (cost factor 12)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comparación timing-safe. Nunca comparar strings directamente."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
```

**Reglas de seguridad:**
- Nunca almacenar contraseñas en texto plano.
- Nunca loguear `plain_password` bajo ninguna circunstancia.
- Cost factor mínimo: 12 (ajustar según benchmark de hardware en producción).

---

## Patrón 3: Generación y Validación de JWT

```python
# domain/auth_service.py
import jwt
from datetime import datetime, timedelta, timezone

# La clave secreta llega SIEMPRE desde MCP o variable de entorno. Nunca hardcodeada.
def create_access_token(subject: str, secret_key: str, expires_delta_hours: int = 1) -> str:
    """Genera JWT firmado HS256 con expiración."""
    payload = {
        "sub": subject,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_delta_hours),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

def decode_access_token(token: str, secret_key: str) -> dict:
    """Valida firma y expiración. Lanza excepción si el token es inválido."""
    return jwt.decode(token, secret_key, algorithms=["HS256"])
```

---

## Patrón 4: Caché de Tokens con Dict (Hashmap)

Para invalidación de tokens (logout, revocación) se usa un **dict** en memoria:

```python
# domain/token_cache.py

# DECISIÓN DE ESTRUCTURA: Dict (Hashmap) — O(1) por clave
# Justificación: La operación crítica es lookup por token ID (jti).
# Un dict garantiza O(1) para insert, lookup y delete por clave string.
# Un array/lista sería O(n) para búsqueda por valor — inaceptable en producción.

_revoked_tokens: dict[str, datetime] = {}

def revoke_token(jti: str, expires_at: datetime) -> None:
    _revoked_tokens[jti] = expires_at

def is_token_revoked(jti: str) -> bool:
    return jti in _revoked_tokens

def purge_expired(now: datetime) -> None:
    """Limpieza periódica para evitar crecimiento ilimitado."""
    expired = [jti for jti, exp in _revoked_tokens.items() if exp < now]
    for jti in expired:
        del _revoked_tokens[jti]
```

**Nota:** En producción, reemplazar el dict en memoria por Redis vía MCP para persistencia distribuida.

---

## Patrón 5: Endpoint POST /login (Capa Transporte)

```python
# transport/auth_router.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, auth_service=Depends(get_auth_service)):
    token = await auth_service.authenticate(body.email, body.password)
    if not token:
        # RF-04: Mensaje genérico — no revelar si el fallo fue email o contraseña
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=token)
```

---

## Patrón 6: Sanitización de Errores (RF-04)

**Regla:** Los errores de autenticación NUNCA deben distinguir entre "usuario no existe" y "contraseña incorrecta". Siempre retornar el mismo mensaje genérico y el mismo HTTP 401.

```python
# INCORRECTO — revela información:
# raise HTTPException(404, "Usuario no encontrado")
# raise HTTPException(401, "Contraseña incorrecta")

# CORRECTO — mensaje unificado:
# raise HTTPException(401, "Credenciales inválidas.")
```

**Timing attacks:** Siempre ejecutar `verify_password` incluso si el usuario no existe (comparar contra hash ficticio) para evitar diferencias de tiempo medibles.

---

## Dependencias Requeridas

```txt
fastapi>=0.111.0
uvicorn>=0.29.0
python-jose[cryptography]>=3.3.0   # JWT
bcrypt>=4.1.0                       # Hashing
pydantic[email]>=2.7.0              # Validación
```

---

## Checklist de Seguridad Pre-Deploy

- [ ] Ninguna credencial hardcodeada en el código fuente
- [ ] SECRET_KEY obtenida exclusivamente desde MCP / variable de entorno
- [ ] Logs no contienen passwords, tokens completos ni emails en texto plano
- [ ] Cost factor BCrypt benchmarkeado (≥ 100ms en hardware objetivo)
- [ ] Endpoint /login con rate limiting activo
- [ ] JWT incluye campo `jti` para soporte de revocación
