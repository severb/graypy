#!/usr/bin/python
# -*- coding: utf-8 -*-

from tests.helper import debug_logger, get_unique_message, log_warning


def test_debug_mode(debug_logger):
    message = get_unique_message()
    graylog_response = log_warning(debug_logger, message)
    assert message == graylog_response['message']
    assert 'helper.py' == graylog_response['file']
    assert 'helper' == graylog_response['module']
    assert 'log_warning' == graylog_response['func']
    assert 'test' == graylog_response['logger_name']
    assert 'line' in graylog_response
