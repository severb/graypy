#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""integration pytests for :mod:`graypy`

.. note::

    These tests require an local instance of Graylog to send messages to.
"""

import requests


def validate_local_graylog_up():
    """Test to see if a localhost instance of Graylog is currently running"""
    try:
        requests.get("http://127.0.0.1:9000/api")
        return True
    except Exception:
        return False


LOCAL_GRAYLOG_UP = validate_local_graylog_up()
