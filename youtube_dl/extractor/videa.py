# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    xpath_element,
    xpath_text,
    xpath_attr,
    urlencode_postdata,
    unescapeHTML,
)


class VideaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?videa\.hu/videok/(?P<id>[^#?]+)'
    _TESTS = [{
        'url': 'http://videa.hu/videok/allatok/az-orult-kigyasz-285-kigyot-kigyo-8YfIAjxwWGwT8HVQ',
        'md5': '97a7af41faeaffd9f1fc864a7c7e7603',
        'info_dict': {
            'id': '8YfIAjxwWGwT8HVQ',
            'display_id': '8YfIAjxwWGwT8HVQ',
            'ext': 'mp4',
            'title': 'Az őrült kígyász 285 kígyót enged szabadon',
            'thumbnail': 'http://videa.hu/static/still/1.4.1.1007274.1204470.3',
            'duration': 21,
        },
    }, {
        'url': 'http://videa.hu/videok/origo/jarmuvek/supercars-elozes-jAHDWfWSJH5XuFhH',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data = self._download_json("http://videa.hu/oembed/?" + urlencode_postdata({"url": url.split('?')[0], "format": "json"}), video_id)
        video_url = self._search_regex(
            r'src="(.+?)"', video_data.get('html'), 'embed url')

        return {
            '_type': 'url_transparent',
            'url': video_url,
            'ie_key': 'VideaEmbed'
        }

class VideaEmbedIE(InfoExtractor):
    _VALID_URL = r'(?P<protocol>https?:)(?P<baseurl>//(?:.+?\.)?videa\.hu)/player(?:\?v=|/v/)(?P<id>[^/#?]+)';
    _TESTS = [{
        'url': 'http://videa.hu/player?v=8YfIAjxwWGwT8HVQ',
        'md5': '97a7af41faeaffd9f1fc864a7c7e7603',
        'info_dict': {
            'id': '8YfIAjxwWGwT8HVQ',
            'ext': 'mp4',
            'title': 'Az őrült kígyász 285 kígyót enged szabadon',
            'thumbnail': 'http://videa.hu/static/still/1.4.1.1007274.1204470.3',
            'duration': 21
        },
    }, {
        'url': 'http://videa.hu/player?v=jAHDWfWSJH5XuFhH',
        'only_matching': True,
    }];

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:.+?\.)?videa\.hu/player(?:\?v=|/v/)[^/#?]+)\1',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        protocol, base_url, display_id = re.search(self._VALID_URL, url).groups()
        xml = self._download_xml(protocol + base_url + "/flvplayer_get_video_xml.php?v=" + display_id, display_id)

        medias = []
        
        for xml_media in xml.findall('video') + xml.findall('audio'):
            media_url = protocol + xpath_attr(xml_media, 'versions/version', 'video_url')
            media = {
                'id': display_id,
                'ext': 'mp4',
                'title': xpath_text(xml_media, 'title', 'title', True),
                'duration': parse_duration(xpath_text(xml_media, 'duration')),
                'thumbnail': protocol + xpath_text(xml_media, 'still', 'still', True),
                'url': media_url,
            }
            medias.append(media)

        if len(medias) > 1:
            self._downloader.report_warning(
                'found multiple medias; please '
                'report this with the video URL to http://yt-dl.org/bug')
        if not medias:
            raise ExtractorError('No media entries found')
        return medias[0]
