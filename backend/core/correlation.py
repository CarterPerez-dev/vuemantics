"""
ⒸAngelaMos | 2026
correlation.py
"""

import time
import uuid
import logging
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger(__name__)

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Correlation ID middleware for distributed tracing and request tracking

    Features:
    - Accepts existing correlation ID
      from upstream services via X-Correlation-ID header
    - Generates new UUID if no correlation ID provided
    - Tracks request timing and performance
    - Logs request lifecycle with correlation ID
    - Exposes correlation ID in response headers
    """
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4()),
        )

        request.state.correlation_id = correlation_id

        start_time = time.time()
        logger.info(
            "[%s] %s %s",
            correlation_id,
            request.method,
            request.url.path
        )

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            "[%s] %s %s - status=%s duration=%.3fs",
            correlation_id,
            request.method,
            request.url.path,
            response.status_code,
            duration
        )

        response.headers["X-Correlation-ID"] = correlation_id
        return response
