"""
ⒸAngelaMos | 2026
Dramatiq broker config for background tasks
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import (
    AgeLimit,
    TimeLimit,
    Callbacks,
    Pipelines,
    Retries,
    CurrentMessage,
)

import config

TASK_TIME_LIMIT = 7 * 24 * 60 * 60 * 1000  # 7 days
TASK_AGE_LIMIT = 7 * 24 * 60 * 60 * 1000  # 7 days

broker = RedisBroker(
    url = config.settings.redis_url,
    max_connections = 50,
    socket_keepalive = True,
    socket_keepalive_options = {
        1: 1,  # TCP_KEEPIDLE
        2: 1,  # TCP_KEEPINTVL
        3: 3,  # TCP_KEEPCNT
    },
)

broker.add_middleware(
    Retries(max_retries = 1,
            retry_when = lambda _r, _e: True)
)
broker.add_middleware(AgeLimit(max_age = TASK_AGE_LIMIT))
broker.add_middleware(TimeLimit(time_limit = TASK_TIME_LIMIT))
broker.add_middleware(Callbacks())
broker.add_middleware(Pipelines())
broker.add_middleware(CurrentMessage())

dramatiq.set_broker(broker)
