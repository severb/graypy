#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import pytest
import mock
from graypy import GELFTCPHandler, GELFUDPHandler
from tests.helper import logger, get_unique_message, log_exception, TEST_KEY, \
    TEST_CERT


def fake_handle(self, record):
    self.format(record)
    record.exc_info = None
    self.emit(record)


def test_full_message(logger):
    message = get_unique_message()

    with mock.patch.object(logging.Handler, 'handle', new=fake_handle):
        try:
            raise ValueError(message)
        except ValueError as e:
            graylog_response = log_exception(logger, message, e)
            assert message in graylog_response['full_message']
            assert 'Traceback (most recent call last)' in graylog_response['full_message']
            assert 'ValueError: ' in graylog_response['full_message']
