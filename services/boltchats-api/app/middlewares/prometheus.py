"""
Prometheus middleware for FastAPI

Captures HTTP metrics automatically (requests, latency, sizes)
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_size_bytes,
    http_response_size_bytes
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = request.url.path
        
        start_time = time.time()
        response = None
        
        try:
            # Calculate request size
            request_size = 0
            if request.headers.get('content-length'):
                request_size = int(request.headers.get('content-length', 0))
            
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as exc:
            status_code = 500
            raise
        
        finally:
            duration = time.time() - start_time
            
            # Normalize endpoint path (remove IDs for cleaner metrics)
            endpoint = self._normalize_path(path)
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
            
            # Response size is in response headers (only if response exists)
            if response and response.headers.get('content-length'):
                response_size = int(response.headers.get('content-length', 0))
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)
        
        return response
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize path to avoid high cardinality metrics.
        
        Examples:
            /api/users/123/messages/456 → /api/users/{id}/messages/{id}
            /api/conversations/abc → /api/conversations/{id}
        """
        import re
        # Replace UUIDs/ULIDs/numbers with {id}
        normalized = re.sub(
            r'/[0-9a-f]{8,}|/\d+',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        return normalized
