# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
import re


class RuutuIE(InfoExtractor):
    _VALID_URL = r'http://(www\.)?ruutu\.fi/ohjelmat/(?:[^/]+/)?(?P<id>.*)$'
    _TESTS = [
        {
            'url': 'http://www.ruutu.fi/ohjelmat/oletko-aina-halunnut-tietaa-mita-tapahtuu-vain-hetki-ennen-lahetysta-nyt-se-selvisi',
            'md5': 'ab2093f39be1ca8581963451b3c0234f',
            'info_dict': {
                'id': 'oletko-aina-halunnut-tietaa-mita-tapahtuu-vain-hetki-ennen-lahetysta-nyt-se-selvisi',
                'ext': 'mp4',
                'title': 'Oletko aina halunnut tietää mitä tapahtuu vain hetki ennen lähetystä? - Nyt se selvisi!',
                'description': 'Toinen toistaan huikeampia ohjelmaideoita ja täysin päätöntä sekoilua? No sitä juuri nimenomaan. Metro Helsingin Iltapäivän vieraaksi saapui Tuomas Kauhanen ja he Petra Kalliomaan kanssa keskustelivat hieman ennen lähetyksen alkua, mutta kamerat olivatkin jo päällä.',
            },
            'params': {
                'format': 'http-1000',
            }
        },
        {
            'url': 'http://www.ruutu.fi/ohjelmat/superpesis/superpesis-katso-koko-kausi-ruudussa',
            'md5': '065a10ae4d5b8cfd9d0c3d332465e3d9',
            'info_dict': {
                'id': 'superpesis-katso-koko-kausi-ruudussa',
                'ext': 'mp4',
                'title': 'Superpesis: katso koko kausi Ruudussa',
                'description': 'Huippujännittävän Superpesiksen suoria ottelulähetyksiä seurataan Ruudussa kauden alusta viimeiseen finaaliin asti. Katso lisätiedot osoitteesta ruutu.fi/superpesis.',
            },
            'params': {
                'format': 'http-1000',
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        media_id = self._html_search_regex(r'data-media-id="(\d+)"', webpage, 'media_id')
        media_json = self._parse_json(self._search_regex(r'jQuery.extend\([^,]+, (.*)\);', webpage, 'media_data'), video_id)
        xml_url = media_json['ruutuplayer']['xmlUrl'].replace('{ID}', media_id)
        media_xml = self._download_xml(xml_url, media_id)

        formats = []
        parsed_urls = []
        for fmt in media_xml.findall('.//Clip//'):
            url = fmt.text
            if not fmt.tag.endswith('File') or url in parsed_urls or \
                    'NOT_USED' in url:
                continue

            if url.endswith('m3u8'):
                formats.extend(self._extract_m3u8_formats(url, media_id, m3u8_id='hls'))
                parsed_urls.append(url)
            elif url.endswith('f4m'):
                formats.extend(self._extract_f4m_formats(url, media_id, f4m_id='hds'))
                parsed_urls.append(url)
            else:
                if not fmt.tag.startswith('HTTP'):
                    continue
                proto = compat_urllib_parse_urlparse(url).scheme
                width_str, height_str = fmt.get('resolution').split('x')
                tbr = int(fmt.get('bitrate', 0))
                formats.append({
                    'format_id': '%s-%d' % (proto, tbr),
                    'url': url,
                    'width': int(width_str),
                    'height': int(height_str),
                    'tbr': tbr,
                    'ext': url.rsplit('.', 1)[-1],
                    'live': True,
                    'protocol': proto,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': int(media_xml.find('.//Runtime').text),
            'age_limit': int(media_xml.find('.//AgeLimit').text),
        }
