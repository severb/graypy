# -*- coding: utf-8 -*-
import datetime
import json
import logging
import pytest
import zlib
import mock
import sys
from graypy.handler import GELFHandler, message_to_pickle


UNICODE_REPLACEMENT = u'\ufffd'


class A(object):
    def __repr__(self):
        return '<A>'


@pytest.fixture
def handler():
    return GELFHandler('127.0.0.1')


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


@pytest.yield_fixture
def mock_send(handler):
    with mock.patch.object(handler, 'send') as mock_send:
        yield mock_send


@pytest.mark.parametrize('message,message2', [
    (u'\u20AC', u'\u20AC'),
    (u'\u20AC'.encode('utf-8'), u'\u20AC'),
    (b"\xc3", UNICODE_REPLACEMENT),
    (["a", b"\xc3"], ["a", UNICODE_REPLACEMENT]),
])
def test_message_to_pickle(message, message2):
    assert json.loads(message_to_pickle(message).decode('utf-8')) == message2


def get_mock_send_arg(mock_send):
    assert mock_send.call_args_list != []
    [[[arg], _]] = mock_send.call_args_list
    return json.loads(zlib.decompress(arg).decode('utf-8'))


def test_normal_exception_handler(logger, mock_send):
    try:
        raise SyntaxError('Syntax error')
    except Exception:
        logger.exception('Failed')
    arg = get_mock_send_arg(mock_send)
    assert arg['short_message'] == 'Failed'
    assert arg['full_message'].startswith('Traceback (most recent call last):')
    assert arg['full_message'].endswith('SyntaxError: Syntax error\n')


def test_unicode(logger, mock_send):
    logger.error(u'Mensaje de registro espa\xf1ol')
    arg = get_mock_send_arg(mock_send)
    assert arg['short_message'] == arg['full_message'] == u'Mensaje de registro espa\xf1ol'


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
    assert (decoded['short_message']
            == decoded['full_message']
            == "b'Broken \\xde log message'")


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
