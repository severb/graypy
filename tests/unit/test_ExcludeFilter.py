#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pytests for :class:`graypy.rabbitmq.ExcludeFilter`"""

import logging

import pytest

from graypy import ExcludeFilter

MOCK_LOG_RECORD_NAME = "MOCK_LOG_RECORD"
MOCK_LOG_RECORD = logging.LogRecord(
    MOCK_LOG_RECORD_NAME,
    logging.INFO,
    pathname=None,
    lineno=None,
    msg="Log message",
    args=(),
    exc_info=(None, None, None),
)


@pytest.mark.parametrize("name", [None, ""])
def test_invalid_name(name):
    """Test constructing:class:`graypy.rabbitmq.ExcludeFilter` with a
    invalid ``name`` argument"""
    with pytest.raises(ValueError):
        ExcludeFilter(name)


@pytest.mark.parametrize("name", ["foobar", ".", b"\00"])
def test_valid_name(name):
    """Test constructing :class:`graypy.rabbitmq.ExcludeFilter` with a
    valid ``name`` argument"""
    filter = ExcludeFilter(name)
    assert filter
    assert name == filter.name
    assert len(name) == filter.nlen


def test_non_filtering_record():
    filter = ExcludeFilter("NOT" + MOCK_LOG_RECORD_NAME)
    assert filter.filter(MOCK_LOG_RECORD)
    assert MOCK_LOG_RECORD.name != filter.name


def test_filtering_record():
    filter = ExcludeFilter(MOCK_LOG_RECORD_NAME)
    assert not filter.filter(MOCK_LOG_RECORD)
    assert MOCK_LOG_RECORD.name == filter.name
