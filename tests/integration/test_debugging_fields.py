#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests validating the emitting of valid debugging fields for graypy
loggers"""

import pytest

from tests.helper import (
    logger,
    TEST_CERT,
    TEST_TCP_PORT,
    TEST_HTTP_PORT,
    TEST_TLS_PORT,
    TEST_UDP_PORT,
)
from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_graylog_response, get_unique_message

from graypy import GELFUDPHandler, GELFTCPHandler, GELFTLSHandler, GELFHTTPHandler


@pytest.fixture(
    params=[
        GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, debugging_fields=True),
        GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, debugging_fields=True),
        GELFUDPHandler(
            "127.0.0.1", TEST_UDP_PORT, compress=False, debugging_fields=True
        ),
        GELFHTTPHandler("127.0.0.1", TEST_HTTP_PORT, debugging_fields=True),
        GELFHTTPHandler(
            "127.0.0.1", TEST_HTTP_PORT, compress=False, debugging_fields=True
        ),
        GELFTLSHandler("127.0.0.1", TEST_TLS_PORT, debugging_fields=True),
        GELFTLSHandler(
            "127.0.0.1",
            TEST_TLS_PORT,
            debugging_fields=True,
            validate=True,
            ca_certs=TEST_CERT,
        ),
    ]
)
def handler(request):
    return request.param


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_debug_mode(logger):
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(
        message, fields=["function", "pid", "thread_name"]
    )
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert graylog_response["file"].endswith("test_debugging_fields.py")
    assert "test_debug_mode" == graylog_response["function"]
    assert "line" in graylog_response
    assert "file" in graylog_response
    assert "pid" in graylog_response
    assert "thread_name" in graylog_response
