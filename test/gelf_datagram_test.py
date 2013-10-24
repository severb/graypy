import json
import logging
import unittest
import zlib

import mock

from graypy.handler import GELFHandler


class FakeCustomObject(object):

    def __repr__(self):
        return 'repr:' + self.__class__.__name__


class GELFHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self.handler = GELFHandler('some.host')
        self.logger = logging.getLogger('test')
        self.logger.addHandler(self.handler)

    def test_normal(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            self.logger.error('Normal log message')
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], decoded['full_message'])
        self.assertEqual(decoded['short_message'], 'Normal log message')

    def test_normal_exception_handler(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            try:
                raise SyntaxError('Syntax error')
            except Exception:
                self.logger.exception('Failed')
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], 'Failed')
        self.assertTrue(decoded['full_message'].startswith(
            'Traceback (most recent call last):'))
        self.assertTrue(decoded['full_message'].endswith(
            'SyntaxError: Syntax error\n'))

    def test_unicode(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            self.logger.error(u'Mensaje de registro espa\xf1ol')
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], decoded['full_message'])
        self.assertEqual(decoded['short_message'],
                         u'Mensaje de registro espa\xf1ol')

    def test_unicode_exception_handler(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            try:
                raise SyntaxError('S\xc2\xa5nt4x 3r\xc2\xae0r')
            except Exception:
                self.logger.exception(u'une d\xc3\xa9faillance')
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], u'une d\xc3\xa9faillance')
        self.assertTrue(decoded['full_message'].startswith(
            u'Traceback (most recent call last):'))
        self.assertTrue(decoded['full_message'].endswith(
            u'SyntaxError: S\xa5nt4x 3r\xae0r\n'))

    def test_broken(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            self.logger.error('Broken \xde log message')
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], decoded['full_message'])
        self.assertEqual(decoded['short_message'],
                         r'Broken \xde log message')

    def test_broken_exception_handler(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            try:
                raise SyntaxError('Syntax \xde error')
            except Exception:
                self.logger.exception('Failed')
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], 'Failed')
        self.assertTrue(decoded['full_message'].startswith(
            'Traceback (most recent call last):'))
        # XXX: the newline here should really be unescaped
        self.assertTrue(decoded['full_message'].endswith(
            'Syntax \\xde error\\n'))

    def test_arbitrary_object(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            self.logger.error('Log message',
                              extra={'foo': FakeCustomObject()})
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], decoded['full_message'])
        self.assertEqual(decoded['short_message'], 'Log message')
        self.assertEqual(decoded['_foo'], 'repr:FakeCustomObject')

    def test_list(self):
        with mock.patch.object(self.handler, 'send') as mock_send:
            self.logger.error('Log message',
                              extra={'foo': ['bar', 'baz']})
            [[[arg], _]] = mock_send.call_args_list
        decoded = json.loads(zlib.decompress(arg))
        self.assertEqual(decoded['short_message'], decoded['full_message'])
        self.assertEqual(decoded['short_message'], 'Log message')
        # XXX: This is, probably, not the most desired behaviour. After all,
        # lists can be json serialized just fine.
        self.assertEqual(decoded['_foo'], repr(['bar', 'baz']))

    def tearDown(self):
        self.logger.removeHandler(self.handler)
