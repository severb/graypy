import logging
import warnings
try:
    from cjson import encode as jdumps
except ImportError:
    warnings.warn('cjson not used!')
    from json import dumps as jdumps

import zlib
import traceback
import struct
import random
import socket
from logging.handlers import DatagramHandler


WAN_CHUNK, LAN_CHUNK = 1420, 8154


class GELFHandler(DatagramHandler):
    def __init__(self, host, port, chunk_size=WAN_CHUNK, debugging_fields=True,
            extra_fields=True):
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields
        self.chunk_size = chunk_size
        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        if len(s) < self.chunk_size:
            DatagramHandler.send(self, s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                DatagramHandler.send(self, chunk)

    def makePickle(self, record):
        message_dict = {}
        for k,v in self.make_message_dict(record).iteritems():
            val = v
            if isinstance(v, str):
                val = v.decode()
            message_dict[k] = val
        return zlib.compress(jdumps(message_dict))

    def convert_level_to_syslog(self, level):
        return {
            logging.CRITICAL: 2,
            logging.ERROR: 3,
            logging.WARNING: 4,
            logging.INFO: 6,
            logging.DEBUG: 7,
        }.get(level, level)

    def get_full_message(self, exc_info):
        return traceback.format_exc(exc_info) if exc_info else ''

    def make_message_dict(self, record):
        fields = {'version': "1.0",
            'host': socket.gethostname(),
            'short_message': record.getMessage(),
            'full_message': self.get_full_message(record.exc_info),
            'timestamp': record.created,
            'level': self.convert_level_to_syslog(record.levelno),
            'facility': record.name,
        }
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
        if self.extra_fields:
            fields = self.add_extra_fields(fields, record)
        return fields

    def add_extra_fields(self, message_dict, record):
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
                message_dict['_%s' % key] = value

        return message_dict


class ChunkedGELF(object):
    def __init__(self, message, size):
        self.message = message
        self.size = size
        self.pieces = struct.pack('B', (len(message) / size) + 1)
        self.id = struct.pack('Q', random.randint(0, 0xFFFFFFFFFFFFFFFF))

    def message_chunks(self):
        return (self.message[i:i+self.size] for i
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
