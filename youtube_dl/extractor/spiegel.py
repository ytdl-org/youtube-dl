# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .nexx import NexxEmbedIE
from .spiegeltv import SpiegeltvIE
from ..compat import compat_urlparse
from ..utils import (
    extract_attributes,
    unified_strdate,
    get_element_by_attribute,
)


class SpiegelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/video/[^/]*-(?P<id>[0-9]+)(?:-embed|-iframe)?(?:\.html)?(?:#.*)?$'
    _TESTS = [{
        'url': 'http://www.spiegel.de/video/vulkan-tungurahua-in-ecuador-ist-wieder-aktiv-video-1259285.html',
        'md5': '2c2754212136f35fb4b19767d242f66e',
        'info_dict': {
            'id': '1259285',
            'ext': 'mp4',
            'title': 'Vulkanausbruch in Ecuador: Der "Feuerschlund" ist wieder aktiv',
            'description': 'md5:8029d8310232196eb235d27575a8b9f4',
            'duration': 49,
            'upload_date': '20130311',
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
            'upload_date': '20131115',
        },
    }, {
        'url': 'http://www.spiegel.de/video/astronaut-alexander-gerst-von-der-iss-station-beantwortet-fragen-video-1519126-embed.html',
        'md5': 'd8eeca6bfc8f1cd6f490eb1f44695d51',
        'info_dict': {
            'id': '1519126',
            'ext': 'mp4',
            'description': 'SPIEGEL ONLINE-Nutzer durften den deutschen Astronauten Alexander Gerst über sein Leben auf der ISS-Station befragen. Hier kommen seine Antworten auf die besten sechs Fragen.',
            'title': 'Fragen an Astronaut Alexander Gerst: "Bekommen Sie die Tageszeiten mit?"',
            'upload_date': '20140904',
        }
    }, {
        'url': 'http://www.spiegel.de/video/astronaut-alexander-gerst-von-der-iss-station-beantwortet-fragen-video-1519126-iframe.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage, handle = self._download_webpage_handle(url, video_id)

        # 302 to spiegel.tv, like http://www.spiegel.de/video/der-film-zum-wochenende-die-wahrheit-ueber-maenner-video-99003272.html
        if SpiegeltvIE.suitable(handle.geturl()):
            return self.url_result(handle.geturl(), 'Spiegeltv')

        video_data = extract_attributes(self._search_regex(r'(<div[^>]+id="spVideoElements"[^>]+>)', webpage, 'video element', default=''))

        title = video_data.get('data-video-title') or get_element_by_attribute('class', 'module-title', webpage)
        description = video_data.get('data-video-teaser') or self._html_search_meta('description', webpage, 'description')

        base_url = self._search_regex(
            [r'server\s*:\s*(["\'])(?P<url>.+?)\1', r'var\s+server\s*=\s*"(?P<url>[^"]+)\"'],
            webpage, 'server URL', group='url')

        xml_url = base_url + video_id + '.xml'
        idoc = self._download_xml(xml_url, video_id)

        formats = []
        for n in list(idoc):
            if n.tag.startswith('type') and n.tag != 'type6':
                format_id = n.tag.rpartition('type')[2]
                video_url = base_url + n.find('./filename').text
                formats.append({
                    'format_id': format_id,
                    'url': video_url,
                    'width': int(n.find('./width').text),
                    'height': int(n.find('./height').text),
                    'abr': int(n.find('./audiobitrate').text),
                    'vbr': int(n.find('./videobitrate').text),
                    'vcodec': n.find('./codec').text,
                    'acodec': 'MP4A',
                })
        duration = float(idoc[0].findall('./duration')[0].text)

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description.strip() if description else None,
            'duration': duration,
            'upload_date': unified_strdate(video_data.get('data-video-date')),
            'formats': formats,
        }


class SpiegelArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/(?!video/)[^?#]*?-(?P<id>[0-9]+)\.html'
    IE_NAME = 'Spiegel:Article'
    IE_DESC = 'Articles on spiegel.de'
    _TESTS = [{
        'url': 'http://www.spiegel.de/sport/sonst/badminton-wm-die-randsportart-soll-populaerer-werden-a-987092.html',
        'info_dict': {
            'id': '1516455',
            'ext': 'mp4',
            'title': 'Faszination Badminton: Nennt es bloß nicht Federball',
            'description': 're:^Patrick Kämnitz gehört.{100,}',
            'upload_date': '20140825',
        },
    }, {
        'url': 'http://www.spiegel.de/wissenschaft/weltall/astronaut-alexander-gerst-antwortet-spiegel-online-lesern-a-989876.html',
        'info_dict': {

        },
        'playlist_count': 6,
    }, {
        # Nexx iFrame embed
        'url': 'http://www.spiegel.de/sptv/spiegeltv/spiegel-tv-ueber-schnellste-katapult-achterbahn-der-welt-taron-a-1137884.html',
        'info_dict': {
            'id': '161464',
            'ext': 'mp4',
            'title': 'Nervenkitzel Achterbahn',
            'alt_title': 'Karussellbauer in Deutschland',
            'description': 'md5:ffe7b1cc59a01f585e0569949aef73cc',
            'release_year': 2005,
            'creator': 'SPIEGEL TV',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2761,
            'timestamp': 1394021479,
            'upload_date': '20140305',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
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
            for embed_path in embeds]
        if embeds:
            return self.playlist_result(entries)

        return self.playlist_from_matches(
            NexxEmbedIE._extract_urls(webpage), ie=NexxEmbedIE.ie_key())
