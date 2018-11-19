#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests validating the emitting of valid debugging fields for graypy
loggers"""

import pytest

from tests.helper import logger, TEST_CERT, TEST_TCP_PORT, TEST_HTTP_PORT, \
    TEST_TLS_PORT, TEST_UDP_PORT
from tests.integration.helper import get_graylog_response, get_unique_message

from graypy import GELFUDPHandler, GELFTCPHandler, GELFTLSHandler, \
    GELFHTTPHandler


@pytest.fixture(params=[
    GELFTCPHandler('127.0.0.1', TEST_TCP_PORT, debugging_fields=True),
    GELFUDPHandler('127.0.0.1', TEST_UDP_PORT, debugging_fields=True),
    GELFUDPHandler('127.0.0.1', TEST_UDP_PORT, compress=False, debugging_fields=True),
    GELFHTTPHandler('127.0.0.1', TEST_HTTP_PORT, debug=True),
    GELFHTTPHandler('127.0.0.1', TEST_HTTP_PORT, compress=False, debugging_fields=True),
    GELFTLSHandler('127.0.0.1', TEST_TLS_PORT, debugging_fields=True),
    GELFTLSHandler('127.0.0.1', TEST_TLS_PORT, debugging_fields=True, validate=True, ca_certs=TEST_CERT),
])
def handler(request):
    return request.param


def test_debug_mode(logger):
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(message)
    assert message == graylog_response['message']
    assert 'helper.py' == graylog_response['file']
    assert 'helper' == graylog_response['module']
    assert 'test_debug_mode' == graylog_response['func']
    assert 'test_logger' == graylog_response['logger_name']
    assert 'line' in graylog_response
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
