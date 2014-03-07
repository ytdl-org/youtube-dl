#!/usr/bin/env python
# coding: utf-8

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Various small unit tests
import io
import xml.etree.ElementTree

#from youtube_dl.utils import htmlentity_transform
from youtube_dl.utils import (
    DateRange,
    encodeFilename,
    find_xpath_attr,
    fix_xml_ampersands,
    get_meta_content,
    orderedSet,
    PagedList,
    parse_duration,
    read_batch_urls,
    sanitize_filename,
    shell_quote,
    smuggle_url,
    str_to_int,
    struct_unpack,
    timeconvert,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    url_basename,
    urlencode_postdata,
    xpath_with_ns,
)

if sys.version_info < (3, 0):
    _compat_str = lambda b: b.decode('unicode-escape')
else:
    _compat_str = lambda s: s


class TestUtil(unittest.TestCase):
    def test_timeconvert(self):
        self.assertTrue(timeconvert('') is None)
        self.assertTrue(timeconvert('bougrg') is None)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename('abc'), 'abc')
        self.assertEqual(sanitize_filename('abc_d-e'), 'abc_d-e')

        self.assertEqual(sanitize_filename('123'), '123')

        self.assertEqual('abc_de', sanitize_filename('abc/de'))
        self.assertFalse('/' in sanitize_filename('abc/de///'))

        self.assertEqual('abc_de', sanitize_filename('abc/<>\\*|de'))
        self.assertEqual('xxx', sanitize_filename('xxx/<>\\*|'))
        self.assertEqual('yes no', sanitize_filename('yes? no'))
        self.assertEqual('this - that', sanitize_filename('this: that'))

        self.assertEqual(sanitize_filename('AT&T'), 'AT&T')
        aumlaut = _compat_str('\xe4')
        self.assertEqual(sanitize_filename(aumlaut), aumlaut)
        tests = _compat_str('\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u0430')
        self.assertEqual(sanitize_filename(tests), tests)

        forbidden = '"\0\\/'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc))

    def test_sanitize_filename_restricted(self):
        self.assertEqual(sanitize_filename('abc', restricted=True), 'abc')
        self.assertEqual(sanitize_filename('abc_d-e', restricted=True), 'abc_d-e')

        self.assertEqual(sanitize_filename('123', restricted=True), '123')

        self.assertEqual('abc_de', sanitize_filename('abc/de', restricted=True))
        self.assertFalse('/' in sanitize_filename('abc/de///', restricted=True))

        self.assertEqual('abc_de', sanitize_filename('abc/<>\\*|de', restricted=True))
        self.assertEqual('xxx', sanitize_filename('xxx/<>\\*|', restricted=True))
        self.assertEqual('yes_no', sanitize_filename('yes? no', restricted=True))
        self.assertEqual('this_-_that', sanitize_filename('this: that', restricted=True))

        tests = _compat_str('a\xe4b\u4e2d\u56fd\u7684c')
        self.assertEqual(sanitize_filename(tests, restricted=True), 'a_b_c')
        self.assertTrue(sanitize_filename(_compat_str('\xf6'), restricted=True) != '')  # No empty filename

        forbidden = '"\0\\/&!: \'\t\n()[]{}$;`^,#'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc, restricted=True))

        # Handle a common case more neatly
        self.assertEqual(sanitize_filename(_compat_str('\u5927\u58f0\u5e26 - Song'), restricted=True), 'Song')
        self.assertEqual(sanitize_filename(_compat_str('\u603b\u7edf: Speech'), restricted=True), 'Speech')
        # .. but make sure the file name is never empty
        self.assertTrue(sanitize_filename('-', restricted=True) != '')
        self.assertTrue(sanitize_filename(':', restricted=True) != '')

    def test_sanitize_ids(self):
        self.assertEqual(sanitize_filename('_n_cd26wFpw', is_id=True), '_n_cd26wFpw')
        self.assertEqual(sanitize_filename('_BD_eEpuzXw', is_id=True), '_BD_eEpuzXw')
        self.assertEqual(sanitize_filename('N0Y__7-UOdI', is_id=True), 'N0Y__7-UOdI')

    def test_ordered_set(self):
        self.assertEqual(orderedSet([1, 1, 2, 3, 4, 4, 5, 6, 7, 3, 5]), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(orderedSet([]), [])
        self.assertEqual(orderedSet([1]), [1])
        #keep the list ordered
        self.assertEqual(orderedSet([135, 1, 1, 1]), [135, 1])

    def test_unescape_html(self):
        self.assertEqual(unescapeHTML(_compat_str('%20;')), _compat_str('%20;'))
        
    def test_daterange(self):
        _20century = DateRange("19000101","20000101")
        self.assertFalse("17890714" in _20century)
        _ac = DateRange("00010101")
        self.assertTrue("19690721" in _ac)
        _firstmilenium = DateRange(end="10000101")
        self.assertTrue("07110427" in _firstmilenium)

    def test_unified_dates(self):
        self.assertEqual(unified_strdate('December 21, 2010'), '20101221')
        self.assertEqual(unified_strdate('8/7/2009'), '20090708')
        self.assertEqual(unified_strdate('Dec 14, 2012'), '20121214')
        self.assertEqual(unified_strdate('2012/10/11 01:56:38 +0000'), '20121011')
        self.assertEqual(unified_strdate('1968-12-10'), '19681210')

    def test_find_xpath_attr(self):
        testxml = u'''<root>
            <node/>
            <node x="a"/>
            <node x="a" y="c" />
            <node x="b" y="d" />
        </root>'''
        doc = xml.etree.ElementTree.fromstring(testxml)

        self.assertEqual(find_xpath_attr(doc, './/fourohfour', 'n', 'v'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', 'a'), doc[1])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y', 'c'), doc[2])

    def test_meta_parser(self):
        testhtml = u'''
        <head>
            <meta name="description" content="foo &amp; bar">
            <meta content='Plato' name='author'/>
        </head>
        '''
        get_meta = lambda name: get_meta_content(name, testhtml)
        self.assertEqual(get_meta('description'), u'foo & bar')
        self.assertEqual(get_meta('author'), 'Plato')

    def test_xpath_with_ns(self):
        testxml = u'''<root xmlns:media="http://example.com/">
            <media:song>
                <media:author>The Author</media:author>
                <url>http://server.com/download.mp3</url>
            </media:song>
        </root>'''
        doc = xml.etree.ElementTree.fromstring(testxml)
        find = lambda p: doc.find(xpath_with_ns(p, {'media': 'http://example.com/'}))
        self.assertTrue(find('media:song') is not None)
        self.assertEqual(find('media:song/media:author').text, u'The Author')
        self.assertEqual(find('media:song/url').text, u'http://server.com/download.mp3')

    def test_smuggle_url(self):
        data = {u"ö": u"ö", u"abc": [3]}
        url = 'https://foo.bar/baz?x=y#a'
        smug_url = smuggle_url(url, data)
        unsmug_url, unsmug_data = unsmuggle_url(smug_url)
        self.assertEqual(url, unsmug_url)
        self.assertEqual(data, unsmug_data)

        res_url, res_data = unsmuggle_url(url)
        self.assertEqual(res_url, url)
        self.assertEqual(res_data, None)

    def test_shell_quote(self):
        args = ['ffmpeg', '-i', encodeFilename(u'ñ€ß\'.mp4')]
        self.assertEqual(shell_quote(args), u"""ffmpeg -i 'ñ€ß'"'"'.mp4'""")

    def test_str_to_int(self):
        self.assertEqual(str_to_int('123,456'), 123456)
        self.assertEqual(str_to_int('123.456'), 123456)

    def test_url_basename(self):
        self.assertEqual(url_basename(u'http://foo.de/'), u'')
        self.assertEqual(url_basename(u'http://foo.de/bar/baz'), u'baz')
        self.assertEqual(url_basename(u'http://foo.de/bar/baz?x=y'), u'baz')
        self.assertEqual(url_basename(u'http://foo.de/bar/baz#x=y'), u'baz')
        self.assertEqual(url_basename(u'http://foo.de/bar/baz/'), u'baz')
        self.assertEqual(
            url_basename(u'http://media.w3.org/2010/05/sintel/trailer.mp4'),
            u'trailer.mp4')

    def test_parse_duration(self):
        self.assertEqual(parse_duration(None), None)
        self.assertEqual(parse_duration('1'), 1)
        self.assertEqual(parse_duration('1337:12'), 80232)
        self.assertEqual(parse_duration('9:12:43'), 33163)
        self.assertEqual(parse_duration('12:00'), 720)
        self.assertEqual(parse_duration('00:01:01'), 61)
        self.assertEqual(parse_duration('x:y'), None)
        self.assertEqual(parse_duration('3h11m53s'), 11513)
        self.assertEqual(parse_duration('62m45s'), 3765)
        self.assertEqual(parse_duration('6m59s'), 419)
        self.assertEqual(parse_duration('49s'), 49)
        self.assertEqual(parse_duration('0h0m0s'), 0)
        self.assertEqual(parse_duration('0m0s'), 0)
        self.assertEqual(parse_duration('0s'), 0)

    def test_fix_xml_ampersands(self):
        self.assertEqual(
            fix_xml_ampersands('"&x=y&z=a'), '"&amp;x=y&amp;z=a')
        self.assertEqual(
            fix_xml_ampersands('"&amp;x=y&wrong;&z=a'),
            '"&amp;x=y&amp;wrong;&amp;z=a')
        self.assertEqual(
            fix_xml_ampersands('&amp;&apos;&gt;&lt;&quot;'),
            '&amp;&apos;&gt;&lt;&quot;')
        self.assertEqual(
            fix_xml_ampersands('&#1234;&#x1abC;'), '&#1234;&#x1abC;')
        self.assertEqual(fix_xml_ampersands('&#&#'), '&amp;#&amp;#')

    def test_paged_list(self):
        def testPL(size, pagesize, sliceargs, expected):
            def get_page(pagenum):
                firstid = pagenum * pagesize
                upto = min(size, pagenum * pagesize + pagesize)
                for i in range(firstid, upto):
                    yield i

            pl = PagedList(get_page, pagesize)
            got = pl.getslice(*sliceargs)
            self.assertEqual(got, expected)

        testPL(5, 2, (), [0, 1, 2, 3, 4])
        testPL(5, 2, (1,), [1, 2, 3, 4])
        testPL(5, 2, (2,), [2, 3, 4])
        testPL(5, 2, (4,), [4])
        testPL(5, 2, (0, 3), [0, 1, 2])
        testPL(5, 2, (1, 4), [1, 2, 3])
        testPL(5, 2, (2, 99), [2, 3, 4])
        testPL(5, 2, (20, 99), [])

    def test_struct_unpack(self):
        self.assertEqual(struct_unpack(u'!B', b'\x00'), (0,))

    def test_read_batch_urls(self):
        f = io.StringIO(u'''\xef\xbb\xbf foo
            bar\r
            baz
            # More after this line\r
            ; or after this
            bam''')
        self.assertEqual(read_batch_urls(f), [u'foo', u'bar', u'baz', u'bam'])

    def test_urlencode_postdata(self):
        data = urlencode_postdata({'username': 'foo@bar.com', 'password': '1234'})
        self.assertTrue(isinstance(data, bytes))

if __name__ == '__main__':
    unittest.main()
