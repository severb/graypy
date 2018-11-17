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

TEST_UDP_PORT = 12202
TEST_TCP_PORT = 12201
TEST_TLS_PORT = 12204


@pytest.fixture(params=[
    GELFTCPHandler(host="localhost", port=TEST_TCP_PORT),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TCP_PORT),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TCP_PORT,
                   extra_fields=True),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TCP_PORT,
                   extra_fields=True, debugging_fields=True),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TLS_PORT,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TLS_PORT,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True),
    GELFTCPHandler(host="127.0.0.1", port=TEST_TLS_PORT,
                   tls=True, tls_client_cert=TEST_CERT,
                   tls_client_key=TEST_KEY, tls_client_password=KEY_PASS,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host="localhost", port=TEST_UDP_PORT),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   compress=False),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True, compress=False),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True, debugging_fields=True),
    GELFUDPHandler(host="127.0.0.1", port=TEST_UDP_PORT,
                   extra_fields=True, debugging_fields=True, compress=False),
])
def handler(request):
    return request.param


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


@pytest.yield_fixture
def formatted_logger(handler):
    logger = logging.getLogger("formatted_test_logger")
    handler.setFormatter(logging.Formatter("%(levelname)s : %(message)s"))
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


def get_unique_message():
    return str(uuid.uuid4())


DEFAULT_FIELDS = [
    "message", "full_message", "source", "level",
    "func", "file", "line", "module", "logger_name",
]

BASE_API_URL = "http://127.0.0.1:9000/api/search/universal/relative?query={0}&range=5&fields="


def get_graylog_response(message, fields=None):
    fields = fields if fields else []
    api_resp = _get_api_response(message, fields)
    return _parse_api_response(api_resp)


def _build_api_string(message, fields):
    return BASE_API_URL.format(message) + "%2C".join(set(DEFAULT_FIELDS + fields))


def _get_api_response(message, fields):
    time.sleep(3)
    url = _build_api_string(message, fields)
    api_response = requests.get(
        url,
        auth=("admin", "admin"),
        headers={"accept": "application/json"}
    )
    return api_response


def _parse_api_response(api_response):
    assert api_response.status_code == 200
    messages = api_response.json()["messages"]
    return messages[0]["message"]
