# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import float_or_none


class AudioBoomIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audioboom\.com/(?:boos|posts)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://audioboom.com/boos/4279833-3-09-2016-czaban-hour-3?t=0',
        'md5': '63a8d73a055c6ed0f1e51921a10a5a76',
        'info_dict': {
            'id': '4279833',
            'ext': 'mp3',
            'title': '3/09/2016 Czaban Hour 3',
            'description': 'Guest:   Nate Davis - NFL free agency,   Guest:   Stan Gans',
            'duration': 2245.72,
            'uploader': 'SB Nation A.M.',
            'uploader_url': r're:https?://(?:www\.)?audioboom\.com/channel/steveczabanyahoosportsradio',
        }
    }, {
        'url': 'https://audioboom.com/posts/4279833-3-09-2016-czaban-hour-3?t=0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        clip = None

        clip_store = self._parse_json(
            self._search_regex(
                r'data-new-clip-store=(["\'])(?P<json>{.*?"clipId"\s*:\s*%s.*?})\1' % video_id,
                webpage, 'clip store', default='{}', group='json'),
            video_id, fatal=False)
        if clip_store:
            clips = clip_store.get('clips')
            if clips and isinstance(clips, list) and isinstance(clips[0], dict):
                clip = clips[0]

        def from_clip(field):
            if clip:
                clip.get(field)

        audio_url = from_clip('clipURLPriorToLoading') or self._og_search_property(
            'audio', webpage, 'audio url')
        title = from_clip('title') or self._og_search_title(webpage)
        description = from_clip('description') or self._og_search_description(webpage)

        duration = float_or_none(from_clip('duration') or self._html_search_meta(
            'weibo:audio:duration', webpage))

        uploader = from_clip('author') or self._og_search_property(
            'audio:artist', webpage, 'uploader', fatal=False)
        uploader_url = from_clip('author_url') or self._html_search_meta(
            'audioboo:channel', webpage, 'uploader url')

        return {
            'id': video_id,
            'url': audio_url,
            'title': title,
            'description': description,
            'duration': duration,
            'uploader': uploader,
            'uploader_url': uploader_url,
        }
