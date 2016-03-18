import datetime
import sys
import logging
import json
import zlib
import traceback
import struct
import random
import socket
import math
from logging.handlers import DatagramHandler

PY3 = sys.version_info[0] == 3
WAN_CHUNK, LAN_CHUNK = 1420, 8154

if PY3:
    data, text = bytes, str
else:
    data, text = str, unicode


class GELFHandler(DatagramHandler):
    """Graylog Extended Log Format handler

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
    """

    def __init__(self, host, port=12201, chunk_size=WAN_CHUNK,
            debugging_fields=True, extra_fields=True, fqdn=False,
            localname=None, facility=None, level_names=False):
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.chunk_size = chunk_size
        self.fqdn = fqdn
        self.localname = localname
        self.facility = facility
        self.level_names = level_names
        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        if len(s) < self.chunk_size:
            DatagramHandler.send(self, s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                DatagramHandler.send(self, chunk)

    def makePickle(self, record):
        message_dict = make_message_dict(
            record, self.debugging_fields, self.extra_fields, self.fqdn,
            self.localname, self.level_names, self.facility)
        return zlib.compress(message_to_pickle(message_dict))


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
                      level_names, facility=None):
    if fqdn:
        host = socket.getfqdn()
    elif localname:
        host = localname
    else:
        host = socket.gethostname()
    fields = {'version': "1.0",
        'host': host,
        'short_message': record.getMessage(),
        'full_message': get_full_message(record.exc_info, record.getMessage()),
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

SYSLOG_LEVELS = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


def get_full_message(exc_info, message):
    return '\n'.join(traceback.format_exception(*exc_info)) if exc_info else message


def add_extra_fields(message_dict, record):
    # skip_list is used to filter additional fields in a log message.
    # It contains all attributes listed in
    # http://docs.python.org/library/logging.html#logrecord-attributes
    # plus exc_text, which is only found in the logging module source,
    # and id, which is prohibited by the GELF format.
    skip_list = (
        'args', 'asctime', 'created', 'exc_info',  'exc_text', 'filename',
        'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
        'msecs', 'message', 'msg', 'name', 'pathname', 'process',
        'processName', 'relativeCreated', 'thread', 'threadName')

    for key, value in record.__dict__.items():
        if key not in skip_list and not key.startswith('_'):
            message_dict['_%s' % key] = value
    return message_dict


def smarter_repr(obj):
    """ convert JSON incompatible object to string"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return repr(obj)


def message_to_pickle(obj):
    """ convert object to a JSON-encoded string"""
    obj = sanitize(obj)
    serialized = json.dumps(obj, separators=',:', default=smarter_repr)
    return serialized.encode('utf-8')


def sanitize(obj):
    """ convert all strings records of the object to unicode """
    if isinstance(obj, dict):
        return dict((sanitize(k), sanitize(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return obj.__class__([sanitize(i) for i in obj])
    if isinstance(obj, data):
        obj = obj.decode('utf-8', errors='replace')
    return obj
