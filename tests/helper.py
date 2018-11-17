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

TEST_UDP_PORT = 12202
TEST_TCP_PORT = 12201
TEST_TLS_PORT = 12204


@pytest.fixture(params=[
    GELFTCPHandler(host="localhost", port=TEST_TCP_PORT),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TCP_PORT),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TCP_PORT,
                   extra_fields=True),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TCP_PORT,
                   extra_fields=True, debugging_fields=True),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TLS_PORT,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TLS_PORT,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TLS_PORT,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host="localhost", port=TEST_UDP_PORT),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   compress=False),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True, compress=False),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True, debugging_fields=True, compress=False),
])
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


@pytest.yield_fixture
def formatted_logger(handler):
    logger = logging.getLogger("formatted_test_logger")
    handler.setFormatter(logging.Formatter("%(levelname)s : %(message)s"))
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)
