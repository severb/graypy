#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy

These functions are used for both the integration and unit testing.
"""

import logging
import pytest

from graypy import GELFUDPHandler, GELFTCPHandler, GELFTLSHandler, GELFHTTPHandler

TEST_CERT = "tests/config/localhost.cert.pem"
KEY_PASS = "secret"

TEST_TCP_PORT = 12201
TEST_UDP_PORT = 12202
TEST_HTTP_PORT = 12203
TEST_TLS_PORT = 12204


@pytest.fixture(
    params=[
        GELFTCPHandler("127.0.0.1", TEST_TCP_PORT),
        GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, extra_fields=True),
        GELFTCPHandler(
            "127.0.0.1", TEST_TCP_PORT, extra_fields=True, debugging_fields=True
        ),
        GELFTLSHandler("localhost", TEST_TLS_PORT),
        GELFTLSHandler("localhost", TEST_TLS_PORT, validate=True, ca_certs=TEST_CERT),
        GELFTLSHandler("127.0.0.1", TEST_TLS_PORT),
        GELFTLSHandler("127.0.0.1", TEST_TLS_PORT, validate=True, ca_certs=TEST_CERT),
        GELFHTTPHandler("127.0.0.1", TEST_HTTP_PORT),
        GELFHTTPHandler("127.0.0.1", TEST_HTTP_PORT, compress=False),
        GELFUDPHandler("127.0.0.1", TEST_UDP_PORT),
        GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, compress=False),
        # the below handler tests are essentially smoke tests
        # that help cover the argument permutations of BaseGELFHandler
        GELFUDPHandler(
            "127.0.0.1",
            TEST_UDP_PORT,
            debugging_fields=True,
            extra_fields=True,
            localname="foobar_localname",
            facility="foobar_facility",
            level_names=True,
            compress=False,
        ),
        GELFUDPHandler(
            "127.0.0.1",
            TEST_UDP_PORT,
            debugging_fields=True,
            extra_fields=True,
            fqdn=True,
            facility="foobar_facility",
            level_names=True,
            compress=False,
        ),
    ]
)
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger_ = logging.getLogger("test_logger")
    logger_.addHandler(handler)
    yield logger_
    logger_.removeHandler(handler)


@pytest.yield_fixture
def formatted_logger(handler):
    logger_ = logging.getLogger("formatted_test_logger")
    handler.setFormatter(logging.Formatter("%(levelname)s : %(message)s"))
    logger_.addHandler(handler)
    yield logger_
    logger_.removeHandler(handler)
