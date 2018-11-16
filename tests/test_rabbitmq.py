#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests for :mod:`graypy.rabbitmq`"""

import pytest

from graypy.rabbitmq import GELFRabbitHandler


def test_invalid_url():
    with pytest.raises(ValueError):
        GELFRabbitHandler("BADURL")


def test_valid_url():
    GELFRabbitHandler("amqp://localhost")
