#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests sending logs to a local Graylog instance"""

import logging

import pytest

from graypy.handler import SYSLOG_LEVELS

from tests.helper import handler, logger
from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_unique_message, get_graylog_response


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_common_logging(logger):
    """Test sending a common usage log"""
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(message)
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert SYSLOG_LEVELS[logging.ERROR] == graylog_response["level"]
