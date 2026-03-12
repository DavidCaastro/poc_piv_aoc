# PLAN: T-02 auth-service
## Domain Orchestrator: DomainOrchestrator-T02
## RF cubiertos: RF-01, RF-02, RF-03, RF-04

## Objetivo
Implementar servicio de autenticacion completo: login, tokens JWT, revocacion.

## Archivo a crear
- `src/domain/__init__.py`
- `src/domain/auth_service.py`

## Funciones:
1. `verify_password(plain, hashed) -> bool` — timing-safe BCrypt comparison
2. `login(email, password) -> TokenPair | None` — authenticate user, return token pair
3. `create_token_pair(user) -> TokenPair` — generate access + refresh JWT tokens
4. `create_token(user, token_type, expires_delta) -> str` — generate single JWT
5. `verify_token(token) -> TokenPayload` — decode and validate JWT
6. `revoke_token(jti, exp) -> None` — add jti to revoked cache
7. `is_token_revoked(jti) -> bool` — check revocation cache
8. `refresh_tokens(refresh_token) -> TokenPair` — validate refresh token, issue new pair

## Schema JWT (acordado con T-03 via CoherenceAgent):
```json
{
  "sub": "user_id",
  "email": "user@test.com",
  "role": "ADMIN",
  "jti": "uuid4-string",
  "type": "access" | "refresh",
  "exp": unix_timestamp
}
```

## Seguridad:
- BCrypt cost >= 12
- verify_password SIEMPRE se ejecuta aunque usuario no exista (anti-timing)
- JWT_SECRET_KEY desde os.environ, fallback "test-secret-key-for-testing-only" SOLO para tests
- Dummy hash para anti-timing: generado con bcrypt al inicio del modulo
- Mensajes de error genericos (401, nunca distinguir email vs password)
