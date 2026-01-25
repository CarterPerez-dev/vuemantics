"""
ⒸAngelaMos | 2026
Rate limiting configuration.
"""

from jose import jwt  # type: ignore[import-untyped]
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request



def get_identifier(request: Request) -> str:
    """
    Get rate limit identifier.

    Uses user ID if authenticated, otherwise falls back to IP address
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(  # pylint: disable=no-value-for-parameter
                token,
                "",  # key not needed when verify_signature=False
                options = {"verify_signature": False},
            )
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:  # noqa: S110
            pass

    return get_remote_address(request)


limiter = Limiter(
    key_func = get_identifier,
    default_limits = ["1000/hour"],
    headers_enabled = False,
    in_memory_fallback_enabled = True,
)
