#!/usr/bin/python
# -*- coding: utf-8 -*-

""""""

from tests.helper import simple_handler, simple_logger, log_warning, \
    get_unique_message

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
