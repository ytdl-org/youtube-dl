from __future__ import unicode_literals

import hashlib
import hmac
import re
import time

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    js_to_json,
    int_or_none,
    parse_iso8601,
    try_get,
    unescapeHTML,
    update_url_query,
)


class ABCIE(InfoExtractor):
    IE_NAME = 'abc.net.au'
    _VALID_URL = r'https?://(?:www\.)?abc\.net\.au/news/(?:[^/]+/){1,2}(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.abc.net.au/news/2014-11-05/australia-to-staff-ebola-treatment-centre-in-sierra-leone/5868334',
        'md5': 'cb3dd03b18455a661071ee1e28344d9f',
        'info_dict': {
            'id': '5868334',
            'ext': 'mp4',
            'title': 'Australia to help staff Ebola treatment centre in Sierra Leone',
            'description': 'md5:809ad29c67a05f54eb41f2a105693a67',
        },
        'skip': 'this video has expired',
    }, {
        'url': 'http://www.abc.net.au/news/2015-08-17/warren-entsch-introduces-same-sex-marriage-bill/6702326',
        'md5': 'db2a5369238b51f9811ad815b69dc086',
        'info_dict': {
            'id': 'NvqvPeNZsHU',
            'ext': 'mp4',
            'upload_date': '20150816',
            'uploader': 'ABC News (Australia)',
            'description': 'Government backbencher Warren Entsch introduces a cross-party sponsored bill to legalise same-sex marriage, saying the bill is designed to promote "an inclusive Australia, not a divided one.". Read more here: http://ab.co/1Mwc6ef',
            'uploader_id': 'NewsOnABC',
            'title': 'Marriage Equality: Warren Entsch introduces same sex marriage bill',
        },
        'add_ie': ['Youtube'],
        'skip': 'Not accessible from Travis CI server',
    }, {
        'url': 'http://www.abc.net.au/news/2015-10-23/nab-lifts-interest-rates-following-westpac-and-cba/6880080',
        'md5': 'b96eee7c9edf4fc5a358a0252881cc1f',
        'info_dict': {
            'id': '6880080',
            'ext': 'mp3',
            'title': 'NAB lifts interest rates, following Westpac and CBA',
            'description': 'md5:f13d8edc81e462fce4a0437c7dc04728',
        },
    }, {
        'url': 'http://www.abc.net.au/news/2015-10-19/6866214',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(
            r'inline(?P<type>Video|Audio|YouTube)Data\.push\((?P<json_data>[^)]+)\);',
            webpage)
        if mobj is None:
            expired = self._html_search_regex(r'(?s)class="expired-(?:video|audio)".+?<span>(.+?)</span>', webpage, 'expired', None)
            if expired:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, expired), expected=True)
            raise ExtractorError('Unable to extract video urls')

        urls_info = self._parse_json(
            mobj.group('json_data'), video_id, transform_source=js_to_json)

        if not isinstance(urls_info, list):
            urls_info = [urls_info]

        if mobj.group('type') == 'YouTube':
            return self.playlist_result([
                self.url_result(url_info['url']) for url_info in urls_info])

        formats = [{
            'url': url_info['url'],
            'vcodec': url_info.get('codec') if mobj.group('type') == 'Video' else 'none',
            'width': int_or_none(url_info.get('width')),
            'height': int_or_none(url_info.get('height')),
            'tbr': int_or_none(url_info.get('bitrate')),
            'filesize': int_or_none(url_info.get('filesize')),
        } for url_info in urls_info]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }


class ABCIViewIE(InfoExtractor):
    IE_NAME = 'abc.net.au:iview'
    _VALID_URL = r'https?://iview\.abc\.net\.au/(?:[^/]+/)*video/(?P<id>[^/?#]+)'
    _GEO_COUNTRIES = ['AU']

    # ABC iview programs are normally available for 14 days only.
    _TESTS = [{
        'url': 'https://iview.abc.net.au/show/ben-and-hollys-little-kingdom/series/0/video/ZX9371A050S00',
        'md5': 'cde42d728b3b7c2b32b1b94b4a548afc',
        'info_dict': {
            'id': 'ZX9371A050S00',
            'ext': 'mp4',
            'title': "Gaston's Birthday",
            'series': "Ben And Holly's Little Kingdom",
            'description': 'md5:f9de914d02f226968f598ac76f105bcf',
            'upload_date': '20180604',
            'uploader_id': 'abc4kids',
            'timestamp': 1528140219,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_params = self._download_json(
            'https://iview.abc.net.au/api/programs/' + video_id, video_id)
        title = unescapeHTML(video_params.get('title') or video_params['seriesTitle'])
        stream = next(s for s in video_params['playlist'] if s.get('type') in ('program', 'livestream'))

        house_number = video_params.get('episodeHouseNumber') or video_id
        path = '/auth/hls/sign?ts={0}&hn={1}&d=android-tablet'.format(
            int(time.time()), house_number)
        sig = hmac.new(
            b'android.content.res.Resources',
            path.encode('utf-8'), hashlib.sha256).hexdigest()
        token = self._download_webpage(
            'http://iview.abc.net.au{0}&sig={1}'.format(path, sig), video_id)

        def tokenize_url(url, token):
            return update_url_query(url, {
                'hdnea': token,
            })

        for sd in ('sd', 'sd-low'):
            sd_url = try_get(
                stream, lambda x: x['streams']['hls'][sd], compat_str)
            if not sd_url:
                continue
            formats = self._extract_m3u8_formats(
                tokenize_url(sd_url, token), video_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
            if formats:
                break
        self._sort_formats(formats)

        subtitles = {}
        src_vtt = stream.get('captions', {}).get('src-vtt')
        if src_vtt:
            subtitles['en'] = [{
                'url': src_vtt,
                'ext': 'vtt',
            }]

        is_live = video_params.get('livestream') == '1'
        if is_live:
            title = self._live_title(title)

        return {
            'id': video_id,
            'title': title,
            'description': video_params.get('description'),
            'thumbnail': video_params.get('thumbnail'),
            'duration': int_or_none(video_params.get('eventDuration')),
            'timestamp': parse_iso8601(video_params.get('pubDate'), ' '),
            'series': unescapeHTML(video_params.get('seriesTitle')),
            'series_id': video_params.get('seriesHouseNumber') or video_id[:7],
            'season_number': int_or_none(self._search_regex(
                r'\bSeries\s+(\d+)\b', title, 'season number', default=None)),
            'episode_number': int_or_none(self._search_regex(
                r'\bEp\s+(\d+)\b', title, 'episode number', default=None)),
            'episode_id': house_number,
            'uploader_id': video_params.get('channel'),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
        }
