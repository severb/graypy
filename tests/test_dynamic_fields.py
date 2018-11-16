#!/usr/bin/python
# -*- coding: utf-8 -*-

from tests.helper import get_unique_message, log_warning, filtered_logger


def test_dynamic_fields(filtered_logger):
    message = get_unique_message()
    graylog_response = log_warning(filtered_logger, message)
    assert message == graylog_response['message']
    assert 'diary of a madman' == graylog_response['ozzy']
    assert 1984 == graylog_response['van_halen']
    assert 42 != graylog_response['_id']
    assert 'id' not in graylog_response
