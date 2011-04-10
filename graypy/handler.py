import logging
import json
import zlib
import traceback
import struct
import random
from socket import gethostname
from logging.handlers import DatagramHandler


WAN_CHUNK, LAN_CHUNK = 1420, 8154


class GELFHandler(DatagramHandler):
    def __init__(self, host, port, chunk_size=WAN_CHUNK):
        self.chunk_size = chunk_size
        self.version = "1.0"
        self.hostname = gethostname()
        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        if len(s) < self.chunk_size:
            DatagramHandler.send(self, s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                DatagramHandler.send(self, chunk)

    def makePickle(self, record):
        message_dict = self.make_message_dict(record)
        return zlib.compress(json.dumps(message_dict))

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
        return {
            'version': self.version,
            'host': self.hostname,
            'short_message': record.getMessage(),
            'full_message': self.get_full_message(record.exc_info),
            'timestamp': record.created,
            'level': self.convert_level_to_syslog(record.levelno),
            'facility': record.name,
            'file': record.pathname,
            'line': record.lineno,
            '_function': record.funcName,
            '_pid': record.process,
            '_process_name': record.processName,
            '_thread_name': record.threadName,
        }


class ChunkedGELF(object):
    def __init__(self, message, size):
        self.message = message
        self.size = size
        self.pieces = struct.pack('>H', (len(message) / size) + 1)
        self.id = struct.pack('Q', random.randint(0, 0xFFFFFFFFFFFFFFFF)) * 4

    def message_chunks(self):
        return (self.message[i:i+self.size] for i
                    in range(0, len(self.message), self.size))

    def encode(self, sequence, chunk):
        return ''.join([
            '\x1e\x0f',
            self.id,
            struct.pack('>H', sequence),
            self.pieces,
            chunk
        ])    

    def __iter__(self):
        for sequence, chunk in enumerate(self.message_chunks()):
            yield self.encode(sequence, chunk)
