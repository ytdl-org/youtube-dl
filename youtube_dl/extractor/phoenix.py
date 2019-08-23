from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    xpath_text,
    determine_ext,
    ExtractorError,
)


class PhoenixIE(InfoExtractor):
    IE_NAME = 'phoenix.de'
    _VALID_URL = r'''(?x)https?://(?:www\.)?phoenix\.de/content/
        (?:
            phoenix/die_sendungen/(?:[^/]+/)?
        )?
        (?P<id>[0-9]+)'''
    _TESTS = [
        {
            'url': 'http://www.phoenix.de/content/884301',
            'md5': 'ed249f045256150c92e72dbb70eadec6',
            'info_dict': {
                'id': '884301',
                'ext': 'mp4',
                'title': 'Michael Krons mit Hans-Werner Sinn',
                'description': 'Im Dialog - Sa. 25.10.14, 00.00 - 00.35 Uhr',
                'upload_date': '20141025',
                'uploader': 'Im Dialog',
            }
        },
        {
            'url': 'http://www.phoenix.de/content/phoenix/die_sendungen/869815',
            'only_matching': True,
        },
        {
            'url': 'http://www.phoenix.de/content/phoenix/die_sendungen/diskussionen/928234',
            'only_matching': True,
        },
    ]

    def extract_from_xml_url(self, video_id, xml_url):
        doc = self._download_xml(
            xml_url, video_id,
            note='Downloading video info',
            errnote='Failed to download video info')

        status_code = xpath_text(doc, './status/statuscode')
        if status_code and status_code != 'ok':
            if status_code == 'notVisibleAnymore':
                message = 'Video %s is not available' % video_id
            else:
                message = '%s returned error: %s' % (self.IE_NAME, status_code)
            raise ExtractorError(message, expected=True)

        title = xpath_text(doc, './/information/title', 'title', True)

        urls = []
        formats = []
        for fnode in doc.findall('.//formitaeten/formitaet'):
            video_url = xpath_text(fnode, 'url')
            if not video_url or video_url in urls:
                continue
            urls.append(video_url)

            is_available = 'http://www.metafilegenerator' not in video_url
            geoloced = 'static_geoloced_online' in video_url
            if not is_available or geoloced:
                continue

            format_id = fnode.attrib['basetype']
            format_m = re.match(r'''(?x)
                (?P<vcodec>[^_]+)_(?P<acodec>[^_]+)_(?P<container>[^_]+)_
                (?P<proto>[^_]+)_(?P<index>[^_]+)_(?P<indexproto>[^_]+)
            ''', format_id)

            ext = determine_ext(video_url, None) or format_m.group('container')

            if ext == 'meta':
                continue
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    video_url, video_id, fatal=False))
            elif ext == 'm3u8':
                # the certificates are misconfigured (see
                # https://github.com/ytdl-org/youtube-dl/issues/8665)
                if video_url.startswith('https://'):
                    continue
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    video_url, video_id, f4m_id=format_id, fatal=False))
            else:
                quality = xpath_text(fnode, './quality')
                if quality:
                    format_id += '-' + quality

                abr = int_or_none(xpath_text(fnode, './audioBitrate'), 1000)
                vbr = int_or_none(xpath_text(fnode, './videoBitrate'), 1000)

                tbr = int_or_none(self._search_regex(
                    r'_(\d+)k', video_url, 'bitrate', None))
                if tbr and vbr and not abr:
                    abr = tbr - vbr

                formats.append({
                    'format_id': format_id,
                    'url': video_url,
                    'ext': ext,
                    'acodec': format_m.group('acodec'),
                    'vcodec': format_m.group('vcodec'),
                    'abr': abr,
                    'vbr': vbr,
                    'tbr': tbr,
                    'width': int_or_none(xpath_text(fnode, './width')),
                    'height': int_or_none(xpath_text(fnode, './height')),
                    'filesize': int_or_none(xpath_text(fnode, './filesize')),
                    'protocol': format_m.group('proto').lower(),
                })

        geolocation = xpath_text(doc, './/details/geolocation')
        if not formats and geolocation and geolocation != 'none':
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        self._sort_formats(formats)

        thumbnails = []
        for node in doc.findall('.//teaserimages/teaserimage'):
            thumbnail_url = node.text
            if not thumbnail_url:
                continue
            thumbnail = {
                'url': thumbnail_url,
            }
            thumbnail_key = node.get('key')
            if thumbnail_key:
                m = re.match('^([0-9]+)x([0-9]+)$', thumbnail_key)
                if m:
                    thumbnail['width'] = int(m.group(1))
                    thumbnail['height'] = int(m.group(2))
            thumbnails.append(thumbnail)

        upload_date = unified_strdate(xpath_text(doc, './/details/airtime'))

        return {
            'id': video_id,
            'title': title,
            'description': xpath_text(doc, './/information/detail'),
            'duration': int_or_none(xpath_text(doc, './/details/lengthSec')),
            'thumbnails': thumbnails,
            'uploader': xpath_text(doc, './/details/originChannelTitle'),
            'uploader_id': xpath_text(doc, './/details/originChannelId'),
            'upload_date': upload_date,
            'formats': formats,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        internal_id = self._search_regex(
            r'<div class="phx_vod" id="phx_vod_([0-9]+)"',
            webpage, 'internal video ID')

        api_url = 'http://www.phoenix.de/php/mediaplayer/data/beitrags_details.php?ak=web&id=%s' % internal_id
        return self.extract_from_xml_url(video_id, api_url)
