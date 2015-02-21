from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
    str_to_int,
)


class AdobeTVIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.adobe\.com/watch/[^/]+/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://tv.adobe.com/watch/the-complete-picture-with-julieanne-kost/quick-tip-how-to-draw-a-circle-around-an-object-in-photoshop/',
        'md5': '9bc5727bcdd55251f35ad311ca74fa1e',
        'info_dict': {
            'id': 'quick-tip-how-to-draw-a-circle-around-an-object-in-photoshop',
            'ext': 'mp4',
            'title': 'Quick Tip - How to Draw a Circle Around an Object in Photoshop',
            'description': 'md5:99ec318dc909d7ba2a1f2b038f7d2311',
            'thumbnail': 're:https?://.*\.jpg$',
            'upload_date': '20110914',
            'duration': 60,
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        player = self._parse_json(
            self._search_regex(r'html5player:\s*({.+?})\s*\n', webpage, 'player'),
            video_id)

        title = player.get('title') or self._search_regex(
            r'data-title="([^"]+)"', webpage, 'title')
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(
            self._html_search_meta('datepublished', webpage, 'upload date'))

        duration = parse_duration(
            self._html_search_meta('duration', webpage, 'duration')
            or self._search_regex(r'Runtime:\s*(\d{2}:\d{2}:\d{2})', webpage, 'duration'))

        view_count = str_to_int(self._search_regex(
            r'<div class="views">\s*Views?:\s*([\d,.]+)\s*</div>',
            webpage, 'view count'))

        formats = [{
            'url': source['src'],
            'format_id': source.get('quality') or source['src'].split('-')[-1].split('.')[0] or None,
            'tbr': source.get('bitrate'),
        } for source in player['sources']]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
