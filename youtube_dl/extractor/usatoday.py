# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    get_element_by_attribute,
    parse_duration,
    update_url_query,
    ExtractorError,
)
from ..compat import compat_str


class USATodayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?usatoday\.com/(?:[^/]+/)*(?P<id>[^?/#]+)'
    _TEST = {
        'url': 'http://www.usatoday.com/media/cinematic/video/81729424/us-france-warn-syrian-regime-ahead-of-new-peace-talks/',
        'md5': '4d40974481fa3475f8bccfd20c5361f8',
        'info_dict': {
            'id': '81729424',
            'ext': 'mp4',
            'title': 'US, France warn Syrian regime ahead of new peace talks',
            'timestamp': 1457891045,
            'description': 'md5:7e50464fdf2126b0f533748d3c78d58f',
            'uploader_id': '29906170001',
            'upload_date': '20160313',
        }
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/29906170001/38a9eecc-bdd8-42a3-ba14-95397e48b3f8_default/index.html?videoId=%s'

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(update_url_query(url, {'ajax': 'true'}), display_id)
        ui_video_data = get_element_by_attribute('class', 'ui-video-data', webpage)
        if not ui_video_data:
            raise ExtractorError('no video on the webpage', expected=True)
        video_data = self._parse_json(ui_video_data, display_id)

        return {
            '_type': 'url_transparent',
            'url': self.BRIGHTCOVE_URL_TEMPLATE % video_data['brightcove_id'],
            'id': compat_str(video_data['id']),
            'title': video_data['title'],
            'thumbnail': video_data.get('thumbnail'),
            'description': video_data.get('description'),
            'duration': parse_duration(video_data.get('length')),
            'ie_key': 'BrightcoveNew',
        }
