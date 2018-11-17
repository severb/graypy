#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests for :class:`graypy.rabbitmq.GELFRabbitHandler`"""

import pytest

from graypy.rabbitmq import GELFRabbitHandler


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


def test_socket_creation_failure():
    """Test attempting to open a socket to a rabbitmq instance when no such
    service exists"""
    handler = GELFRabbitHandler("amqp://localhost")
    with pytest.raises(UnboundLocalError):
        handler.makeSocket()
