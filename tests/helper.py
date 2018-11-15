#!/usr/bin/python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy"""

import uuid
import time
import logging
import pytest
import requests


@pytest.yield_fixture
def logger(handler):
    logger = logging.getLogger('test')
    logger.addHandler(handler)
    yield logger
    logger.removeHandler(handler)


def log_warning(logger, message, args=None, fields=None):
    args = args if args else []
    fields = fields if fields else []
    logger.warning(message, *args)
    api_response = _get_api_response(message % args, fields)
    return _parse_api_response(api_response)


def log_exception(logger, message, exception, fields=None):
    fields = fields if fields else []
    logger.exception(exception)
    api_response = _get_api_response(message, fields)
    return _parse_api_response(api_response)


def get_unique_message():
    return str(uuid.uuid4())


DEFAULT_FIELDS = [
    'message', 'full_message', 'source', 'level',
    'func', 'file', 'line', 'module', 'logger_name',
]

BASE_API_URL = 'http://127.0.0.1:9000/api/search/universal/relative?query={0}&range=5&fields='


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
