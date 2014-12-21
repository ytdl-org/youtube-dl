# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from .spiegeltv import SpiegeltvIE


class SpiegelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/video/[^/]*-(?P<id>[0-9]+)(?:-embed)?(?:\.html)?(?:#.*)?$'
    _TESTS = [{
        'url': 'http://www.spiegel.de/video/vulkan-tungurahua-in-ecuador-ist-wieder-aktiv-video-1259285.html',
        'md5': '2c2754212136f35fb4b19767d242f66e',
        'info_dict': {
            'id': '1259285',
            'ext': 'mp4',
            'title': 'Vulkanausbruch in Ecuador: Der "Feuerschlund" ist wieder aktiv',
            'description': 'md5:8029d8310232196eb235d27575a8b9f4',
            'duration': 49,
        },
    }, {
        'url': 'http://www.spiegel.de/video/schach-wm-videoanalyse-des-fuenften-spiels-video-1309159.html',
        'md5': 'f2cdf638d7aa47654e251e1aee360af1',
        'info_dict': {
            'id': '1309159',
            'ext': 'mp4',
            'title': 'Schach-WM in der Videoanalyse: Carlsen nutzt die Fehlgriffe des Titelverteidigers',
            'description': 'md5:c2322b65e58f385a820c10fa03b2d088',
            'duration': 983,
        },
    }, {
        'url': 'http://www.spiegel.de/video/astronaut-alexander-gerst-von-der-iss-station-beantwortet-fragen-video-1519126-embed.html',
        'md5': 'd8eeca6bfc8f1cd6f490eb1f44695d51',
        'info_dict': {
            'id': '1519126',
            'ext': 'mp4',
            'description': 'SPIEGEL ONLINE-Nutzer durften den deutschen Astronauten Alexander Gerst über sein Leben auf der ISS-Station befragen. Hier kommen seine Antworten auf die besten sechs Fragen.',
            'title': 'Fragen an Astronaut Alexander Gerst: "Bekommen Sie die Tageszeiten mit?"',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, handle = self._download_webpage_handle(url, video_id)

        # 302 to spiegel.tv, like http://www.spiegel.de/video/der-film-zum-wochenende-die-wahrheit-ueber-maenner-video-99003272.html
        if SpiegeltvIE.suitable(handle.geturl()):
            return self.url_result(handle.geturl(), 'Spiegeltv')

        title = re.sub(r'\s+', ' ', self._html_search_regex(
            r'(?s)<(?:h1|div) class="module-title"[^>]*>(.*?)</(?:h1|div)>',
            webpage, 'title'))
        description = self._html_search_meta('description', webpage, 'description')

        base_url = self._search_regex(
            r'var\s+server\s*=\s*"([^"]+)\"', webpage, 'server URL')

        xml_url = base_url + video_id + '.xml'
        idoc = self._download_xml(xml_url, video_id)

        formats = [
            {
                'format_id': n.tag.rpartition('type')[2],
                'url': base_url + n.find('./filename').text,
                'width': int(n.find('./width').text),
                'height': int(n.find('./height').text),
                'abr': int(n.find('./audiobitrate').text),
                'vbr': int(n.find('./videobitrate').text),
                'vcodec': n.find('./codec').text,
                'acodec': 'MP4A',
            }
            for n in list(idoc)
            # Blacklist type 6, it's extremely LQ and not available on the same server
            if n.tag.startswith('type') and n.tag != 'type6'
        ]
        duration = float(idoc[0].findall('./duration')[0].text)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats,
        }


class SpiegelArticleIE(InfoExtractor):
    _VALID_URL = 'https?://www\.spiegel\.de/(?!video/)[^?#]*?-(?P<id>[0-9]+)\.html'
    IE_NAME = 'Spiegel:Article'
    IE_DESC = 'Articles on spiegel.de'
    _TESTS = [{
        'url': 'http://www.spiegel.de/sport/sonst/badminton-wm-die-randsportart-soll-populaerer-werden-a-987092.html',
        'info_dict': {
            'id': '1516455',
            'ext': 'mp4',
            'title': 'Faszination Badminton: Nennt es bloß nicht Federball',
            'description': 're:^Patrick Kämnitz gehört.{100,}',
        },
    }, {
        'url': 'http://www.spiegel.de/wissenschaft/weltall/astronaut-alexander-gerst-antwortet-spiegel-online-lesern-a-989876.html',
        'info_dict': {

        },
        'playlist_count': 6,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Single video on top of the page
        video_link = self._search_regex(
            r'<a href="([^"]+)" onclick="return spOpenVideo\(this,', webpage,
            'video page URL', default=None)
        if video_link:
            video_url = compat_urlparse.urljoin(
                self.http_scheme() + '//spiegel.de/', video_link)
            return self.url_result(video_url)

        # Multiple embedded videos
        embeds = re.findall(
            r'<div class="vid_holder[0-9]+.*?</div>\s*.*?url\s*=\s*"([^"]+)"',
            webpage)
        entries = [
            self.url_result(compat_urlparse.urljoin(
                self.http_scheme() + '//spiegel.de/', embed_path))
            for embed_path in embeds
        ]
        return self.playlist_result(entries)
