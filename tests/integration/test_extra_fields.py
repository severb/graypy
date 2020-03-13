#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for validating the addition of extra fields within GELF logs"""

import logging
import pytest
from graypy import GELFTLSHandler, GELFTCPHandler, GELFUDPHandler, GELFHTTPHandler

from tests.helper import (
    TEST_CERT,
    TEST_TCP_PORT,
    TEST_HTTP_PORT,
    TEST_TLS_PORT,
    TEST_UDP_PORT,
)
from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_unique_message, get_graylog_response


class DummyFilter(logging.Filter):
    def filter(self, record):
        record.ozzy = "diary of a madman"
        record.van_halen = 1984
        record.id = 42
        return True


@pytest.fixture(
    params=[
        GELFTCPHandler("127.0.0.1", TEST_TCP_PORT, extra_fields=True),
        GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, extra_fields=True),
        GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, compress=False, extra_fields=True),
        GELFHTTPHandler("127.0.0.1", TEST_HTTP_PORT, extra_fields=True),
        GELFHTTPHandler("127.0.0.1", TEST_HTTP_PORT, compress=False, extra_fields=True),
        GELFTLSHandler("127.0.0.1", TEST_TLS_PORT, extra_fields=True),
        GELFTLSHandler(
            "127.0.0.1",
            TEST_TLS_PORT,
            validate=True,
            ca_certs=TEST_CERT,
            extra_fields=True,
        ),
    ]
)
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger("test")
    dummy_filter = DummyFilter()
    logger.addFilter(dummy_filter)
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)
    logger.removeFilter(dummy_filter)


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_dynamic_fields(logger):
    message = get_unique_message()
    logger.error(message)
    graylog_response = get_graylog_response(message, fields=["ozzy", "van_halen"])
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert "diary of a madman" == graylog_response["ozzy"]
    assert 1984 == graylog_response["van_halen"]
    assert 42 != graylog_response["_id"]
    assert "id" not in graylog_response
