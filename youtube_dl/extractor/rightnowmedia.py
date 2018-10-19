from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext
)

class RightNowMediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rightnowmedia\.org/Content/(?:VideoElement|Series|KidsShow)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.rightnowmedia.org/Content/VideoElement/231113',
        'info_dict': {
            'id': '231113',
            'ext': 'mp4',
            'title': 'Augustana (S.D.) Baseball vs University of Mary',
            'description': 'md5:7578478614aae3bdd4a90f578f787438',
            'timestamp': 1490468400,
            'upload_date': '20170325',
        }
    }

    def _real_extract(self, url):
    
        # Video Id
        video_id = self._match_id(url)
        # Download
        video_info_dicts = self._download_json(
            'https://www.rightnowmedia.org/Content/%s/downloadAndEmbed'
            % video_id, video_id)

        video_url = 'https://%s' % video_info_dicts['downloadLinks']
        formats = []
        
        
        
        for video_info in video_info_dicts['downloadLinks']:
            video_url = video_info.get('src')
            quality = 'high' if 'HD 1080p' in video_info["QualityName"] else 'low'
            formats.append({
                'url': video_info["Link"],
                'preference': 10 if quality == 'high' else 0,
                'format_note': quality,
                'format_id': '%s-%s' % (quality, determine_ext(video_info["Link"])),
            })
        self._sort_formats(formats)

        title = "Test 01"
        description = "aaaa"

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
