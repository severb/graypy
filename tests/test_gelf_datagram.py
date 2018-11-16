#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import json
import logging
import sys
import zlib

import mock
import pytest

from graypy.handler import GELFUDPHandler, BaseGELFHandler, GELFTCPHandler
from tests.helper import TEST_KEY, TEST_CERT

UNICODE_REPLACEMENT = u'\ufffd'


class A(object):
    def __repr__(self):
        return '<A>'


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201),
    GELFTCPHandler(host='127.0.0.1', port=12201, extra_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201, extra_fields=True,
                   debugging_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201, tls=True,
                   tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY,
                   tls_client_password="secret"),
    GELFUDPHandler(host='127.0.0.1', port=12202, compress=False),
    GELFUDPHandler(host='127.0.0.1', port=12202),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True,
                   debugging_fields=True),
])
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger('test_logger')
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


@pytest.yield_fixture
def formatted_logger(handler):
    logger = logging.getLogger('test_formatted_logger')
    handler.setFormatter(logging.Formatter('%(levelname)s : %(message)s'))
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


def test_setFormatter(formatted_logger, mock_send):
    formatted_logger.error("test log")
    decoded = get_mock_send_arg(mock_send)
    assert (decoded['short_message'] == "ERROR : test log")


@pytest.yield_fixture
def mock_send(handler):
    with mock.patch.object(handler, 'send') as mock_send:
        yield mock_send


@pytest.mark.parametrize('message,expected', [
    (u'\u20AC', u'\u20AC'),
    (u'\u20AC'.encode('utf-8'), u'\u20AC'),
    (b"\xc3", UNICODE_REPLACEMENT),
    (["a", b"\xc3"], ["a", UNICODE_REPLACEMENT]),
])
def test_message_to_pickle(message, expected):
    assert json.loads(BaseGELFHandler.pack(message).decode('utf-8')) == expected


def get_mock_send_arg(mock_send):
    assert mock_send.call_args_list != []
    [[[arg], _]] = mock_send.call_args_list
    try:
        return json.loads(zlib.decompress(arg).decode('utf-8'))
    except zlib.error:  # we have a uncompress message
        try:
            return json.loads(arg)
        except json.JSONDecodeError:  # that is null terminated
            return json.loads(arg[:-1])


def test_manual_exc_info_handler(logger, mock_send):
    """Check that a the ``full_message`` traceback info is passed when
    the ``exc_info=1`` flag is given within a log message"""
    try:
        raise SyntaxError('Syntax error')
    except SyntaxError:
        logger.error("Failed", exc_info=1)
    arg = get_mock_send_arg(mock_send)
    assert arg['short_message'] == 'Failed'
    assert arg['full_message'].startswith('Traceback (most recent call last):')
    assert arg['full_message'].endswith('SyntaxError: Syntax error\n')


def test_normal_exception_handler(logger, mock_send):
    try:
        raise SyntaxError('Syntax error')
    except SyntaxError:
        logger.exception('Failed')
    arg = get_mock_send_arg(mock_send)
    assert arg['short_message'] == 'Failed'
    assert arg['full_message'].startswith('Traceback (most recent call last):')
    assert arg['full_message'].endswith('SyntaxError: Syntax error\n')


def test_unicode(logger, mock_send):
    logger.error(u'Mensaje de registro espa\xf1ol')
    arg = get_mock_send_arg(mock_send)
    assert arg['short_message'] == u'Mensaje de registro espa\xf1ol'


@pytest.mark.skipif(sys.version_info[0] >= 3, reason='python2 only')
def test_broken_unicode_python2(logger, mock_send):
    # py3 record.getMessage() returns a binary string here
    # which is safely converted to unicode during the sanitization
    # process
    logger.error(b'Broken \xde log message')
    decoded = get_mock_send_arg(mock_send)
    assert (decoded['short_message']
            == decoded['full_message']
            == u'Broken %s log message' % UNICODE_REPLACEMENT)


@pytest.mark.skipif(sys.version_info[0] < 3, reason='python3 only')
def test_broken_unicode_python3(logger, mock_send):
    # py3 record.getMessage() returns somewhat broken "b'foo'" if the
    # message string is not a string, but a binary object: b"foo"
    logger.error(b'Broken \xde log message')
    decoded = get_mock_send_arg(mock_send)
    assert (decoded['short_message'] == "b'Broken \\xde log message'")


def test_arbitrary_object(logger, mock_send):
    logger.error('Log message', extra={'foo': A()})
    decoded = get_mock_send_arg(mock_send)
    assert decoded['_foo'] == '<A>'


def test_list(logger, mock_send):
    logger.error('Log message', extra={'foo': ['bar', 'baz']})
    decoded = get_mock_send_arg(mock_send)
    assert decoded['_foo'] == ['bar', 'baz']


def test_message_to_pickle_serializes_datetime_objects_instead_of_blindly_repring_them(logger, mock_send):
    timestamp = datetime.datetime(2001, 2, 3, 4, 5, 6, 7)
    logger.error('Log message', extra={'ts': timestamp})
    decoded = get_mock_send_arg(mock_send)

    assert 'datetime.datetime' not in decoded['_ts']
    assert decoded['_ts'] == timestamp.isoformat()

