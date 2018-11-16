#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import mock
from tests.helper import logger, handler, simple_logger, simple_handler, \
    get_unique_message, log_warning, log_exception

SYSLOG_LEVEL_ERROR = 3


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


def test_source(logger):
    original_source = socket.getfqdn()
    with mock.patch('socket.getfqdn', return_value='different_domain'):
        message = get_unique_message()
        graylog_response = log_warning(logger, message)
        assert original_source == graylog_response['source']
