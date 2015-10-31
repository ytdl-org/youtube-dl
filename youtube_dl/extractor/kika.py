# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class KikaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kika\.de/(?:[a-z-]+/)*(?:video|(?:einzel)?sendung)(?P<id>\d+).*'

    _TESTS = [
        {
            'url': 'http://www.kika.de/baumhaus/videos/video19636.html',
            'md5': '4930515e36b06c111213e80d1e4aad0e',
            'info_dict': {
                'id': '19636',
                'ext': 'mp4',
                'title': 'Baumhaus vom 30. Oktober 2015',
                'description': None,
            },
        },
        {
            'url': 'http://www.kika.de/sendungen/einzelsendungen/weihnachtsprogramm/videos/video8182.html',
            'md5': '5fe9c4dd7d71e3b238f04b8fdd588357',
            'info_dict': {
                'id': '8182',
                'ext': 'mp4',
                'title': 'Beutolomäus und der geheime Weihnachtswunsch',
                'description': 'md5:b69d32d7b2c55cbe86945ab309d39bbd',
            },
        },
        {
            'url': 'http://www.kika.de/baumhaus/sendungen/video19636_zc-fea7f8a0_zs-4bf89c60.html',
            'md5': '4930515e36b06c111213e80d1e4aad0e',
            'info_dict': {
                'id': '19636',
                'ext': 'mp4',
                'title': 'Baumhaus vom 30. Oktober 2015',
                'description': None,
            },
        },
        {
            'url': 'http://www.kika.de/sendungen/einzelsendungen/weihnachtsprogramm/einzelsendung2534.html',
            'md5': '5fe9c4dd7d71e3b238f04b8fdd588357',
            'info_dict': {
                'id': '8182',
                'ext': 'mp4',
                'title': 'Beutolomäus und der geheime Weihnachtswunsch',
                'description': 'md5:b69d32d7b2c55cbe86945ab309d39bbd',
            },
        },
    ]

    def _real_extract(self, url):
        # broadcast_id may be the same as the video_id
        broadcast_id = self._match_id(url)
        webpage = self._download_webpage(url, broadcast_id)

        xml_re = r'sectionArticle[ "](?:(?!sectionA[ "])(?:.|\n))*?dataURL:\'(?:/[a-z-]+?)*?/video(\d+)-avCustom\.xml'
        video_id = self._search_regex(xml_re, webpage, "xml_url", default=None)
        if not video_id:
            err_msg = 'Video %s is not available online' % broadcast_id
            raise ExtractorError(err_msg, expected=True)

        xml_url = 'http://www.kika.de/video%s-avCustom.xml' % (video_id)
        xml_tree = self._download_xml(xml_url, video_id)

        title = xml_tree.find('title').text
        webpage_url = xml_tree.find('htmlUrl').text

        # Try to get the description, not available for all videos
        try:
            broadcast_elem = xml_tree.find('broadcast')
            description = broadcast_elem.find('broadcastDescription').text
        except AttributeError:
            description = None

        # duration string format is mm:ss (even if it is >= 1 hour, e.g. 78:42)
        tmp = xml_tree.find('duration').text.split(':')
        duration = int(tmp[0]) * 60 + int(tmp[1])

        formats = [{
            'url': elem.find('progressiveDownloadUrl').text,
            'ext': elem.find('mediaType').text.lower(),
            'format': elem.find('profileName').text,
            'width': int(elem.find('frameWidth').text),
            'height': int(elem.find('frameHeight').text),
            'abr': int(elem.find('bitrateAudio').text),
            'vbr': int(elem.find('bitrateVideo').text),
            'filesize': int(elem.find('fileSize').text),
        } for elem in xml_tree.find('assets')]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'duration': duration,
            'webpage_url': webpage_url,
        }
