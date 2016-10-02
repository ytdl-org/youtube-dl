from __future__ import unicode_literals

from .zdf import ZDFIE


class PhoenixIE(ZDFIE):
    IE_NAME = 'phoenix.de'
    _VALID_URL = r'''(?x)https?://(?:www\.)?phoenix\.de/content/
        (?:
            phoenix/die_sendungen/(?:[^/]+/)?
        )?
        (?P<id>[0-9]+)'''
    _TESTS = [
        {
            'url': 'http://www.phoenix.de/content/884301',
            'md5': 'ed249f045256150c92e72dbb70eadec6',
            'info_dict': {
                'id': '884301',
                'ext': 'mp4',
                'title': 'Michael Krons mit Hans-Werner Sinn',
                'description': 'Im Dialog - Sa. 25.10.14, 00.00 - 00.35 Uhr',
                'upload_date': '20141025',
                'uploader': 'Im Dialog',
            }
        },
        {
            'url': 'http://www.phoenix.de/content/phoenix/die_sendungen/869815',
            'only_matching': True,
        },
        {
            'url': 'http://www.phoenix.de/content/phoenix/die_sendungen/diskussionen/928234',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        internal_id = self._search_regex(
            r'<div class="phx_vod" id="phx_vod_([0-9]+)"',
            webpage, 'internal video ID')

        api_url = 'http://www.phoenix.de/php/mediaplayer/data/beitrags_details.php?ak=web&id=%s' % internal_id
        return self.extract_from_xml_url(video_id, api_url)
