import json
from amqplib import client_0_8 as amqp
from graypy.handler import make_message_dict
from logging import Filter
from logging.handlers import SocketHandler
from urlparse import urlparse


_ifnone = lambda v, x: x if v is None else v


class GELFRabbitHandler(SocketHandler):
    """RabbitMQ / Graylog Extended Log Format handler

    NOTE: this handler ingores all messages logged by amqplib.

    :param url: RabbitMQ URL (ex: amqp://guest:guest@localhost:5672/).
    :param exchange: RabbitMQ exchange. Default 'logging.gelf'.
        A queue binding must be defined on the server to prevent
        log messages from being dropped.
    :param debugging_fields: Send debug fields if true (the default).
    :param extra_fields: Send extra fields on the log record to graylog
        if true (the default).
    """

    def __init__(self, url, exchange='logging.gelf', debugging_fields=True,
            extra_fields=True, fqdn=False):
        self.url = url
        parsed = urlparse(url)
        if parsed.scheme != 'amqp':
            raise ValueError('invalid URL scheme (expected "amqp"): %s' % url)
        host = parsed.hostname or 'localhost'
        port = _ifnone(parsed.port, 5672)
        self.cn_args = {
            'host': '%s:%s' % (host, port),
            'username': _ifnone(parsed.username, 'guest'),
            'password': _ifnone(parsed.password, 'guest'),
            'virtual_host': '/',
            'insist': False,
        }
        self.exchange = exchange
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.fqdn = fqdn
        SocketHandler.__init__(self, host, port)
        self.addFilter(ExcludeFilter('amqplib'))

    def makeSocket(self, timeout=1):
        return RabbitSocket(self.cn_args, timeout, self.exchange)

    def makePickle(self, record):
        message_dict = make_message_dict(
            record, self.debugging_fields, self.extra_fields, self.fqdn)
        return json.dumps(message_dict)


class RabbitSocket(object):

    def __init__(self, cn_args, timeout, exchange):
        self.cn_args = cn_args
        self.timeout = timeout
        self.exchange = exchange
        self.connection = amqp.Connection(
            connection_timeout=timeout, **self.cn_args)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange,
            type='fanout',
            durable=True,
            auto_delete=False,
        )

    def sendall(self, data):
        msg = amqp.Message(data, delivery_mode=2)
        self.channel.basic_publish(msg, exchange=self.exchange)

    def close(self):
        try:
            self.connection.close()
        except Exception:
            pass


class ExcludeFilter(Filter):

    def __init__(self, name):
        """Initialize filter.

        Initialize with the name of the logger which, together with its
        children, will have its events excluded (filtered out).
        """
        if not name:
            raise ValueError('ExcludeFilter requires a non-empty name')
        self.name = name
        self.nlen = len(name)

    def filter(self, record):
        return not (record.name.startswith(self.name) and (
            len(record.name) == self.nlen or record.name[self.nlen] == "."))
