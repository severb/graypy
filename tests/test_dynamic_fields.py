#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import pytest
from graypy import GELFTCPHandler, GELFUDPHandler
from tests.helper import logger, get_unique_message, log_warning


class DummyFilter(logging.Filter):
    def filter(self, record):
        record.ozzy = 'diary of a madman'
        record.van_halen = 1984
        record.id = 42
        return True


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201, extra_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True, compress=False),
])
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger('test')
    dummy_filter = DummyFilter()
    logger.addFilter(dummy_filter)
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)
    logger.removeFilter(dummy_filter)


def test_dynamic_fields(logger):
    message = get_unique_message()
    graylog_response = log_warning(logger, message, fields=['ozzy', 'van_halen'])
    assert graylog_response['message'] == message
    assert graylog_response['ozzy'] == 'diary of a madman'
    assert graylog_response['van_halen'] == 1984
    assert graylog_response['_id'] != 42
    assert 'id' not in graylog_response
