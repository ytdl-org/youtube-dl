# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import RegexNotFoundError
import json
import time


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redbull\.com/[^/]+/(?:videos|recap-videos|events|episodes|films)/(?P<id>AP-\w+)(?:/live/AP-\w+)?(?:\?playlist)?(?:\?playlistId=rrn:content:collections:[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}:[\w-]+)?'
    _TESTS = [{
        # videos
        'url': 'https://www.redbull.com/int-en/videos/AP-1YM911N612111',
        'md5': 'e2d92baecce184ecd521fa3d72f36aa8',
        'info_dict': {
            'id': 'AP-1YM911N612111',
            'ext': 'mp4',
            'title': 'Preview the Lenzerheide DH course with Gee Atherton\'s POV',
            'description': 'md5:99b46ed1e2abb02c4c6f6113cff13ba4',
        },
    }, {
        # recap-videos
        'url': 'https://www.redbull.com/int-en/recap-videos/AP-1YM8YXTC52111?playlistId=rrn:content:collections:e916768e-7b47-413d-a254-bc97d7f808f7:en-INT',
        'md5': 'aa7c6ab92ea6103f61d5fc5cbb85fd53',
        'info_dict': {
            'id': 'AP-1YM8YXTC52111',
            'ext': 'mp4',
            'title': 'Val di Sole DH recap',
            'description': 'md5:df0fd44b4d1a396a692998fc395b75b8',
        },
    }, {
        # events
        'url': 'https://www.redbull.com/int-en/recap-videos/AP-1ZYQN7WNW2111',
        'md5': '0f2043deef92405249c8ca96ba197901',
        'info_dict': {
            'id': 'AP-1ZYQN7WNW2111',
            'ext': 'mp4',
            'title': 'Jokkis Race',
            'description': 'md5:dc2be9d7b3e7048967468d39a889a5e1',
        },
    }, {
        # episodes
        'url': 'https://www.redbull.com/int-en/episodes/AP-1PMHKJFCW1W11',
        'md5': 'db8271a7200d40053a1809ed0dd574ff',
        'info_dict': {
            'id': 'AP-1PMHKJFCW1W11',
            'ext': 'mp4',
            'title': 'Grime',
            'description': 'md5:7b4bdf2edd53d6c0c5e2e336c02e6fbb',
        },
    }, {
        # films
        'url': 'https://www.redbull.com/int-en/films/AP-1ZSMAW8FH2111',
        'md5': '3a753f7c3c1f9966ae660e05c3c7862b',
        'info_dict': {
            'id': 'AP-1ZSMAW8FH2111',
            'ext': 'mp4',
            'title': 'Against the Odds',
            'description': 'md5:6db1cf4c4f85442a91f4d9cd03b7f4e3',
        },
    }]

    def _real_extract(self, url):
        # video_id is "AP-..." ID
        video_id = self._match_id(url)

        # Try downloading the webpage multiple times in order to get a repsonse
        # cache which will contain the result of a query to 
        # 'https://www.redbull.com/v3/api/composition/v3/query/en-INT?rb3Schema=v1:pageConfig&filter[uriSlug]=%s' % video_id
        # We use the response cache to get the rrn ID and other metadata. We do
        # this instead of simply querying the API in order to preserve the
        # provided URL's locale. (Annoyingly, the locale in the input URL 
        # ('en-us', for example) is of a different format than the locale
        # required for the API request.)
        tries = 3
        for i in range(tries):
            try:
                if i == 0:
                    webpage = self._download_webpage(url, video_id)
                else:
                    webpage = self._download_webpage(url, video_id, note='Redownloading webpage')
                # extract response cache
                response_cache = json.loads(self._html_search_regex(r'<script type="application/json" id="response-cache">(.+?)</script>', webpage, 'response-cache'))
                break
            except RegexNotFoundError:
                if i < tries - 1:
                    self.to_screen('Waiting before redownloading webpage')
                    time.sleep(2)
                else:
                    raise

        # select the key that includes the string 'pageConfig'
        metadata = json.loads(
                response_cache[
                    [key for key in response_cache.keys() if 'pageConfig' in key][0]
                ]['response']
            )['data']

        # extract rrn ID
        rrn_id_ext = metadata['analytics']['asset']['trackingDimensions']['masterID']
        # trim locale from the end of rrn_id_ext
        rrn_id = ':'.join(rrn_id_ext.split(':')[:-1])

        # extract metadata
        title = metadata['analytics']['asset']['title']
        short_description = metadata['pageMeta']['og:title']
        long_description = metadata['pageMeta']['og:description']

        # get access token for download
        session = self._download_json(
            'https://api.redbull.tv/v3/session', video_id,
            note='Downloading access token', query={
                'category': 'personal_computer',
                'os_family': 'http',
            })
        if session.get('code') == 'error':
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, session['message']))
        token = session['token']

        formats = self._extract_m3u8_formats(
            'https://dms.redbull.tv/v3/%s/%s/playlist.m3u8' % (rrn_id, token),
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': long_description or short_description,
            'formats': formats,
        }
