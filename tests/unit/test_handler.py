#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for the formatting and construction of GELF logs by the graypy
logging handlers

.. note::

    These tests mock sending to Graylog and do not require an active graylog
    instance to operate.
"""

import datetime
import json
import logging
import socket
import sys
import zlib

import mock
import pytest

from graypy.handler import BaseGELFHandler, GELFHTTPHandler, GELFTLSHandler

from tests.helper import handler, logger, formatted_logger
from tests.unit.helper import MOCK_LOG_RECORD, MOCK_LOG_RECORD_NAME

UNICODE_REPLACEMENT = u"\ufffd"


class TestClass(object):
    def __repr__(self):
        return "<TestClass>"


@pytest.yield_fixture
def mock_send(handler):
    try:
        with mock.patch.object(handler, "send") as mock_send:
            yield mock_send
    except Exception:
        with mock.patch.object(handler, "emit") as mock_send:
            yield mock_send


def get_mock_send_arg(mock_send):
    assert mock_send.call_args_list != []
    [[[arg], _]] = mock_send.call_args_list

    # TODO: this is inaccurate solution for mocking non-send handlers
    if isinstance(arg, logging.LogRecord):
        return json.loads(
            BaseGELFHandler(compress=False).makePickle(arg).decode("utf-8")
        )
    try:
        return json.loads(zlib.decompress(arg).decode("utf-8"))
    except zlib.error:  # we have a uncompress message
        try:
            return json.loads(arg.decode("utf-8"))
        except Exception:  # that is null terminated
            return json.loads(arg[:-1].decode("utf-8"))


@pytest.mark.parametrize(
    "message,expected",
    [
        (u"\u20AC", u"\u20AC"),
        (u"\u20AC".encode("utf-8"), u"\u20AC"),
        (b"\xc3", UNICODE_REPLACEMENT),
        (["a", b"\xc3"], ["a", UNICODE_REPLACEMENT]),
    ],
)
def test_pack(message, expected):
    assert expected == json.loads(
        BaseGELFHandler._pack_gelf_dict(message).decode("utf-8")
    )


def test_manual_exc_info_handler(logger, mock_send):
    """Check that a the ``full_message`` traceback info is passed when
    the ``exc_info=1`` flag is given within a log message"""
    try:
        raise SyntaxError("Syntax error")
    except SyntaxError:
        logger.error("Failed", exc_info=1)
    arg = get_mock_send_arg(mock_send)
    assert "Failed" == arg["short_message"]
    assert arg["full_message"].startswith("Traceback (most recent call last):")

    # GELFHTTPHandler mocking does not complete the stacktrace
    # thus a missing \n
    assert arg["full_message"].endswith("SyntaxError: Syntax error") or arg[
        "full_message"
    ].endswith("SyntaxError: Syntax error\n")


def test_normal_exception_handler(logger, mock_send):
    try:
        raise SyntaxError("Syntax error")
    except SyntaxError:
        logger.exception("Failed")
    arg = get_mock_send_arg(mock_send)
    assert "Failed" == arg["short_message"]
    assert arg["full_message"].startswith("Traceback (most recent call last):")

    # GELFHTTPHandler mocking does not complete the stacktrace
    # thus a missing \n
    assert arg["full_message"].endswith("SyntaxError: Syntax error") or arg[
        "full_message"
    ].endswith("SyntaxError: Syntax error\n")


def test_unicode(logger, mock_send):
    logger.error(u"Mensaje de registro espa\xf1ol")
    arg = get_mock_send_arg(mock_send)
    assert u"Mensaje de registro espa\xf1ol" == arg["short_message"]


@pytest.mark.skipif(sys.version_info[0] >= 3, reason="python2 only")
def test_broken_unicode_python2(logger, mock_send):
    # py3 record.getMessage() returns a binary string here
    # which is safely converted to unicode during the sanitization
    # process
    logger.error(b"Broken \xde log message")
    decoded = get_mock_send_arg(mock_send)
    assert u"Broken %s log message" % UNICODE_REPLACEMENT == decoded["short_message"]


@pytest.mark.skipif(sys.version_info[0] < 3, reason="python3 only")
def test_broken_unicode_python3(logger, mock_send):
    # py3 record.getMessage() returns somewhat broken "b"foo"" if the
    # message string is not a string, but a binary object: b"foo"
    logger.error(b"Broken \xde log message")
    decoded = get_mock_send_arg(mock_send)
    assert "b'Broken \\xde log message'" == decoded["short_message"]


def test_extra_field(logger, mock_send):
    logger.error("Log message", extra={"foo": "bar"})
    decoded = get_mock_send_arg(mock_send)
    assert "Log message" == decoded["short_message"]
    assert "bar" == decoded["_foo"]


def test_list(logger, mock_send):
    logger.error("Log message", extra={"foo": ["bar", "baz"]})
    decoded = get_mock_send_arg(mock_send)
    assert "Log message" == decoded["short_message"]
    assert ["bar", "baz"] == decoded["_foo"]


def test_arbitrary_object(logger, mock_send):
    logger.error("Log message", extra={"foo": TestClass()})
    decoded = get_mock_send_arg(mock_send)
    assert "Log message" == decoded["short_message"]
    assert "<TestClass>" == decoded["_foo"]


def test_message_to_pickle_serializes_datetime_objects_instead_of_blindly_repring_them(
    logger, mock_send
):
    timestamp = datetime.datetime(2001, 2, 3, 4, 5, 6, 7)
    logger.error("Log message", extra={"ts": timestamp})
    decoded = get_mock_send_arg(mock_send)
    assert "datetime.datetime" not in decoded["_ts"]
    assert timestamp.isoformat() == decoded["_ts"]


def test_status_field_issue(logger, mock_send):
    logger.error("Log message", extra={"status": "OK"})
    decoded = get_mock_send_arg(mock_send)
    assert "Log message" == decoded["short_message"]
    assert "OK" == decoded["_status"]


def test_add_level_name():
    gelf_dict = dict()
    BaseGELFHandler._add_level_names(gelf_dict, MOCK_LOG_RECORD)
    assert "INFO" == gelf_dict["level_name"]


def test_resolve_host():
    """Test all posible resolutions of :meth:`BaseGELFHandler._resolve_host`"""
    assert socket.gethostname() == BaseGELFHandler._resolve_host(False, None)
    assert socket.getfqdn() == BaseGELFHandler._resolve_host(True, None)
    assert socket.getfqdn() == BaseGELFHandler._resolve_host(True, "localhost")
    assert "localhost" == BaseGELFHandler._resolve_host(False, "localhost")
    assert "" == BaseGELFHandler._resolve_host(False, "")


def test_set_custom_facility():
    gelf_dict = dict()
    facility = "test facility"
    BaseGELFHandler._set_custom_facility(gelf_dict, facility, MOCK_LOG_RECORD)
    assert MOCK_LOG_RECORD_NAME == gelf_dict["_logger"]
    assert "test facility" == gelf_dict["facility"]


def test_formatted_logger(formatted_logger, mock_send):
    """Test the ability to set and modify the graypy handler's
    :class:`logging.Formatter` and have the resultant ``short_message`` be
    formatted by the set :class:`logging.Formatter`"""
    for handler in formatted_logger.handlers:
        if isinstance(handler, GELFHTTPHandler):
            pytest.skip("formatting not mocked for GELFHTTPHandler")
    formatted_logger.error("Log message")
    decoded = get_mock_send_arg(mock_send)
    assert "ERROR : Log message" == decoded["short_message"]


def test_invalid_fqdn_localhost():
    """Test constructing :class:`graypy.handler.BaseGELFHandler` with
    specifying conflicting arguments ``fqdn`` and ``localname``"""
    with pytest.raises(ValueError):
        BaseGELFHandler(fqdn=True, localname="localhost")


def test_invalid_ca_certs():
    """Test constructing :class:`graypy.handler.GELFTLSHandler` with
    incorrect arguments specifying server ca cert verification"""
    with pytest.raises(ValueError):
        GELFTLSHandler("127.0.0.1", validate=True)


def test_invalid_client_certs():
    """Test constructing :class:`graypy.handler.GELFTLSHandler` with
    incorrect arguments specifying client cert/key verification"""
    with pytest.raises(ValueError):
        # missing client cert
        GELFTLSHandler("127.0.0.1", keyfile="/dev/null")
