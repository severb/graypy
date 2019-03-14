#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""graypy

Python logging handler that sends messages in
Graylog Extended Log Format (GELF).

Modules:
 + :mod:`.handler` - Logging Handlers that send messages in GELF
 + :mod:`.rabbitmq` - RabbitMQ and BaseGELFHandler Logging Handler composition
"""

from graypy.handler import GELFUDPHandler, GELFTCPHandler, GELFTLSHandler, \
    GELFHTTPHandler, WAN_CHUNK, LAN_CHUNK

try:
    from graypy.rabbitmq import GELFRabbitHandler, ExcludeFilter
except ImportError:
    pass  # amqplib is probably not installed


__version__ = (0, 3, 2)
