from __future__ import unicode_literals

from .nuevo import NuevoBaseIE


class RulePornIE(NuevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ruleporn\.com/(?:[^/?#&]+/)*(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://ruleporn.com/brunette-nympho-chick-takes-her-boyfriend-in-every-angle/',
        'md5': '86861ebc624a1097c7c10eaf06d7d505',
        'info_dict': {
            'id': '48212',
            'display_id': 'brunette-nympho-chick-takes-her-boyfriend-in-every-angle',
            'ext': 'mp4',
            'title': 'Brunette Nympho Chick Takes Her Boyfriend In Every Angle',
            'description': 'md5:6d28be231b981fff1981deaaa03a04d5',
            'age_limit': 18,
            'duration': 635.1,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'lovehomeporn\.com/embed/(\d+)', webpage, 'video id')

        title = self._search_regex(
            r'<h2[^>]+title=(["\'])(?P<url>.+?)\1',
            webpage, 'title', group='url')
        description = self._html_search_meta('description', webpage)

        info = self._extract_nuevo(
            'http://lovehomeporn.com/media/nuevo/econfig.php?key=%s&rp=true' % video_id,
            video_id)
        info.update({
            'display_id': display_id,
            'title': title,
            'description': description,
            'age_limit': 18
        })
        return info
