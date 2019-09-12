#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pytests for various GELF UDP message chunkers"""

import json
import logging
import struct
import zlib

import pytest

from graypy.handler import GELFTruncatingChunker, GELFWarningChunker, \
    BaseGELFChunker, BaseGELFHandler, SYSLOG_LEVELS, GELFChunkOverflowWarning


@pytest.mark.parametrize(
    "gelf_chunker",
    [
        BaseGELFChunker,
        GELFWarningChunker,
        GELFTruncatingChunker
    ]
)
def test_gelf_chunking(gelf_chunker):
    """Test various GELF chunkers"""
    message = b'12345'
    header = b'\x1e\x0f'
    chunks = list(gelf_chunker(chunk_size=2).chunk_message(message))
    expected = [
        (struct.pack('b', 0), struct.pack('b', 3), b'12'),
        (struct.pack('b', 1), struct.pack('b', 3), b'34'),
        (struct.pack('b', 2), struct.pack('b', 3), b'5')
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
    for chunk in chunks:
        stripped_chunk = b"".join(chunk.split(b'\x1e\x0f')[1:])
        message_id, chunk_seq, total_chunks = struct.unpack_from('QBB', stripped_chunk)
        chunk = stripped_chunk[struct.calcsize('QBB'):]
        gelf_bytes += chunk
    return gelf_bytes


@pytest.mark.parametrize(
    "gelf_chunker",
    [
        BaseGELFChunker,
        GELFWarningChunker,
        GELFTruncatingChunker
    ]
)
def test_gelf_chunkers(gelf_chunker):
    message = BaseGELFHandler().makePickle(
        logging.LogRecord("test_gelf_chunkers", logging.INFO,
                          None, None, "1" * 10, None, None))
    chunks = list(gelf_chunker(chunk_size=2).chunk_message(message))
    assert len(chunks) <= 128


@pytest.mark.parametrize(
    "gelf_chunker",
    [
        BaseGELFChunker,
        GELFWarningChunker,
        GELFTruncatingChunker
    ]
)
def test_gelf_chunkers_overflow(gelf_chunker):
    message = BaseGELFHandler().makePickle(
        logging.LogRecord("test_gelf_chunkers_overflow", logging.INFO,
                          None, None, "1" * 1000, None, None))
    chunks = list(gelf_chunker(chunk_size=2).chunk_message(message))
    assert len(chunks) <= 128


def test_chunk_overflow_truncate_uncompressed():
    message = BaseGELFHandler(compress=False).makePickle(
        logging.LogRecord("test_chunk_overflow_truncate_uncompressed",
                          logging.INFO, None, None, "1"*1000, None, None))
    with pytest.warns(GELFChunkOverflowWarning):
        chunks = list(GELFTruncatingChunker(chunk_size=2, compress=False).chunk_message(message))
    assert len(chunks) <= 128
    payload = rebuild_gelf_bytes_from_udp_chunks(chunks).decode("UTF-8")
    glef_json = json.loads(payload)
    assert glef_json["_chunk_overflow"] is True
    assert glef_json["short_message"] != "1"*1000
    assert glef_json["level"] == SYSLOG_LEVELS.get(logging.ERROR, logging.ERROR)


def test_chunk_overflow_truncate_compressed():
    message = BaseGELFHandler(compress=True).makePickle(
        logging.LogRecord("test_chunk_overflow_truncate_compressed",
                          logging.INFO, None, None, "123412345"*5000, None, None))
    with pytest.warns(GELFChunkOverflowWarning):
        chunks = list(GELFTruncatingChunker(chunk_size=2, compress=True).chunk_message(message))
    assert len(chunks) <= 128
    payload = zlib.decompress(rebuild_gelf_bytes_from_udp_chunks(chunks)).decode("UTF-8")
    glef_json = json.loads(payload)
    assert glef_json["_chunk_overflow"] is True
    assert glef_json["short_message"] != "123412345"*5000
    assert glef_json["level"] == SYSLOG_LEVELS.get(logging.ERROR, logging.ERROR)


def test_chunk_overflow_truncate_fail():
    message = BaseGELFHandler().makePickle(
        logging.LogRecord("test_chunk_overflow_truncate_fail", logging.INFO,
                          None, None, "1"*128, None, None))
    with pytest.warns(GELFChunkOverflowWarning):
        list(GELFWarningChunker(1).chunk_message(message))
