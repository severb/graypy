#!/usr/bin/python
# -*- coding: utf-8 -*-

from tests.helper import _get_api_response, _parse_api_response, \
    get_unique_message, logger, handler


def test_status_field_issue(logger):
    message = get_unique_message()
    logger.info(message, extra={'fld1': 1, 'fld2': 2, 'status': 'OK'})
    api_response = _get_api_response(message, [])
    graylog_response = _parse_api_response(api_response)
    assert "OK" == graylog_response['status']
