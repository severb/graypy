#!/usr/bin/python
# -*- coding: utf-8 -*-

from tests.helper import get_unique_message, log_warning, filtered_logger


def test_dynamic_fields(filtered_logger):
    message = get_unique_message()
    graylog_response = log_warning(filtered_logger, message)
    assert graylog_response['message'] == message
    assert graylog_response['ozzy'] == 'diary of a madman'
    assert graylog_response['van_halen'] == 1984
    assert graylog_response['_id'] != 42
    assert 'id' not in graylog_response
