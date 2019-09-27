#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""integration pytests for :mod:`graypy`

.. note::

    These tests require an local instance of Graylog to send messages to.
"""

try:
    import httplib
except ImportError:
    import http.client as httplib


def validate_local_graylog_up():
    """Test to see if a localhost instance of Graylog is currently running"""
    try:
        connection = httplib.HTTPConnection(
            host="127.0.0.1",
            port=9000,
        )
        connection.request('GET', "/api")
        resp = connection.getresponse()
        assert resp.status == 200
        return True
    except Exception:
        return False


LOCAL_GRAYLOG_UP = validate_local_graylog_up()
