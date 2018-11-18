#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests sending logs to a local graylog instance that need to be chunked"""

import logging

import pytest

from graypy.handler import SYSLOG_LEVELS, GELFUDPHandler

from tests.integration import LOCAL_GRAYLOG_UP
from tests.helper import TEST_UDP_PORT
from tests.integration.helper import get_unique_message, get_graylog_response


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local graylog instance not up")
def test_chunked_logging():
    """Test sending a common usage log"""
    logger = logging.getLogger("test_logger")
    handler = GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, chunk_size=10)
    logger.addHandler(handler)
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(message)
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert SYSLOG_LEVELS[logging.ERROR] == graylog_response["level"]