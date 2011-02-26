import logging
import json
import zlib
import traceback
import struct
import random
from socket import gethostname
from logging.handlers import DatagramHandler

WAN, LAN = 1, 2
_CHUNK_SIZE = {WAN: 1420, LAN: 8154}
_VERSION = "1.0"
_PY_TO_SYSLOG = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}

class GELFHandler(DatagramHandler):
    def __init__(self, host, port, network=1):
        self.chunk_size = _CHUNK_SIZE[network]
        self.version = _VERSION
        self.hostname = gethostname()
        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        if len(s) < self.chunk_size:
            DatagramHandler.send(self, s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                print 'chunked'
                DatagramHandler.send(self, chunk)

    def makePickle(self, record):
        message_dict = self.make_message_dict(record)
        return zlib.compress(json.dumps(message_dict))

    def make_message_dict(self, record):
        full_message = ''
        if record.exc_info:
            full_message = traceback.format_exc(record.exc_info)
        level = record.levelno
        if level in _PY_TO_SYSLOG:
            level = _PY_TO_SYSLOG[level]
        return {
            'version': self.version,
            'host': self.hostname,
            'short_message': record.getMessage(),
            'full_message': full_message,
            'timestamp': record.created,
            'level': level,
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
        self.msg_id = struct.pack('Q', random.randint(0, 0xFFFFFFFFFFFFFFFF))

    def __iter__(self):
        return self.chunks()

    def chunks(self):
        sequence = 0
        chunks = (self.message[i:i+self.size]
                    for i in range(0, len(self.message), self.size))
        for chunk in chunks:
            seq = struct.pack('>H', sequence)
            yield '\x1e\x0f' + self.msg_id*4 + seq + self.pieces + chunk
            sequence += 1
