#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests for :mod:`graypy.handler`"""

import logging

import pytest

from graypy import GELFTCPHandler, GELFUDPHandler
from tests.helper import TEST_CERT, TEST_KEY


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201, extra_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201, tls=True,
                   tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY,
                   tls_client_password="secret"),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True),
])
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


@pytest.yield_fixture
def formatted_logger(handler):
    logger = logging.getLogger('test')
    handler.setFormatter(logging.Formatter('%(levelname)s : %(message)s'))
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


def test_setFormatter(formatted_logger):
    formatted_logger.error("test log")
    # TODO: validate
    assert (decoded['short_message'] == "ERROR : test log")


def test_manaul_exec_info_logging(logger):
    """Check that a the full_message traceback info is passed when
    the ``exc_info=1`` flag is given within a log message"""
    try:
        raise Exception("exception")
    except Exception:
        logger.error("caught test exception", exc_info=1)
        # TODO: validate
