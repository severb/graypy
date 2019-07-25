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
    exclude_filter = ExcludeFilter(name)
    assert exclude_filter
    assert name == exclude_filter.name
    assert len(name) == exclude_filter.nlen


def test_non_filtering_record():
    exclude_filter = ExcludeFilter("NOT" + MOCK_LOG_RECORD_NAME)
    assert exclude_filter.filter(MOCK_LOG_RECORD)
    assert MOCK_LOG_RECORD.name != exclude_filter.name


def test_filtering_record():
    exclude_filter = ExcludeFilter(MOCK_LOG_RECORD_NAME)
    assert not exclude_filter.filter(MOCK_LOG_RECORD)
    assert MOCK_LOG_RECORD.name == exclude_filter.name
