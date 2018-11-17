#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest

from tests.integration import LOCAL_GRAYLOG_UP
from tests.helper import get_graylog_response, get_unique_message, \
    logger, handler


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local graylog instance not up")
def test_non_status_field_log(logger):
    message = get_unique_message()
    logger.error(message, extra={"foo": "bar"})
    graylog_response = get_graylog_response(message, fields=["foo"])
    assert message == graylog_response["message"]
    assert "bar" == graylog_response["foo"]


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local graylog instance not up")
def test_status_field_issue(logger):
    message = get_unique_message()
    logger.error(message, extra={"status": "OK"})
    graylog_response = get_graylog_response(message, fields=["status"])
    assert message == graylog_response["message"]
    assert "OK" == graylog_response["status"]


@pytest.mark.skipif(not LOCAL_GRAYLOG_UP,
                    reason="local graylog instance not up")
def test_status_field_issue_multi(logger):
    message = get_unique_message()
    logger.error(message, extra={"foo": "bar", "status": "OK"})
    graylog_response = get_graylog_response(message, fields=["foo", "status"])
    assert message == graylog_response["message"]
    assert "bar" == graylog_response["foo"]
    assert "OK" == graylog_response["status"]
