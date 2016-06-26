# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    unescapeHTML,
)


class MSNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?msn\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/[a-z]{2}-(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'http://www.msn.com/en-ae/foodanddrink/joinourtable/criminal-minds-shemar-moore-shares-a-touching-goodbye-message/vp-BBqQYNE',
        'md5': '8442f66c116cbab1ff7098f986983458',
        'info_dict': {
            'id': 'BBqQYNE',
            'display_id': 'criminal-minds-shemar-moore-shares-a-touching-goodbye-message',
            'ext': 'mp4',
            'title': 'Criminal Minds - Shemar Moore Shares A Touching Goodbye Message',
            'description': 'md5:e8e89b897b222eb33a6b5067a8f1bc25',
            'duration': 104,
            'uploader': 'CBS Entertainment',
            'uploader_id': 'IT0X5aoJ6bJgYerJXSDCgFmYPB1__54v',
        },
    }, {
        'url': 'http://www.msn.com/en-ae/news/offbeat/meet-the-nine-year-old-self-made-millionaire/ar-BBt6ZKf',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/video/watch/obama-a-lot-of-people-will-be-disappointed/vi-AAhxUMH',
        'only_matching': True,
    }, {
        # geo restricted
        'url': 'http://www.msn.com/en-ae/foodanddrink/joinourtable/the-first-fart-makes-you-laugh-the-last-fart-makes-you-cry/vp-AAhzIBU',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/entertainment/bollywood/watch-how-salman-khan-reacted-when-asked-if-he-would-apologize-for-his-‘raped-woman’-comment/vi-AAhvzW6',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, display_id = mobj.group('id', 'display_id')

        webpage = self._download_webpage(url, display_id)

        video = self._parse_json(
            self._search_regex(
                r'data-metadata\s*=\s*(["\'])(?P<data>.+?)\1',
                webpage, 'video data', default='{}', group='data'),
            display_id, transform_source=unescapeHTML)

        if not video:
            error = unescapeHTML(self._search_regex(
                r'data-error=(["\'])(?P<error>.+?)\1',
                webpage, 'error', group='error'))
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error), expected=True)

        title = video['title']

        formats = []
        for file_ in video.get('videoFiles', []):
            format_url = file_.get('url')
            if not format_url:
                continue
            ext = determine_ext(format_url)
            # .ism is not yet supported (see
            # https://github.com/rg3/youtube-dl/issues/8118)
            if ext == 'ism':
                continue
            if 'm3u8' in format_url:
                # m3u8_native should not be used here until
                # https://github.com/rg3/youtube-dl/issues/9913 is fixed
                m3u8_formats = self._extract_m3u8_formats(
                    format_url, display_id, 'mp4',
                    m3u8_id='hls', fatal=False)
                # Despite metadata in m3u8 all video+audio formats are
                # actually video-only (no audio)
                for f in m3u8_formats:
                    if f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        f['acodec'] = 'none'
                formats.extend(m3u8_formats)
            else:
                formats.append({
                    'url': format_url,
                    'ext': 'mp4',
                    'format_id': 'http',
                    'width': int_or_none(file_.get('width')),
                    'height': int_or_none(file_.get('height')),
                })
        self._sort_formats(formats)

        subtitles = {}
        for file_ in video.get('files', []):
            format_url = file_.get('url')
            format_code = file_.get('formatCode')
            if not format_url or not format_code:
                continue
            if compat_str(format_code) == '3100':
                subtitles.setdefault(file_.get('culture', 'en'), []).append({
                    'ext': determine_ext(format_url, 'ttml'),
                    'url': format_url,
                })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': video.get('headlineImage', {}).get('url'),
            'duration': int_or_none(video.get('durationSecs')),
            'uploader': video.get('sourceFriendly'),
            'uploader_id': video.get('providerId'),
            'creator': video.get('creator'),
            'subtitles': subtitles,
            'formats': formats,
        }
