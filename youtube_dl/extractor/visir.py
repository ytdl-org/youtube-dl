# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    determine_ext,
    RegexNotFoundError)


class VisirIE(InfoExtractor):
    IE_NAME = 'visir'
    _VALID_URL = r'https?://(?:www.)visir.is/(?:.*)/(?P<id>.*)'
    # _VALID_URL = r'https?://(?:www.)visir.is/(k|g)/(?P<id>.*)'
    _TEST = {
        'url': 'https://www.visir.is/k/clp4238',
        'md5': '30fe8b7cb54ac47115f45d8a1be7438e',
        'info_dict': {
            'id': 'clp4238',
            'ext': 'mp4',
            'title': 'Eldgos í Grímsvötnum - Vísir',
            'description': 'Egill Aðalsteinsson kvikmyndatökumaður flaug yfir gosstöðvarnar í kvöld. '
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        thumbnails = []
        description = self._og_search_description(webpage)
        if ('/article/' in url) or ('/g/' in url):
            try:
                article_vid = self._html_search_regex(r"(?P<url>https\:\/\/www\.visir\.is\/player\/.*?)\".", webpage,
                                                      'url')
            except RegexNotFoundError as e:
                article_vid = self._html_search_regex(
                    r"(?:src=)\"(?P<url>https?://(www.)?visir.is/section/media/\?template=iplayer.*?)\"", webpage,
                    'url')
            webpage = self._download_webpage(article_vid, video_id)

        title = self._html_search_regex(r"Title:.'(.*?)'", webpage, 'title')
        filename = self._html_search_regex(r"File:.'(.*?)'", webpage, 'filenme')
        hostname = self._html_search_regex(r"Host:.'(.*?)'", webpage, 'hostname')
        thumb_url = self._html_search_regex(r"image:.'(.*?)'", webpage, 'thumb_url')
        thumbnails.append({'url': thumb_url})
        media_url = ''.join(['https://', hostname, filename])
        ext = determine_ext(media_url)

        formats = [{'url': media_url}]
        if ext == 'm3u8':
            m3u8_formats = self._extract_m3u8_formats(media_url, video_id, 'mp4', fatal=False)
            formats.extend(m3u8_formats)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'thumbnails': thumbnails
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
