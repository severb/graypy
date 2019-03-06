#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Logging Handlers that send messages in GELF (Graylog Extended Log Format)"""

import datetime
import json
import logging
import math
import random
import socket
import ssl
import struct
import sys
import traceback
import zlib
from logging.handlers import DatagramHandler, SocketHandler

PY3 = sys.version_info[0] == 3
WAN_CHUNK, LAN_CHUNK = 1420, 8154

if PY3:
    data, text = bytes, str
else:
    data, text = str, unicode  # pylint: disable=undefined-variable

SYSLOG_LEVELS = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


class BaseGELFHandler(object):
    def __init__(self, host, port=12201, chunk_size=WAN_CHUNK,
                 debugging_fields=True, extra_fields=True, fqdn=False,
                 localname=None, facility=None, level_names=False,
                 compress=True):
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.chunk_size = chunk_size
        self.fqdn = fqdn
        self.localname = localname
        self.facility = facility
        self.level_names = level_names
        self.compress = compress
        self.formatter = None

    def setFormatter(self, fmt):
        """Set the formatter for this handler

        :param fmt: The :class:`logging.Formatter` to be applied to
            the GLEF log's ``short_message`` and ``full_message``
        """
        self.formatter = fmt

    def makePickle(self, record):
        message_dict = make_message_dict(
            record, self.debugging_fields, self.extra_fields, self.fqdn,
            self.localname, self.level_names, self.facility, self.formatter)
        packed = message_to_pickle(message_dict)
        frame = zlib.compress(packed) if self.compress else packed
        return frame


class GELFHandler(BaseGELFHandler, DatagramHandler):
    """Graylog Extended Log Format UDP handler

    :param host: The host of the graylog server.
    :param port: The port of the graylog server (default 12201).
    :param chunk_size: Message chunk size. Messages larger than this
        size will be sent to graylog in multiple chunks. Defaults to
        `WAN_CHUNK=1420`.
    :param debugging_fields: Send debug fields if true (the default).
    :param extra_fields: Send extra fields on the log record to graylog
        if true (the default).
    :param fqdn: Use fully qualified domain name of localhost as source
        host (socket.getfqdn()).
    :param localname: Use specified hostname as source host.
    :param facility: Replace facility with specified value. If specified,
        record.name will be passed as `logger` parameter.
    :param level_names: Allows the use of string error level names instead
        of numerical values. Defaults to False
    :param compress: Use message compression. Defaults to True
    """

    def __init__(self, host, port=12201, chunk_size=WAN_CHUNK,
                 debugging_fields=True, extra_fields=True, fqdn=False,
                 localname=None, facility=None, level_names=False,
                 compress=True):
        BaseGELFHandler.__init__(self, host, port, chunk_size,
                                 debugging_fields, extra_fields, fqdn,
                                 localname, facility, level_names, compress)
        DatagramHandler.__init__(self, host, int(port))

    def send(self, s):
        if len(s) < self.chunk_size:
            DatagramHandler.send(self, s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                DatagramHandler.send(self, chunk)


# TODO: Write tests
class GELFTcpHandler(BaseGELFHandler, SocketHandler):
    """Graylog Extended Log Format TCP handler

    :param host: The host of the graylog server.
    :param port: The port of the graylog server (default 12201).
    :param chunk_size: Message chunk size. Messages larger than this
        size will be sent to graylog in multiple chunks. Defaults to
        `WAN_CHUNK=1420`.
    :param debugging_fields: Send debug fields if true (the default).
    :param extra_fields: Send extra fields on the log record to graylog
        if true (the default).
    :param fqdn: Use fully qualified domain name of localhost as source
        host (socket.getfqdn()).
    :param localname: Use specified hostname as source host.
    :param facility: Replace facility with specified value. If specified,
        record.name will be passed as `logger` parameter.
    :param level_names: Allows the use of string error level names instead
        of numerical values. Defaults to False
    :param tls: Use transport layer security on connection to graylog
        if true (not the default)
    :param tls_server_name: If using TLS, specify the name of the host
        to which the connection is being made. If not specified, hostname
        checking will not be performed.
    :param tls_cafile: If using TLS, optionally specify a file with a set
        of certificate authority certificates to use in certificate
        validation.
    :param tls_capath: If using TLS, optionally specify a path to files
        with a set of certificate authority certificates to use in
        certificate validation.
    :param tls_cadata: If using TLS, optionally specify an object with
        a set of certificate authority certificates to use in certificate
        validation.
    :param tls_client_cert: If using TLS, optionally specify a certificate
        to authenticate the client to the graylog server.
    :param tls_client_key: If using TLS, optionally specify a key file
        corresponding to the client certificate.
    :param tls_client_password: If using TLS, optionally specify a
        password corresponding to the client key file.
    """

    def __init__(self, host, port=12201, chunk_size=WAN_CHUNK,
                 debugging_fields=True, extra_fields=True, fqdn=False,
                 localname=None, facility=None, level_names=False,
                 tls=False, tls_server_name=None, tls_cafile=None,
                 tls_capath=None, tls_cadata=None, tls_client_cert=None,
                 tls_client_key=None, tls_client_password=None):
        BaseGELFHandler.__init__(self, host, port, chunk_size,
                                 debugging_fields, extra_fields, fqdn,
                                 localname, facility, level_names, False)
        SocketHandler.__init__(self, host, int(port))
        self.tls = tls
        if self.tls:
            self.tls_cafile = tls_cafile
            self.tls_capath = tls_capath
            self.tls_cadata = tls_cadata
            self.tls_client_cert = tls_client_cert
            self.tls_client_key = tls_client_key
            self.tls_client_password = tls_client_password

            self.ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH, cafile=self.tls_cafile,
                capath=self.tls_capath, cadata=self.tls_cadata
            )
            self.tls_server_name = tls_server_name
            self.ssl_context.check_hostname = (self.tls_server_name
                                               is not None)
            if self.tls_client_cert is not None:
                self.ssl_context.load_cert_chain(self.tls_client_cert,
                                                 self.tls_client_key,
                                                 self.tls_client_password)

    def makeSocket(self, timeout=None):
        """Override SocketHandler.makeSocket, to allow creating
        wrapped TLS sockets.
        """
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

        if self.tls:
            sock = self.ssl_context.wrap_socket(
                sock=sock,
                server_side=False,
                server_hostname=self.tls_server_name
            )

        sock.connect((self.host, self.port))
        return sock

    def makePickle(self, record):
        # TCP frame object needs to be null terminated
        return BaseGELFHandler.makePickle(self, record) + b'\x00'


class ChunkedGELF(object):
    def __init__(self, message, size):
        self.message = message
        self.size = size
        self.pieces = struct.pack('B', int(math.ceil(len(message) * 1.0/size)))
        self.id = struct.pack('Q', random.randint(0, 0xFFFFFFFFFFFFFFFF))

    def message_chunks(self):
        return (self.message[i:i + self.size] for i
                in range(0, len(self.message), self.size))

    def encode(self, sequence, chunk):
        return b''.join([
            b'\x1e\x0f',
            self.id,
            struct.pack('B', sequence),
            self.pieces,
            chunk
        ])

    def __iter__(self):
        for sequence, chunk in enumerate(self.message_chunks()):
            yield self.encode(sequence, chunk)


def make_message_dict(record, debugging_fields, extra_fields, fqdn, localname,
                      level_names, facility=None, formatter=None):
    if fqdn:
        host = socket.getfqdn()
    elif localname:
        host = localname
    else:
        host = socket.gethostname()
    fields = {
        'version': "1.0",
        'host': host,
        'short_message': formatter.format(record) if formatter else record.getMessage(),
        'full_message': formatter.format(record) if formatter else get_full_message(record),
        'timestamp': record.created,
        'level': SYSLOG_LEVELS.get(record.levelno, record.levelno),
        'facility': facility or record.name,
    }

    if level_names:
        fields['level_name'] = logging.getLevelName(record.levelno)

    if facility is not None:
        fields.update({
            '_logger': record.name
        })

    if debugging_fields:
        fields.update({
            'file': record.pathname,
            'line': record.lineno,
            '_function': record.funcName,
            '_pid': record.process,
            '_thread_name': record.threadName,
        })
        # record.processName was added in Python 2.6.2
        pn = getattr(record, 'processName', None)
        if pn is not None:
            fields['_process_name'] = pn
    if extra_fields:
        fields = add_extra_fields(fields, record)
    return fields


def get_full_message(record):
    """Given a logging.LogRecord return its full message"""
    # format exception information if present
    if record.exc_info:
        return '\n'.join(traceback.format_exception(*record.exc_info))
    # use pre-formatted exception information in cases where the primary
    # exception information was removed, eg. for LogRecord serialization
    if record.exc_text:
        return record.exc_text
    return record.getMessage()


def add_extra_fields(message_dict, record):
    # skip_list is used to filter additional fields in a log message.
    # It contains all attributes listed in
    # http://docs.python.org/library/logging.html#logrecord-attributes
    # plus exc_text, which is only found in the logging module source,
    # and id, which is prohibited by the GELF format.
    skip_list = (
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
        'msecs', 'message', 'msg', 'name', 'pathname', 'process',
        'processName', 'relativeCreated', 'thread', 'threadName')

    for key, value in record.__dict__.items():
        if key not in skip_list and not key.startswith('_'):
            message_dict['_%s' % key] = value
    return message_dict


def smarter_repr(obj):
    """Convert JSON incompatible object to string"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
      
    return repr(obj)

def introspective_repr(obj):
    """ introspective repr() - alternative to smarter_repr() """

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if isinstance(obj, enum.Enum):
        return repr({obj.name: obj.value})
    
    return repr(dir(obj))

def message_to_pickle(obj):
    """Convert object to a JSON-encoded string"""
    obj = sanitize(obj)
    serialized = json.dumps(obj, separators=',:', default=smarter_repr)
    return serialized.encode('utf-8')


def sanitize(obj):
    """Convert all strings records of the object to unicode"""
    if isinstance(obj, dict):
        return dict((sanitize(k), sanitize(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return obj.__class__([sanitize(i) for i in obj])
    if isinstance(obj, data):
        obj = obj.decode('utf-8', errors='replace')
    return obj
