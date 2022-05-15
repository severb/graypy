#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for addressing potential issues when an overflowing
message warning gets logged by graypy.

Related issue:
- warnings.warn print whole overflowing message, I think this is a bug #134

URL:
- https://github.com/severb/graypy/issues/134
"""

import logging
import warnings
from importlib import reload

import pytest
import timeout_decorator

from graypy.handler import (
    SYSLOG_LEVELS,
    GELFUDPHandler,
    GELFWarningChunker,
    GELFTruncatingChunker,
    GELFChunkOverflowWarning,
)

from tests.helper import TEST_UDP_PORT
from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import (
    get_unique_message,
    get_graylog_response,
    message_check_contains,
)


def refresh_logging():
    """Refresh the logging library to avoid any issues"""
    logging.shutdown()
    reload(logging)


@pytest.mark.parametrize("gelf_chunker", [GELFWarningChunker, GELFTruncatingChunker])
@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_graypy_warnings_can_be_graypy_logged(gelf_chunker):
    """Test that python warnings can be configured to be captured and logged
    by a graypy handler"""
    refresh_logging()

    logging.captureWarnings(True)

    handler = GELFUDPHandler("127.0.0.1", TEST_UDP_PORT, gelf_chunker=gelf_chunker())
    handler.setLevel(logging.DEBUG)

    logger = logging.getLogger("test_graypy_warnings_can_be_graypy_logged")
    logger.addHandler(handler)

    py_warnings_logger = logging.getLogger("py.warnings")
    py_warnings_logger.addHandler(handler)

    unique_warning = get_unique_message()

    warnings.warn(unique_warning)

    graylog_response = get_graylog_response(
        unique_warning, message_check=message_check_contains
    )
    assert unique_warning in graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert SYSLOG_LEVELS[logging.WARNING] == graylog_response["level"]


@pytest.mark.parametrize("gelf_chunker", [GELFWarningChunker, GELFTruncatingChunker])
@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_graypy_overflowing_warnings_recurse_forever(gelf_chunker):
    """Test that if we setup Python warnings to be logged with graypy
    and we send a GELF chunk overflowing message we will recurse forever.
    """
    refresh_logging()

    logging.captureWarnings(True)

    handler = GELFUDPHandler(
        "127.0.0.1", TEST_UDP_PORT, gelf_chunker=gelf_chunker(chunk_size=2)
    )
    handler.setLevel(logging.DEBUG)

    logger = logging.getLogger("test_graypy_overflowing_warnings_recurse_forever")
    logger.addHandler(handler)

    py_warnings_logger = logging.getLogger("py.warnings")
    py_warnings_logger.addHandler(handler)

    unique_message = get_unique_message()

    @timeout_decorator.timeout(5)
    def log_error_that_should_warning_loop_forever():
        logger.error(unique_message * 6000)

    log_error_that_should_warning_loop_forever()


@pytest.mark.parametrize("gelf_chunker", [GELFWarningChunker, GELFTruncatingChunker])
@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_graypy_ignored_overflowing_warnings_halt(gelf_chunker):
    """Test that if we ignore :class:`.handler.GELFChunkOverflowWarning`
    graypy will not recurse forever.
    """
    refresh_logging()
    # NOTE: if `warnings.filterwarnings("ignore", category=GELFChunkOverflowWarning)`
    #   is not present the overflowing message warning will be logged by grapy
    #   making another overflowing message that will be logged by graypy
    #   making another...
    warnings.filterwarnings("ignore", category=GELFChunkOverflowWarning)

    logging.captureWarnings(True)

    handler = GELFUDPHandler(
        "127.0.0.1", TEST_UDP_PORT, gelf_chunker=gelf_chunker(chunk_size=2)
    )
    handler.setLevel(logging.DEBUG)

    logger = logging.getLogger("test_graypy_ignored_overflowing_warnings_halt")
    logger.addHandler(handler)

    py_warnings_logger = logging.getLogger("py.warnings")
    py_warnings_logger.addHandler(handler)

    unique_message = get_unique_message()

    logger.error(unique_message * 6000)
    # the overflowing message warning is ignored and the overflowing logger
    # error message is silently dropped
