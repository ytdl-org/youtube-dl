# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    float_or_none,
    int_or_none,
    try_get,
    # unified_timestamp,
    ExtractorError,
)


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redbull\.tv/(?:video|film|live)/(?:AP-\w+/segment/)?(?P<id>AP-\w+)'
    _TESTS = [{
        # film
        'url': 'https://www.redbull.tv/video/AP-1Q756YYX51W11/abc-of-wrc',
        'md5': 'fb0445b98aa4394e504b413d98031d1f',
        'info_dict': {
            'id': 'AP-1Q756YYX51W11',
            'ext': 'mp4',
            'title': 'ABC of...WRC',
            'description': 'md5:5c7ed8f4015c8492ecf64b6ab31e7d31',
            'duration': 1582.04,
            # 'timestamp': 1488405786,
            # 'upload_date': '20170301',
        },
    }, {
        # episode
        'url': 'https://www.redbull.tv/video/AP-1PMT5JCWH1W11/grime?playlist=shows:shows-playall:web',
        'info_dict': {
            'id': 'AP-1PMT5JCWH1W11',
            'ext': 'mp4',
            'title': 'Grime - Hashtags S2 E4',
            'description': 'md5:334b741c8c1ce65be057eab6773c1cf5',
            'duration': 904.6,
            # 'timestamp': 1487290093,
            # 'upload_date': '20170217',
            'series': 'Hashtags',
            'season_number': 2,
            'episode_number': 4,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # segment
        'url': 'https://www.redbull.tv/live/AP-1R5DX49XS1W11/segment/AP-1QSAQJ6V52111/semi-finals',
        'info_dict': {
            'id': 'AP-1QSAQJ6V52111',
            'ext': 'mp4',
            'title': 'Semi Finals - Vans Park Series Pro Tour',
            'description': 'md5:306a2783cdafa9e65e39aa62f514fd97',
            'duration': 11791.991,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.redbull.tv/film/AP-1MSKKF5T92111/in-motion',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        session = self._download_json(
            'https://api-v2.redbull.tv/session', video_id,
            note='Downloading access token', query={
                'build': '4.370.0',
                'category': 'personal_computer',
                'os_version': '1.0',
                'os_family': 'http',
            })
        if session.get('code') == 'error':
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, session['message']))
        auth = '%s %s' % (session.get('token_type', 'Bearer'), session['access_token'])

        try:
            info = self._download_json(
                'https://api-v2.redbull.tv/content/%s' % video_id,
                video_id, note='Downloading video information',
                headers={'Authorization': auth}
            )
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                error_message = self._parse_json(
                    e.cause.read().decode(), video_id)['message']
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error_message), expected=True)
            raise

        video = info['video_product']

        title = info['title'].strip()

        formats = self._extract_m3u8_formats(
            video['url'], video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')
        self._sort_formats(formats)

        subtitles = {}
        for _, captions in (try_get(
                video, lambda x: x['attachments']['captions'],
                dict) or {}).items():
            if not captions or not isinstance(captions, list):
                continue
            for caption in captions:
                caption_url = caption.get('url')
                if not caption_url:
                    continue
                ext = caption.get('format')
                if ext == 'xml':
                    ext = 'ttml'
                subtitles.setdefault(caption.get('lang') or 'en', []).append({
                    'url': caption_url,
                    'ext': ext,
                })

        subheading = info.get('subheading')
        if subheading:
            title += ' - %s' % subheading

        return {
            'id': video_id,
            'title': title,
            'description': info.get('long_description') or info.get(
                'short_description'),
            'duration': float_or_none(video.get('duration'), scale=1000),
            # 'timestamp': unified_timestamp(info.get('published')),
            'series': info.get('show_title'),
            'season_number': int_or_none(info.get('season_number')),
            'episode_number': int_or_none(info.get('episode_number')),
            'formats': formats,
            'subtitles': subtitles,
        }
