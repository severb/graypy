#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for addressing potential issues with adding an ``status`` extra
field withing a given log and having the log failing to appear within graylog.

Related issue:
- Fails to log silently with specific extra field #85

URL:
- https://github.com/severb/graypy/issues/85
"""

import pytest

from tests.helper import handler, logger
from tests.integration import LOCAL_GRAYLOG_UP
from tests.integration.helper import get_unique_message, get_graylog_response


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_non_status_field_log(logger):
    message = get_unique_message()
    logger.error(message, extra={"foo": "bar"})
    graylog_response = get_graylog_response(message, fields=["foo"])
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert "bar" == graylog_response["foo"]


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_status_field_issue(logger):
    message = get_unique_message()
    logger.error(message, extra={"status": "OK"})
    graylog_response = get_graylog_response(message, fields=["status"])
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert "OK" == graylog_response["status"]


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP, reason="local Graylog instance not up")
def test_status_field_issue_multi(logger):
    message = get_unique_message()
    logger.error(message, extra={"foo": "bar", "status": "OK"})
    graylog_response = get_graylog_response(message, fields=["foo", "status"])
    assert message == graylog_response["message"]
    assert "long_message" not in graylog_response
    assert "timestamp" in graylog_response
    assert "bar" == graylog_response["foo"]
    assert "OK" == graylog_response["status"]
