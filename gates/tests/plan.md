# PLAN: T-06 tests
## RF cubiertos: RF-10

## Archivos:
- tests/conftest.py: fixtures
- tests/test_auth.py: login, refresh, logout, revoked token
- tests/test_rbac.py: privilege escalation scenarios
- tests/test_rate_limit.py: rate limiting
- tests/test_resources.py: CRUD with different roles
- requirements-test.txt: pytest, httpx, pytest-cov

## RF-10 mandatory scenarios:
1. Privilege escalation: VIEWER -> ADMIN endpoint -> 403
2. Revoked token -> 401
3. Rate limit: VIEWER > 10 req/min -> 429
4. Refresh with invalid token -> 401
5. EDITOR DELETE -> 403
