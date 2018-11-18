#!/usr/bin/python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy

These functions are used for both the integration and unit testing.
"""

import os
import logging
import pytest

from graypy import GELFUDPHandler, GELFTCPHandler

TEST_CONFIG_DIR = os.path.join(os.path.dirname(__file__),
                               os.path.join("integration", "config"))
TEST_CERT = os.path.join(TEST_CONFIG_DIR, "cert.pem")
TEST_KEY = os.path.join(TEST_CONFIG_DIR, "key.pem")
KEY_PASS = "secret"

TEST_TCP_PORT = 12201
TEST_UDP_PORT = 12202
TEST_TLS_PORT = 12204


@pytest.fixture(params=[
    GELFTCPHandler("127.0.0.1", TEST_TCP_PORT),
    GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, extra_fields=True),
    GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, extra_fields=True, debugging_fields=True),
    GELFTCPHandler("127.0.0.1", TEST_TLS_PORT, tls=True, tls_cafile=TEST_CERT),
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
    logger_ = logging.getLogger("test_logger")
    logger_.addHandler(handler)
    yield logger_
    logger_.removeHandler(handler)

