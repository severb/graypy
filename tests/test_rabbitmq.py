#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests for :mod:`graypy.rabbitmq`"""

import pytest

from graypy.rabbitmq import GELFRabbitHandler, ExcludeFilter


def test_invalid_url():
    with pytest.raises(ValueError):
        GELFRabbitHandler("BADURL")


def test_valid_url():
    handler = GELFRabbitHandler("amqp://localhost")
    assert handler
    assert "amqp://localhost" == handler.url


def test_invalid_ExcludeFilter():
    with pytest.raises(ValueError):
        ExcludeFilter("")


def test_ExcludeFilter():
    filter = ExcludeFilter("foobar")
    assert filter
    assert "foobar" == filter.name
    assert len("foobar") == filter.nlen
