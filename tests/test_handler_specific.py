#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
from graypy import GELFTCPHandler


def test_tls_handler_init():
    with pytest.raises(ValueError):
        GELFTCPHandler(host='127.0.0.1', port=12204, tls=True)

    with pytest.raises(ValueError):
        # TODO:
        GELFTCPHandler(host='127.0.0.1', port=12204, ='/dev/null')
