# PLAN: T-01 core-schemas
## Domain Orchestrator: DomainOrchestrator-T01
## RF cubiertos: RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08

## Objetivo
Crear los schemas Pydantic compartidos y el almacenamiento in-memory que todas las demas tareas consumiran.

## Modulos a crear

### Experto-1: src/schemas/
- `src/schemas/__init__.py` — re-exports
- `src/schemas/roles.py` — Enum Role(ADMIN, EDITOR, VIEWER), Permission enum
- `src/schemas/tokens.py` — TokenPayload, TokenPair, RefreshRequest
- `src/schemas/users.py` — UserInDB, LoginRequest, UserResponse
- `src/schemas/resources.py` — Resource, ResourceCreate, ResourceUpdate
- `src/schemas/errors.py` — ErrorResponse

### Experto-2: src/data/
- `src/data/__init__.py`
- `src/data/store.py` — Estado global in-memory:
  - users: dict[str, UserInDB] (indexado por email)
  - resources: list[dict]
  - revoked_tokens: dict[str, float] (jti -> expiry timestamp, O(1))
  - rate_windows: dict[str, list[float]] (user_id -> timestamps)
  - audit_log: list[dict]
- `src/data/seed.py` — Usuarios predefinidos:
  - admin@test.com / Admin123! -> ADMIN
  - editor@test.com / Editor123! -> EDITOR
  - viewer@test.com / Viewer123! -> VIEWER
  - Passwords hasheados con BCrypt cost 12

## Decisiones de diseno
1. revoked_tokens usa dict (O(1) por jti), NO lista
2. Passwords se hashean en tiempo de carga del modulo seed.py usando bcrypt
3. JWT_SECRET_KEY NO aparece en ningun archivo de schemas ni data
4. UserInDB contiene hashed_password, pero UserResponse NO lo expone
5. Schema JWT acordado para coherencia con T-02 y T-03:
   ```
   {
     "sub": "user_id",
     "email": "user@test.com",
     "role": "ADMIN",
     "jti": "uuid4-string",
     "type": "access" | "refresh",
     "exp": unix_timestamp
   }
   ```

## Validacion de arquitectura
- src/schemas/ es capa compartida, no importa nada de transport/ ni domain/
- src/data/ solo importa de src/schemas/ (flujo unidireccional)
- Ninguna credencial hardcodeada (passwords se hashean via bcrypt)
