#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests sending a common usage logs to a local graylog instance"""

import logging

import pytest

from graypy.handler import SYSLOG_LEVELS, GELFUDPHandler

from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_unique_message, get_graylog_response

TEST_UDP_PORT = 12202


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local graylog instance not up")
def test_common_logging():
    """Test sending a log message that requires chunking to be sent to
    graylog"""
    logger = logging.getLogger("test_logger")
    logger.addHandler(GELFUDPHandler("127.0.0.1", TEST_UDP_PORT))
    message = get_unique_message()
    logger.error(message)

    graylog_response = get_graylog_response(message)
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert SYSLOG_LEVELS[logging.ERROR] == graylog_response["level"]
