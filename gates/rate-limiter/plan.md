# PLAN: T-04 rate-limiter
## RF cubiertos: RF-07
## Archivo: src/domain/rate_limiter.py
## Funcion: check_rate_limit(user_id, role) -> bool
## Sliding window con dict[str, list[float]]
## Limites: VIEWER=10, EDITOR=30, ADMIN=100 por minuto
