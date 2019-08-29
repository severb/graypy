#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Logging Handlers that send messages in Graylog Extended Log Format (GELF)"""

import abc
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


WAN_CHUNK = 1420
LAN_CHUNK = 8154

if sys.version_info[0] == 3:  # check if python3+
    data, text = bytes, str
else:
    data, text = str, unicode  # pylint: disable=undefined-variable

# fixes for using ABC
if sys.version_info >= (3, 4):  # check if python3.4+
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta(str('ABC'), (), {})

try:
    import httplib
except ImportError:
    import http.client as httplib

SYSLOG_LEVELS = {
    logging.CRITICAL: 2,
    logging.ERROR: 3,
    logging.WARNING: 4,
    logging.INFO: 6,
    logging.DEBUG: 7,
}


class BaseGELFHandler(logging.Handler, ABC):
    """Abstract class defining the basic functionality of converting a
    :obj:`logging.LogRecord` into a GELF log. Provides the boilerplate for
    all GELF handlers defined within graypy."""

    def __init__(self, debugging_fields=True, extra_fields=True,
                 fqdn=False, localname=None, facility=None,
                 level_names=False, compress=True):
        """Initialize the BaseGELFHandler.

        :param debugging_fields: If :obj:`True` add debug fields from the
            log record into the GELF logs to be sent to Graylog.
        :type debugging_fields: bool

        :param extra_fields: If :obj:`True` add extra fields from the log
            record into the GELF logs to be sent to Graylog.
        :type extra_fields: bool

        :param fqdn: If :obj:`True` use the fully qualified domain name of
            localhost to populate the ``host`` GELF field.
        :type fqdn: bool

        :param localname: If specified and ``fqdn`` is :obj:`False`, use the
            specified hostname to populate the ``host`` GELF field.
        :type localname: str or None

        :param facility: If specified, replace the ``facility`` GELF field
            with the specified value. Also add a additional ``_logger``
            GELF field containing the ``LogRecord.name``.
        :type facility: str

        :param level_names: If :obj:`True` use python logging error level name
            strings instead of syslog numerical values.
        :type level_names: bool

        :param compress: If :obj:`True` compress the GELF message before
            sending it to the Graylog server.
        :type compress: bool
        """
        logging.Handler.__init__(self)
        self.debugging_fields = debugging_fields
        self.extra_fields = extra_fields

        if fqdn and localname:
            raise ValueError(
                "cannot specify 'fqdn' and 'localname' arguments together")

        self.fqdn = fqdn
        self.localname = localname
        self.facility = facility
        self.level_names = level_names
        self.compress = compress

    def makePickle(self, record):
        """Convert a :class:`logging.LogRecord` into bytes representing
        a GELF log

        :param record: :class:`logging.LogRecord` to convert into a GELF log.
        :type record: logging.LogRecord

        :return: bytes representing a GELF log.
        :rtype: bytes
        """
        gelf_dict = self._make_gelf_dict(record)
        packed = self._pack_gelf_dict(gelf_dict)
        pickle = zlib.compress(packed) if self.compress else packed
        return pickle

    def _make_gelf_dict(self, record):
        """Create a dictionary representing a GELF log from a
        python :class:`logging.LogRecord`

        :param record: :class:`logging.LogRecord` to create a GELF log from.
        :type record: logging.LogRecord

        :return: dictionary representing a GELF log.
        :rtype: dict
        """
        # construct the base GELF format
        gelf_dict = {
            'version': "1.0",
            'host': self._resolve_host(self.fqdn, self.localname),
            'short_message': self.formatter.format(record) if self.formatter else record.getMessage(),
            'timestamp': record.created,
            'level': SYSLOG_LEVELS.get(record.levelno, record.levelno),
            'facility': self.facility or record.name,
        }

        # add in specified optional extras
        self._add_full_message(gelf_dict, record)
        if self.level_names:
            self._add_level_names(gelf_dict, record)
        if self.facility is not None:
            self._set_custom_facility(gelf_dict, self.facility, record)
        if self.debugging_fields:
            self._add_debugging_fields(gelf_dict, record)
        if self.extra_fields:
            self._add_extra_fields(gelf_dict, record)
        return gelf_dict

    @staticmethod
    def _add_level_names(gelf_dict, record):
        """Add the ``level_name`` field to the ``gelf_dict`` which notes
        the logging level via the string error level names instead of
        numerical values

        :param gelf_dict: dictionary representing a GELF log.
        :type gelf_dict: dict

        :param record: :class:`logging.LogRecord` to extract a logging
            level from to insert into the given ``gelf_dict``.
        :type record: logging.LogRecord
        """
        gelf_dict['level_name'] = logging.getLevelName(record.levelno)

    @staticmethod
    def _set_custom_facility(gelf_dict, facility_value, record):
        """Set the ``gelf_dict``'s ``facility`` field to the specified value

        Also add a additional ``_logger`` field containing the
        ``LogRecord.name``.

        :param gelf_dict: dictionary representing a GELF log.
        :type gelf_dict: dict

        :param facility_value: Value to set as the ``gelf_dict``'s
            ``facility`` field.
        :type facility_value: str

        :param record: :class:`logging.LogRecord` to extract it's record
            name to insert into the given ``gelf_dict`` as the ``_logger``
            field.
        :type record: logging.LogRecord
        """
        gelf_dict.update({"facility": facility_value, '_logger': record.name})

    @staticmethod
    def _add_full_message(gelf_dict, record):
        """Add the ``full_message`` field to the ``gelf_dict`` if any
        traceback information exists within the logging record

        :param gelf_dict: dictionary representing a GELF log.
        :type gelf_dict: dict

        :param record: :class:`logging.LogRecord` to extract a full
            logging message from to insert into the given ``gelf_dict``.
        :type record: logging.LogRecord
        """
        # if a traceback exists add it to the log as the full_message field
        full_message = None
        # format exception information if present
        if record.exc_info:
            full_message = '\n'.join(
                traceback.format_exception(*record.exc_info))
        # use pre-formatted exception information in cases where the primary
        # exception information was removed, e.g. for LogRecord serialization
        if record.exc_text:
            full_message = record.exc_text
        if full_message:
            gelf_dict["full_message"] = full_message

    @staticmethod
    def _resolve_host(fqdn, localname):
        """Resolve the ``host`` GELF field

        :param fqdn: Boolean indicating whether to use :meth:`socket.getfqdn`
            to obtain the ``host`` GELF field.
        :type fqdn: bool

        :param localname: Use specified hostname as the ``host`` GELF field.
        :type localname: str or None

        :return: String representing the ``host`` GELF field.
        :rtype: str
        """
        if fqdn:
            return socket.getfqdn()
        elif localname is not None:
            return localname
        return socket.gethostname()

    @staticmethod
    def _add_debugging_fields(gelf_dict, record):
        """Add debugging fields to the given ``gelf_dict``

        :param gelf_dict: dictionary representing a GELF log.
        :type gelf_dict: dict

        :param record: :class:`logging.LogRecord` to extract debugging
            fields from to insert into the given ``gelf_dict``.
        :type record: logging.LogRecord
        """
        gelf_dict.update({
            'file': record.pathname,
            'line': record.lineno,
            '_function': record.funcName,
            '_pid': record.process,
            '_thread_name': record.threadName,
        })
        # record.processName was added in Python 2.6.2
        pn = getattr(record, 'processName', None)
        if pn is not None:
            gelf_dict['_process_name'] = pn

    @staticmethod
    def _add_extra_fields(gelf_dict, record):
        """Add extra fields to the given ``gelf_dict``

        However, this does not add additional fields in to ``message_dict``
        that are either duplicated from standard :class:`logging.LogRecord`
        attributes, duplicated from the python logging module source
        (e.g. ``exc_text``), or violate GELF format (i.e. ``id``).

        .. seealso::

            The list of standard :class:`logging.LogRecord` attributes can be
            found at:

                http://docs.python.org/library/logging.html#logrecord-attributes

        :param gelf_dict: dictionary representing a GELF log.
        :type gelf_dict: dict

        :param record: :class:`logging.LogRecord` to extract extra fields
            from to insert into the given ``gelf_dict``.
        :type record: logging.LogRecord
        """

        # skip_list is used to filter additional fields in a log message.
        skip_list = (
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName')

        for key, value in record.__dict__.items():
            if key not in skip_list and not key.startswith('_'):
                gelf_dict['_%s' % key] = value

    @classmethod
    def _pack_gelf_dict(cls, gelf_dict):
        """Convert a given ``gelf_dict`` into JSON-encoded UTF-8 bytes, thus,
        creating an uncompressed GELF log ready for consumption by Graylog.

        Since we cannot be 100% sure of what is contained in the ``gelf_dict``
        we have to do some sanitation.

        :param gelf_dict: dictionary representing a GELF log.
        :type gelf_dict: dict

        :return: bytes representing a uncompressed GELF log.
        :rtype: bytes
        """
        gelf_dict = cls._sanitize_to_unicode(gelf_dict)
        packed = json.dumps(
            gelf_dict,
            separators=',:',
            default=cls._object_to_json
        )
        return packed.encode('utf-8')

    @classmethod
    def _sanitize_to_unicode(cls, obj):
        """Convert all strings records of the object to unicode

        :param obj: object to sanitize to unicode.
        :type obj: object

        :return: Unicode string representing the given object.
        :rtype: str
        """
        if isinstance(obj, dict):
            return dict((cls._sanitize_to_unicode(k), cls._sanitize_to_unicode(v)) for k, v in obj.items())
        if isinstance(obj, (list, tuple)):
            return obj.__class__([cls._sanitize_to_unicode(i) for i in obj])
        if isinstance(obj, data):
            obj = obj.decode('utf-8', errors='replace')
        return obj

    @staticmethod
    def _object_to_json(obj):
        """Convert objects that cannot be natively serialized into JSON
        into their string representation (for later JSON serialization).

        :class:`datetime.datetime` based objects will be converted into a
        ISO formatted timestamp string.

        :param obj: object to convert into a string representation.
        :type obj: object

        :return: String representing the given object.
        :rtype: str
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return repr(obj)


class GELFUDPHandler(BaseGELFHandler, DatagramHandler):
    """GELF UDP handler"""

    def __init__(self, host, port=12202, chunk_size=WAN_CHUNK, **kwargs):
        """Initialize the GELFUDPHandler

        :param host: GELF UDP input host.
        :type host: str

        :param port: GELF UDP input port.
        :type port: int

        :param chunk_size: Message chunk size. Messages larger than this
            size will be sent to Graylog in multiple chunks.
        :type chunk_size: int
        """
        self.chunk_size = chunk_size

        BaseGELFHandler.__init__(self, **kwargs)
        DatagramHandler.__init__(self, host, port)

    def send(self, s):
        if len(s) < self.chunk_size:
            super(GELFUDPHandler, self).send(s)
        else:
            for chunk in ChunkedGELF(s, self.chunk_size):
                super(GELFUDPHandler, self).send(chunk)


class GELFTCPHandler(BaseGELFHandler, SocketHandler):
    """GELF TCP handler"""

    def __init__(self, host, port=12201, **kwargs):
        """Initialize the GELFTCPHandler

        :param host: GELF TCP input host.
        :type host: str

        :param port: GELF TCP input port.
        :type port: int

        .. attention::
            GELF TCP does not support compression due to the use of the null
            byte (``\\0``) as frame delimiter.

            Thus, :class:`.handler.GELFTCPHandler` does not support setting
            ``compress`` to :obj:`True` and is locked to :obj:`False`.
        """
        BaseGELFHandler.__init__(self, compress=False, **kwargs)
        SocketHandler.__init__(self, host, port)

    def makePickle(self, record):
        """Add a null terminator to generated pickles as TCP frame objects
        need to be null terminated

        :param record: :class:`logging.LogRecord` to create a null
            terminated GELF log.
        :type record: logging.LogRecord

        :return: Null terminated bytes representing a GELF log.
        :rtype: bytes
        """
        return super(GELFTCPHandler, self).makePickle(record) + b'\x00'


class GELFTLSHandler(GELFTCPHandler):
    """GELF TCP handler with TLS support"""

    def __init__(self, host, port=12204, validate=False, ca_certs=None,
                 certfile=None, keyfile=None, **kwargs):
        """Initialize the GELFTLSHandler

        :param host: GELF TLS input host.
        :type host: str

        :param port: GELF TLS input port.
        :type port: int

        :param validate: If :obj:`True`, validate the Graylog server's
            certificate. In this case specifying ``ca_certs`` is also
            required.
        :type validate: bool

        :param ca_certs: Path to CA bundle file.
        :type ca_certs: str

        :param certfile: Path to the client certificate file.
        :type certfile: str

        :param keyfile: Path to the client private key. If the private key is
            stored with the certificate, this parameter can be ignored.
        :type keyfile: str
        """

        if validate and ca_certs is None:
            raise ValueError('CA bundle file path must be specified')

        if keyfile is not None and certfile is None:
            raise ValueError('certfile must be specified')

        GELFTCPHandler.__init__(self, host=host, port=port, **kwargs)

        self.ca_certs = ca_certs
        self.reqs = ssl.CERT_REQUIRED if validate else ssl.CERT_NONE
        self.certfile = certfile
        self.keyfile = keyfile if keyfile else certfile

    def makeSocket(self, timeout=1):
        """Create a TLS wrapped socket"""
        plain_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if hasattr(plain_socket, 'settimeout'):
            plain_socket.settimeout(timeout)

        wrapped_socket = ssl.wrap_socket(
            plain_socket,
            ca_certs=self.ca_certs,
            cert_reqs=self.reqs,
            keyfile=self.keyfile,
            certfile=self.certfile
        )
        wrapped_socket.connect((self.host, self.port))

        return wrapped_socket


# TODO: add https?
class GELFHTTPHandler(BaseGELFHandler):
    """GELF HTTP handler"""

    def __init__(self, host, port=12203, compress=True, path='/gelf',
                 timeout=5, **kwargs):
        """Initialize the GELFHTTPHandler

        :param host: GELF HTTP input host.
        :type host: str

        :param port: GELF HTTP input port.
        :type port: int

        :param compress: If :obj:`True` compress the GELF message before
            sending it to the Graylog server.
        :type compress: bool

        :param path: Path of the HTTP input.
            (see http://docs.graylog.org/en/latest/pages/sending_data.html#gelf-via-http)
        :type path: str

        :param timeout: Number of seconds the HTTP client should wait before
            it discards the request if the Graylog server doesn't respond.
        :type timeout: int
        """

        BaseGELFHandler.__init__(self, compress=compress, **kwargs)

        self.host = host
        self.port = port
        self.path = path
        self.timeout = timeout
        self.headers = {}

        if compress:
            self.headers['Content-Encoding'] = 'gzip,deflate'

    def emit(self, record):
        """Convert a :class:`logging.LogRecord` to GELF and emit it to Graylog
        via a HTTP POST request

        :param record: :class:`logging.LogRecord` to convert into a GELF log
            and emit to Graylog via a HTTP POST request.
        :type record: logging.LogRecord
        """
        pickle = self.makePickle(record)
        connection = httplib.HTTPConnection(
            host=self.host,
            port=self.port,
            timeout=self.timeout
        )
        connection.request('POST', self.path, pickle, self.headers)


class ChunkedGELF(object):
    """Class that chunks a message into a GELF compatible chunks"""

    def __init__(self, message, size):
        """Initialize the ChunkedGELF message class

        :param message: The message to chunk.
        :type message: bytes

        :param size: The size of the chunks.
        :type size: int
        """
        self.message = message
        self.size = size
        self.pieces = \
            struct.pack('B', int(math.ceil(len(message) * 1.0 / size)))
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
