#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Logging Handler integrating RabbitMQ and
Graylog Extended Log Format (GELF)"""

import json
from logging import Filter
from logging.handlers import SocketHandler

from amqplib import client_0_8 as amqp  # pylint: disable=import-error

from graypy.handler import BaseGELFHandler

try:
    from urllib.parse import urlparse, unquote
except ImportError:
    from urlparse import urlparse
    from urllib import unquote


_ifnone = lambda v, x: x if v is None else v


class GELFRabbitHandler(BaseGELFHandler, SocketHandler):
    """RabbitMQ / GELF handler

    .. note::

        This handler ignores all messages logged by amqplib.
    """

    def __init__(
        self,
        url,
        exchange="logging.gelf",
        exchange_type="fanout",
        virtual_host="/",
        routing_key="",
        **kwargs
    ):
        """Initialize the GELFRabbitHandler

        :param url: RabbitMQ URL (ex: amqp://guest:guest@localhost:5672/)
        :type url: str

        :param exchange: RabbitMQ exchange. A queue binding must be defined
            on the server to prevent GELF logs from being dropped.
        :type exchange: str

        :param exchange_type: RabbitMQ exchange type.
        :type exchange_type: str

        :param virtual_host:
        :type virtual_host: str

        :param routing_key:
        :type routing_key: str
        """
        self.url = url
        parsed = urlparse(url)
        if parsed.scheme != "amqp":
            raise ValueError('invalid URL scheme (expected "amqp"): %s' % url)
        host = parsed.hostname or "localhost"
        port = _ifnone(parsed.port, 5672)
        self.virtual_host = (
            virtual_host if not unquote(parsed.path[1:]) else unquote(parsed.path[1:])
        )
        self.cn_args = {
            "host": "%s:%s" % (host, port),
            "userid": _ifnone(parsed.username, "guest"),
            "password": _ifnone(parsed.password, "guest"),
            "virtual_host": self.virtual_host,
            "insist": False,
        }
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.routing_key = routing_key
        BaseGELFHandler.__init__(self, **kwargs)
        SocketHandler.__init__(self, host, port)
        self.addFilter(ExcludeFilter("amqplib"))

    def makeSocket(self, timeout=1):
        return RabbitSocket(
            self.cn_args, timeout, self.exchange, self.exchange_type, self.routing_key
        )

    def makePickle(self, record):
        message_dict = self._make_gelf_dict(record)
        return json.dumps(message_dict)


class RabbitSocket(object):
    def __init__(self, cn_args, timeout, exchange, exchange_type, routing_key):
        self.cn_args = cn_args
        self.timeout = timeout
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.routing_key = routing_key
        self.connection = amqp.Connection(connection_timeout=timeout, **self.cn_args)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange,
            type=self.exchange_type,
            durable=True,
            auto_delete=False,
        )

    def sendall(self, data):
        msg = amqp.Message(data, delivery_mode=2)
        self.channel.basic_publish(
            msg, exchange=self.exchange, routing_key=self.routing_key
        )

    def close(self):
        """Close the connection to the RabbitMQ socket"""
        try:
            self.connection.close()
        except Exception:
            pass


class ExcludeFilter(Filter):
    """A subclass of :class:`logging.Filter` which should be instantiated
    with the name of the logger which, together with its children, will have
    its events excluded (filtered out)"""

    def __init__(self, name):
        """Initialize the ExcludeFilter

        :param name: Name to match for within a :class:`logging.LogRecord`'s
            ``name`` field for filtering.
        :type name: str
        """
        if not name:
            raise ValueError("ExcludeFilter requires a non-empty name")
        Filter.__init__(self, name)

    def filter(self, record):
        return not (
            record.name.startswith(self.name)
            and (len(record.name) == self.nlen or record.name[self.nlen] == ".")
        )
