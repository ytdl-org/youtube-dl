# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    try_get,
    unified_timestamp,
)


class RedBullTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redbull\.tv/(?:video|film)/(?P<id>AP-\w+)'
    _TESTS = [{
        # film
        'url': 'https://www.redbull.tv/video/AP-1Q756YYX51W11/abc-of-wrc',
        'md5': '78e860f631d7a846e712fab8c5fe2c38',
        'info_dict': {
            'id': 'AP-1Q756YYX51W11',
            'ext': 'mp4',
            'title': 'ABC of...WRC',
            'description': 'md5:5c7ed8f4015c8492ecf64b6ab31e7d31',
            'duration': 1582.04,
            'timestamp': 1488405786,
            'upload_date': '20170301',
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
            'timestamp': 1487290093,
            'upload_date': '20170217',
            'series': 'Hashtags',
            'season_number': 2,
            'episode_number': 4,
        },
    }, {
        'url': 'https://www.redbull.tv/film/AP-1MSKKF5T92111/in-motion',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        access_token = self._download_json(
            'https://api-v2.redbull.tv/start', video_id,
            note='Downloading access token', query={
                'build': '4.0.9',
                'category': 'smartphone',
                'os_version': 23,
                'os_family': 'android',
            })['auth']['access_token']

        info = self._download_json(
            'https://api-v2.redbull.tv/views/%s' % video_id,
            video_id, note='Downloading video information',
            headers={'Authorization': 'Bearer ' + access_token}
        )['blocks'][0]['top'][0]

        video = info['video_product']

        title = info['title'].strip()
        m3u8_url = video['url']

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

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
                subtitles.setdefault(caption.get('lang') or 'en', []).append({
                    'url': caption_url,
                    'ext': caption.get('format'),
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
            'timestamp': unified_timestamp(info.get('published')),
            'series': info.get('show_title'),
            'season_number': int_or_none(info.get('season_number')),
            'episode_number': int_or_none(info.get('episode_number')),
            'formats': formats,
            'subtitles': subtitles,
        }
