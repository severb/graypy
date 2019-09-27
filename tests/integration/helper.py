#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy with a local Graylog instance"""

from base64 import b64encode
from time import sleep
from uuid import uuid4
import json

try:
    import httplib
except ImportError:
    import http.client as httplib


def get_unique_message():
    return str(uuid4())


DEFAULT_FIELDS = [
    "message", "full_message", "source", "level",
    "func", "file", "line", "module", "logger_name",
]

BASE_API_URL_PATH = '/api/search/universal/relative?query=message:"{0}"&range=300&fields='


def get_graylog_response(message, fields=None):
    """Search for a given log message (with possible additional fields)
    within a local Graylog instance"""
    fields = fields if fields else []
    tries = 0

    while True:
        try:
            return _get_api_response(message, fields)
        except ValueError:
            sleep(2)
            if tries == 5:
                raise
            tries += 1


def _build_api_string(message, fields):
    return BASE_API_URL_PATH.format(message) + "%2C".join(set(DEFAULT_FIELDS + fields))


def _get_api_response(message, fields):
    connection = httplib.HTTPConnection(
        host="127.0.0.1",
        port=9000,
    )
    connection.request(
        'GET',
        url=_build_api_string(message, fields),
        headers={
            "Accept": "application/json",
            'Authorization': 'Basic %s' % b64encode(b"admin:admin").decode("ascii")
        }
    )
    resp = connection.getresponse()
    assert resp.status == 200
    api_response = resp.read()
    search_results = json.loads(api_response)
    print(api_response)
    for search_message in search_results["messages"]:
        if search_message["message"]["message"] == message:
            return search_message["message"]
    raise ValueError("message: '{}' not within api_response: {}".format(message, api_response))


