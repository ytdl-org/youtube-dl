# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    RegexNotFoundError,
    ExtractorError,
    try_get,
    float_or_none,
    unified_strdate,
)
import json
import time


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r"""(?x)^
                     https?://
                     (?:www\.)?redbull\.com/
                     [^/]+/                                                   # locale/language code
                     (?:videos|recap-videos|events|episodes|films)/
                     (?P<id>AP-\w{13})(?:/live/AP-\w{13})?
                     (?:\?playlist)?(?:\?playlistId=rrn:content:collections:[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}:[\w-]+)?
                     $"""
    _TESTS = [{
        # videos
        'url': 'https://www.redbull.com/int-en/videos/AP-1YM911N612111',
        'md5': 'e2d92baecce184ecd521fa3d72f36aa8',
        'info_dict': {
            'id': 'AP-1YM911N612111',
            'ext': 'mp4',
            'title': 'md5:fa027630eb511593fe91e4323762e95d',
            'description': 'md5:7f769874c63e45f9b6f43315a99094c7',
            'duration': 255.0,
            'release_date': '20190809',
        },
    }, {
        # recap-videos
        'url': 'https://www.redbull.com/int-en/recap-videos/AP-1YM8YXTC52111?playlistId=rrn:content:collections:e916768e-7b47-413d-a254-bc97d7f808f7:en-INT',
        'md5': 'aa7c6ab92ea6103f61d5fc5cbb85fd53',
        'info_dict': {
            'id': 'AP-1YM8YXTC52111',
            'ext': 'mp4',
            'title': 'md5:dc9aec63e687a534a6bb13adbb86571c',
            'description': 'md5:3774af48bf6fbc5fb6c8ebad6891f728',
            'duration': 1560.0,
            'release_date': '20190808',
        },
    }, {
        # events
        'url': 'https://www.redbull.com/int-en/recap-videos/AP-1ZYQN7WNW2111',
        'md5': '0f2043deef92405249c8ca96ba197901',
        'info_dict': {
            'id': 'AP-1ZYQN7WNW2111',
            'ext': 'mp4',
            'title': 'md5:c2a490a9db25823c2c9790093e3563ab',
            'description': 'md5:fb7e7a8cfaa72f7dc139238186d69800',
            'duration': 933.0,
            'release_date': '20190727',
        },
    }, {
        # episodes
        'url': 'https://www.redbull.com/int-en/episodes/AP-1PMHKJFCW1W11',
        'md5': 'db8271a7200d40053a1809ed0dd574ff',
        'info_dict': {
            'id': 'AP-1PMHKJFCW1W11',
            'ext': 'mp4',
            'title': 'md5:f767c9809c12c3411632cb7de9d30608',
            'description': 'md5:b5f522b89b72e1e23216e5018810bb25',
            'duration': 904.0,
            'release_date': '20170221',
        },
    }, {
        # films
        'url': 'https://www.redbull.com/int-en/films/AP-1ZSMAW8FH2111',
        'md5': '3a753f7c3c1f9966ae660e05c3c7862b',
        'info_dict': {
            'id': 'AP-1ZSMAW8FH2111',
            'ext': 'mp4',
            'title': 'md5:47478de1e62dadcda748c2b58ae7e343',
            'description': 'md5:9a885f6f5344b98c684f8aaf6bdfbc38',
            'duration': 4837.0,
            'release_date': '20190801',
        },
    }]

    def _real_extract(self, url):
        # video_id is 'AP-...' ID
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
                    webpage = self._download_webpage(url, video_id,
                        note='Redownloading webpage')
                # extract response cache
                response_cache = json.loads(self._html_search_regex(
                    r'<script type="application/json" id="response-cache">(.+?)</script>',
                    webpage, 'response-cache'))
            except RegexNotFoundError:
                if i < tries - 1:
                    self.to_screen('Waiting before redownloading webpage')
                    time.sleep(2)
                    continue
                else:
                    self.to_screen('Failed to download/locate response cache. Wait a few seconds and try running the command again.')
                    raise
            break

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

        # extract formats from m3u8
        # subtitle tracks are also listed in this m3u8, but yt-dl does not
        # currently implement an easy way to download m3u8 VTT subtitles
        formats = self._extract_m3u8_formats(
            'https://dms.redbull.tv/v3/%s/%s/playlist.m3u8' % (rrn_id, token),
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        # download more metadata
        metadata2 = self._download_json(
            'https://api.redbull.tv/v3/products/%s' % rrn_id,
            video_id, note='Downloading video information',
            headers={'Authorization': token}
        )

        # extract metadata
        title = try_get(metadata2, lambda x: x['title'], compat_str) or \
            try_get(metadata, lambda x: x['analytics']['asset']['title'], compat_str)

        subheading = try_get(metadata2, lambda x: x['subheading'], compat_str)
        if subheading:
            title += ' - %s' % subheading

        long_description = try_get(metadata2, lambda x: x['long_description'], compat_str)
        short_description = try_get(metadata2, lambda x: x['short_description'], compat_str) or \
            try_get(metadata, lambda x: x['pageMeta']['og:description'],
                compat_str)

        duration = float_or_none(try_get(metadata2, lambda x: x['duration'], int),
            scale=1000)

        release_dates = [try_get(metadata,
            lambda x: x['analytics']['asset']['publishDate'], compat_str)]
        release_dates.append(try_get(metadata,
            lambda x: x['analytics']['asset']['trackingDimensions']['originalPublishingDate'],
            compat_str))
        release_dates.append(try_get(metadata,
            lambda x: x['analytics']['asset']['trackingDimensions']['publishingDate'],
            compat_str))

        release_date = unified_strdate(release_dates[0] or release_dates[1] or \
            release_dates[2])

        return {
            'id': video_id,
            'title': title,
            'description': long_description or short_description,
            'duration': duration,
            'release_date': release_date,
            'formats': formats,
        }
