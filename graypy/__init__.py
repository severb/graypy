#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""graypy

Python logging handlers that send messages in the
Graylog Extended Log Format (GELF).

Modules:
 + :mod:`.handler` - Basic GELF Logging Handlers
 + :mod:`.rabbitmq` - RabbitMQ GELF Logging Handler
"""

from graypy.handler import (
    GELFUDPHandler,
    GELFTCPHandler,
    GELFTLSHandler,
    GELFHTTPHandler,
    WAN_CHUNK,
    LAN_CHUNK,
)

try:
    from graypy.rabbitmq import GELFRabbitHandler, ExcludeFilter
except ImportError:
    pass  # amqplib is probably not installed


__version__ = (2, 1, 0)
