from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    unified_timestamp,
)


class BeegIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beeg\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://beeg.com/5416503',
        'md5': 'a1a1b1a8bc70a89e49ccfd113aed0820',
        'info_dict': {
            'id': '5416503',
            'ext': 'mp4',
            'title': 'Sultry Striptease',
            'description': 'md5:d22219c09da287c14bed3d6c37ce4bc2',
            'timestamp': 1391813355,
            'upload_date': '20140207',
            'duration': 383,
            'tags': list,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        beeg_version = self._search_regex(
            r'beeg_version\s*=\s*([\da-zA-Z_-]+)', webpage, 'beeg version',
            default='1546225636701')

        for api_path in ('', 'api.'):
            video = self._download_json(
                'https://%sbeeg.com/api/v6/%s/video/%s'
                % (api_path, beeg_version, video_id), video_id,
                fatal=api_path == 'api.')
            if video:
                break

        formats = []
        for format_id, video_url in video.items():
            if not video_url:
                continue
            height = self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)
            if not height:
                continue
            formats.append({
                'url': self._proto_relative_url(
                    video_url.replace('{DATA_MARKERS}', 'data=pc_XX__%s_0' % beeg_version), 'https:'),
                'format_id': format_id,
                'height': int(height),
            })
        self._sort_formats(formats)

        title = video['title']
        video_id = compat_str(video.get('id') or video_id)
        display_id = video.get('code')
        description = video.get('desc')
        series = video.get('ps_name')

        timestamp = unified_timestamp(video.get('date'))
        duration = int_or_none(video.get('duration'))

        tags = [tag.strip() for tag in video['tags'].split(',')] if video.get('tags') else None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'series': series,
            'timestamp': timestamp,
            'duration': duration,
            'tags': tags,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
        }
