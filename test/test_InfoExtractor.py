#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL, expect_dict
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.extractor import YoutubeIE, get_info_extractor
from youtube_dl.utils import encode_data_uri, strip_jsonp, ExtractorError, RegexNotFoundError


class TestIE(InfoExtractor):
    pass


class TestInfoExtractor(unittest.TestCase):
    def setUp(self):
        self.ie = TestIE(FakeYDL())

    def test_ie_key(self):
        self.assertEqual(get_info_extractor(YoutubeIE.ie_key()), YoutubeIE)

    def test_html_search_regex(self):
        html = '<p id="foo">Watch this <a href="http://www.youtube.com/watch?v=BaW_jenozKc">video</a></p>'
        search = lambda re, *args: self.ie._html_search_regex(re, html, *args)
        self.assertEqual(search(r'<p id="foo">(.+?)</p>', 'foo'), 'Watch this video')

    def test_opengraph(self):
        ie = self.ie
        html = '''
            <meta name="og:title" content='Foo'/>
            <meta content="Some video's description " name="og:description"/>
            <meta property='og:image' content='http://domain.com/pic.jpg?key1=val1&amp;key2=val2'/>
            <meta content='application/x-shockwave-flash' property='og:video:type'>
            <meta content='Foo' property=og:foobar>
            <meta name="og:test1" content='foo > < bar'/>
            <meta name="og:test2" content="foo >//< bar"/>
            '''
        self.assertEqual(ie._og_search_title(html), 'Foo')
        self.assertEqual(ie._og_search_description(html), 'Some video\'s description ')
        self.assertEqual(ie._og_search_thumbnail(html), 'http://domain.com/pic.jpg?key1=val1&key2=val2')
        self.assertEqual(ie._og_search_video_url(html, default=None), None)
        self.assertEqual(ie._og_search_property('foobar', html), 'Foo')
        self.assertEqual(ie._og_search_property('test1', html), 'foo > < bar')
        self.assertEqual(ie._og_search_property('test2', html), 'foo >//< bar')
        self.assertEqual(ie._og_search_property(('test0', 'test1'), html), 'foo > < bar')
        self.assertRaises(RegexNotFoundError, ie._og_search_property, 'test0', html, None, fatal=True)
        self.assertRaises(RegexNotFoundError, ie._og_search_property, ('test0', 'test00'), html, None, fatal=True)

    def test_html_search_meta(self):
        ie = self.ie
        html = '''
            <meta name="a" content="1" />
            <meta name='b' content='2'>
            <meta name="c" content='3'>
            <meta name=d content='4'>
            <meta property="e" content='5' >
            <meta content="6" name="f">
        '''

        self.assertEqual(ie._html_search_meta('a', html), '1')
        self.assertEqual(ie._html_search_meta('b', html), '2')
        self.assertEqual(ie._html_search_meta('c', html), '3')
        self.assertEqual(ie._html_search_meta('d', html), '4')
        self.assertEqual(ie._html_search_meta('e', html), '5')
        self.assertEqual(ie._html_search_meta('f', html), '6')
        self.assertEqual(ie._html_search_meta(('a', 'b', 'c'), html), '1')
        self.assertEqual(ie._html_search_meta(('c', 'b', 'a'), html), '3')
        self.assertEqual(ie._html_search_meta(('z', 'x', 'c'), html), '3')
        self.assertRaises(RegexNotFoundError, ie._html_search_meta, 'z', html, None, fatal=True)
        self.assertRaises(RegexNotFoundError, ie._html_search_meta, ('z', 'x'), html, None, fatal=True)

    def test_download_json(self):
        uri = encode_data_uri(b'{"foo": "blah"}', 'application/json')
        self.assertEqual(self.ie._download_json(uri, None), {'foo': 'blah'})
        uri = encode_data_uri(b'callback({"foo": "blah"})', 'application/javascript')
        self.assertEqual(self.ie._download_json(uri, None, transform_source=strip_jsonp), {'foo': 'blah'})
        uri = encode_data_uri(b'{"foo": invalid}', 'application/json')
        self.assertRaises(ExtractorError, self.ie._download_json, uri, None)
        self.assertEqual(self.ie._download_json(uri, None, fatal=False), None)

    def test_extract_jwplayer_data_realworld(self):
        # from http://www.suffolk.edu/sjc/
        expect_dict(
            self,
            self.ie._extract_jwplayer_data(r'''
                <script type='text/javascript'>
                    jwplayer('my-video').setup({
                        file: 'rtmp://192.138.214.154/live/sjclive',
                        fallback: 'true',
                        width: '95%',
                      aspectratio: '16:9',
                      primary: 'flash',
                      mediaid:'XEgvuql4'
                    });
                </script>
                ''', None, require_title=False),
            {
                'id': 'XEgvuql4',
                'formats': [{
                    'url': 'rtmp://192.138.214.154/live/sjclive',
                    'ext': 'flv'
                }]
            })

        # from https://www.pornoxo.com/videos/7564/striptease-from-sexy-secretary/
        expect_dict(
            self,
            self.ie._extract_jwplayer_data(r'''
<script type="text/javascript">
    jwplayer("mediaplayer").setup({
        'videoid': "7564",
        'width': "100%",
        'aspectratio': "16:9",
        'stretching': "exactfit",
        'autostart': 'false',
        'flashplayer': "https://t04.vipstreamservice.com/jwplayer/v5.10/player.swf",
        'file': "https://cdn.pornoxo.com/key=MF+oEbaxqTKb50P-w9G3nA,end=1489689259,ip=104.199.146.27/ip=104.199.146.27/speed=6573765/buffer=3.0/2009-12/4b2157147afe5efa93ce1978e0265289c193874e02597.flv",
        'image': "https://t03.vipstreamservice.com/thumbs/pxo-full/2009-12/14/a4b2157147afe5efa93ce1978e0265289c193874e02597.flv-full-13.jpg",
        'filefallback': "https://cdn.pornoxo.com/key=9ZPsTR5EvPLQrBaak2MUGA,end=1489689259,ip=104.199.146.27/ip=104.199.146.27/speed=6573765/buffer=3.0/2009-12/m_4b2157147afe5efa93ce1978e0265289c193874e02597.mp4",
        'logo.hide': true,
        'skin': "https://t04.vipstreamservice.com/jwplayer/skin/modieus-blk.zip",
        'plugins': "https://t04.vipstreamservice.com/jwplayer/dock/dockableskinnableplugin.swf",
        'dockableskinnableplugin.piclink': "/index.php?key=ajax-videothumbsn&vid=7564&data=2009-12--14--4b2157147afe5efa93ce1978e0265289c193874e02597.flv--17370",
        'controlbar': 'bottom',
        'modes': [
            {type: 'flash', src: 'https://t04.vipstreamservice.com/jwplayer/v5.10/player.swf'}
        ],
        'provider': 'http'
    });
    //noinspection JSAnnotator
    invideo.setup({
        adsUrl: "/banner-iframe/?zoneId=32",
        adsUrl2: "",
        autostart: false
    });
</script>
            ''', 'dummy', require_title=False),
            {
                'thumbnail': 'https://t03.vipstreamservice.com/thumbs/pxo-full/2009-12/14/a4b2157147afe5efa93ce1978e0265289c193874e02597.flv-full-13.jpg',
                'formats': [{
                    'url': 'https://cdn.pornoxo.com/key=MF+oEbaxqTKb50P-w9G3nA,end=1489689259,ip=104.199.146.27/ip=104.199.146.27/speed=6573765/buffer=3.0/2009-12/4b2157147afe5efa93ce1978e0265289c193874e02597.flv',
                    'ext': 'flv'
                }]
            })

        # from http://www.indiedb.com/games/king-machine/videos
        expect_dict(
            self,
            self.ie._extract_jwplayer_data(r'''
<script>
jwplayer("mediaplayer").setup({"abouttext":"Visit Indie DB","aboutlink":"http:\/\/www.indiedb.com\/","displaytitle":false,"autostart":false,"repeat":false,"title":"king machine trailer 1","sharing":{"link":"http:\/\/www.indiedb.com\/games\/king-machine\/videos\/king-machine-trailer-1","code":"<iframe width=\"560\" height=\"315\" src=\"http:\/\/www.indiedb.com\/media\/iframe\/1522983\" frameborder=\"0\" allowfullscreen><\/iframe><br><a href=\"http:\/\/www.indiedb.com\/games\/king-machine\/videos\/king-machine-trailer-1\">king machine trailer 1 - Indie DB<\/a>"},"related":{"file":"http:\/\/rss.indiedb.com\/media\/recommended\/1522983\/feed\/rss.xml","dimensions":"160x120","onclick":"link"},"sources":[{"file":"http:\/\/cdn.dbolical.com\/cache\/videos\/games\/1\/50\/49678\/encode_mp4\/king-machine-trailer.mp4","label":"360p SD","default":"true"},{"file":"http:\/\/cdn.dbolical.com\/cache\/videos\/games\/1\/50\/49678\/encode720p_mp4\/king-machine-trailer.mp4","label":"720p HD"}],"image":"http:\/\/media.indiedb.com\/cache\/images\/games\/1\/50\/49678\/thumb_620x2000\/king-machine-trailer.mp4.jpg","advertising":{"client":"vast","tag":"http:\/\/ads.intergi.com\/adrawdata\/3.0\/5205\/4251742\/0\/1013\/ADTECH;cors=yes;width=560;height=315;referring_url=http:\/\/www.indiedb.com\/games\/king-machine\/videos\/king-machine-trailer-1;content_url=http:\/\/www.indiedb.com\/games\/king-machine\/videos\/king-machine-trailer-1;media_id=1522983;title=king+machine+trailer+1;device=__DEVICE__;model=__MODEL__;os=Windows+OS;osversion=__OSVERSION__;ua=__UA__;ip=109.171.17.81;uniqueid=1522983;tags=__TAGS__;number=58cac25928151;time=1489683033"},"width":620,"height":349}).once("play", function(event) {
            videoAnalytics("play");
}).once("complete", function(event) {
    videoAnalytics("completed");
});
</script>
                ''', 'dummy'),
            {
                'title': 'king machine trailer 1',
                'thumbnail': 'http://media.indiedb.com/cache/images/games/1/50/49678/thumb_620x2000/king-machine-trailer.mp4.jpg',
                'formats': [{
                    'url': 'http://cdn.dbolical.com/cache/videos/games/1/50/49678/encode_mp4/king-machine-trailer.mp4',
                    'height': 360,
                    'ext': 'mp4'
                }, {
                    'url': 'http://cdn.dbolical.com/cache/videos/games/1/50/49678/encode720p_mp4/king-machine-trailer.mp4',
                    'height': 720,
                    'ext': 'mp4'
                }]
            })


if __name__ == '__main__':
    unittest.main()
