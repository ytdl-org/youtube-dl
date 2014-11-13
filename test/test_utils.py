#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Various small unit tests
import io
import json
import xml.etree.ElementTree

from youtube_dl.utils import (
    clean_html,
    DateRange,
    encodeFilename,
    find_xpath_attr,
    fix_xml_ampersands,
    orderedSet,
    OnDemandPagedList,
    InAdvancePagedList,
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
    parse_iso8601,
    strip_jsonp,
    uppercase_escape,
    limit_length,
    escape_rfc3986,
    escape_url,
    js_to_json,
    get_filesystem_encoding,
    intlist_to_bytes,
)


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
        aumlaut = 'ä'
        self.assertEqual(sanitize_filename(aumlaut), aumlaut)
        tests = '\u043a\u0438\u0440\u0438\u043b\u043b\u0438\u0446\u0430'
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

        tests = 'a\xe4b\u4e2d\u56fd\u7684c'
        self.assertEqual(sanitize_filename(tests, restricted=True), 'a_b_c')
        self.assertTrue(sanitize_filename('\xf6', restricted=True) != '')  # No empty filename

        forbidden = '"\0\\/&!: \'\t\n()[]{}$;`^,#'
        for fc in forbidden:
            for fbc in forbidden:
                self.assertTrue(fbc not in sanitize_filename(fc, restricted=True))

        # Handle a common case more neatly
        self.assertEqual(sanitize_filename('\u5927\u58f0\u5e26 - Song', restricted=True), 'Song')
        self.assertEqual(sanitize_filename('\u603b\u7edf: Speech', restricted=True), 'Speech')
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
        self.assertEqual(unescapeHTML('%20;'), '%20;')
        self.assertEqual(
            unescapeHTML('&eacute;'), 'é')
        
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
        self.assertEqual(unified_strdate('28/01/2014 21:00:00 +0100'), '20140128')

    def test_find_xpath_attr(self):
        testxml = '''<root>
            <node/>
            <node x="a"/>
            <node x="a" y="c" />
            <node x="b" y="d" />
        </root>'''
        doc = xml.etree.ElementTree.fromstring(testxml)

        self.assertEqual(find_xpath_attr(doc, './/fourohfour', 'n', 'v'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', 'a'), doc[1])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y', 'c'), doc[2])

    def test_xpath_with_ns(self):
        testxml = '''<root xmlns:media="http://example.com/">
            <media:song>
                <media:author>The Author</media:author>
                <url>http://server.com/download.mp3</url>
            </media:song>
        </root>'''
        doc = xml.etree.ElementTree.fromstring(testxml)
        find = lambda p: doc.find(xpath_with_ns(p, {'media': 'http://example.com/'}))
        self.assertTrue(find('media:song') is not None)
        self.assertEqual(find('media:song/media:author').text, 'The Author')
        self.assertEqual(find('media:song/url').text, 'http://server.com/download.mp3')

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
        args = ['ffmpeg', '-i', encodeFilename('ñ€ß\'.mp4')]
        self.assertEqual(shell_quote(args), """ffmpeg -i 'ñ€ß'"'"'.mp4'""")

    def test_str_to_int(self):
        self.assertEqual(str_to_int('123,456'), 123456)
        self.assertEqual(str_to_int('123.456'), 123456)

    def test_url_basename(self):
        self.assertEqual(url_basename('http://foo.de/'), '')
        self.assertEqual(url_basename('http://foo.de/bar/baz'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz?x=y'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz#x=y'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz/'), 'baz')
        self.assertEqual(
            url_basename('http://media.w3.org/2010/05/sintel/trailer.mp4'),
            'trailer.mp4')

    def test_parse_duration(self):
        self.assertEqual(parse_duration(None), None)
        self.assertEqual(parse_duration('1'), 1)
        self.assertEqual(parse_duration('1337:12'), 80232)
        self.assertEqual(parse_duration('9:12:43'), 33163)
        self.assertEqual(parse_duration('12:00'), 720)
        self.assertEqual(parse_duration('00:01:01'), 61)
        self.assertEqual(parse_duration('x:y'), None)
        self.assertEqual(parse_duration('3h11m53s'), 11513)
        self.assertEqual(parse_duration('3h 11m 53s'), 11513)
        self.assertEqual(parse_duration('3 hours 11 minutes 53 seconds'), 11513)
        self.assertEqual(parse_duration('3 hours 11 mins 53 secs'), 11513)
        self.assertEqual(parse_duration('62m45s'), 3765)
        self.assertEqual(parse_duration('6m59s'), 419)
        self.assertEqual(parse_duration('49s'), 49)
        self.assertEqual(parse_duration('0h0m0s'), 0)
        self.assertEqual(parse_duration('0m0s'), 0)
        self.assertEqual(parse_duration('0s'), 0)
        self.assertEqual(parse_duration('01:02:03.05'), 3723.05)

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

            pl = OnDemandPagedList(get_page, pagesize)
            got = pl.getslice(*sliceargs)
            self.assertEqual(got, expected)

            iapl = InAdvancePagedList(get_page, size // pagesize + 1, pagesize)
            got = iapl.getslice(*sliceargs)
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
        self.assertEqual(struct_unpack('!B', b'\x00'), (0,))

    def test_read_batch_urls(self):
        f = io.StringIO('''\xef\xbb\xbf foo
            bar\r
            baz
            # More after this line\r
            ; or after this
            bam''')
        self.assertEqual(read_batch_urls(f), ['foo', 'bar', 'baz', 'bam'])

    def test_urlencode_postdata(self):
        data = urlencode_postdata({'username': 'foo@bar.com', 'password': '1234'})
        self.assertTrue(isinstance(data, bytes))

    def test_parse_iso8601(self):
        self.assertEqual(parse_iso8601('2014-03-23T23:04:26+0100'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26+0000'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26Z'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26.1234Z'), 1395612266)

    def test_strip_jsonp(self):
        stripped = strip_jsonp('cb ([ {"id":"532cb",\n\n\n"x":\n3}\n]\n);')
        d = json.loads(stripped)
        self.assertEqual(d, [{"id": "532cb", "x": 3}])

        stripped = strip_jsonp('parseMetadata({"STATUS":"OK"})\n\n\n//epc')
        d = json.loads(stripped)
        self.assertEqual(d, {'STATUS': 'OK'})

    def test_uppercase_escape(self):
        self.assertEqual(uppercase_escape('aä'), 'aä')
        self.assertEqual(uppercase_escape('\\U0001d550'), '𝕐')

    def test_limit_length(self):
        self.assertEqual(limit_length(None, 12), None)
        self.assertEqual(limit_length('foo', 12), 'foo')
        self.assertTrue(
            limit_length('foo bar baz asd', 12).startswith('foo bar'))
        self.assertTrue('...' in limit_length('foo bar baz asd', 12))

    def test_escape_rfc3986(self):
        reserved = "!*'();:@&=+$,/?#[]"
        unreserved = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~'
        self.assertEqual(escape_rfc3986(reserved), reserved)
        self.assertEqual(escape_rfc3986(unreserved), unreserved)
        self.assertEqual(escape_rfc3986('тест'), '%D1%82%D0%B5%D1%81%D1%82')
        self.assertEqual(escape_rfc3986('%D1%82%D0%B5%D1%81%D1%82'), '%D1%82%D0%B5%D1%81%D1%82')
        self.assertEqual(escape_rfc3986('foo bar'), 'foo%20bar')
        self.assertEqual(escape_rfc3986('foo%20bar'), 'foo%20bar')

    def test_escape_url(self):
        self.assertEqual(
            escape_url('http://wowza.imust.org/srv/vod/telemb/new/UPLOAD/UPLOAD/20224_IncendieHavré_FD.mp4'),
            'http://wowza.imust.org/srv/vod/telemb/new/UPLOAD/UPLOAD/20224_IncendieHavre%CC%81_FD.mp4'
        )
        self.assertEqual(
            escape_url('http://www.ardmediathek.de/tv/Sturm-der-Liebe/Folge-2036-Zu-Mann-und-Frau-erklärt/Das-Erste/Video?documentId=22673108&bcastId=5290'),
            'http://www.ardmediathek.de/tv/Sturm-der-Liebe/Folge-2036-Zu-Mann-und-Frau-erkl%C3%A4rt/Das-Erste/Video?documentId=22673108&bcastId=5290'
        )
        self.assertEqual(
            escape_url('http://тест.рф/фрагмент'),
            'http://тест.рф/%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82'
        )
        self.assertEqual(
            escape_url('http://тест.рф/абв?абв=абв#абв'),
            'http://тест.рф/%D0%B0%D0%B1%D0%B2?%D0%B0%D0%B1%D0%B2=%D0%B0%D0%B1%D0%B2#%D0%B0%D0%B1%D0%B2'
        )
        self.assertEqual(escape_url('http://vimeo.com/56015672#at=0'), 'http://vimeo.com/56015672#at=0')

    def test_js_to_json_realworld(self):
        inp = '''{
            'clip':{'provider':'pseudo'}
        }'''
        self.assertEqual(js_to_json(inp), '''{
            "clip":{"provider":"pseudo"}
        }''')
        json.loads(js_to_json(inp))

        inp = '''{
            'playlist':[{'controls':{'all':null}}]
        }'''
        self.assertEqual(js_to_json(inp), '''{
            "playlist":[{"controls":{"all":null}}]
        }''')

    def test_js_to_json_edgecases(self):
        on = js_to_json("{abc_def:'1\\'\\\\2\\\\\\'3\"4'}")
        self.assertEqual(json.loads(on), {"abc_def": "1'\\2\\'3\"4"})

        on = js_to_json('{"abc": true}')
        self.assertEqual(json.loads(on), {'abc': True})

    def test_clean_html(self):
        self.assertEqual(clean_html('a:\nb'), 'a: b')
        self.assertEqual(clean_html('a:\n   "b"'), 'a:    "b"')

    def test_intlist_to_bytes(self):
        self.assertEqual(
            intlist_to_bytes([0, 1, 127, 128, 255]),
            b'\x00\x01\x7f\x80\xff')

if __name__ == '__main__':
    unittest.main()
