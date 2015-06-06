# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    determine_ext,
    int_or_none,
    xpath_text,
)


class RuutuIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?ruutu\.fi/ohjelmat/(?:[^/?#]+/)*(?P<id>[^/?#]+)'
    _TESTS = [
        {
            'url': 'http://www.ruutu.fi/ohjelmat/oletko-aina-halunnut-tietaa-mita-tapahtuu-vain-hetki-ennen-lahetysta-nyt-se-selvisi',
            'md5': 'ab2093f39be1ca8581963451b3c0234f',
            'info_dict': {
                'id': '2058907',
                'display_id': 'oletko-aina-halunnut-tietaa-mita-tapahtuu-vain-hetki-ennen-lahetysta-nyt-se-selvisi',
                'ext': 'mp4',
                'title': 'Oletko aina halunnut tietää mitä tapahtuu vain hetki ennen lähetystä? - Nyt se selvisi!',
                'description': 'md5:cfc6ccf0e57a814360df464a91ff67d6',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 114,
                'age_limit': 0,
            },
        },
        {
            'url': 'http://www.ruutu.fi/ohjelmat/superpesis/superpesis-katso-koko-kausi-ruudussa',
            'md5': '065a10ae4d5b8cfd9d0c3d332465e3d9',
            'info_dict': {
                'id': '2057306',
                'display_id': 'superpesis-katso-koko-kausi-ruudussa',
                'ext': 'mp4',
                'title': 'Superpesis: katso koko kausi Ruudussa',
                'description': 'md5:44c44a99fdbe5b380ab74ebd75f0af77',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 40,
                'age_limit': 0,
            },
        },
    ]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            r'data-media-id="(\d+)"', webpage, 'media id')

        video_xml_url = None

        media_data = self._search_regex(
            r'jQuery\.extend\([^,]+,\s*(.+?)\);', webpage,
            'media data', default=None)
        if media_data:
            media_json = self._parse_json(media_data, display_id, fatal=False)
            if media_json:
                xml_url = media_json.get('ruutuplayer', {}).get('xmlUrl')
                if xml_url:
                    video_xml_url = xml_url.replace('{ID}', video_id)

        if not video_xml_url:
            video_xml_url = 'http://gatling.ruutu.fi/media-xml-cache?id=%s' % video_id

        video_xml = self._download_xml(video_xml_url, video_id)

        formats = []
        processed_urls = []

        def extract_formats(node):
            for child in node:
                if child.tag.endswith('Files'):
                    extract_formats(child)
                elif child.tag.endswith('File'):
                    video_url = child.text
                    if not video_url or video_url in processed_urls or 'NOT_USED' in video_url:
                        return
                    processed_urls.append(video_url)
                    ext = determine_ext(video_url)
                    if ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4', m3u8_id='hls'))
                    elif ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            video_url, video_id, f4m_id='hds'))
                    else:
                        proto = compat_urllib_parse_urlparse(video_url).scheme
                        if not child.tag.startswith('HTTP') and proto != 'rtmp':
                            continue
                        preference = -1 if proto == 'rtmp' else 1
                        label = child.get('label')
                        tbr = int_or_none(child.get('bitrate'))
                        width, height = [int_or_none(x) for x in child.get('resolution', '').split('x')]
                        formats.append({
                            'format_id': '%s-%s' % (proto, label if label else tbr),
                            'url': video_url,
                            'width': width,
                            'height': height,
                            'tbr': tbr,
                            'preference': preference,
                        })

        extract_formats(video_xml.find('./Clip'))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': int_or_none(xpath_text(video_xml, './/Runtime', 'duration')),
            'age_limit': int_or_none(xpath_text(video_xml, './/AgeLimit', 'age limit')),
            'formats': formats,
        }
