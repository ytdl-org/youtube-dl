# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class KikaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kika\.de/(?:[a-z-]+/)*(?:video|sendung)(?P<id>\d+).*'

    _TESTS = [
        {
            'url': 'http://www.kika.de/baumhaus/videos/video9572.html',
            'md5': '94fc748cf5d64916571d275a07ffe2d5',
            'info_dict': {
                'id': '9572',
                'ext': 'mp4',
                'title': 'Baumhaus vom 29. Oktober 2014',
                'description': None
            }
        },
        {
            'url': 'http://www.kika.de/sendungen/einzelsendungen/weihnachtsprogramm/videos/video8182.html',
            'md5': '5fe9c4dd7d71e3b238f04b8fdd588357',
            'info_dict': {
                'id': '8182',
                'ext': 'mp4',
                'title': 'Beutolomäus und der geheime Weihnachtswunsch',
                'description': 'md5:b69d32d7b2c55cbe86945ab309d39bbd'
            }
        },
        {
            'url': 'http://www.kika.de/videos/allevideos/video9572_zc-32ca94ad_zs-3f535991.html',
            'md5': '94fc748cf5d64916571d275a07ffe2d5',
            'info_dict': {
                'id': '9572',
                'ext': 'mp4',
                'title': 'Baumhaus vom 29. Oktober 2014',
                'description': None
            }
        },
        {
            'url': 'http://www.kika.de/sendungen/einzelsendungen/weihnachtsprogramm/videos/sendung81244_zc-81d703f8_zs-f82d5e31.html',
            'md5': '5fe9c4dd7d71e3b238f04b8fdd588357',
            'info_dict': {
                'id': '8182',
                'ext': 'mp4',
                'title': 'Beutolomäus und der geheime Weihnachtswunsch',
                'description': 'md5:b69d32d7b2c55cbe86945ab309d39bbd'
            }
        }
    ]

    def _real_extract(self, url):
        # broadcast_id may be the same as the video_id
        broadcast_id = self._match_id(url)
        webpage = self._download_webpage(url, broadcast_id)

        xml_re = r'sectionArticle[ "](?:(?!sectionA[ "])(?:.|\n))*?dataURL:\'(?:/[a-z-]+?)*?/video(\d+)-avCustom\.xml'
        video_id = self._search_regex(xml_re, webpage, "xml_url", default=None)
        if not video_id:
            # Video is not available online
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
            # No description available
            description = None

        # duration string format is mm:ss (even if it is >= 1 hour, e.g. 78:42)
        tmp = xml_tree.find('duration').text.split(':')
        duration = int(tmp[0]) * 60 + int(tmp[1])

        formats_list = []
        for elem in xml_tree.find('assets'):
            format_dict = {}
            format_dict['url'] = elem.find('progressiveDownloadUrl').text
            format_dict['ext'] = elem.find('mediaType').text.lower()
            format_dict['format'] = elem.find('profileName').text
            width = int(elem.find('frameWidth').text)
            height = int(elem.find('frameHeight').text)
            format_dict['width'] = width
            format_dict['height'] = height
            format_dict['resolution'] = '%dx%d' % (width, height)
            format_dict['abr'] = int(elem.find('bitrateAudio').text)
            format_dict['vbr'] = int(elem.find('bitrateVideo').text)
            format_dict['tbr'] = format_dict['abr'] + format_dict['vbr']
            format_dict['filesize'] = int(elem.find('fileSize').text)

            # append resolution and dict for sorting by resolution
            formats_list.append((width * height, format_dict))

        # Sort by resolution (=quality)
        formats_list.sort()

        out_list = [x[1] for x in formats_list]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': out_list,
            'duration': duration,
            'webpage_url': webpage_url
        }
