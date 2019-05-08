# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    try_get,
    url_or_none,
    ExtractorError,
    js_to_json,
)


class OtomadsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?otomads\.com/v/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://otomads.com/v/jr2sdei3',
        'md5': '319001c3fa242b23c75dcf5b28837079',
        'info_dict': {
            'id': 'jr2sdei3',
            'ext': 'mp4',
            'title': '【合体】国際的男尻祭2017 - DREAM COME TRUE -【10周年記念】',
            'thumbnail': r're:^https?://.*\.(jpg|png)$',
            'description': 'sm32591786',
            'uploader_id': 'MariAli',
            'upload_date': '20190119',
        }
    }, { 
        'url': 'https://otomads.com/v/n8leajcnumc',
        'md5': '6bc865679b3245fa75c6d19717db3dfb',
        'info_dict': {
            'id': 'n8leajcnumc',
            'ext': 'mp4',
            'title': 'iwashi',
            'thumbnail': r're:^https?://.*\.(jpg|png)$',
            'description': 'obj',
            'upload_date': '20190422',
            'uploader_id': '灰色マテリアル',
        }
    }, {
        'url': 'https://otomads.com/v/om1780',
        'md5': 'bebafc8d1361676a3fb8963ca5a38f03',
        'info_dict': {
            'id': 'om1780',
            'ext': 'mp4',
            'title': 'Nyan LiuZe',
            'thumbnail': r're:^https?://.*\.(jpg|png)$',
            'description': '屑站死妈刘泽死爹',
            'upload_date': '20170704',
            'uploader_id': 'pineandbamboo',
        }
    }]
    _API_BASE_URL_ = 'https://otomads.com/api/video/'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_data = self._search_regex(r'<script>[^<]*__NEXT_DATA__\s*=\s*({[^<]*});[^<]*</script>', webpage, 'json')
        json_info = self._parse_json(js_to_json(json_data), video_id)
        video_info = json_info['props']['pageProps']['initialState']['video']['video']

        video_qualities = video_info.get('qualities') or []
        video_qualities.sort()
        video_formats = []
        for quality in video_qualities:
            api_url = self._API_BASE_URL_ + video_info['_id'] + '/url/{0}'.format(quality)
            video_url = self._download_json(api_url, video_id, fatal=False).get('data')
            if url_or_none(video_url) is None:
                continue
            video_quality = 1 if quality == 999 else 2
            video_formats.append({ 'url': video_url, quality: video_quality })

        if len(video_formats) == 0:
            raise ExtractorError('Unable to extract video urls')

        title = self._html_search_meta('title', webpage, default=None)
        author = self._html_search_meta('author', webpage, default=None)
        description = self._html_search_meta('description', webpage, default=None)
        thumbnailUrl = self._html_search_meta('thumbnailUrl', webpage, default=None)
        uploadDate = self._html_search_meta('uploadDate', webpage, default=None)
        if uploadDate is not None and len(uploadDate) >= 10:
            uploadDate = '{0}{1}{2}'.format(uploadDate[0:4],uploadDate[5:7],uploadDate[8:10])

        return {
            'id': video_id,
            'formats': video_formats,
            'title': title or self._og_search_title(webpage),
            'uploader_id': author,
            'upload_date': uploadDate,
            'description': description or self._og_search_description(webpage),
            'thumbnail': url_or_none(thumbnailUrl) or self._og_search_thumbnail(webpage),
        }