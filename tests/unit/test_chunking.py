#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for various GELF UDP message chunkers"""

import json
import logging
import struct
import zlib

import pytest

from graypy.handler import (
    GELFTruncatingChunker,
    GELFWarningChunker,
    BaseGELFChunker,
    BaseGELFHandler,
    SYSLOG_LEVELS,
    GELFChunkOverflowWarning,
    GELFTruncationFailureWarning,
)


@pytest.mark.parametrize(
    "gelf_chunker", [BaseGELFChunker, GELFWarningChunker, GELFTruncatingChunker]
)
def test_gelf_chunking(gelf_chunker):
    """Test various GELF chunkers"""
    message = b"12345"
    header = b"\x1e\x0f"
    chunks = list(gelf_chunker(chunk_size=2).chunk_message(message))
    expected = [
        (struct.pack("b", 0), struct.pack("b", 3), b"12"),
        (struct.pack("b", 1), struct.pack("b", 3), b"34"),
        (struct.pack("b", 2), struct.pack("b", 3), b"5"),
    ]

    assert len(chunks) == len(expected)

    for index, chunk in enumerate(chunks):
        expected_index, expected_chunks_count, expected_chunk = expected[index]
        assert header == chunk[:2]
        assert expected_index == chunk[10:11]
        assert expected_chunks_count == chunk[11:12]
        assert expected_chunk == chunk[12:]


def rebuild_gelf_bytes_from_udp_chunks(chunks):
    gelf_bytes = b""
    bsize = len(chunks[0])
    for chunk in chunks:
        if len(chunk) < bsize:
            gelf_bytes += chunk[-(bsize - len(chunk)) :]
        else:
            gelf_bytes += chunk[((2 + struct.calcsize("QBB")) - len(chunk)) :]
    return gelf_bytes


@pytest.mark.parametrize(
    "gelf_chunker", [BaseGELFChunker, GELFWarningChunker, GELFTruncatingChunker]
)
def test_gelf_chunkers(gelf_chunker):
    message = BaseGELFHandler().makePickle(
        logging.LogRecord(
            "test_gelf_chunkers", logging.INFO, None, None, "1" * 10, None, None
        )
    )
    chunks = list(gelf_chunker(chunk_size=2).chunk_message(message))
    assert len(chunks) <= 128


@pytest.mark.parametrize(
    "gelf_chunker", [BaseGELFChunker, GELFWarningChunker, GELFTruncatingChunker]
)
def test_gelf_chunkers_overflow(gelf_chunker):
    message = BaseGELFHandler().makePickle(
        logging.LogRecord(
            "test_gelf_chunkers_overflow",
            logging.INFO,
            None,
            None,
            "1" * 1000,
            None,
            None,
        )
    )
    chunks = list(gelf_chunker(chunk_size=1).chunk_message(message))
    assert len(chunks) <= 128


def test_chunk_overflow_truncate_uncompressed():
    message = BaseGELFHandler(compress=False).makePickle(
        logging.LogRecord(
            "test_chunk_overflow_truncate_uncompressed",
            logging.INFO,
            None,
            None,
            "1" * 1000,
            None,
            None,
        )
    )
    with pytest.warns(GELFChunkOverflowWarning):
        chunks = list(
            GELFTruncatingChunker(chunk_size=2, compress=False).chunk_message(message)
        )
    assert len(chunks) <= 128
    payload = rebuild_gelf_bytes_from_udp_chunks(chunks).decode("UTF-8")
    glef_json = json.loads(payload)
    assert glef_json["_chunk_overflow"] is True
    assert glef_json["short_message"] in "1" * 1000
    assert glef_json["level"] == SYSLOG_LEVELS.get(logging.ERROR, logging.ERROR)


def test_chunk_overflow_truncate_compressed():
    message = BaseGELFHandler(compress=True).makePickle(
        logging.LogRecord(
            "test_chunk_overflow_truncate_compressed",
            logging.INFO,
            None,
            None,
            "123412345" * 5000,
            None,
            None,
        )
    )
    with pytest.warns(GELFChunkOverflowWarning):
        chunks = list(
            GELFTruncatingChunker(chunk_size=2, compress=True).chunk_message(message)
        )
    assert len(chunks) <= 128
    payload = zlib.decompress(rebuild_gelf_bytes_from_udp_chunks(chunks)).decode(
        "UTF-8"
    )
    glef_json = json.loads(payload)
    assert glef_json["_chunk_overflow"] is True
    assert glef_json["short_message"] in "123412345" * 5000
    assert glef_json["level"] == SYSLOG_LEVELS.get(logging.ERROR, logging.ERROR)


def test_chunk_overflow_truncate_fail():
    message = BaseGELFHandler().makePickle(
        logging.LogRecord(
            "test_chunk_overflow_truncate_fail",
            logging.INFO,
            None,
            None,
            "1" * 1000,
            None,
            None,
        )
    )
    with pytest.warns(GELFTruncationFailureWarning):
        list(GELFTruncatingChunker(1).chunk_message(message))


def test_chunk_overflow_truncate_fail_large_inherited_field():
    message = BaseGELFHandler(
        facility="this is a really long facility" * 5000
    ).makePickle(
        logging.LogRecord(
            "test_chunk_overflow_truncate_fail",
            logging.INFO,
            None,
            None,
            "reasonable message",
            None,
            None,
        )
    )
    with pytest.warns(GELFTruncationFailureWarning):
        list(GELFTruncatingChunker(2).chunk_message(message))
