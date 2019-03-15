#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy with mocks of python logging and
Graylog services"""

import logging

MOCK_LOG_RECORD_NAME = "MOCK_LOG_RECORD"
MOCK_LOG_RECORD = logging.LogRecord(
    MOCK_LOG_RECORD_NAME,
    logging.INFO,
    pathname=None,
    lineno=None,
    msg="Log message",
    args=(),
    exc_info=None,
)
