#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for :class:`graypy.rabbitmq.ExcludeFilter`"""

import pytest

from graypy import ExcludeFilter

from tests.unit.helper import MOCK_LOG_RECORD_NAME, MOCK_LOG_RECORD


@pytest.mark.parametrize("name", [None, ""])
def test_invalid_name(name):
    """Test constructing:class:`graypy.rabbitmq.ExcludeFilter` with a
    invalid ``name`` argument"""
    with pytest.raises(ValueError):
        ExcludeFilter(name)


@pytest.mark.parametrize("name", ["foobar", ".", " "])
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
