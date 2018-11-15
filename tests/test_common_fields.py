#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import pytest
import mock
from graypy import GELFTCPHandler, GELFUDPHandler
from tests.helper import logger, get_unique_message, log_warning, log_exception


SYSLOG_LEVEL_ERROR = 3
SYSLOG_LEVEL_WARNING = 4


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201),
    GELFTCPHandler(host='127.0.0.1', port=12201, tls=True,
                   tls_client_cert="config/cert.pem",
                   tls_client_key="config/key.pem",
                   tls_client_password="secret"),
    GELFUDPHandler(host='127.0.0.1', port=12202),
    GELFUDPHandler(host='127.0.0.1', port=12202, compress=False),
])
def handler(request):
    return request.param


def test_simple_message(logger):
    message = get_unique_message()
    graylog_response = log_warning(logger, message)
    assert graylog_response['message'] == message
    assert graylog_response['level'] == SYSLOG_LEVEL_WARNING
    assert 'full_message' not in graylog_response
    assert 'file' not in graylog_response
    assert 'module' not in graylog_response
    assert 'func' not in graylog_response
    assert 'logger_name' not in graylog_response
    assert 'line' not in graylog_response


def test_formatted_message(logger):
    message = get_unique_message()
    template = message + '_%s_%s'
    graylog_response = log_warning(logger, template, args=('hello', 'gelf'))
    assert graylog_response['message'] == message + '_hello_gelf'
    assert graylog_response['level'] == SYSLOG_LEVEL_WARNING
    assert 'full_message' not in graylog_response


def test_full_message(logger):
    message = get_unique_message()

    try:
        raise ValueError(message)
    except ValueError as e:
        graylog_response = log_exception(logger, message, e)
        assert graylog_response['message'] == message
        assert graylog_response['level'] == SYSLOG_LEVEL_ERROR
        assert message in graylog_response['full_message']
        assert 'Traceback (most recent call last)' in graylog_response['full_message']
        assert 'ValueError: ' in graylog_response['full_message']
        assert 'file' not in graylog_response
        assert 'module' not in graylog_response
        assert 'func' not in graylog_response
        assert 'logger_name' not in graylog_response
        assert 'line' not in graylog_response


def test_source(logger):
    original_source = socket.getfqdn()
    with mock.patch('socket.getfqdn', return_value='different_domain'):
        message = get_unique_message()
        graylog_response = log_warning(logger, message)
        assert graylog_response['source'] == original_source
