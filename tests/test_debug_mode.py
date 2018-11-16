#!/usr/bin/python
# -*- coding: utf-8 -*-

from tests.helper import debug_logger, get_unique_message, log_warning


def test_debug_mode(debug_logger):
    message = get_unique_message()
    graylog_response = log_warning(debug_logger, message)
    assert graylog_response['message'] == message
    assert graylog_response['file'] == 'helper.py'
    assert graylog_response['module'] == 'helper'
    assert graylog_response['func'] == 'log_warning'
    assert graylog_response['logger_name'] == 'test'
    assert 'line' in graylog_response
