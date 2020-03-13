#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""helper functions for testing graypy with a local Graylog instance"""

from time import sleep
from uuid import uuid4

import requests


def get_unique_message():
    return str(uuid4())


DEFAULT_FIELDS = [
    "message",
    "full_message",
    "source",
    "level",
    "func",
    "file",
    "line",
    "module",
    "logger_name",
]

BASE_API_URL = 'http://127.0.0.1:9000/api/search/universal/relative?query=message:"{0}"&range=300&fields='


def get_graylog_response(message, fields=None):
    """Search for a given log message (with possible additional fields)
    within a local Graylog instance"""
    fields = fields if fields else []
    tries = 0

    while True:
        try:
            return _parse_api_response(
                api_response=_get_api_response(message, fields), wanted_message=message
            )
        except ValueError:
            sleep(2)
            if tries == 5:
                raise
            tries += 1


def _build_api_string(message, fields):
    return BASE_API_URL.format(message) + "%2C".join(set(DEFAULT_FIELDS + fields))


def _get_api_response(message, fields):
    url = _build_api_string(message, fields)
    api_response = requests.get(
        url, auth=("admin", "admin"), headers={"accept": "application/json"}
    )
    return api_response


def _parse_api_response(api_response, wanted_message):
    assert api_response.status_code == 200
    print(api_response.json())
    for message in api_response.json()["messages"]:
        if message["message"]["message"] == wanted_message:
            return message["message"]
    raise ValueError(
        "wanted_message: '{}' not within api_response: {}".format(
            wanted_message, api_response
        )
    )
