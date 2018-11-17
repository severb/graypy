#!/usr/bin/python
# -*- coding: utf-8 -*-

"""integration pytests for :mod:`graypy`

.. note::

    These tests require an local instance of graylog to send messages to.
"""


import requests


try:
    requests.get("http://127.0.0.1:9000/api")
    LOCAL_GRAYLOG_UP = True
except Exception:
    LOCAL_GRAYLOG_UP = False
