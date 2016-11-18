#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.postprocessor import MetadataFromTitlePP
from youtube_dl.postprocessor import XAttrMetadataPP

from test.helper import (
    FakeYDL
)

class TestMetadataFromTitle(unittest.TestCase):
    def test_format_to_regex(self):
        pp = MetadataFromTitlePP(None, '%(title)s - %(artist)s')
        self.assertEqual(pp._titleregex, '(?P<title>.+)\ \-\ (?P<artist>.+)')


class TestXAttrMetadataPP(unittest.TestCase):
    def test_run(self):
        def sort_by_key(x):
            return sorted(x, key=lambda x: x.get('key'))

        pp = XAttrMetadataPP(None)
        pp._downloader = FakeYDL()

        written_xattrs = []
        pp.write_xattr = lambda path, key, value: written_xattrs.append({'path': path, 'key': key, 'value': value})

        # test empty raise exception
        with self.assertRaises(KeyError) as context:
            info = {}
            pp.run(info)
        self.assertEqual(written_xattrs, [])

        # minimal test case
        written_xattrs = []
        info = {'filepath': 'foo'}
        a, b = pp.run(info)
        self.assertEqual(a, [])
        self.assertEqual(b, info)
        self.assertEqual(sort_by_key(written_xattrs), [
            {'key': 'user.creator', 'path': 'foo', 'value': b'youtube-dl'},
            {'key': 'user.dublincore.audience', 'path': 'foo', 'value': b'everybody'},
            {'key': 'user.dublincore.type', 'path': 'foo', 'value': b'MovingImage'}
        ])

        # minimal test case with age limit >= 18
        written_xattrs = []
        info = {'filepath': 'foo', 'age_limit': 18}
        a, b = pp.run(info)
        self.assertEqual(a, [])
        self.assertEqual(b, info)
        self.assertEqual(sort_by_key(written_xattrs), [
            {'key': 'user.creator', 'value': b'youtube-dl', 'path': 'foo'},
            {'key': 'user.dublincore.audience', 'value': b'adults', 'path': 'foo'},
            {'key': 'user.dublincore.type', 'value': b'MovingImage', 'path': 'foo'}
        ])

        # complete test-case
        written_xattrs = []
        info = {
            'filepath': 'foo_filepath',
            'age_limit': 19,
            'webpage_url': 'foo_webpage',
            'title': 'foo_title',
            'upload_date': 'foo_upload_date',
            'description': 'foo_description',
            'uploader': 'foo_uploader',
            'format': 'foo_format',
            'tags': ['foo', 'bar'],
            'categories':  ['FOO', 'baz', 'bar'],
            'foo': 'this_should_be_ignored',
        }
        a, b = pp.run(info)
        self.assertEqual(a, [])
        self.assertEqual(b, info)
        self.assertListEqual(sort_by_key(written_xattrs), [
            {'key': 'user.creator', 'path': 'foo_filepath', 'value': b'youtube-dl'},
            {'key': 'user.dublincore.audience', 'path': 'foo_filepath', 'value': b'adults'},
            {'key': 'user.dublincore.contributor', 'path': 'foo_filepath', 'value': b'foo_uploader'},
            {'key': 'user.dublincore.date', 'path': 'foo_filepath', 'value': b'foo_upload_date'},
            {'key': 'user.dublincore.description', 'path': 'foo_filepath', 'value': b'foo_description'},
            {'key': 'user.dublincore.format', 'path': 'foo_filepath', 'value': b'foo_format'},
            {'key': 'user.dublincore.subject', 'path': 'foo_filepath', 'value': b'bar,baz,foo'},
            {'key': 'user.dublincore.title', 'path': 'foo_filepath', 'value': b'foo_title'},
            {'key': 'user.dublincore.type', 'path': 'foo_filepath', 'value': b'MovingImage'},
            {'key': 'user.xdg.origin.url', 'path': 'foo_filepath', 'value': b'foo_webpage'},
            {'key': 'user.xdg.referrer.url', 'path': 'foo_filepath', 'value': b'foo_webpage'},
            {'key': 'user.xdg.tags', 'path': 'foo_filepath', 'value': b'bar,baz,foo'}
        ])

        # test-case with empty tags and categories
        written_xattrs = []
        info = {
            'filepath': 'foo_filepath',
            'age_limit': 19,
            'webpage_url': 'foo_webpage',
            'title': 'foo_title',
            'upload_date': 'foo_upload_date',
            'description': 'foo_description',
            'uploader': 'foo_uploader',
            'format': 'foo_format',
            'tags': [],
            'categories': None,
            'foo': 'this_should_be_ignored',
        }
        a, b = pp.run(info)
        self.assertEqual(a, [])
        self.assertEqual(b, info)
        self.assertEqual(sort_by_key(written_xattrs), [
            {'path': 'foo_filepath', 'value': b'youtube-dl', 'key': 'user.creator'},
            {'path': 'foo_filepath', 'value': b'adults', 'key': 'user.dublincore.audience'},
            {'path': 'foo_filepath', 'value': b'foo_uploader', 'key': 'user.dublincore.contributor'},
            {'path': 'foo_filepath', 'value': b'foo_upload_date', 'key': 'user.dublincore.date'},
            {'path': 'foo_filepath', 'value': b'foo_description', 'key': 'user.dublincore.description'},
            {'path': 'foo_filepath', 'value': b'foo_format', 'key': 'user.dublincore.format'},
            {'path': 'foo_filepath', 'value': b'foo_title', 'key': 'user.dublincore.title'},
            {'path': 'foo_filepath', 'value': b'MovingImage', 'key': 'user.dublincore.type'},
            {'path': 'foo_filepath', 'value': b'foo_webpage', 'key': 'user.xdg.origin.url'},
            {'path': 'foo_filepath', 'value': b'foo_webpage', 'key': 'user.xdg.referrer.url'}
        ])

    def test_get_tags(self):
        # test empty values
        self.assertEqual(XAttrMetadataPP.get_tags({}), None)
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': None}), None)
        self.assertEqual(XAttrMetadataPP.get_tags({'categories': None}), None)
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': None, 'categories': None}), None)

        # lower-case tags
        self.assertEqual(XAttrMetadataPP.get_tags({
            'tags': ['foo', 'FOO'],
            'categories': ['Foo', 'BAR']
        }), 'bar,foo'.encode('utf-8'))

        # test tags alone
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': ['foo']}), 'foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': ['foo', 'foo']}), 'foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': ['foo', 'bar']}), 'bar,foo'.encode('utf-8'))  # tags are sorted

        # test categories alone
        self.assertEqual(XAttrMetadataPP.get_tags({'categories': ['foo']}), 'foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'categories': ['foo', 'foo']}), 'foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'categories': ['foo', 'bar']}), 'bar,foo'.encode('utf-8'))  # tags are sorted

        # test tags + categories
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': ['foo'], 'categories': None}), 'foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': None, 'categories': ['foo']}), 'foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': ['foo'], 'categories': ['bar']}), 'bar,foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({'tags': ['bar'], 'categories': ['foo']}), 'bar,foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({
            'tags': ['foo', 'bar'],
            'categories': ['foo']
        }), 'bar,foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({
            'tags': ['foo', 'bar'],
            'categories': ['bar', 'foo']
        }), 'bar,foo'.encode('utf-8'))
        self.assertEqual(XAttrMetadataPP.get_tags({
            'tags': ['bar', 'baz'],
            'categories': ['bar', 'foo']
        }), 'bar,baz,foo'.encode('utf-8'))

        # test unicode
        categories = ['H₂O', 'РУ́ССКИЙ', '€ÃĂÀÂÁÅÄ']
        if sys.version_info.major < 3:
            categories = ['H₂O'.encode('utf-8'), 'РУ́ССКИЙ'.encode('utf-8'), '€ÃĂÀÂÁÅÄ'.encode('utf-8')]

        self.assertEqual(
            XAttrMetadataPP.get_tags({'categories': categories}),
            'h₂o,ру́сский,€ãăàâáåä'.encode('utf-8')
        )

if __name__ == '__main__':
    unittest.main()
