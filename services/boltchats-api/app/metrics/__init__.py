"""
Prometheus metrics for boltchats-api

Tracks:
- HTTP request metrics (latency, count, errors)
- Database operation metrics
- Redis operation metrics
- Business logic metrics (messages sent, conversations created)
"""

from prometheus_client import Counter, Histogram, Gauge
import time


# ─────────────────────────────────────────────────────────────
# HTTP Metrics
# ─────────────────────────────────────────────────────────────

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 500, 1000, 5000, 10000)
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 500, 1000, 5000, 10000, 50000)
)

# ─────────────────────────────────────────────────────────────
# Database Metrics
# ─────────────────────────────────────────────────────────────

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['collection', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

db_query_errors_total = Counter(
    'db_query_errors_total',
    'Total database query errors',
    ['collection', 'operation', 'error_type']
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_query_count = Counter(
    'db_query_count',
    'Total database queries executed',
    ['collection', 'operation']
)

# ─────────────────────────────────────────────────────────────
# Redis Metrics
# ─────────────────────────────────────────────────────────────

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5)
)

redis_operation_errors_total = Counter(
    'redis_operation_errors_total',
    'Total Redis operation errors',
    ['operation', 'error_type']
)

redis_key_hits_total = Counter(
    'redis_key_hits_total',
    'Total Redis cache hits',
    ['key_pattern']
)

redis_key_misses_total = Counter(
    'redis_key_misses_total',
    'Total Redis cache misses',
    ['key_pattern']
)

# ─────────────────────────────────────────────────────────────
# Business Logic Metrics
# ─────────────────────────────────────────────────────────────

messages_sent_total = Counter(
    'messages_sent_total',
    'Total messages sent',
    ['channel', 'status']
)

conversations_created_total = Counter(
    'conversations_created_total',
    'Total conversations created',
    ['channel']
)

conversations_active = Gauge(
    'conversations_active',
    'Active conversations',
    ['organization_id', 'status']
)

users_active = Gauge(
    'users_active',
    'Active users',
    ['organization_id']
)

integrations_active = Gauge(
    'integrations_active',
    'Active integrations',
    ['provider', 'status']
)

webhook_deliveries_total = Counter(
    'webhook_deliveries_total',
    'Total webhook deliveries',
    ['provider', 'status']
)

webhook_delivery_duration_seconds = Histogram(
    'webhook_delivery_duration_seconds',
    'Webhook delivery duration in seconds',
    ['provider'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ─────────────────────────────────────────────────────────────
# Authentication Metrics
# ─────────────────────────────────────────────────────────────

login_attempts_total = Counter(
    'login_attempts_total',
    'Total login attempts',
    ['status']  # success, failed
)

login_duration_seconds = Histogram(
    'login_duration_seconds',
    'Login duration in seconds',
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
)

token_validations_total = Counter(
    'token_validations_total',
    'Total token validations',
    ['status']  # valid, expired, invalid
)

# ─────────────────────────────────────────────────────────────
# Permission Metrics
# ─────────────────────────────────────────────────────────────

permission_checks_total = Counter(
    'permission_checks_total',
    'Total permission checks',
    ['resource', 'result']  # result: allowed, denied
)

permission_cache_hits = Counter(
    'permission_cache_hits',
    'Permission cache hits'
)

permission_cache_misses = Counter(
    'permission_cache_misses',
    'Permission cache misses'
)

# ─────────────────────────────────────────────────────────────
# Health Metrics
# ─────────────────────────────────────────────────────────────

health_check_duration_seconds = Histogram(
    'health_check_duration_seconds',
    'Health check duration in seconds',
    ['component'],  # mongodb, redis, etc.
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0)
)

service_health = Gauge(
    'service_health',
    'Service health status (1=healthy, 0=unhealthy)',
    ['component']
)
