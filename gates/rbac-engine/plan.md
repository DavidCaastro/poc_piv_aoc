# PLAN: T-03 rbac-engine
## RF cubiertos: RF-05, RF-06

## Objetivo
Implementar motor RBAC con matriz de permisos explicita y centralizada.

## Archivo: src/domain/rbac_engine.py

## Funciones:
1. `check_permission(role: str, endpoint: str, method: str) -> bool`
2. `get_required_role(endpoint: str, method: str) -> Role | None`

## Matriz de permisos (RF-05 + RF-06):
- GET /resources: VIEWER, EDITOR, ADMIN
- POST /resources: EDITOR, ADMIN
- PUT /resources/{id}: EDITOR, ADMIN
- DELETE /resources/{id}: ADMIN
- GET /admin/audit-log: ADMIN

## Schema JWT consumido (acordado con T-02):
El campo "role" del token decodificado es un string (e.g. "ADMIN")
que se convierte a Role enum para verificacion.
