#!/usr/bin/python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy"""

import os
import uuid
import time
import logging
import pytest
import requests

from graypy import GELFUDPHandler, GELFTCPHandler

TEST_CONFIG_DIR = os.path.join(os.path.dirname(__file__),
                               os.path.join("integration", "config"))
TEST_CERT = os.path.join(TEST_CONFIG_DIR, "cert.pem")
TEST_KEY = os.path.join(TEST_CONFIG_DIR, "key.pem")
KEY_PASS = "secret"


@pytest.fixture(params=[
    GELFTCPHandler(host='localhost', port=12201),
    GELFTCPHandler(host='127.0.0.1', port=12201),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   extra_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   extra_fields=True, debugging_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host='localhost', port=12202),
    GELFUDPHandler(host='127.0.0.1', port=12202),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   compress=False),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   extra_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   extra_fields=True, compress=False),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   extra_fields=True, debugging_fields=True, compress=False),
])
def handler(request):
    return request.param


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   debugging_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   extra_fields=True, debugging_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   debugging_fields=True),
    GELFTCPHandler(host='127.0.0.1', port=12201,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   debugging_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202,
                   compress=False, debugging_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True,
                   debugging_fields=True),
    GELFUDPHandler(host='127.0.0.1', port=12202, extra_fields=True,
                   compress=False, debugging_fields=True),
])
def debugging_handler(request):
    return request.param


@pytest.fixture(params=[
    GELFTCPHandler(host='127.0.0.1', port=12201),
    GELFTCPHandler(host='127.0.0.1', port=12201, tls=True,
                   tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY,
                   tls_client_password=KEY_PASS),
    GELFUDPHandler(host='127.0.0.1', port=12202),
    GELFUDPHandler(host='127.0.0.1', port=12202, compress=False),
])
def simple_handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger('test_logger')
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


@pytest.yield_fixture
def simple_logger(simple_handler):
    logger = logging.getLogger('simple_test_logger')
    logger.addHandler(simple_handler)
    yield logger
    logger.removeHandler(simple_handler)


@pytest.yield_fixture
def debug_logger(debugging_handler):
    logger = logging.getLogger('debugging_test_logger')
    logger.addHandler(debugging_handler)
    yield logger
    logger.removeHandler(debugging_handler)


class DummyFilter(logging.Filter):
    def filter(self, record):
        record.ozzy = 'diary of a madman'
        record.van_halen = 1984
        record.id = 42
        return True


@pytest.yield_fixture
def filtered_logger(logger):
    dummy_filter = DummyFilter()
    logger.addFilter(dummy_filter)
    yield logger
    logger.removeFilter(dummy_filter)


@pytest.yield_fixture
def formatted_logger(handler):
    logger = logging.getLogger('formatted_test_logger')
    handler.setFormatter(logging.Formatter('%(levelname)s : %(message)s'))
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


def get_unique_message():
    return str(uuid.uuid4())


DEFAULT_FIELDS = [
    'message', 'full_message', 'source', 'level',
    'func', 'file', 'line', 'module', 'logger_name',
]

BASE_API_URL = 'http://127.0.0.1:9000/api/search/universal/relative?query={0}&range=5&fields='


def get_graylog_response(message, fields=None):
    fields = fields if fields else []
    api_resp = _get_api_response(message, fields)
    return _parse_api_response(api_resp)


def _build_api_string(message, fields):
    return BASE_API_URL.format(message) + '%2C'.join(set(DEFAULT_FIELDS + fields))


def _get_api_response(message, fields):
    time.sleep(3)
    url = _build_api_string(message, fields)
    api_response = requests.get(
        url,
        auth=('admin', 'admin'),
        headers={'accept': 'application/json'}
    )
    return api_response


def _parse_api_response(api_response):
    assert api_response.status_code == 200

    messages = api_response.json()['messages']
    assert len(messages) == 1

    return messages[0]['message']
