# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_request


class DcnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dcndigital\.ae/(?:#/)?(?:video/.+|show/\d+/.+?)/(?P<id>\d+)/?'
    _TEST = {
        'url': 'http://www.dcndigital.ae/#/show/199074/%D8%B1%D8%AD%D9%84%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D8%B1-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1/17375/6887',
        'info_dict':
        {
            'id': '17375',
            'ext': 'm3u8',
            'title': 'رحلة العمر : الحلقة 1',
            'description': 'في هذه الحلقة من برنامج رحلة العمر يقدّم الدكتور عمر عبد الكافي تبسيطاً لمناسك الحج والعمرة ويجيب مباشرة على استفسارات حجاج بيت الله الحرام بخصوص مناسك الحج والعمرة\n1',
            'thumbnail': 'http://admin.mangomolo.com/analytics/uploads/71/images/media/2/2cefc09d7bec80afa754682f40e49503.jpg',
            'duration': '2041'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        request = compat_urllib_request.Request(
            'http://admin.mangomolo.com/analytics/index.php/plus/video?id=' + video_id,
            headers={'Origin': 'http://www.dcndigital.ae'}
        )
        json_data = self._download_json(request, video_id)
        title = json_data['title_ar']
        thumbnail = 'http://admin.mangomolo.com/analytics/' + json_data['img']
        duration = json_data['duration']
        description = json_data['description_ar']
        webpage = self._download_webpage(
            'http://admin.mangomolo.com/analytics/index.php/customers/embed/video?id=' + json_data['id'] + '&user_id=' + json_data['user_id'] + '&countries=Q0M=&w=100%&h=100%&filter=DENY&signature=' + json_data['signature'],
            video_id
        )
        m3u8_url = self._html_search_regex(
            r'file:\s*"([^"]+)',
            webpage,
            'm3u8_url'
        )
        formats = self._extract_m3u8_formats(m3u8_url, video_id)
        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'description': description,
            'formats': formats,
        }
