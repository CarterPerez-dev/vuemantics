"""
ⒸAngelaMos | 2026
Dramatiq broker configuration for background tasks
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import (
    AgeLimit,
    TimeLimit,
    Callbacks,
    Pipelines,
    Prometheus,
    CurrentMessage,
    Retries,
)

import config

# EXTREME timeouts for multi-hour batch processing
# User requirement: Can process for DAYS without timing out
TASK_TIME_LIMIT = 7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds
TASK_AGE_LIMIT = 7 * 24 * 60 * 60 * 1000  # 7 days in milliseconds

# Redis broker for task queue
broker = RedisBroker(
    url=config.settings.redis_url,
    # Connection pool settings for long-running tasks
    max_connections=50,
    # Socket keepalive to prevent connection drops during long tasks
    socket_keepalive=True,
    socket_keepalive_options={
        1: 1,  # TCP_KEEPIDLE
        2: 1,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    },
)

# Add middleware for robustness
broker.add_middleware(Retries(max_retries=1, retry_when=lambda r, e: True))
broker.add_middleware(AgeLimit(max_age=TASK_AGE_LIMIT))
broker.add_middleware(TimeLimit(time_limit=TASK_TIME_LIMIT))
broker.add_middleware(Callbacks())
broker.add_middleware(Pipelines())
broker.add_middleware(CurrentMessage())

# Set as default broker
dramatiq.set_broker(broker)
