# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_request
from ..utils import (
    int_or_none,
    unified_strdate,
)


class EitbIE(InfoExtractor):
    IE_NAME = 'eitb.tv'
    _VALID_URL = r'https?://www\.eitb\.tv/(eu/bideoa|es/video)/[^/]+/\d+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.eitb.tv/es/video/60-minutos-60-minutos-2013-2014/4104995148001/4090227752001/lasa-y-zabala-30-anos/',
        'md5': 'edf4436247185adee3ea18ce64c47998',
        'info_dict': {
            'id': '4090227752001',
            'ext': 'mp4',
            'title': '60 minutos (Lasa y Zabala, 30 años)',
            'description': '',
            'duration': 3996760,
            'upload_date': '20131014',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json('http://mam.eitb.eus/mam/REST/ServiceMultiweb/Video/MULTIWEBTV/%s/' % video_id, video_id)['web_media'][0]

        formats = []
        for rendition in video_data['RENDITIONS']:
            formats.append({
                'url': rendition['PMD_URL'],
                'width': int_or_none(rendition.get('FRAME_WIDTH')),
                'height': int_or_none(rendition.get('FRAME_HEIGHT')),
                'tbr': int_or_none(rendition.get('ENCODING_RATE')),
            })

        # TODO: parse f4m manifest
        request = compat_urllib_request.Request(
            'http://mam.eitb.eus/mam/REST/ServiceMultiweb/DomainRestrictedSecurity/TokenAuth/',
            headers={'Referer': url})
        token_data = self._download_json(request, video_id, fatal=False)
        if token_data:
            m3u8_formats = self._extract_m3u8_formats('%s?hdnts=%s' % (video_data['HLS_SURL'], token_data['token']), video_id, m3u8_id='hls', fatal=False)
            if m3u8_formats:
                formats.extend(m3u8_formats)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data['NAME_ES'],
            'description': video_data.get('SHORT_DESC_ES'),
            'thumbnail': video_data.get('STILL_URL'),
            'duration': int_or_none(video_data.get('LENGTH')),
            'upload_date': unified_strdate(video_data.get('BROADCST_DATE')),
            'formats': formats,
        }
