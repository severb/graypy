import json
from logging.handlers import SocketHandler

from graypy.handler import make_message_dict


class GELFTCPHandler(SocketHandler):
    """Graylog Extended Log Format handler using TCP

    NOTE: this handler ingores all messages logged by amqplib.

    :param host: The host of the graylog server.
    :param port: The port of the graylog server (default 12201).
    :param debugging_fields: Send debug fields if true (the default).
    :param extra_fields: Send extra fields on the log record to graylog
        if true (the default).
    :param fqdn: Use fully qualified domain name of localhost as source
        host (socket.getfqdn()).
    :param localname: Use specified hostname as source host.
    :param facility: Replace facility with specified value. If specified,
        record.name will be passed as `logger` parameter.
    """

    def __init__(self, host, port=12201, debugging_fields=True, extra_fields=True, fqdn=False, localname=None,
                 facility=None):
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.fqdn = fqdn
        self.localname = localname
        self.facility = facility
        GELFTCPHandler.__init__(self, host, port)

    def makePickle(self, record):
        message_dict = make_message_dict(
            record, self.debugging_fields, self.extra_fields, self.fqdn, self.localname,
            self.facility)
        return json.dumps(message_dict)


