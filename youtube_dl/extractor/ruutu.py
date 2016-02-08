# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    determine_ext,
    int_or_none,
    xpath_attr,
    xpath_text,
)


class RuutuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ruutu\.fi/video/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.ruutu.fi/video/2058907',
            'md5': 'ab2093f39be1ca8581963451b3c0234f',
            'info_dict': {
                'id': '2058907',
                'ext': 'mp4',
                'title': 'Oletko aina halunnut tietää mitä tapahtuu vain hetki ennen lähetystä? - Nyt se selvisi!',
                'description': 'md5:cfc6ccf0e57a814360df464a91ff67d6',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 114,
                'age_limit': 0,
            },
        },
        {
            'url': 'http://www.ruutu.fi/video/2057306',
            'md5': '065a10ae4d5b8cfd9d0c3d332465e3d9',
            'info_dict': {
                'id': '2057306',
                'ext': 'mp4',
                'title': 'Superpesis: katso koko kausi Ruudussa',
                'description': 'md5:da2736052fef3b2bd5e0005e63c25eac',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 40,
                'age_limit': 0,
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_xml = self._download_xml(
            'http://gatling.ruutu.fi/media-xml-cache?id=%s' % video_id, video_id)

        formats = []
        processed_urls = []

        def extract_formats(node):
            for child in node:
                if child.tag.endswith('Files'):
                    extract_formats(child)
                elif child.tag.endswith('File'):
                    video_url = child.text
                    if (not video_url or video_url in processed_urls or
                            any(p in video_url for p in ('NOT_USED', 'NOT-USED'))):
                        return
                    processed_urls.append(video_url)
                    ext = determine_ext(video_url)
                    if ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                    elif ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            video_url, video_id, f4m_id='hds', fatal=False))
                    else:
                        proto = compat_urllib_parse_urlparse(video_url).scheme
                        if not child.tag.startswith('HTTP') and proto != 'rtmp':
                            continue
                        preference = -1 if proto == 'rtmp' else 1
                        label = child.get('label')
                        tbr = int_or_none(child.get('bitrate'))
                        format_id = '%s-%s' % (proto, label if label else tbr) if label or tbr else proto
                        if not self._is_valid_url(video_url, video_id, format_id):
                            continue
                        width, height = [int_or_none(x) for x in child.get('resolution', 'x').split('x')[:2]]
                        formats.append({
                            'format_id': format_id,
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
            'title': xpath_attr(video_xml, './/Behavior/Program', 'program_name', 'title', fatal=True),
            'description': xpath_attr(video_xml, './/Behavior/Program', 'description', 'description'),
            'thumbnail': xpath_attr(video_xml, './/Behavior/Startpicture', 'href', 'thumbnail'),
            'duration': int_or_none(xpath_text(video_xml, './/Runtime', 'duration')),
            'age_limit': int_or_none(xpath_text(video_xml, './/AgeLimit', 'age limit')),
            'formats': formats,
        }
