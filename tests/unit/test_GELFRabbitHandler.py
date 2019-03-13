#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for :class:`graypy.rabbitmq.GELFRabbitHandler`"""

import json

import pytest

from graypy.rabbitmq import GELFRabbitHandler
from graypy.handler import SYSLOG_LEVELS

from tests.unit.helper import MOCK_LOG_RECORD


def test_invalid_url():
    """Test constructing :class:`graypy.rabbitmq.GELFRabbitHandler` with
    an invalid rabbitmq url"""
    with pytest.raises(ValueError):
        GELFRabbitHandler("BADURL")


def test_valid_url():
    """Test constructing :class:`graypy.rabbitmq.GELFRabbitHandler` with
    a valid rabbitmq url"""
    handler = GELFRabbitHandler("amqp://localhost")
    assert handler
    assert "amqp://localhost" == handler.url


@pytest.mark.xfail(reason="rabbitmq service is not up")
def test_socket_creation_failure():
    """Test attempting to open a socket to a rabbitmq instance when no such
    service exists"""
    handler = GELFRabbitHandler("amqp://localhost")
    handler.makeSocket()


def test_make_pickle():
    handler = GELFRabbitHandler("amqp://localhost")
    pickle = json.loads(handler.makePickle(MOCK_LOG_RECORD))
    assert "Log message" == pickle["short_message"]
    assert SYSLOG_LEVELS[MOCK_LOG_RECORD.levelno] == pickle["level"]
