import logging
import json
import zlib
import traceback
import struct
import random
import socket
import math
from logging.handlers import DatagramHandler
import sys

WAN_CHUNK, LAN_CHUNK = 1420, 8154
FULL_MESSAGE_KEYS = ("FULLMESSAGE", "FULL_MESSAGE", "MESSAGE")
SHORT_MESSAGE_KEYS = ("SHORTMESSAGE", "SHORT_MESSAGE", "MESSAGE")
SHORT_MESSAGE_LENGTH = 250
SYSLOG_LEVELS = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}

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
    """

    def __init__(self, host, port=12201, chunk_size=WAN_CHUNK,
            debugging_fields=True, extra_fields=True, fqdn=False, 
            localname=None, facility=None):
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.chunk_size = chunk_size
        self.facility = facility
        self.local_host_name = get_host_name(fqdn, localname)
        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        if len(s) < self.chunk_size:
            DatagramHandler.send(self, s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                DatagramHandler.send(self, chunk)

    def makePickle(self, record):
        message_dict = format_gelf_message(self, record)
        return zlib.compress(json.dumps(message_dict))


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
        return ''.join([
            '\x1e\x0f',
            self.id,
            struct.pack('B', sequence),
            self.pieces,
            chunk
        ])

    def __iter__(self):
        for sequence, chunk in enumerate(self.message_chunks()):
            yield self.encode(sequence, chunk)


def format_gelf_message(self, record):
    gelf_message = get_base_gelf_message(self, record)      
    build_message(self, gelf_message, record)
    add_extra_fields(gelf_message, record)
    return gelf_message


def build_message(self, gelf_message, record):
    """
    Builds the actual message fields and sets any additional fields 
    if the log message is a dictionary.
    """

    if isinstance(record.msg, dict):
        add_to_message(gelf_message, record.msg)

    gelf_message.update({ 
        'full_message': gelf_message.get('full_message') or get_full_message(record.exc_info)
    })

    gelf_message.update({ 
        'short_message': gelf_message.get('short_message') or gelf_message.get('full_message')[:SHORT_MESSAGE_LENGTH] or record.getMessage()[:SHORT_MESSAGE_LENGTH],
    })


def add_to_message(gelf_message, obj):
    """Add each entry in the dictionary as an additional field in the GELF message."""

    for key, value in obj.items():
        k = str(key)
        v = str(value)

        if k.upper() in FULL_MESSAGE_KEYS:
            gelf_message.update({ "full_message": v })
        elif k.upper() in SHORT_MESSAGE_KEYS:
            gelf_message.update({ "short_message": v[:SHORT_MESSAGE_LENGTH] })
        else:
            k = k if k.startswith('_') else '_%s' % k
            gelf_message[k] = v


def get_base_gelf_message(self, record):
    fields = {
        'facility': self.facility or record.name,
        'file': '',
        'host': self.local_host_name,
        'level': SYSLOG_LEVELS.get(record.levelno, record.levelno),
        'line': '',
        'timestamp': record.created,
        'version': '1.0',
        '_logger': record.name
    }

    #Add a bunch of debugging information
    if self.debugging_fields:
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

    return fields


def get_host_name(fqdn, localname):
    if fqdn:
        return socket.getfqdn()
    elif localname:
        return localname
    else:
        return socket.gethostname()


def get_full_message(exc_info):
    return '\n'.join(traceback.format_exception(*exc_info)) if exc_info else ''


def add_extra_fields(gelf_message, record):
    # skip_list is used to filter additional fields in a log message.
    # It contains all attributes listed in
    # http://docs.python.org/library/logging.html#logrecord-attributes
    # plus exc_text, which is only found in the logging module source,
    # and id, which is prohibited by the GELF format.
    skip_list = (
        'args', 'asctime', 'created', 'exc_info',  'exc_text', 'filename',
        'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
        'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
        'processName', 'relativeCreated', 'thread', 'threadName')

    for key, value in record.__dict__.items():
        if key not in skip_list and not key.startswith('_'):
            gelf_message['_%s' % key] = str(value)
