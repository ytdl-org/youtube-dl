# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_duration,
)


class BRIE(InfoExtractor):
    IE_DESC = 'Bayerischer Rundfunk Mediathek'
    _VALID_URL = r'https?://(?:www\.)?br\.de/(?:[a-z0-9\-_]+/)+(?P<id>[a-z0-9\-_]+)\.html'
    _BASE_URL = 'http://www.br.de'

    _TESTS = [
        {
            'url': 'http://www.br.de/mediathek/video/sendungen/abendschau/betriebliche-altersvorsorge-104.html',
            'md5': '83a0477cf0b8451027eb566d88b51106',
            'info_dict': {
                'id': '48f656ef-287e-486f-be86-459122db22cc',
                'ext': 'mp4',
                'title': 'Die böse Überraschung',
                'description': 'Betriebliche Altersvorsorge: Die böse Überraschung',
                'duration': 180,
                'uploader': 'Reinhard Weber',
                'upload_date': '20150422',
            }
        },
        {
            'url': 'http://www.br.de/nachrichten/oberbayern/inhalt/muenchner-polizeipraesident-schreiber-gestorben-100.html',
            'md5': 'a44396d73ab6a68a69a568fae10705bb',
            'info_dict': {
                'id': 'a4b83e34-123d-4b81-9f4e-c0d3121a4e05',
                'ext': 'mp4',
                'title': 'Manfred Schreiber ist tot',
                'description': 'Abendschau kompakt: Manfred Schreiber ist tot',
                'duration': 26,
            }
        },
        {
            'url': 'http://www.br.de/radio/br-klassik/sendungen/allegro/premiere-urauffuehrung-the-land-2015-dance-festival-muenchen-100.html',
            'md5': '8b5b27c0b090f3b35eac4ab3f7a73d3d',
            'info_dict': {
                'id': '74c603c9-26d3-48bb-b85b-079aeed66e0b',
                'ext': 'aac',
                'title': 'Kurzweilig und sehr bewegend',
                'description': '"The Land" von Peeping Tom: Kurzweilig und sehr bewegend',
                'duration': 296,
            }
        },
        {
            'url': 'http://www.br.de/radio/bayern1/service/team/videos/team-video-erdelt100.html',
            'md5': 'dbab0aef2e047060ea7a21fc1ce1078a',
            'info_dict': {
                'id': '6ba73750-d405-45d3-861d-1ce8c524e059',
                'ext': 'mp4',
                'title': 'Umweltbewusster Häuslebauer',
                'description': 'Uwe Erdelt: Umweltbewusster Häuslebauer',
                'duration': 116,
            }
        },
        {
            'url': 'http://www.br.de/fernsehen/br-alpha/sendungen/kant-fuer-anfaenger/kritik-der-reinen-vernunft/kant-kritik-01-metaphysik100.html',
            'md5': '23bca295f1650d698f94fc570977dae3',
            'info_dict': {
                'id': 'd982c9ce-8648-4753-b358-98abb8aec43d',
                'ext': 'mp4',
                'title': 'Folge 1 - Metaphysik',
                'description': 'Kant für Anfänger: Folge 1 - Metaphysik',
                'duration': 893,
                'uploader': 'Eva Maria Steimle',
                'upload_date': '20140117',
            }
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        page = self._download_webpage(url, display_id)
        xml_url = self._search_regex(
            r"return BRavFramework\.register\(BRavFramework\('avPlayer_(?:[a-f0-9-]{36})'\)\.setup\({dataURL:'(/(?:[a-z0-9\-]+/)+[a-z0-9/~_.-]+)'}\)\);", page, 'XMLURL')
        xml = self._download_xml(self._BASE_URL + xml_url, None)

        medias = []

        for xml_media in xml.findall('video') + xml.findall('audio'):
            media = {
                'id': xml_media.get('externalId'),
                'title': xml_media.find('title').text,
                'duration': parse_duration(xml_media.find('duration').text),
                'formats': self._extract_formats(xml_media.find('assets')),
                'thumbnails': self._extract_thumbnails(xml_media.find('teaserImage/variants')),
                'description': ' '.join(xml_media.find('shareTitle').text.splitlines()),
                'webpage_url': xml_media.find('permalink').text
            }
            if xml_media.find('author').text:
                media['uploader'] = xml_media.find('author').text
            if xml_media.find('broadcastDate').text:
                media['upload_date'] = ''.join(reversed(xml_media.find('broadcastDate').text.split('.')))
            medias.append(media)

        if len(medias) > 1:
            self._downloader.report_warning(
                'found multiple medias; please '
                'report this with the video URL to http://yt-dl.org/bug')
        if not medias:
            raise ExtractorError('No media entries found')
        return medias[0]

    def _extract_formats(self, assets):

        def text_or_none(asset, tag):
            elem = asset.find(tag)
            return None if elem is None else elem.text

        formats = [{
            'url': text_or_none(asset, 'downloadUrl'),
            'ext': text_or_none(asset, 'mediaType'),
            'format_id': asset.get('type'),
            'width': int_or_none(text_or_none(asset, 'frameWidth')),
            'height': int_or_none(text_or_none(asset, 'frameHeight')),
            'tbr': int_or_none(text_or_none(asset, 'bitrateVideo')),
            'abr': int_or_none(text_or_none(asset, 'bitrateAudio')),
            'vcodec': text_or_none(asset, 'codecVideo'),
            'acodec': text_or_none(asset, 'codecAudio'),
            'container': text_or_none(asset, 'mediaType'),
            'filesize': int_or_none(text_or_none(asset, 'size')),
        } for asset in assets.findall('asset')
            if asset.find('downloadUrl') is not None]

        self._sort_formats(formats)
        return formats

    def _extract_thumbnails(self, variants):
        thumbnails = [{
            'url': self._BASE_URL + variant.find('url').text,
            'width': int_or_none(variant.find('width').text),
            'height': int_or_none(variant.find('height').text),
        } for variant in variants.findall('variant')]
        thumbnails.sort(key=lambda x: x['width'] * x['height'], reverse=True)
        return thumbnails
