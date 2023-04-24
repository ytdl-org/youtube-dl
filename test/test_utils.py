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
import itertools
import json
import re
import xml.etree.ElementTree

from youtube_dl.utils import (
    age_restricted,
    args_to_str,
    encode_base_n,
    caesar,
    clean_html,
    clean_podcast_url,
    date_from_str,
    DateRange,
    detect_exe_version,
    determine_ext,
    dict_get,
    encode_compat_str,
    encodeFilename,
    escape_rfc3986,
    escape_url,
    extract_attributes,
    ExtractorError,
    find_xpath_attr,
    fix_xml_ampersands,
    float_or_none,
    get_element_by_class,
    get_element_by_attribute,
    get_elements_by_class,
    get_elements_by_attribute,
    get_first,
    InAdvancePagedList,
    int_or_none,
    intlist_to_bytes,
    is_html,
    join_nonempty,
    js_to_json,
    LazyList,
    limit_length,
    merge_dicts,
    mimetype2ext,
    month_by_name,
    multipart_encode,
    ohdave_rsa_encrypt,
    OnDemandPagedList,
    orderedSet,
    parse_age_limit,
    parse_duration,
    parse_filesize,
    parse_count,
    parse_iso8601,
    parse_resolution,
    parse_bitrate,
    pkcs1pad,
    read_batch_urls,
    sanitize_filename,
    sanitize_path,
    sanitize_url,
    expand_path,
    prepend_extension,
    replace_extension,
    remove_start,
    remove_end,
    remove_quotes,
    rot47,
    shell_quote,
    smuggle_url,
    str_to_int,
    strip_jsonp,
    strip_or_none,
    subtitles_filename,
    timeconvert,
    traverse_obj,
    try_call,
    unescapeHTML,
    unified_strdate,
    unified_timestamp,
    unsmuggle_url,
    uppercase_escape,
    lowercase_escape,
    url_basename,
    url_or_none,
    base_url,
    urljoin,
    urlencode_postdata,
    urshift,
    update_url_query,
    variadic,
    version_tuple,
    xpath_with_ns,
    xpath_element,
    xpath_text,
    xpath_attr,
    render_table,
    match_str,
    parse_dfxp_time_expr,
    dfxp2srt,
    cli_option,
    cli_valueless_option,
    cli_bool_option,
    parse_codecs,
)
from youtube_dl.compat import (
    compat_chr,
    compat_etree_fromstring,
    compat_getenv,
    compat_os_name,
    compat_setenv,
    compat_str,
    compat_urlparse,
    compat_parse_qs,
)


class TestUtil(unittest.TestCase):

    # yt-dlp shim
    def assertCountEqual(self, expected, got, msg='count should be the same'):
        return self.assertEqual(len(tuple(expected)), len(tuple(got)), msg=msg)

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

        self.assertEqual(
            sanitize_filename('New World record at 0:12:34'),
            'New World record at 0_12_34')

        self.assertEqual(sanitize_filename('--gasdgf'), '_-gasdgf')
        self.assertEqual(sanitize_filename('--gasdgf', is_id=True), '--gasdgf')
        self.assertEqual(sanitize_filename('.gasdgf'), 'gasdgf')
        self.assertEqual(sanitize_filename('.gasdgf', is_id=True), '.gasdgf')

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

        tests = 'aäb\u4e2d\u56fd\u7684c'
        self.assertEqual(sanitize_filename(tests, restricted=True), 'aab_c')
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

        self.assertEqual(sanitize_filename(
            'ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ', restricted=True),
            'AAAAAAAECEEEEIIIIDNOOOOOOOOEUUUUUYTHssaaaaaaaeceeeeiiiionooooooooeuuuuuythy')

    def test_sanitize_ids(self):
        self.assertEqual(sanitize_filename('_n_cd26wFpw', is_id=True), '_n_cd26wFpw')
        self.assertEqual(sanitize_filename('_BD_eEpuzXw', is_id=True), '_BD_eEpuzXw')
        self.assertEqual(sanitize_filename('N0Y__7-UOdI', is_id=True), 'N0Y__7-UOdI')

    def test_sanitize_path(self):
        if sys.platform != 'win32':
            return

        self.assertEqual(sanitize_path('abc'), 'abc')
        self.assertEqual(sanitize_path('abc/def'), 'abc\\def')
        self.assertEqual(sanitize_path('abc\\def'), 'abc\\def')
        self.assertEqual(sanitize_path('abc|def'), 'abc#def')
        self.assertEqual(sanitize_path('<>:"|?*'), '#######')
        self.assertEqual(sanitize_path('C:/abc/def'), 'C:\\abc\\def')
        self.assertEqual(sanitize_path('C?:/abc/def'), 'C##\\abc\\def')

        self.assertEqual(sanitize_path('\\\\?\\UNC\\ComputerName\\abc'), '\\\\?\\UNC\\ComputerName\\abc')
        self.assertEqual(sanitize_path('\\\\?\\UNC/ComputerName/abc'), '\\\\?\\UNC\\ComputerName\\abc')

        self.assertEqual(sanitize_path('\\\\?\\C:\\abc'), '\\\\?\\C:\\abc')
        self.assertEqual(sanitize_path('\\\\?\\C:/abc'), '\\\\?\\C:\\abc')
        self.assertEqual(sanitize_path('\\\\?\\C:\\ab?c\\de:f'), '\\\\?\\C:\\ab#c\\de#f')
        self.assertEqual(sanitize_path('\\\\?\\C:\\abc'), '\\\\?\\C:\\abc')

        self.assertEqual(
            sanitize_path('youtube/%(uploader)s/%(autonumber)s-%(title)s-%(upload_date)s.%(ext)s'),
            'youtube\\%(uploader)s\\%(autonumber)s-%(title)s-%(upload_date)s.%(ext)s')

        self.assertEqual(
            sanitize_path('youtube/TheWreckingYard ./00001-Not bad, Especially for Free! (1987 Yamaha 700)-20141116.mp4.part'),
            'youtube\\TheWreckingYard #\\00001-Not bad, Especially for Free! (1987 Yamaha 700)-20141116.mp4.part')
        self.assertEqual(sanitize_path('abc/def...'), 'abc\\def..#')
        self.assertEqual(sanitize_path('abc.../def'), 'abc..#\\def')
        self.assertEqual(sanitize_path('abc.../def...'), 'abc..#\\def..#')

        self.assertEqual(sanitize_path('../abc'), '..\\abc')
        self.assertEqual(sanitize_path('../../abc'), '..\\..\\abc')
        self.assertEqual(sanitize_path('./abc'), 'abc')
        self.assertEqual(sanitize_path('./../abc'), '..\\abc')

    def test_sanitize_url(self):
        self.assertEqual(sanitize_url('//foo.bar'), 'http://foo.bar')
        self.assertEqual(sanitize_url('httpss://foo.bar'), 'https://foo.bar')
        self.assertEqual(sanitize_url('rmtps://foo.bar'), 'rtmps://foo.bar')
        self.assertEqual(sanitize_url('https://foo.bar'), 'https://foo.bar')
        self.assertEqual(sanitize_url('foo bar'), 'foo bar')

    def test_expand_path(self):
        def env(var):
            return '%{0}%'.format(var) if sys.platform == 'win32' else '${0}'.format(var)

        compat_setenv('YOUTUBE_DL_EXPATH_PATH', 'expanded')
        self.assertEqual(expand_path(env('YOUTUBE_DL_EXPATH_PATH')), 'expanded')
        self.assertEqual(expand_path(env('HOME')), compat_getenv('HOME'))
        self.assertEqual(expand_path('~'), compat_getenv('HOME'))
        self.assertEqual(
            expand_path('~/%s' % env('YOUTUBE_DL_EXPATH_PATH')),
            '%s/expanded' % compat_getenv('HOME'))

    def test_prepend_extension(self):
        self.assertEqual(prepend_extension('abc.ext', 'temp'), 'abc.temp.ext')
        self.assertEqual(prepend_extension('abc.ext', 'temp', 'ext'), 'abc.temp.ext')
        self.assertEqual(prepend_extension('abc.unexpected_ext', 'temp', 'ext'), 'abc.unexpected_ext.temp')
        self.assertEqual(prepend_extension('abc', 'temp'), 'abc.temp')
        self.assertEqual(prepend_extension('.abc', 'temp'), '.abc.temp')
        self.assertEqual(prepend_extension('.abc.ext', 'temp'), '.abc.temp.ext')

    def test_replace_extension(self):
        self.assertEqual(replace_extension('abc.ext', 'temp'), 'abc.temp')
        self.assertEqual(replace_extension('abc.ext', 'temp', 'ext'), 'abc.temp')
        self.assertEqual(replace_extension('abc.unexpected_ext', 'temp', 'ext'), 'abc.unexpected_ext.temp')
        self.assertEqual(replace_extension('abc', 'temp'), 'abc.temp')
        self.assertEqual(replace_extension('.abc', 'temp'), '.abc.temp')
        self.assertEqual(replace_extension('.abc.ext', 'temp'), '.abc.temp')

    def test_subtitles_filename(self):
        self.assertEqual(subtitles_filename('abc.ext', 'en', 'vtt'), 'abc.en.vtt')
        self.assertEqual(subtitles_filename('abc.ext', 'en', 'vtt', 'ext'), 'abc.en.vtt')
        self.assertEqual(subtitles_filename('abc.unexpected_ext', 'en', 'vtt', 'ext'), 'abc.unexpected_ext.en.vtt')

    def test_remove_start(self):
        self.assertEqual(remove_start(None, 'A - '), None)
        self.assertEqual(remove_start('A - B', 'A - '), 'B')
        self.assertEqual(remove_start('B - A', 'A - '), 'B - A')

    def test_remove_end(self):
        self.assertEqual(remove_end(None, ' - B'), None)
        self.assertEqual(remove_end('A - B', ' - B'), 'A')
        self.assertEqual(remove_end('B - A', ' - B'), 'B - A')

    def test_remove_quotes(self):
        self.assertEqual(remove_quotes(None), None)
        self.assertEqual(remove_quotes('"'), '"')
        self.assertEqual(remove_quotes("'"), "'")
        self.assertEqual(remove_quotes(';'), ';')
        self.assertEqual(remove_quotes('";'), '";')
        self.assertEqual(remove_quotes('""'), '')
        self.assertEqual(remove_quotes('";"'), ';')

    def test_ordered_set(self):
        self.assertEqual(orderedSet([1, 1, 2, 3, 4, 4, 5, 6, 7, 3, 5]), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(orderedSet([]), [])
        self.assertEqual(orderedSet([1]), [1])
        # keep the list ordered
        self.assertEqual(orderedSet([135, 1, 1, 1]), [135, 1])

    def test_unescape_html(self):
        self.assertEqual(unescapeHTML('%20;'), '%20;')
        self.assertEqual(unescapeHTML('&#x2F;'), '/')
        self.assertEqual(unescapeHTML('&#47;'), '/')
        self.assertEqual(unescapeHTML('&eacute;'), 'é')
        self.assertEqual(unescapeHTML('&#2013266066;'), '&#2013266066;')
        self.assertEqual(unescapeHTML('&a&quot;'), '&a"')
        # HTML5 entities
        self.assertEqual(unescapeHTML('&period;&apos;'), '.\'')

    def test_date_from_str(self):
        self.assertEqual(date_from_str('yesterday'), date_from_str('now-1day'))
        self.assertEqual(date_from_str('now+7day'), date_from_str('now+1week'))
        self.assertEqual(date_from_str('now+14day'), date_from_str('now+2week'))
        self.assertEqual(date_from_str('now+365day'), date_from_str('now+1year'))
        self.assertEqual(date_from_str('now+30day'), date_from_str('now+1month'))

    def test_daterange(self):
        _20century = DateRange("19000101", "20000101")
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
        self.assertEqual(unified_strdate('1968 12 10'), '19681210')
        self.assertEqual(unified_strdate('1968-12-10'), '19681210')
        self.assertEqual(unified_strdate('28/01/2014 21:00:00 +0100'), '20140128')
        self.assertEqual(
            unified_strdate('11/26/2014 11:30:00 AM PST', day_first=False),
            '20141126')
        self.assertEqual(
            unified_strdate('2/2/2015 6:47:40 PM', day_first=False),
            '20150202')
        self.assertEqual(unified_strdate('Feb 14th 2016 5:45PM'), '20160214')
        self.assertEqual(unified_strdate('25-09-2014'), '20140925')
        self.assertEqual(unified_strdate('27.02.2016 17:30'), '20160227')
        self.assertEqual(unified_strdate('UNKNOWN DATE FORMAT'), None)
        self.assertEqual(unified_strdate('Feb 7, 2016 at 6:35 pm'), '20160207')
        self.assertEqual(unified_strdate('July 15th, 2013'), '20130715')
        self.assertEqual(unified_strdate('September 1st, 2013'), '20130901')
        self.assertEqual(unified_strdate('Sep 2nd, 2013'), '20130902')
        self.assertEqual(unified_strdate('November 3rd, 2019'), '20191103')
        self.assertEqual(unified_strdate('October 23rd, 2005'), '20051023')

    def test_unified_timestamps(self):
        self.assertEqual(unified_timestamp('December 21, 2010'), 1292889600)
        self.assertEqual(unified_timestamp('8/7/2009'), 1247011200)
        self.assertEqual(unified_timestamp('Dec 14, 2012'), 1355443200)
        self.assertEqual(unified_timestamp('2012/10/11 01:56:38 +0000'), 1349920598)
        self.assertEqual(unified_timestamp('1968 12 10'), -33436800)
        self.assertEqual(unified_timestamp('1968-12-10'), -33436800)
        self.assertEqual(unified_timestamp('28/01/2014 21:00:00 +0100'), 1390939200)
        self.assertEqual(
            unified_timestamp('11/26/2014 11:30:00 AM PST', day_first=False),
            1417001400)
        self.assertEqual(
            unified_timestamp('2/2/2015 6:47:40 PM', day_first=False),
            1422902860)
        self.assertEqual(unified_timestamp('Feb 14th 2016 5:45PM'), 1455471900)
        self.assertEqual(unified_timestamp('25-09-2014'), 1411603200)
        self.assertEqual(unified_timestamp('27.02.2016 17:30'), 1456594200)
        self.assertEqual(unified_timestamp('UNKNOWN DATE FORMAT'), None)
        self.assertEqual(unified_timestamp('May 16, 2016 11:15 PM'), 1463440500)
        self.assertEqual(unified_timestamp('Feb 7, 2016 at 6:35 pm'), 1454870100)
        self.assertEqual(unified_timestamp('2017-03-30T17:52:41Q'), 1490896361)
        self.assertEqual(unified_timestamp('Sep 11, 2013 | 5:49 AM'), 1378878540)
        self.assertEqual(unified_timestamp('December 15, 2017 at 7:49 am'), 1513324140)
        self.assertEqual(unified_timestamp('2018-03-14T08:32:43.1493874+00:00'), 1521016363)
        self.assertEqual(unified_timestamp('December 31 1969 20:00:01 EDT'), 1)
        self.assertEqual(unified_timestamp('Wednesday 31 December 1969 18:01:26 MDT'), 86)
        self.assertEqual(unified_timestamp('12/31/1969 20:01:18 EDT', False), 78)

    def test_determine_ext(self):
        self.assertEqual(determine_ext('http://example.com/foo/bar.mp4/?download'), 'mp4')
        self.assertEqual(determine_ext('http://example.com/foo/bar/?download', None), None)
        self.assertEqual(determine_ext('http://example.com/foo/bar.nonext/?download', None), None)
        self.assertEqual(determine_ext('http://example.com/foo/bar/mp4?download', None), None)
        self.assertEqual(determine_ext('http://example.com/foo/bar.m3u8//?download'), 'm3u8')
        self.assertEqual(determine_ext('foobar', None), None)

    def test_find_xpath_attr(self):
        testxml = '''<root>
            <node/>
            <node x="a"/>
            <node x="a" y="c" />
            <node x="b" y="d" />
            <node x="" />
        </root>'''
        doc = compat_etree_fromstring(testxml)

        self.assertEqual(find_xpath_attr(doc, './/fourohfour', 'n'), None)
        self.assertEqual(find_xpath_attr(doc, './/fourohfour', 'n', 'v'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'n'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'n', 'v'), None)
        self.assertEqual(find_xpath_attr(doc, './/node', 'x'), doc[1])
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', 'a'), doc[1])
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', 'b'), doc[3])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y'), doc[2])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y', 'c'), doc[2])
        self.assertEqual(find_xpath_attr(doc, './/node', 'y', 'd'), doc[3])
        self.assertEqual(find_xpath_attr(doc, './/node', 'x', ''), doc[4])

    def test_xpath_with_ns(self):
        testxml = '''<root xmlns:media="http://example.com/">
            <media:song>
                <media:author>The Author</media:author>
                <url>http://server.com/download.mp3</url>
            </media:song>
        </root>'''
        doc = compat_etree_fromstring(testxml)
        find = lambda p: doc.find(xpath_with_ns(p, {'media': 'http://example.com/'}))
        self.assertTrue(find('media:song') is not None)
        self.assertEqual(find('media:song/media:author').text, 'The Author')
        self.assertEqual(find('media:song/url').text, 'http://server.com/download.mp3')

    def test_xpath_element(self):
        doc = xml.etree.ElementTree.Element('root')
        div = xml.etree.ElementTree.SubElement(doc, 'div')
        p = xml.etree.ElementTree.SubElement(div, 'p')
        p.text = 'Foo'
        self.assertEqual(xpath_element(doc, 'div/p'), p)
        self.assertEqual(xpath_element(doc, ['div/p']), p)
        self.assertEqual(xpath_element(doc, ['div/bar', 'div/p']), p)
        self.assertEqual(xpath_element(doc, 'div/bar', default='default'), 'default')
        self.assertEqual(xpath_element(doc, ['div/bar'], default='default'), 'default')
        self.assertTrue(xpath_element(doc, 'div/bar') is None)
        self.assertTrue(xpath_element(doc, ['div/bar']) is None)
        self.assertTrue(xpath_element(doc, ['div/bar'], 'div/baz') is None)
        self.assertRaises(ExtractorError, xpath_element, doc, 'div/bar', fatal=True)
        self.assertRaises(ExtractorError, xpath_element, doc, ['div/bar'], fatal=True)
        self.assertRaises(ExtractorError, xpath_element, doc, ['div/bar', 'div/baz'], fatal=True)

    def test_xpath_text(self):
        testxml = '''<root>
            <div>
                <p>Foo</p>
            </div>
        </root>'''
        doc = compat_etree_fromstring(testxml)
        self.assertEqual(xpath_text(doc, 'div/p'), 'Foo')
        self.assertEqual(xpath_text(doc, 'div/bar', default='default'), 'default')
        self.assertTrue(xpath_text(doc, 'div/bar') is None)
        self.assertRaises(ExtractorError, xpath_text, doc, 'div/bar', fatal=True)

    def test_xpath_attr(self):
        testxml = '''<root>
            <div>
                <p x="a">Foo</p>
            </div>
        </root>'''
        doc = compat_etree_fromstring(testxml)
        self.assertEqual(xpath_attr(doc, 'div/p', 'x'), 'a')
        self.assertEqual(xpath_attr(doc, 'div/bar', 'x'), None)
        self.assertEqual(xpath_attr(doc, 'div/p', 'y'), None)
        self.assertEqual(xpath_attr(doc, 'div/bar', 'x', default='default'), 'default')
        self.assertEqual(xpath_attr(doc, 'div/p', 'y', default='default'), 'default')
        self.assertRaises(ExtractorError, xpath_attr, doc, 'div/bar', 'x', fatal=True)
        self.assertRaises(ExtractorError, xpath_attr, doc, 'div/p', 'y', fatal=True)

    def test_smuggle_url(self):
        data = {"ö": "ö", "abc": [3]}
        url = 'https://foo.bar/baz?x=y#a'
        smug_url = smuggle_url(url, data)
        unsmug_url, unsmug_data = unsmuggle_url(smug_url)
        self.assertEqual(url, unsmug_url)
        self.assertEqual(data, unsmug_data)

        res_url, res_data = unsmuggle_url(url)
        self.assertEqual(res_url, url)
        self.assertEqual(res_data, None)

        smug_url = smuggle_url(url, {'a': 'b'})
        smug_smug_url = smuggle_url(smug_url, {'c': 'd'})
        res_url, res_data = unsmuggle_url(smug_smug_url)
        self.assertEqual(res_url, url)
        self.assertEqual(res_data, {'a': 'b', 'c': 'd'})

    def test_shell_quote(self):
        args = ['ffmpeg', '-i', encodeFilename('ñ€ß\'.mp4')]
        self.assertEqual(
            shell_quote(args),
            """ffmpeg -i 'ñ€ß'"'"'.mp4'""" if compat_os_name != 'nt' else '''ffmpeg -i "ñ€ß'.mp4"''')

    def test_float_or_none(self):
        self.assertEqual(float_or_none('42.42'), 42.42)
        self.assertEqual(float_or_none('42'), 42.0)
        self.assertEqual(float_or_none(''), None)
        self.assertEqual(float_or_none(None), None)
        self.assertEqual(float_or_none([]), None)
        self.assertEqual(float_or_none(set()), None)

    def test_int_or_none(self):
        self.assertEqual(int_or_none('42'), 42)
        self.assertEqual(int_or_none(''), None)
        self.assertEqual(int_or_none(None), None)
        self.assertEqual(int_or_none([]), None)
        self.assertEqual(int_or_none(set()), None)

    def test_str_to_int(self):
        self.assertEqual(str_to_int('123,456'), 123456)
        self.assertEqual(str_to_int('123.456'), 123456)
        self.assertEqual(str_to_int(523), 523)
        # Python 3 has no long
        if sys.version_info < (3, 0):
            eval('self.assertEqual(str_to_int(123456L), 123456)')
        self.assertEqual(str_to_int('noninteger'), None)
        self.assertEqual(str_to_int([]), None)

    def test_url_basename(self):
        self.assertEqual(url_basename('http://foo.de/'), '')
        self.assertEqual(url_basename('http://foo.de/bar/baz'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz?x=y'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz#x=y'), 'baz')
        self.assertEqual(url_basename('http://foo.de/bar/baz/'), 'baz')
        self.assertEqual(
            url_basename('http://media.w3.org/2010/05/sintel/trailer.mp4'),
            'trailer.mp4')

    def test_base_url(self):
        self.assertEqual(base_url('http://foo.de/'), 'http://foo.de/')
        self.assertEqual(base_url('http://foo.de/bar'), 'http://foo.de/')
        self.assertEqual(base_url('http://foo.de/bar/'), 'http://foo.de/bar/')
        self.assertEqual(base_url('http://foo.de/bar/baz'), 'http://foo.de/bar/')
        self.assertEqual(base_url('http://foo.de/bar/baz?x=z/x/c'), 'http://foo.de/bar/')

    def test_urljoin(self):
        self.assertEqual(urljoin('http://foo.de/', '/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin(b'http://foo.de/', '/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de/', b'/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin(b'http://foo.de/', b'/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('//foo.de/', '/a/b/c.txt'), '//foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de/', 'a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de', '/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de', 'a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de/', 'http://foo.de/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de/', '//foo.de/a/b/c.txt'), '//foo.de/a/b/c.txt')
        self.assertEqual(urljoin(None, 'http://foo.de/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin(None, '//foo.de/a/b/c.txt'), '//foo.de/a/b/c.txt')
        self.assertEqual(urljoin('', 'http://foo.de/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin(['foobar'], 'http://foo.de/a/b/c.txt'), 'http://foo.de/a/b/c.txt')
        self.assertEqual(urljoin('http://foo.de/', None), None)
        self.assertEqual(urljoin('http://foo.de/', ''), None)
        self.assertEqual(urljoin('http://foo.de/', ['foobar']), None)
        self.assertEqual(urljoin('http://foo.de/a/b/c.txt', '.././../d.txt'), 'http://foo.de/d.txt')
        self.assertEqual(urljoin('http://foo.de/a/b/c.txt', 'rtmp://foo.de'), 'rtmp://foo.de')
        self.assertEqual(urljoin(None, 'rtmp://foo.de'), 'rtmp://foo.de')

    def test_url_or_none(self):
        self.assertEqual(url_or_none(None), None)
        self.assertEqual(url_or_none(''), None)
        self.assertEqual(url_or_none('foo'), None)
        self.assertEqual(url_or_none('http://foo.de'), 'http://foo.de')
        self.assertEqual(url_or_none('https://foo.de'), 'https://foo.de')
        self.assertEqual(url_or_none('http$://foo.de'), None)
        self.assertEqual(url_or_none('http://foo.de'), 'http://foo.de')
        self.assertEqual(url_or_none('//foo.de'), '//foo.de')
        self.assertEqual(url_or_none('s3://foo.de'), None)
        self.assertEqual(url_or_none('rtmpte://foo.de'), 'rtmpte://foo.de')
        self.assertEqual(url_or_none('mms://foo.de'), 'mms://foo.de')
        self.assertEqual(url_or_none('rtspu://foo.de'), 'rtspu://foo.de')
        self.assertEqual(url_or_none('ftps://foo.de'), 'ftps://foo.de')

    def test_parse_age_limit(self):
        self.assertEqual(parse_age_limit(None), None)
        self.assertEqual(parse_age_limit(False), None)
        self.assertEqual(parse_age_limit('invalid'), None)
        self.assertEqual(parse_age_limit(0), 0)
        self.assertEqual(parse_age_limit(18), 18)
        self.assertEqual(parse_age_limit(21), 21)
        self.assertEqual(parse_age_limit(22), None)
        self.assertEqual(parse_age_limit('18'), 18)
        self.assertEqual(parse_age_limit('18+'), 18)
        self.assertEqual(parse_age_limit('PG-13'), 13)
        self.assertEqual(parse_age_limit('TV-14'), 14)
        self.assertEqual(parse_age_limit('TV-MA'), 17)
        self.assertEqual(parse_age_limit('TV14'), 14)
        self.assertEqual(parse_age_limit('TV_G'), 0)

    def test_parse_duration(self):
        self.assertEqual(parse_duration(None), None)
        self.assertEqual(parse_duration(False), None)
        self.assertEqual(parse_duration('invalid'), None)
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
        self.assertEqual(parse_duration('T30M38S'), 1838)
        self.assertEqual(parse_duration('5 s'), 5)
        self.assertEqual(parse_duration('3 min'), 180)
        self.assertEqual(parse_duration('2.5 hours'), 9000)
        self.assertEqual(parse_duration('02:03:04'), 7384)
        self.assertEqual(parse_duration('01:02:03:04'), 93784)
        self.assertEqual(parse_duration('1 hour 3 minutes'), 3780)
        self.assertEqual(parse_duration('87 Min.'), 5220)
        self.assertEqual(parse_duration('PT1H0.040S'), 3600.04)
        self.assertEqual(parse_duration('PT00H03M30SZ'), 210)
        self.assertEqual(parse_duration('P0Y0M0DT0H4M20.880S'), 260.88)

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

    def test_update_url_query(self):
        def query_dict(url):
            return compat_parse_qs(compat_urlparse.urlparse(url).query)
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'quality': ['HD'], 'format': ['mp4']})),
            query_dict('http://example.com/path?quality=HD&format=mp4'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'system': ['LINUX', 'WINDOWS']})),
            query_dict('http://example.com/path?system=LINUX&system=WINDOWS'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'fields': 'id,formats,subtitles'})),
            query_dict('http://example.com/path?fields=id,formats,subtitles'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'fields': ('id,formats,subtitles', 'thumbnails')})),
            query_dict('http://example.com/path?fields=id,formats,subtitles&fields=thumbnails'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path?manifest=f4m', {'manifest': []})),
            query_dict('http://example.com/path'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path?system=LINUX&system=WINDOWS', {'system': 'LINUX'})),
            query_dict('http://example.com/path?system=LINUX'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'fields': b'id,formats,subtitles'})),
            query_dict('http://example.com/path?fields=id,formats,subtitles'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'width': 1080, 'height': 720})),
            query_dict('http://example.com/path?width=1080&height=720'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'bitrate': 5020.43})),
            query_dict('http://example.com/path?bitrate=5020.43'))
        self.assertEqual(query_dict(update_url_query(
            'http://example.com/path', {'test': '第二行тест'})),
            query_dict('http://example.com/path?test=%E7%AC%AC%E4%BA%8C%E8%A1%8C%D1%82%D0%B5%D1%81%D1%82'))

    def test_multipart_encode(self):
        self.assertEqual(
            multipart_encode({b'field': b'value'}, boundary='AAAAAA')[0],
            b'--AAAAAA\r\nContent-Disposition: form-data; name="field"\r\n\r\nvalue\r\n--AAAAAA--\r\n')
        self.assertEqual(
            multipart_encode({'欄位'.encode('utf-8'): '值'.encode('utf-8')}, boundary='AAAAAA')[0],
            b'--AAAAAA\r\nContent-Disposition: form-data; name="\xe6\xac\x84\xe4\xbd\x8d"\r\n\r\n\xe5\x80\xbc\r\n--AAAAAA--\r\n')
        self.assertRaises(
            ValueError, multipart_encode, {b'field': b'value'}, boundary='value')

    def test_dict_get(self):
        FALSE_VALUES = {
            'none': None,
            'false': False,
            'zero': 0,
            'empty_string': '',
            'empty_list': [],
        }
        d = FALSE_VALUES.copy()
        d['a'] = 42
        self.assertEqual(dict_get(d, 'a'), 42)
        self.assertEqual(dict_get(d, 'b'), None)
        self.assertEqual(dict_get(d, 'b', 42), 42)
        self.assertEqual(dict_get(d, ('a', )), 42)
        self.assertEqual(dict_get(d, ('b', 'a', )), 42)
        self.assertEqual(dict_get(d, ('b', 'c', 'a', 'd', )), 42)
        self.assertEqual(dict_get(d, ('b', 'c', )), None)
        self.assertEqual(dict_get(d, ('b', 'c', ), 42), 42)
        for key, false_value in FALSE_VALUES.items():
            self.assertEqual(dict_get(d, ('b', 'c', key, )), None)
            self.assertEqual(dict_get(d, ('b', 'c', key, ), skip_false_values=False), false_value)

    def test_merge_dicts(self):
        self.assertEqual(merge_dicts({'a': 1}, {'b': 2}), {'a': 1, 'b': 2})
        self.assertEqual(merge_dicts({'a': 1}, {'a': 2}), {'a': 1})
        self.assertEqual(merge_dicts({'a': 1}, {'a': None}), {'a': 1})
        self.assertEqual(merge_dicts({'a': 1}, {'a': ''}), {'a': 1})
        self.assertEqual(merge_dicts({'a': 1}, {}), {'a': 1})
        self.assertEqual(merge_dicts({'a': None}, {'a': 1}), {'a': 1})
        self.assertEqual(merge_dicts({'a': ''}, {'a': 1}), {'a': ''})
        self.assertEqual(merge_dicts({'a': ''}, {'a': 'abc'}), {'a': 'abc'})
        self.assertEqual(merge_dicts({'a': None}, {'a': ''}, {'a': 'abc'}), {'a': 'abc'})

    def test_encode_compat_str(self):
        self.assertEqual(encode_compat_str(b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82', 'utf-8'), 'тест')
        self.assertEqual(encode_compat_str('тест', 'utf-8'), 'тест')

    def test_parse_iso8601(self):
        self.assertEqual(parse_iso8601('2014-03-23T23:04:26+0100'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26+0000'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26Z'), 1395612266)
        self.assertEqual(parse_iso8601('2014-03-23T22:04:26.1234Z'), 1395612266)
        self.assertEqual(parse_iso8601('2015-09-29T08:27:31.727'), 1443515251)
        self.assertEqual(parse_iso8601('2015-09-29T08-27-31.727'), None)

    def test_strip_jsonp(self):
        stripped = strip_jsonp('cb ([ {"id":"532cb",\n\n\n"x":\n3}\n]\n);')
        d = json.loads(stripped)
        self.assertEqual(d, [{"id": "532cb", "x": 3}])

        stripped = strip_jsonp('parseMetadata({"STATUS":"OK"})\n\n\n//epc')
        d = json.loads(stripped)
        self.assertEqual(d, {'STATUS': 'OK'})

        stripped = strip_jsonp('ps.embedHandler({"status": "success"});')
        d = json.loads(stripped)
        self.assertEqual(d, {'status': 'success'})

        stripped = strip_jsonp('window.cb && window.cb({"status": "success"});')
        d = json.loads(stripped)
        self.assertEqual(d, {'status': 'success'})

        stripped = strip_jsonp('window.cb && cb({"status": "success"});')
        d = json.loads(stripped)
        self.assertEqual(d, {'status': 'success'})

        stripped = strip_jsonp('({"status": "success"});')
        d = json.loads(stripped)
        self.assertEqual(d, {'status': 'success'})

    def test_strip_or_none(self):
        self.assertEqual(strip_or_none(' abc'), 'abc')
        self.assertEqual(strip_or_none('abc '), 'abc')
        self.assertEqual(strip_or_none(' abc '), 'abc')
        self.assertEqual(strip_or_none('\tabc\t'), 'abc')
        self.assertEqual(strip_or_none('\n\tabc\n\t'), 'abc')
        self.assertEqual(strip_or_none('abc'), 'abc')
        self.assertEqual(strip_or_none(''), '')
        self.assertEqual(strip_or_none(None), None)
        self.assertEqual(strip_or_none(42), None)
        self.assertEqual(strip_or_none([]), None)

    def test_uppercase_escape(self):
        self.assertEqual(uppercase_escape('aä'), 'aä')
        self.assertEqual(uppercase_escape('\\U0001d550'), '𝕐')

    def test_lowercase_escape(self):
        self.assertEqual(lowercase_escape('aä'), 'aä')
        self.assertEqual(lowercase_escape('\\u0026'), '&')

    def test_limit_length(self):
        self.assertEqual(limit_length(None, 12), None)
        self.assertEqual(limit_length('foo', 12), 'foo')
        self.assertTrue(
            limit_length('foo bar baz asd', 12).startswith('foo bar'))
        self.assertTrue('...' in limit_length('foo bar baz asd', 12))

    def test_mimetype2ext(self):
        self.assertEqual(mimetype2ext(None), None)
        self.assertEqual(mimetype2ext('video/x-flv'), 'flv')
        self.assertEqual(mimetype2ext('application/x-mpegURL'), 'm3u8')
        self.assertEqual(mimetype2ext('text/vtt'), 'vtt')
        self.assertEqual(mimetype2ext('text/vtt;charset=utf-8'), 'vtt')
        self.assertEqual(mimetype2ext('text/html; charset=utf-8'), 'html')
        self.assertEqual(mimetype2ext('audio/x-wav'), 'wav')
        self.assertEqual(mimetype2ext('audio/x-wav;codec=pcm'), 'wav')

    def test_month_by_name(self):
        self.assertEqual(month_by_name(None), None)
        self.assertEqual(month_by_name('December', 'en'), 12)
        self.assertEqual(month_by_name('décembre', 'fr'), 12)
        self.assertEqual(month_by_name('December'), 12)
        self.assertEqual(month_by_name('décembre'), None)
        self.assertEqual(month_by_name('Unknown', 'unknown'), None)

    def test_parse_codecs(self):
        self.assertEqual(parse_codecs(''), {})
        self.assertEqual(parse_codecs('avc1.77.30, mp4a.40.2'), {
            'vcodec': 'avc1.77.30',
            'acodec': 'mp4a.40.2',
        })
        self.assertEqual(parse_codecs('mp4a.40.2'), {
            'vcodec': 'none',
            'acodec': 'mp4a.40.2',
        })
        self.assertEqual(parse_codecs('mp4a.40.5,avc1.42001e'), {
            'vcodec': 'avc1.42001e',
            'acodec': 'mp4a.40.5',
        })
        self.assertEqual(parse_codecs('avc3.640028'), {
            'vcodec': 'avc3.640028',
            'acodec': 'none',
        })
        self.assertEqual(parse_codecs(', h264,,newcodec,aac'), {
            'vcodec': 'h264',
            'acodec': 'aac',
        })
        self.assertEqual(parse_codecs('av01.0.05M.08'), {
            'vcodec': 'av01.0.05M.08',
            'acodec': 'none',
        })
        self.assertEqual(parse_codecs('theora, vorbis'), {
            'vcodec': 'theora',
            'acodec': 'vorbis',
        })
        self.assertEqual(parse_codecs('unknownvcodec, unknownacodec'), {
            'vcodec': 'unknownvcodec',
            'acodec': 'unknownacodec',
        })
        self.assertEqual(parse_codecs('unknown'), {})

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
            'http://xn--e1aybc.xn--p1ai/%D1%84%D1%80%D0%B0%D0%B3%D0%BC%D0%B5%D0%BD%D1%82'
        )
        self.assertEqual(
            escape_url('http://тест.рф/абв?абв=абв#абв'),
            'http://xn--e1aybc.xn--p1ai/%D0%B0%D0%B1%D0%B2?%D0%B0%D0%B1%D0%B2=%D0%B0%D0%B1%D0%B2#%D0%B0%D0%B1%D0%B2'
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

        inp = '''"The CW\\'s \\'Crazy Ex-Girlfriend\\'"'''
        self.assertEqual(js_to_json(inp), '''"The CW's 'Crazy Ex-Girlfriend'"''')

        inp = '"SAND Number: SAND 2013-7800P\\nPresenter: Tom Russo\\nHabanero Software Training - Xyce Software\\nXyce, Sandia\\u0027s"'
        json_code = js_to_json(inp)
        self.assertEqual(json.loads(json_code), json.loads(inp))

        inp = '''{
            0:{src:'skipped', type: 'application/dash+xml'},
            1:{src:'skipped', type: 'application/vnd.apple.mpegURL'},
        }'''
        self.assertEqual(js_to_json(inp), '''{
            "0":{"src":"skipped", "type": "application/dash+xml"},
            "1":{"src":"skipped", "type": "application/vnd.apple.mpegURL"}
        }''')

        inp = '''{"foo":101}'''
        self.assertEqual(js_to_json(inp), '''{"foo":101}''')

        inp = '''{"duration": "00:01:07"}'''
        self.assertEqual(js_to_json(inp), '''{"duration": "00:01:07"}''')

        inp = '''{segments: [{"offset":-3.885780586188048e-16,"duration":39.75000000000001}]}'''
        self.assertEqual(js_to_json(inp), '''{"segments": [{"offset":-3.885780586188048e-16,"duration":39.75000000000001}]}''')

    def test_js_to_json_edgecases(self):
        on = js_to_json("{abc_def:'1\\'\\\\2\\\\\\'3\"4'}")
        self.assertEqual(json.loads(on), {"abc_def": "1'\\2\\'3\"4"})

        on = js_to_json('{"abc": true}')
        self.assertEqual(json.loads(on), {'abc': True})

        # Ignore JavaScript code as well
        on = js_to_json('''{
            "x": 1,
            y: "a",
            z: some.code
        }''')
        d = json.loads(on)
        self.assertEqual(d['x'], 1)
        self.assertEqual(d['y'], 'a')

        # Just drop ! prefix for now though this results in a wrong value
        on = js_to_json('''{
            a: !0,
            b: !1,
            c: !!0,
            d: !!42.42,
            e: !!![],
            f: !"abc",
            g: !"",
            !42: 42
        }''')
        self.assertEqual(json.loads(on), {
            'a': 0,
            'b': 1,
            'c': 0,
            'd': 42.42,
            'e': [],
            'f': "abc",
            'g': "",
            '42': 42
        })

        on = js_to_json('["abc", "def",]')
        self.assertEqual(json.loads(on), ['abc', 'def'])

        on = js_to_json('[/*comment\n*/"abc"/*comment\n*/,/*comment\n*/"def",/*comment\n*/]')
        self.assertEqual(json.loads(on), ['abc', 'def'])

        on = js_to_json('[//comment\n"abc" //comment\n,//comment\n"def",//comment\n]')
        self.assertEqual(json.loads(on), ['abc', 'def'])

        on = js_to_json('{"abc": "def",}')
        self.assertEqual(json.loads(on), {'abc': 'def'})

        on = js_to_json('{/*comment\n*/"abc"/*comment\n*/:/*comment\n*/"def"/*comment\n*/,/*comment\n*/}')
        self.assertEqual(json.loads(on), {'abc': 'def'})

        on = js_to_json('{ 0: /* " \n */ ",]" , }')
        self.assertEqual(json.loads(on), {'0': ',]'})

        on = js_to_json('{ /*comment\n*/0/*comment\n*/: /* " \n */ ",]" , }')
        self.assertEqual(json.loads(on), {'0': ',]'})

        on = js_to_json('{ 0: // comment\n1 }')
        self.assertEqual(json.loads(on), {'0': 1})

        on = js_to_json(r'["<p>x<\/p>"]')
        self.assertEqual(json.loads(on), ['<p>x</p>'])

        on = js_to_json(r'["\xaa"]')
        self.assertEqual(json.loads(on), ['\u00aa'])

        on = js_to_json("['a\\\nb']")
        self.assertEqual(json.loads(on), ['ab'])

        on = js_to_json("/*comment\n*/[/*comment\n*/'a\\\nb'/*comment\n*/]/*comment\n*/")
        self.assertEqual(json.loads(on), ['ab'])

        on = js_to_json('{0xff:0xff}')
        self.assertEqual(json.loads(on), {'255': 255})

        on = js_to_json('{/*comment\n*/0xff/*comment\n*/:/*comment\n*/0xff/*comment\n*/}')
        self.assertEqual(json.loads(on), {'255': 255})

        on = js_to_json('{077:077}')
        self.assertEqual(json.loads(on), {'63': 63})

        on = js_to_json('{/*comment\n*/077/*comment\n*/:/*comment\n*/077/*comment\n*/}')
        self.assertEqual(json.loads(on), {'63': 63})

        on = js_to_json('{42:42}')
        self.assertEqual(json.loads(on), {'42': 42})

        on = js_to_json('{/*comment\n*/42/*comment\n*/:/*comment\n*/42/*comment\n*/}')
        self.assertEqual(json.loads(on), {'42': 42})

        on = js_to_json('{42:4.2e1}')
        self.assertEqual(json.loads(on), {'42': 42.0})

        on = js_to_json('{ "0x40": "0x40" }')
        self.assertEqual(json.loads(on), {'0x40': '0x40'})

        on = js_to_json('{ "040": "040" }')
        self.assertEqual(json.loads(on), {'040': '040'})

    def test_js_to_json_malformed(self):
        self.assertEqual(js_to_json('42a1'), '42"a1"')
        self.assertEqual(js_to_json('42a-1'), '42"a"-1')

    def test_extract_attributes(self):
        self.assertEqual(extract_attributes('<e x="y">'), {'x': 'y'})
        self.assertEqual(extract_attributes("<e x='y'>"), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x=y>'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x="a \'b\' c">'), {'x': "a 'b' c"})
        self.assertEqual(extract_attributes('<e x=\'a "b" c\'>'), {'x': 'a "b" c'})
        self.assertEqual(extract_attributes('<e x="&#121;">'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x="&#x79;">'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x="&amp;">'), {'x': '&'})  # XML
        self.assertEqual(extract_attributes('<e x="&quot;">'), {'x': '"'})
        self.assertEqual(extract_attributes('<e x="&pound;">'), {'x': '£'})  # HTML 3.2
        self.assertEqual(extract_attributes('<e x="&lambda;">'), {'x': 'λ'})  # HTML 4.0
        self.assertEqual(extract_attributes('<e x="&foo">'), {'x': '&foo'})
        self.assertEqual(extract_attributes('<e x="\'">'), {'x': "'"})
        self.assertEqual(extract_attributes('<e x=\'"\'>'), {'x': '"'})
        self.assertEqual(extract_attributes('<e x >'), {'x': None})
        self.assertEqual(extract_attributes('<e x=y a>'), {'x': 'y', 'a': None})
        self.assertEqual(extract_attributes('<e x= y>'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e x=1 y=2 x=3>'), {'y': '2', 'x': '3'})
        self.assertEqual(extract_attributes('<e \nx=\ny\n>'), {'x': 'y'})
        self.assertEqual(extract_attributes('<e \nx=\n"y"\n>'), {'x': 'y'})
        self.assertEqual(extract_attributes("<e \nx=\n'y'\n>"), {'x': 'y'})
        self.assertEqual(extract_attributes('<e \nx="\ny\n">'), {'x': '\ny\n'})
        self.assertEqual(extract_attributes('<e CAPS=x>'), {'caps': 'x'})  # Names lowercased
        self.assertEqual(extract_attributes('<e x=1 X=2>'), {'x': '2'})
        self.assertEqual(extract_attributes('<e X=1 x=2>'), {'x': '2'})
        self.assertEqual(extract_attributes('<e _:funny-name1=1>'), {'_:funny-name1': '1'})
        self.assertEqual(extract_attributes('<e x="Fáilte 世界 \U0001f600">'), {'x': 'Fáilte 世界 \U0001f600'})
        self.assertEqual(extract_attributes('<e x="décompose&#769;">'), {'x': 'décompose\u0301'})
        # "Narrow" Python builds don't support unicode code points outside BMP.
        try:
            compat_chr(0x10000)
            supports_outside_bmp = True
        except ValueError:
            supports_outside_bmp = False
        if supports_outside_bmp:
            self.assertEqual(extract_attributes('<e x="Smile &#128512;!">'), {'x': 'Smile \U0001f600!'})
        # Malformed HTML should not break attributes extraction on older Python
        self.assertEqual(extract_attributes('<mal"formed/>'), {})

    def test_clean_html(self):
        self.assertEqual(clean_html('a:\nb'), 'a: b')
        self.assertEqual(clean_html('a:\n   "b"'), 'a:    "b"')
        self.assertEqual(clean_html('a<br>\xa0b'), 'a\nb')

    def test_intlist_to_bytes(self):
        self.assertEqual(
            intlist_to_bytes([0, 1, 127, 128, 255]),
            b'\x00\x01\x7f\x80\xff')

    def test_args_to_str(self):
        self.assertEqual(
            args_to_str(['foo', 'ba/r', '-baz', '2 be', '']),
            'foo ba/r -baz \'2 be\' \'\'' if compat_os_name != 'nt' else 'foo ba/r -baz "2 be" ""'
        )

    def test_parse_filesize(self):
        self.assertEqual(parse_filesize(None), None)
        self.assertEqual(parse_filesize(''), None)
        self.assertEqual(parse_filesize('91 B'), 91)
        self.assertEqual(parse_filesize('foobar'), None)
        self.assertEqual(parse_filesize('2 MiB'), 2097152)
        self.assertEqual(parse_filesize('5 GB'), 5000000000)
        self.assertEqual(parse_filesize('1.2Tb'), 1200000000000)
        self.assertEqual(parse_filesize('1.2tb'), 1200000000000)
        self.assertEqual(parse_filesize('1,24 KB'), 1240)
        self.assertEqual(parse_filesize('1,24 kb'), 1240)
        self.assertEqual(parse_filesize('8.5 megabytes'), 8500000)

    def test_parse_count(self):
        self.assertEqual(parse_count(None), None)
        self.assertEqual(parse_count(''), None)
        self.assertEqual(parse_count('0'), 0)
        self.assertEqual(parse_count('1000'), 1000)
        self.assertEqual(parse_count('1.000'), 1000)
        self.assertEqual(parse_count('1.1k'), 1100)
        self.assertEqual(parse_count('1.1kk'), 1100000)
        self.assertEqual(parse_count('1.1kk '), 1100000)
        self.assertEqual(parse_count('1.1kk views'), 1100000)

    def test_parse_resolution(self):
        self.assertEqual(parse_resolution(None), {})
        self.assertEqual(parse_resolution(''), {})
        self.assertEqual(parse_resolution('1920x1080'), {'width': 1920, 'height': 1080})
        self.assertEqual(parse_resolution('1920×1080'), {'width': 1920, 'height': 1080})
        self.assertEqual(parse_resolution('1920 x 1080'), {'width': 1920, 'height': 1080})
        self.assertEqual(parse_resolution('720p'), {'height': 720})
        self.assertEqual(parse_resolution('4k'), {'height': 2160})
        self.assertEqual(parse_resolution('8K'), {'height': 4320})

    def test_parse_bitrate(self):
        self.assertEqual(parse_bitrate(None), None)
        self.assertEqual(parse_bitrate(''), None)
        self.assertEqual(parse_bitrate('300kbps'), 300)
        self.assertEqual(parse_bitrate('1500kbps'), 1500)
        self.assertEqual(parse_bitrate('300 kbps'), 300)

    def test_version_tuple(self):
        self.assertEqual(version_tuple('1'), (1,))
        self.assertEqual(version_tuple('10.23.344'), (10, 23, 344))
        self.assertEqual(version_tuple('10.1-6'), (10, 1, 6))  # avconv style

    def test_detect_exe_version(self):
        self.assertEqual(detect_exe_version('''ffmpeg version 1.2.1
built on May 27 2013 08:37:26 with gcc 4.7 (Debian 4.7.3-4)
configuration: --prefix=/usr --extra-'''), '1.2.1')
        self.assertEqual(detect_exe_version('''ffmpeg version N-63176-g1fb4685
built on May 15 2014 22:09:06 with gcc 4.8.2 (GCC)'''), 'N-63176-g1fb4685')
        self.assertEqual(detect_exe_version('''X server found. dri2 connection failed!
Trying to open render node...
Success at /dev/dri/renderD128.
ffmpeg version 2.4.4 Copyright (c) 2000-2014 the FFmpeg ...'''), '2.4.4')

    def test_age_restricted(self):
        self.assertFalse(age_restricted(None, 10))  # unrestricted content
        self.assertFalse(age_restricted(1, None))  # unrestricted policy
        self.assertFalse(age_restricted(8, 10))
        self.assertTrue(age_restricted(18, 14))
        self.assertFalse(age_restricted(18, 18))

    def test_is_html(self):
        self.assertFalse(is_html(b'\x49\x44\x43<html'))
        self.assertTrue(is_html(b'<!DOCTYPE foo>\xaaa'))
        self.assertTrue(is_html(  # UTF-8 with BOM
            b'\xef\xbb\xbf<!DOCTYPE foo>\xaaa'))
        self.assertTrue(is_html(  # UTF-16-LE
            b'\xff\xfe<\x00h\x00t\x00m\x00l\x00>\x00\xe4\x00'
        ))
        self.assertTrue(is_html(  # UTF-16-BE
            b'\xfe\xff\x00<\x00h\x00t\x00m\x00l\x00>\x00\xe4'
        ))
        self.assertTrue(is_html(  # UTF-32-BE
            b'\x00\x00\xFE\xFF\x00\x00\x00<\x00\x00\x00h\x00\x00\x00t\x00\x00\x00m\x00\x00\x00l\x00\x00\x00>\x00\x00\x00\xe4'))
        self.assertTrue(is_html(  # UTF-32-LE
            b'\xFF\xFE\x00\x00<\x00\x00\x00h\x00\x00\x00t\x00\x00\x00m\x00\x00\x00l\x00\x00\x00>\x00\x00\x00\xe4\x00\x00\x00'))

    def test_render_table(self):
        self.assertEqual(
            render_table(
                ['a', 'bcd'],
                [[123, 4], [9999, 51]]),
            'a    bcd\n'
            '123  4\n'
            '9999 51')

    def test_match_str(self):
        self.assertRaises(ValueError, match_str, 'xy>foobar', {})
        self.assertFalse(match_str('xy', {'x': 1200}))
        self.assertTrue(match_str('!xy', {'x': 1200}))
        self.assertTrue(match_str('x', {'x': 1200}))
        self.assertFalse(match_str('!x', {'x': 1200}))
        self.assertTrue(match_str('x', {'x': 0}))
        self.assertFalse(match_str('x>0', {'x': 0}))
        self.assertFalse(match_str('x>0', {}))
        self.assertTrue(match_str('x>?0', {}))
        self.assertTrue(match_str('x>1K', {'x': 1200}))
        self.assertFalse(match_str('x>2K', {'x': 1200}))
        self.assertTrue(match_str('x>=1200 & x < 1300', {'x': 1200}))
        self.assertFalse(match_str('x>=1100 & x < 1200', {'x': 1200}))
        self.assertFalse(match_str('y=a212', {'y': 'foobar42'}))
        self.assertTrue(match_str('y=foobar42', {'y': 'foobar42'}))
        self.assertFalse(match_str('y!=foobar42', {'y': 'foobar42'}))
        self.assertTrue(match_str('y!=foobar2', {'y': 'foobar42'}))
        self.assertFalse(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 90, 'description': 'foo'}))
        self.assertTrue(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 190, 'description': 'foo'}))
        self.assertFalse(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 190, 'dislike_count': 60, 'description': 'foo'}))
        self.assertFalse(match_str(
            'like_count > 100 & dislike_count <? 50 & description',
            {'like_count': 190, 'dislike_count': 10}))
        self.assertTrue(match_str('is_live', {'is_live': True}))
        self.assertFalse(match_str('is_live', {'is_live': False}))
        self.assertFalse(match_str('is_live', {'is_live': None}))
        self.assertFalse(match_str('is_live', {}))
        self.assertFalse(match_str('!is_live', {'is_live': True}))
        self.assertTrue(match_str('!is_live', {'is_live': False}))
        self.assertTrue(match_str('!is_live', {'is_live': None}))
        self.assertTrue(match_str('!is_live', {}))
        self.assertTrue(match_str('title', {'title': 'abc'}))
        self.assertTrue(match_str('title', {'title': ''}))
        self.assertFalse(match_str('!title', {'title': 'abc'}))
        self.assertFalse(match_str('!title', {'title': ''}))

    def test_parse_dfxp_time_expr(self):
        self.assertEqual(parse_dfxp_time_expr(None), None)
        self.assertEqual(parse_dfxp_time_expr(''), None)
        self.assertEqual(parse_dfxp_time_expr('0.1'), 0.1)
        self.assertEqual(parse_dfxp_time_expr('0.1s'), 0.1)
        self.assertEqual(parse_dfxp_time_expr('00:00:01'), 1.0)
        self.assertEqual(parse_dfxp_time_expr('00:00:01.100'), 1.1)
        self.assertEqual(parse_dfxp_time_expr('00:00:01:100'), 1.1)

    def test_dfxp2srt(self):
        dfxp_data = '''<?xml version="1.0" encoding="UTF-8"?>
            <tt xmlns="http://www.w3.org/ns/ttml" xml:lang="en" xmlns:tts="http://www.w3.org/ns/ttml#parameter">
            <body>
                <div xml:lang="en">
                    <p begin="0" end="1">The following line contains Chinese characters and special symbols</p>
                    <p begin="1" end="2">第二行<br/>♪♪</p>
                    <p begin="2" dur="1"><span>Third<br/>Line</span></p>
                    <p begin="3" end="-1">Lines with invalid timestamps are ignored</p>
                    <p begin="-1" end="-1">Ignore, two</p>
                    <p begin="3" dur="-1">Ignored, three</p>
                </div>
            </body>
            </tt>'''.encode('utf-8')
        srt_data = '''1
00:00:00,000 --> 00:00:01,000
The following line contains Chinese characters and special symbols

2
00:00:01,000 --> 00:00:02,000
第二行
♪♪

3
00:00:02,000 --> 00:00:03,000
Third
Line

'''
        self.assertEqual(dfxp2srt(dfxp_data), srt_data)

        dfxp_data_no_default_namespace = '''<?xml version="1.0" encoding="UTF-8"?>
            <tt xml:lang="en" xmlns:tts="http://www.w3.org/ns/ttml#parameter">
            <body>
                <div xml:lang="en">
                    <p begin="0" end="1">The first line</p>
                </div>
            </body>
            </tt>'''.encode('utf-8')
        srt_data = '''1
00:00:00,000 --> 00:00:01,000
The first line

'''
        self.assertEqual(dfxp2srt(dfxp_data_no_default_namespace), srt_data)

        dfxp_data_with_style = '''<?xml version="1.0" encoding="utf-8"?>
<tt xmlns="http://www.w3.org/2006/10/ttaf1" xmlns:ttp="http://www.w3.org/2006/10/ttaf1#parameter" ttp:timeBase="media" xmlns:tts="http://www.w3.org/2006/10/ttaf1#style" xml:lang="en" xmlns:ttm="http://www.w3.org/2006/10/ttaf1#metadata">
  <head>
    <styling>
      <style id="s2" style="s0" tts:color="cyan" tts:fontWeight="bold" />
      <style id="s1" style="s0" tts:color="yellow" tts:fontStyle="italic" />
      <style id="s3" style="s0" tts:color="lime" tts:textDecoration="underline" />
      <style id="s0" tts:backgroundColor="black" tts:fontStyle="normal" tts:fontSize="16" tts:fontFamily="sansSerif" tts:color="white" />
    </styling>
  </head>
  <body tts:textAlign="center" style="s0">
    <div>
      <p begin="00:00:02.08" id="p0" end="00:00:05.84">default style<span tts:color="red">custom style</span></p>
      <p style="s2" begin="00:00:02.08" id="p0" end="00:00:05.84"><span tts:color="lime">part 1<br /></span><span tts:color="cyan">part 2</span></p>
      <p style="s3" begin="00:00:05.84" id="p1" end="00:00:09.56">line 3<br />part 3</p>
      <p style="s1" tts:textDecoration="underline" begin="00:00:09.56" id="p2" end="00:00:12.36"><span style="s2" tts:color="lime">inner<br /> </span>style</p>
    </div>
  </body>
</tt>'''.encode('utf-8')
        srt_data = '''1
00:00:02,080 --> 00:00:05,839
<font color="white" face="sansSerif" size="16">default style<font color="red">custom style</font></font>

2
00:00:02,080 --> 00:00:05,839
<b><font color="cyan" face="sansSerif" size="16"><font color="lime">part 1
</font>part 2</font></b>

3
00:00:05,839 --> 00:00:09,560
<u><font color="lime">line 3
part 3</font></u>

4
00:00:09,560 --> 00:00:12,359
<i><u><font color="yellow"><font color="lime">inner
 </font>style</font></u></i>

'''
        self.assertEqual(dfxp2srt(dfxp_data_with_style), srt_data)

        dfxp_data_non_utf8 = '''<?xml version="1.0" encoding="UTF-16"?>
            <tt xmlns="http://www.w3.org/ns/ttml" xml:lang="en" xmlns:tts="http://www.w3.org/ns/ttml#parameter">
            <body>
                <div xml:lang="en">
                    <p begin="0" end="1">Line 1</p>
                    <p begin="1" end="2">第二行</p>
                </div>
            </body>
            </tt>'''.encode('utf-16')
        srt_data = '''1
00:00:00,000 --> 00:00:01,000
Line 1

2
00:00:01,000 --> 00:00:02,000
第二行

'''
        self.assertEqual(dfxp2srt(dfxp_data_non_utf8), srt_data)

    def test_cli_option(self):
        self.assertEqual(cli_option({'proxy': '127.0.0.1:3128'}, '--proxy', 'proxy'), ['--proxy', '127.0.0.1:3128'])
        self.assertEqual(cli_option({'proxy': None}, '--proxy', 'proxy'), [])
        self.assertEqual(cli_option({}, '--proxy', 'proxy'), [])
        self.assertEqual(cli_option({'retries': 10}, '--retries', 'retries'), ['--retries', '10'])

    def test_cli_valueless_option(self):
        self.assertEqual(cli_valueless_option(
            {'downloader': 'external'}, '--external-downloader', 'downloader', 'external'), ['--external-downloader'])
        self.assertEqual(cli_valueless_option(
            {'downloader': 'internal'}, '--external-downloader', 'downloader', 'external'), [])
        self.assertEqual(cli_valueless_option(
            {'nocheckcertificate': True}, '--no-check-certificate', 'nocheckcertificate'), ['--no-check-certificate'])
        self.assertEqual(cli_valueless_option(
            {'nocheckcertificate': False}, '--no-check-certificate', 'nocheckcertificate'), [])
        self.assertEqual(cli_valueless_option(
            {'checkcertificate': True}, '--no-check-certificate', 'checkcertificate', False), [])
        self.assertEqual(cli_valueless_option(
            {'checkcertificate': False}, '--no-check-certificate', 'checkcertificate', False), ['--no-check-certificate'])

    def test_cli_bool_option(self):
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--no-check-certificate', 'nocheckcertificate'),
            ['--no-check-certificate', 'true'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--no-check-certificate', 'nocheckcertificate', separator='='),
            ['--no-check-certificate=true'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--check-certificate', 'nocheckcertificate', 'false', 'true'),
            ['--check-certificate', 'false'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': True}, '--check-certificate', 'nocheckcertificate', 'false', 'true', '='),
            ['--check-certificate=false'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': False}, '--check-certificate', 'nocheckcertificate', 'false', 'true'),
            ['--check-certificate', 'true'])
        self.assertEqual(
            cli_bool_option(
                {'nocheckcertificate': False}, '--check-certificate', 'nocheckcertificate', 'false', 'true', '='),
            ['--check-certificate=true'])
        self.assertEqual(
            cli_bool_option(
                {}, '--check-certificate', 'nocheckcertificate', 'false', 'true', '='),
            [])

    def test_ohdave_rsa_encrypt(self):
        N = 0xab86b6371b5318aaa1d3c9e612a9f1264f372323c8c0f19875b5fc3b3fd3afcc1e5bec527aa94bfa85bffc157e4245aebda05389a5357b75115ac94f074aefcd
        e = 65537

        self.assertEqual(
            ohdave_rsa_encrypt(b'aa111222', e, N),
            '726664bd9a23fd0c70f9f1b84aab5e3905ce1e45a584e9cbcf9bcc7510338fc1986d6c599ff990d923aa43c51c0d9013cd572e13bc58f4ae48f2ed8c0b0ba881')

    def test_pkcs1pad(self):
        data = [1, 2, 3]
        padded_data = pkcs1pad(data, 32)
        self.assertEqual(padded_data[:2], [0, 2])
        self.assertEqual(padded_data[28:], [0, 1, 2, 3])

        self.assertRaises(ValueError, pkcs1pad, data, 8)

    def test_encode_base_n(self):
        self.assertEqual(encode_base_n(0, 30), '0')
        self.assertEqual(encode_base_n(80, 30), '2k')

        custom_table = '9876543210ZYXWVUTSRQPONMLKJIHGFEDCBA'
        self.assertEqual(encode_base_n(0, 30, custom_table), '9')
        self.assertEqual(encode_base_n(80, 30, custom_table), '7P')

        self.assertRaises(ValueError, encode_base_n, 0, 70)
        self.assertRaises(ValueError, encode_base_n, 0, 60, custom_table)

    def test_caesar(self):
        self.assertEqual(caesar('ace', 'abcdef', 2), 'cea')
        self.assertEqual(caesar('cea', 'abcdef', -2), 'ace')
        self.assertEqual(caesar('ace', 'abcdef', -2), 'eac')
        self.assertEqual(caesar('eac', 'abcdef', 2), 'ace')
        self.assertEqual(caesar('ace', 'abcdef', 0), 'ace')
        self.assertEqual(caesar('xyz', 'abcdef', 2), 'xyz')
        self.assertEqual(caesar('abc', 'acegik', 2), 'ebg')
        self.assertEqual(caesar('ebg', 'acegik', -2), 'abc')

    def test_rot47(self):
        self.assertEqual(rot47('youtube-dl'), r'J@FEF36\5=')
        self.assertEqual(rot47('YOUTUBE-DL'), r'*~&%&qt\s{')

    def test_urshift(self):
        self.assertEqual(urshift(3, 1), 1)
        self.assertEqual(urshift(-3, 1), 2147483646)

    def test_get_element_by_class(self):
        html = '''
            <span class="foo bar">nice</span>
        '''

        self.assertEqual(get_element_by_class('foo', html), 'nice')
        self.assertEqual(get_element_by_class('no-such-class', html), None)

    def test_get_element_by_attribute(self):
        html = '''
            <span class="foo bar">nice</span>
        '''

        self.assertEqual(get_element_by_attribute('class', 'foo bar', html), 'nice')
        self.assertEqual(get_element_by_attribute('class', 'foo', html), None)
        self.assertEqual(get_element_by_attribute('class', 'no-such-foo', html), None)

        html = '''
            <div itemprop="author" itemscope>foo</div>
        '''

        self.assertEqual(get_element_by_attribute('itemprop', 'author', html), 'foo')

    def test_get_elements_by_class(self):
        html = '''
            <span class="foo bar">nice</span><span class="foo bar">also nice</span>
        '''

        self.assertEqual(get_elements_by_class('foo', html), ['nice', 'also nice'])
        self.assertEqual(get_elements_by_class('no-such-class', html), [])

    def test_get_elements_by_attribute(self):
        html = '''
            <span class="foo bar">nice</span><span class="foo bar">also nice</span>
        '''

        self.assertEqual(get_elements_by_attribute('class', 'foo bar', html), ['nice', 'also nice'])
        self.assertEqual(get_elements_by_attribute('class', 'foo', html), [])
        self.assertEqual(get_elements_by_attribute('class', 'no-such-foo', html), [])

    def test_clean_podcast_url(self):
        self.assertEqual(clean_podcast_url('https://www.podtrac.com/pts/redirect.mp3/chtbl.com/track/5899E/traffic.megaphone.fm/HSW7835899191.mp3'), 'https://traffic.megaphone.fm/HSW7835899191.mp3')
        self.assertEqual(clean_podcast_url('https://play.podtrac.com/npr-344098539/edge1.pod.npr.org/anon.npr-podcasts/podcast/npr/waitwait/2020/10/20201003_waitwait_wwdtmpodcast201003-015621a5-f035-4eca-a9a1-7c118d90bc3c.mp3'), 'https://edge1.pod.npr.org/anon.npr-podcasts/podcast/npr/waitwait/2020/10/20201003_waitwait_wwdtmpodcast201003-015621a5-f035-4eca-a9a1-7c118d90bc3c.mp3')

    def test_LazyList(self):
        it = list(range(10))

        self.assertEqual(list(LazyList(it)), it)
        self.assertEqual(LazyList(it).exhaust(), it)
        self.assertEqual(LazyList(it)[5], it[5])

        self.assertEqual(LazyList(it)[5:], it[5:])
        self.assertEqual(LazyList(it)[:5], it[:5])
        self.assertEqual(LazyList(it)[::2], it[::2])
        self.assertEqual(LazyList(it)[1::2], it[1::2])
        self.assertEqual(LazyList(it)[5::-1], it[5::-1])
        self.assertEqual(LazyList(it)[6:2:-2], it[6:2:-2])
        self.assertEqual(LazyList(it)[::-1], it[::-1])

        self.assertTrue(LazyList(it))
        self.assertFalse(LazyList(range(0)))
        self.assertEqual(len(LazyList(it)), len(it))
        self.assertEqual(repr(LazyList(it)), repr(it))
        self.assertEqual(compat_str(LazyList(it)), compat_str(it))

        self.assertEqual(list(LazyList(it, reverse=True)), it[::-1])
        self.assertEqual(list(reversed(LazyList(it))[::-1]), it)
        self.assertEqual(list(reversed(LazyList(it))[1:3:7]), it[::-1][1:3:7])

    def test_LazyList_laziness(self):

        def test(ll, idx, val, cache):
            self.assertEqual(ll[idx], val)
            self.assertEqual(ll._cache, list(cache))

        ll = LazyList(range(10))
        test(ll, 0, 0, range(1))
        test(ll, 5, 5, range(6))
        test(ll, -3, 7, range(10))

        ll = LazyList(range(10), reverse=True)
        test(ll, -1, 0, range(1))
        test(ll, 3, 6, range(10))

        ll = LazyList(itertools.count())
        test(ll, 10, 10, range(11))
        ll = reversed(ll)
        test(ll, -15, 14, range(15))

    def test_try_call(self):
        def total(*x, **kwargs):
            return sum(x) + sum(kwargs.values())

        self.assertEqual(try_call(None), None,
                         msg='not a fn should give None')
        self.assertEqual(try_call(lambda: 1), 1,
                         msg='int fn with no expected_type should give int')
        self.assertEqual(try_call(lambda: 1, expected_type=int), 1,
                         msg='int fn with expected_type int should give int')
        self.assertEqual(try_call(lambda: 1, expected_type=dict), None,
                         msg='int fn with wrong expected_type should give None')
        self.assertEqual(try_call(total, args=(0, 1, 0, ), expected_type=int), 1,
                         msg='fn should accept arglist')
        self.assertEqual(try_call(total, kwargs={'a': 0, 'b': 1, 'c': 0}, expected_type=int), 1,
                         msg='fn should accept kwargs')
        self.assertEqual(try_call(lambda: 1, expected_type=dict), None,
                         msg='int fn with no expected_type should give None')
        self.assertEqual(try_call(lambda x: {}, total, args=(42, ), expected_type=int), 42,
                         msg='expect first int result with expected_type int')

    def test_variadic(self):
        self.assertEqual(variadic(None), (None, ))
        self.assertEqual(variadic('spam'), ('spam', ))
        self.assertEqual(variadic('spam', allowed_types=dict), 'spam')
        self.assertEqual(variadic('spam', allowed_types=[dict]), 'spam')

    def test_traverse_obj(self):
        _TEST_DATA = {
            100: 100,
            1.2: 1.2,
            'str': 'str',
            'None': None,
            '...': Ellipsis,
            'urls': [
                {'index': 0, 'url': 'https://www.example.com/0'},
                {'index': 1, 'url': 'https://www.example.com/1'},
            ],
            'data': (
                {'index': 2},
                {'index': 3},
            ),
            'dict': {},
        }

        # Test base functionality
        self.assertEqual(traverse_obj(_TEST_DATA, ('str',)), 'str',
                         msg='allow tuple path')
        self.assertEqual(traverse_obj(_TEST_DATA, ['str']), 'str',
                         msg='allow list path')
        self.assertEqual(traverse_obj(_TEST_DATA, (value for value in ("str",))), 'str',
                         msg='allow iterable path')
        self.assertEqual(traverse_obj(_TEST_DATA, 'str'), 'str',
                         msg='single items should be treated as a path')
        self.assertEqual(traverse_obj(_TEST_DATA, None), _TEST_DATA)
        self.assertEqual(traverse_obj(_TEST_DATA, 100), 100)
        self.assertEqual(traverse_obj(_TEST_DATA, 1.2), 1.2)

        # Test Ellipsis behavior
        self.assertCountEqual(traverse_obj(_TEST_DATA, Ellipsis),
                              (item for item in _TEST_DATA.values() if item is not None),
                              msg='`...` should give all values except `None`')
        self.assertCountEqual(traverse_obj(_TEST_DATA, ('urls', 0, Ellipsis)), _TEST_DATA['urls'][0].values(),
                              msg='`...` selection for dicts should select all values')
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, Ellipsis, 'url')),
                         ['https://www.example.com/0', 'https://www.example.com/1'],
                         msg='nested `...` queries should work')
        self.assertCountEqual(traverse_obj(_TEST_DATA, (Ellipsis, Ellipsis, 'index')), range(4),
                              msg='`...` query result should be flattened')

        # Test function as key
        self.assertEqual(traverse_obj(_TEST_DATA, lambda x, y: x == 'urls' and isinstance(y, list)),
                         [_TEST_DATA['urls']],
                         msg='function as query key should perform a filter based on (key, value)')
        self.assertCountEqual(traverse_obj(_TEST_DATA, lambda _, x: isinstance(x[0], compat_str)), {'str'},
                              msg='exceptions in the query function should be caught')

        # Test alternative paths
        self.assertEqual(traverse_obj(_TEST_DATA, 'fail', 'str'), 'str',
                         msg='multiple `paths` should be treated as alternative paths')
        self.assertEqual(traverse_obj(_TEST_DATA, 'str', 100), 'str',
                         msg='alternatives should exit early')
        self.assertEqual(traverse_obj(_TEST_DATA, 'fail', 'fail'), None,
                         msg='alternatives should return `default` if exhausted')
        self.assertEqual(traverse_obj(_TEST_DATA, (Ellipsis, 'fail'), 100), 100,
                         msg='alternatives should track their own branching return')
        self.assertEqual(traverse_obj(_TEST_DATA, ('dict', Ellipsis), ('data', Ellipsis)), list(_TEST_DATA['data']),
                         msg='alternatives on empty objects should search further')

        # Test branch and path nesting
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', (3, 0), 'url')), ['https://www.example.com/0'],
                         msg='tuple as key should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', [3, 0], 'url')), ['https://www.example.com/0'],
                         msg='list as key should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', ((1, 'fail'), (0, 'url')))), ['https://www.example.com/0'],
                         msg='double nesting in path should be treated as paths')
        self.assertEqual(traverse_obj(['0', [1, 2]], [(0, 1), 0]), [1],
                         msg='do not fail early on branching')
        self.assertCountEqual(traverse_obj(_TEST_DATA, ('urls', ((1, ('fail', 'url')), (0, 'url')))),
                              ['https://www.example.com/0', 'https://www.example.com/1'],
                              msg='triple nesting in path should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, ('urls', ('fail', (Ellipsis, 'url')))),
                         ['https://www.example.com/0', 'https://www.example.com/1'],
                         msg='ellipsis as branch path start gets flattened')

        # Test dictionary as key
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 100, 1: 1.2}), {0: 100, 1: 1.2},
                         msg='dict key should result in a dict with the same keys')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', 0, 'url')}),
                         {0: 'https://www.example.com/0'},
                         msg='dict key should allow paths')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', (3, 0), 'url')}),
                         {0: ['https://www.example.com/0']},
                         msg='tuple in dict path should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', ((1, 'fail'), (0, 'url')))}),
                         {0: ['https://www.example.com/0']},
                         msg='double nesting in dict path should be treated as paths')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('urls', ((1, ('fail', 'url')), (0, 'url')))}),
                         {0: ['https://www.example.com/1', 'https://www.example.com/0']},
                         msg='triple nesting in dict path should be treated as branches')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'fail'}), {},
                         msg='remove `None` values when dict key')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'fail'}, default=Ellipsis), {0: Ellipsis},
                         msg='do not remove `None` values if `default`')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'dict'}), {0: {}},
                         msg='do not remove empty values when dict key')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: 'dict'}, default=Ellipsis), {0: {}},
                         msg='do not remove empty values when dict key and a default')
        self.assertEqual(traverse_obj(_TEST_DATA, {0: ('dict', Ellipsis)}), {0: []},
                         msg='if branch in dict key not successful, return `[]`')

        # Testing default parameter behavior
        _DEFAULT_DATA = {'None': None, 'int': 0, 'list': []}
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'fail'), None,
                         msg='default value should be `None`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'fail', 'fail', default=Ellipsis), Ellipsis,
                         msg='chained fails should result in default')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'None', 'int'), 0,
                         msg='should not short cirquit on `None`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'fail', default=1), 1,
                         msg='invalid dict key should result in `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, 'None', default=1), 1,
                         msg='`None` is a deliberate sentinel and should become `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, ('list', 10)), None,
                         msg='`IndexError` should result in `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, (Ellipsis, 'fail'), default=1), 1,
                         msg='if branched but not successful return `default` if defined, not `[]`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, (Ellipsis, 'fail'), default=None), None,
                         msg='if branched but not successful return `default` even if `default` is `None`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, (Ellipsis, 'fail')), [],
                         msg='if branched but not successful return `[]`, not `default`')
        self.assertEqual(traverse_obj(_DEFAULT_DATA, ('list', Ellipsis)), [],
                         msg='if branched but object is empty return `[]`, not `default`')

        # Testing expected_type behavior
        _EXPECTED_TYPE_DATA = {'str': 'str', 'int': 0}
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=compat_str), 'str',
                         msg='accept matching `expected_type` type')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'str', expected_type=int), None,
                         msg='reject non matching `expected_type` type')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'int', expected_type=lambda x: compat_str(x)), '0',
                         msg='transform type using type function')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, 'str',
                                      expected_type=lambda _: 1 / 0), None,
                         msg='wrap expected_type function in try_call')
        self.assertEqual(traverse_obj(_EXPECTED_TYPE_DATA, Ellipsis, expected_type=compat_str), ['str'],
                         msg='eliminate items that expected_type fails on')

        # Test get_all behavior
        _GET_ALL_DATA = {'key': [0, 1, 2]}
        self.assertEqual(traverse_obj(_GET_ALL_DATA, ('key', Ellipsis), get_all=False), 0,
                         msg='if not `get_all`, return only first matching value')
        self.assertEqual(traverse_obj(_GET_ALL_DATA, Ellipsis, get_all=False), [0, 1, 2],
                         msg='do not overflatten if not `get_all`')

        # Test casesense behavior
        _CASESENSE_DATA = {
            'KeY': 'value0',
            0: {
                'KeY': 'value1',
                0: {'KeY': 'value2'},
            },
            # FULLWIDTH LATIN CAPITAL LETTER K
            '\uff2bey': 'value3',
        }
        self.assertEqual(traverse_obj(_CASESENSE_DATA, 'key'), None,
                         msg='dict keys should be case sensitive unless `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, 'keY',
                                      casesense=False), 'value0',
                         msg='allow non matching key case if `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, '\uff4bey',  # FULLWIDTH LATIN SMALL LETTER K
                                      casesense=False), 'value3',
                         msg='allow non matching Unicode key case if `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, (0, ('keY',)),
                                      casesense=False), ['value1'],
                         msg='allow non matching key case in branch if `casesense`')
        self.assertEqual(traverse_obj(_CASESENSE_DATA, (0, ((0, 'keY'),)),
                                      casesense=False), ['value2'],
                         msg='allow non matching key case in branch path if `casesense`')

        # Test traverse_string behavior
        _TRAVERSE_STRING_DATA = {'str': 'str', 1.2: 1.2}
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', 0)), None,
                         msg='do not traverse into string if not `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', 0),
                                      _traverse_string=True), 's',
                         msg='traverse into string if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, (1.2, 1),
                                      _traverse_string=True), '.',
                         msg='traverse into converted data if `traverse_string`')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', Ellipsis),
                                      _traverse_string=True), list('str'),
                         msg='`...` branching into string should result in list')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', (0, 2)),
                                      _traverse_string=True), ['s', 'r'],
                         msg='branching into string should result in list')
        self.assertEqual(traverse_obj(_TRAVERSE_STRING_DATA, ('str', lambda _, x: x),
                                      _traverse_string=True), list('str'),
                         msg='function branching into string should result in list')

        # Test is_user_input behavior
        _IS_USER_INPUT_DATA = {'range8': list(range(8))}
        self.assertEqual(traverse_obj(_IS_USER_INPUT_DATA, ('range8', '3'),
                                      _is_user_input=True), 3,
                         msg='allow for string indexing if `is_user_input`')
        self.assertCountEqual(traverse_obj(_IS_USER_INPUT_DATA, ('range8', '3:'),
                                           _is_user_input=True), tuple(range(8))[3:],
                              msg='allow for string slice if `is_user_input`')
        self.assertCountEqual(traverse_obj(_IS_USER_INPUT_DATA, ('range8', ':4:2'),
                                           _is_user_input=True), tuple(range(8))[:4:2],
                              msg='allow step in string slice if `is_user_input`')
        self.assertCountEqual(traverse_obj(_IS_USER_INPUT_DATA, ('range8', ':'),
                                           _is_user_input=True), range(8),
                              msg='`:` should be treated as `...` if `is_user_input`')
        with self.assertRaises(TypeError, msg='too many params should result in error'):
            traverse_obj(_IS_USER_INPUT_DATA, ('range8', ':::'), _is_user_input=True)

        # Test re.Match as input obj
        mobj = re.match(r'^0(12)(?P<group>3)(4)?$', '0123')
        self.assertEqual(traverse_obj(mobj, Ellipsis), [x for x in mobj.groups() if x is not None],
                         msg='`...` on a `re.Match` should give its `groups()`')
        self.assertEqual(traverse_obj(mobj, lambda k, _: k in (0, 2)), ['0123', '3'],
                         msg='function on a `re.Match` should give groupno, value starting at 0')
        self.assertEqual(traverse_obj(mobj, 'group'), '3',
                         msg='str key on a `re.Match` should give group with that name')
        self.assertEqual(traverse_obj(mobj, 2), '3',
                         msg='int key on a `re.Match` should give group with that name')
        self.assertEqual(traverse_obj(mobj, 'gRoUp', casesense=False), '3',
                         msg='str key on a `re.Match` should respect casesense')
        self.assertEqual(traverse_obj(mobj, 'fail'), None,
                         msg='failing str key on a `re.Match` should return `default`')
        self.assertEqual(traverse_obj(mobj, 'gRoUpS', casesense=False), None,
                         msg='failing str key on a `re.Match` should return `default`')
        self.assertEqual(traverse_obj(mobj, 8), None,
                         msg='failing int key on a `re.Match` should return `default`')

    def test_get_first(self):
        self.assertEqual(get_first([{'a': None}, {'a': 'spam'}], 'a'), 'spam')

    def test_join_nonempty(self):
        self.assertEqual(join_nonempty('a', 'b'), 'a-b')
        self.assertEqual(join_nonempty(
            'a', 'b', 'c', 'd',
            from_dict={'a': 'c', 'c': [], 'b': 'd', 'd': None}), 'c-d')


if __name__ == '__main__':
    unittest.main()
