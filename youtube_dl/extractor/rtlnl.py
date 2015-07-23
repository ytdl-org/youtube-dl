# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
)


class RtlNlIE(InfoExtractor):
    IE_NAME = 'rtl.nl'
    IE_DESC = 'rtl.nl and rtlxl.nl'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?
        (?:
            rtlxl\.nl/\#!/[^/]+/|
            rtl\.nl/system/videoplayer/(?:[^/]+/)+(?:video_)?embed\.html\b.+?\buuid=
        )
        (?P<id>[0-9a-f-]+)'''

    _TESTS = [{
        'url': 'http://www.rtlxl.nl/#!/rtl-nieuws-132237/6e4203a6-0a5e-3596-8424-c599a59e0677',
        'md5': 'cc16baa36a6c169391f0764fa6b16654',
        'info_dict': {
            'id': '6e4203a6-0a5e-3596-8424-c599a59e0677',
            'ext': 'mp4',
            'title': 'RTL Nieuws - Laat',
            'description': 'md5:6b61f66510c8889923b11f2778c72dc5',
            'timestamp': 1408051800,
            'upload_date': '20140814',
            'duration': 576.880,
        },
    }, {
        'url': 'http://www.rtl.nl/system/videoplayer/derden/rtlnieuws/video_embed.html#uuid=84ae5571-ac25-4225-ae0c-ef8d9efb2aed/autoplay=false',
        'md5': 'dea7474214af1271d91ef332fb8be7ea',
        'info_dict': {
            'id': '84ae5571-ac25-4225-ae0c-ef8d9efb2aed',
            'ext': 'mp4',
            'timestamp': 1424039400,
            'title': 'RTL Nieuws - Nieuwe beelden Kopenhagen: chaos direct na aanslag',
            'thumbnail': 're:^https?://screenshots\.rtl\.nl/system/thumb/sz=[0-9]+x[0-9]+/uuid=84ae5571-ac25-4225-ae0c-ef8d9efb2aed$',
            'upload_date': '20150215',
            'description': 'Er zijn nieuwe beelden vrijgegeven die vlak na de aanslag in Kopenhagen zijn gemaakt. Op de video is goed te zien hoe omstanders zich bekommeren om één van de slachtoffers, terwijl de eerste agenten ter plaatse komen.',
        }
    }, {
        # empty synopsis and missing episodes (see https://github.com/rg3/youtube-dl/issues/6275)
        'url': 'http://www.rtl.nl/system/videoplayer/derden/rtlnieuws/video_embed.html#uuid=f536aac0-1dc3-4314-920e-3bd1c5b3811a/autoplay=false',
        'info_dict': {
            'id': 'f536aac0-1dc3-4314-920e-3bd1c5b3811a',
            'ext': 'mp4',
            'title': 'RTL Nieuws - Meer beelden van overval juwelier',
            'thumbnail': 're:^https?://screenshots\.rtl\.nl/system/thumb/sz=[0-9]+x[0-9]+/uuid=f536aac0-1dc3-4314-920e-3bd1c5b3811a$',
            'timestamp': 1437233400,
            'upload_date': '20150718',
            'duration': 30.474,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # encrypted m3u8 streams, georestricted
        'url': 'http://www.rtlxl.nl/#!/afl-2-257632/52a74543-c504-4cde-8aa8-ec66fe8d68a7',
        'only_matching': True,
    }, {
        'url': 'http://www.rtl.nl/system/videoplayer/derden/embed.html#!/uuid=bb0353b0-d6a4-1dad-90e9-18fe75b8d1f0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        uuid = self._match_id(url)
        info = self._download_json(
            'http://www.rtl.nl/system/s4m/vfd/version=2/uuid=%s/fmt=adaptive/' % uuid,
            uuid)

        material = info['material'][0]
        title = info['abstracts'][0]['name']
        subtitle = material.get('title')
        if subtitle:
            title += ' - %s' % subtitle
        description = material.get('synopsis')

        meta = info.get('meta', {})

        # m3u8 streams are encrypted and may not be handled properly by older ffmpeg/avconv.
        # To workaround this previously adaptive -> flash trick was used to obtain
        # unencrypted m3u8 streams (see https://github.com/rg3/youtube-dl/issues/4118)
        # and bypass georestrictions as well.
        # Currently, unencrypted m3u8 playlists are (intentionally?) invalid and therefore
        # unusable albeit can be fixed by simple string replacement (see
        # https://github.com/rg3/youtube-dl/pull/6337)
        # Since recent ffmpeg and avconv handle encrypted streams just fine encrypted
        # streams are used now.
        videopath = material['videopath']
        m3u8_url = meta.get('videohost', 'http://manifest.us.rtl.nl') + videopath

        formats = self._extract_m3u8_formats(m3u8_url, uuid, ext='mp4')

        video_urlpart = videopath.split('/adaptive/')[1][:-5]
        PG_URL_TEMPLATE = 'http://pg.us.rtl.nl/rtlxl/network/%s/progressive/%s.mp4'

        formats.extend([
            {
                'url': PG_URL_TEMPLATE % ('a2m', video_urlpart),
                'format_id': 'pg-sd',
            },
            {
                'url': PG_URL_TEMPLATE % ('a3m', video_urlpart),
                'format_id': 'pg-hd',
                'quality': 0,
            }
        ])
        self._sort_formats(formats)

        thumbnails = []

        for p in ('poster_base_url', '"thumb_base_url"'):
            if not meta.get(p):
                continue

            thumbnails.append({
                'url': self._proto_relative_url(meta[p] + uuid),
                'width': int_or_none(self._search_regex(
                    r'/sz=([0-9]+)', meta[p], 'thumbnail width', fatal=False)),
                'height': int_or_none(self._search_regex(
                    r'/sz=[0-9]+x([0-9]+)',
                    meta[p], 'thumbnail height', fatal=False))
            })

        return {
            'id': uuid,
            'title': title,
            'formats': formats,
            'timestamp': material['original_date'],
            'description': description,
            'duration': parse_duration(material.get('duration')),
            'thumbnails': thumbnails,
        }
