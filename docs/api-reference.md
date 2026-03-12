# Mini Platform API Reference

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints except `POST /auth/login` require a valid JWT access token in the `Authorization` header:
```
Authorization: Bearer <access_token>
```

### JWT Token Structure
```json
{
  "sub": "user_id",
  "email": "user@test.com",
  "role": "ADMIN",
  "jti": "uuid4-string",
  "type": "access",
  "exp": 1234567890
}
```

- Access tokens expire after **1 hour**
- Refresh tokens expire after **24 hours**

---

## Roles and Permissions (RF-05)

| Role | Hierarchy | Rate Limit |
|------|-----------|------------|
| ADMIN | 3 (highest) | 100 req/min |
| EDITOR | 2 | 30 req/min |
| VIEWER | 1 (lowest) | 10 req/min |

### Permission Matrix

| Endpoint | Method | VIEWER | EDITOR | ADMIN |
|----------|--------|--------|--------|-------|
| `/resources` | GET | Yes | Yes | Yes |
| `/resources` | POST | No | Yes | Yes |
| `/resources/{id}` | PUT | No | Yes | Yes |
| `/resources/{id}` | DELETE | No | No | Yes |
| `/admin/audit-log` | GET | No | No | Yes |

---

## Endpoints

### POST /auth/login (RF-01)
Authenticate a user and receive a token pair.

**Request:**
```json
{
  "email": "admin@test.com",
  "password": "Admin123!"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Response 401:**
```json
{
  "detail": "Credenciales invalidas."
}
```

---

### POST /auth/refresh (RF-02)
Obtain a new access token using a valid refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Response 401:** Token invalid or revoked.

---

### POST /auth/logout (RF-03)
Revoke the current access token by adding its `jti` to the revoked tokens cache.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
{
  "detail": "Token revocado exitosamente."
}
```

---

### GET /resources (RF-06)
List all resources. Requires VIEWER, EDITOR, or ADMIN role.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
[
  {
    "id": 1,
    "title": "Example",
    "description": "An example resource",
    "owner_id": "user_admin_001"
  }
]
```

---

### POST /resources (RF-06)
Create a new resource. Requires EDITOR or ADMIN role.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "title": "New Resource",
  "description": "Description here"
}
```

**Response 201:**
```json
{
  "id": 1,
  "title": "New Resource",
  "description": "Description here",
  "owner_id": "user_editor_001"
}
```

---

### PUT /resources/{id} (RF-06)
Update an existing resource. Requires EDITOR or ADMIN role.

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "title": "Updated Title"
}
```

**Response 200:** Updated resource object.
**Response 404:** Resource not found.

---

### DELETE /resources/{id} (RF-06)
Delete a resource. Requires ADMIN role only.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
{
  "detail": "Recurso eliminado."
}
```

**Response 404:** Resource not found.

---

### GET /admin/audit-log (RF-08)
View the audit trail. Requires ADMIN role only.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
[
  {
    "user_id": "user_admin_001",
    "role": "ADMIN",
    "endpoint": "/resources",
    "method": "GET",
    "timestamp": "2026-03-12T10:00:00Z",
    "status_code": 200
  }
]
```

---

## Error Codes (RF-09)

| Code | Meaning | Message |
|------|---------|---------|
| 401 | Invalid credentials or revoked token | "Credenciales invalidas." |
| 403 | Insufficient permissions | "Permisos insuficientes." |
| 404 | Resource not found | "Recurso no encontrado." |
| 429 | Rate limit exceeded | "Limite de solicitudes excedido." |
| 422 | Validation error | Pydantic validation details |

All error messages are generic and never reveal sensitive information.

---

## Test Users

| Email | Password | Role |
|-------|----------|------|
| admin@test.com | Admin123! | ADMIN |
| editor@test.com | Editor123! | EDITOR |
| viewer@test.com | Viewer123! | VIEWER |

---

## Rate Limiting (RF-07)

Sliding window rate limiting per user. Limits are based on role:
- VIEWER: 10 requests/minute
- EDITOR: 30 requests/minute
- ADMIN: 100 requests/minute

When exceeded, returns HTTP 429.
