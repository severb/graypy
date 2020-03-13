#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests sending logs to Graylog through RabbitMQ"""

import logging

import pytest

from graypy.rabbitmq import GELFRabbitHandler
from graypy.handler import SYSLOG_LEVELS

from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_unique_message, get_graylog_response


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local Graylog instance not up")
def test_rmq_logging():
    """Test that verifies the log message was received by Graylog"""
    logger = logging.getLogger("test_rmq_logging")
    handler = GELFRabbitHandler(url="amqp://graylog:graylog@127.0.0.1",
                                exchange="log-messages",
                                exchange_type="direct",
                                routing_key="#")
    logger.addHandler(handler)
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(message)
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert SYSLOG_LEVELS[logging.ERROR] == graylog_response["level"]
