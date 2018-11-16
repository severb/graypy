#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import mock
from tests.helper import logger, simple_logger, get_unique_message, log_warning, \
    log_exception

SYSLOG_LEVEL_ERROR = 3
SYSLOG_LEVEL_WARNING = 4


def test_simple_message(simple_logger):
    message = get_unique_message()
    graylog_response = log_warning(simple_logger, message)
    assert message == graylog_response['message']
    assert SYSLOG_LEVEL_WARNING == graylog_response['level']
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
    assert message + '_hello_gelf' == graylog_response['message']
    assert SYSLOG_LEVEL_WARNING == graylog_response['level']
    assert 'full_message' not in graylog_response


def test_full_message(logger):
    message = get_unique_message()

    try:
        raise ValueError(message)
    except ValueError as e:
        graylog_response = log_exception(logger, message, e)
        assert message == graylog_response['message']
        assert SYSLOG_LEVEL_ERROR == graylog_response['level']
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
        assert original_source == graylog_response['source']
