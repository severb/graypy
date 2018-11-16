#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import pytest

from graypy import GELFUDPHandler, GELFTCPHandler
from tests.helper import log_warning, _get_api_response, _parse_api_response, get_unique_message
#
# mylog=logging.getLogger('order.processing')
# handler=GELFHandler('mylogserver',debugging_fields=True)
# mylog.addHandler(handler)
# #the following line works
# mylog.info("Test123",extra={'fld1':1,'fld2':2})
# # the following line doesn't output anything to GrayLog:


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
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


def status_field_issue(handler):
    logger.info(get_unique_message(), extra={'fld1': 1, 'fld2': 2, 'status': 'OK'})
    api_response = _get_api_response(get_unique_message(), [])
    graylog_response =  _parse_api_response(api_response)
    assert graylog_response['status'] == "OK"
