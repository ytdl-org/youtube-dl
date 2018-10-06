# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor


class SdfIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sdf\.bz\.it/Mediathek/\(video\)/(?P<id>[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.sdf.bz.it/Mediathek/(video)/62982',
            'md5': 'c08bfa83e5a011dae3dab7d935ae1f7d',
            'info_dict': {
                'id': '62982',
                'ext': 'mp4',
                'title': 'Südtiroler Sporthilfe',
                'thumbnail': r're:^https?://.*\.jpg$',
             },
        },  {
             'url': 'http://www.sdf.bz.it/Mediathek/(video)/62981',
             'md5': '9523207e57a0db6b322eccb70825142a',
             'info_dict': {
                 'id': '62981',
                 'ext': 'mp4',
                 'title': 'Seelische Gesundheit',
                 'thumbnail': r're:^https?://.*\.jpg$',
             }
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        url = self._html_search_regex(r'(?s)file:\s\"(http.*?\.mp4)', webpage, 'url', fatal=True)
        thumbnail = self._html_search_regex(r'(?s)image:\s\"(http.*?\.jpg)', webpage, 'thumbnail', fatal=True)
        title = self._html_search_regex(r'(?s)\"og:title\"\scontent\=\"(.+?)\"\/>', webpage, 'title', default=video_id, fatal=False)
        info_dict = {
                'id': video_id,
                'title': title,
                'url': url,
                'format': 'mp4',
                'thumbnail': thumbnail,
            }
        return (info_dict)

