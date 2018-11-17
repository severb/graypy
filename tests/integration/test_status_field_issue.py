#!/usr/bin/python
# -*- coding: utf-8 -*-

from tests.helper import get_graylog_response, \
    get_unique_message, logger, handler


def test_status_field_issue(logger):
    message = get_unique_message()
    logger.error(message, extra={'fld1': 1, 'fld2': 2, 'status': 'OK'})
    graylog_response = get_graylog_response(message)
    assert message == graylog_response['message']
    assert "OK" == graylog_response['status']
