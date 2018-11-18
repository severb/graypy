#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests sending a common usage logs to a local graylog instance"""

import logging

import pytest

from graypy.handler import SYSLOG_LEVELS, GELFUDPHandler, GELFTCPHandler

from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_unique_message, get_graylog_response

TEST_TCP_PORT = 12201
TEST_UDP_PORT = 12202
TEST_TLS_PORT = 12204


@pytest.fixture(params=[
    GELFTCPHandler("127.0.0.1", TEST_TCP_PORT),
    GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, extra_fields=True),
    GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, extra_fields=True, debugging_fields=True),
    GELFUDPHandler("127.0.0.1", TEST_UDP_PORT),
    GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, compress=False),
    GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, extra_fields=True),
    GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, extra_fields=True, compress=False),
    GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, extra_fields=True, debugging_fields=True),
    GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, extra_fields=True, debugging_fields=True, compress=False),
])
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)

@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local graylog instance not up")
def test_common_logging(logger):
    """Test sending a log message that requires chunking to be sent to
    graylog"""
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(message)
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert SYSLOG_LEVELS[logging.ERROR] == graylog_response["level"]
