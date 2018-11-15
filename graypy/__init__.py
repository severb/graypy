#!/usr/bin/python
# -*- coding: utf-8 -*-

"""graypy

Python logging handler that sends messages in
GELF (Graylog Extended Log Format).



"""

from graypy.handler import GELFUDPHandler, GELFTCPHandler, WAN_CHUNK, LAN_CHUNK

try:
    from graypy.rabbitmq import GELFRabbitHandler, ExcludeFilter
except ImportError:
    pass  # amqplib is probably not installed


__version__ = (0, 3, 1)
