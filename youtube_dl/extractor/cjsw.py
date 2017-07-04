# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class CJSWIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cjsw\.com/program/\S+/(?P<id>[0-9]+)'
    IE_NAME = 'cjsw'
    _TEST = {
        'url': 'http://cjsw.com/program/freshly-squeezed/episode/20170620',
        'md5': 'cee14d40f1e9433632c56e3d14977120',
        'info_dict': {
            'id': '20170620',
            'ext': 'mp3',
            'title': 'Freshly Squeezed',
            'description': 'Sled Island artists featured // Live session with Phi Pho, followed by a live session with Sinzere & The Late Nights! // Stay Fresh Y\'all!!',
        }
    }

    def _real_extract(self, url):
        episode_id = self._match_id(url)

        webpage = self._download_webpage(url, episode_id)

        episode_controls = self._search_regex(r'<div[^>]+class=(["\'])episode-controls\1[^>]*>', webpage, 'episode_controls', fatal=False)
        if not episode_controls:
            raise ExtractorError('No streamable podcast', video_id=episode_id, expected=True)

        title = self._html_search_regex(
            r'<button[^>]+data-showname=(["\'])(?P<title>.+?)\1[^>]*>', webpage, 'title', group='title')
        description = self._html_search_regex(
            r'<p>(?P<description>.+?)</p>', webpage, 'description', fatal=False)
        formats = [{
            'url': self._html_search_regex(
                r'<button[^>]+data-audio-src=(["\'])(?P<audio_url>.+?)\1[^>]*>', webpage, 'audio_url', group='audio_url'),
            'ext': 'mp3',
            'vcodec': 'none',
        }]
        return {
            'id': episode_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
