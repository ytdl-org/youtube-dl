# coding: utf-8
from __future__ import unicode_literals

import re

from .turner import TurnerBaseIE
from ..utils import (
    float_or_none,
    parse_duration,
    xpath_text,
    xpath_attr,
    int_or_none,
    strip_or_none,
)


class CartoonNetworkIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?cartoonnetwork\.com/video/(?:[^/]+/)+(?P<id>[^/?#]+)-(?:clip|episode)\.html'
    _TEST = {
        'url': 'http://www.cartoonnetwork.com/video/teen-titans-go/starfire-the-cat-lady-clip.html',
        'info_dict': {
            'id': '8a250ab04ed07e6c014ef3f1e2f9016c',
            'ext': 'mp4',
            'title': 'Starfire the Cat Lady',
            'description': 'Robin decides to become a cat so that Starfire will finally love him.',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        id_type, video_id = re.search(r"_cnglobal\.cvp(Video|Title)Id\s*=\s*'([^']+)';", webpage).groups()

        video_data = self._download_xml('http://video-api.cartoonnetwork.com/contentXML/' + video_id, video_id)

        media_id = video_data.attrib['id']
        title = xpath_text(video_data, 'headline', fatal=True)

        streams_data = self._download_json(
            'http://medium.ngtv.io/media/%s/tv' % media_id,
            media_id)['media']['tv']
        duration = None
        chapters = []
        formats = []
        for supported_type in ('unprotected', 'bulkaes'):
            stream_data = streams_data.get(supported_type, {})
            m3u8_url = stream_data.get('url') or stream_data.get('secureUrl')
            if not m3u8_url:
                continue
            if stream_data.get('playlistProtection') == 'spe':
                m3u8_url = self._add_akamai_spe_token(
                    'http://token.vgtf.net/token/token_spe',
                    m3u8_url, media_id, {
                        'url': url,
                        'site_name': 'CartoonNetwork',
                        'auth_required': self._search_regex(
                            r'_cnglobal\.cvpFullOrPreviewAuth\s*=\s*(true|false);',
                            webpage, 'auth required', default='false') == 'true',
                    })
            m3u8_formats = self._extract_m3u8_formats(
                m3u8_url, media_id, 'mp4', m3u8_id='hls', fatal=False)
            if '?hdnea=' in m3u8_url:
                for f in m3u8_formats:
                    f['_seekable'] = False
            formats.extend(m3u8_formats)

            duration = float_or_none(stream_data.get('totalRuntime') or
                parse_duration(xpath_text(video_data, 'length') or
                xpath_text(video_data, 'trt')))

            if not chapters:
                for chapter in stream_data.get('contentSegments', []):
                    start_time = float_or_none(chapter.get('start'))
                    duration = float_or_none(chapter.get('duration'))
                    if start_time is None or duration is None:
                        continue
                    chapters.append({
                        'start_time': start_time,
                        'end_time': start_time + duration,
                    })
        self._sort_formats(formats)

        thumbnails = [{
            'id': image.get('cut'),
            'url': image.text,
            'width': int_or_none(image.get('width')),
            'height': int_or_none(image.get('height')),
        } for image in video_data.findall('images/image')]

        return {
            'id': media_id,
            'title': title,
            'description': strip_or_none(xpath_text(video_data, 'description')),
            'duration': duration,
            'timestamp': self._extract_timestamp(video_data),
            'upload_date': xpath_attr(video_data, 'metas', 'version'),
            'series': xpath_text(video_data, 'showTitle'),
            'season_number': int_or_none(xpath_text(video_data, 'seasonNumber')),
            'episode_number': int_or_none(xpath_text(video_data, 'episodeNumber')),
            'chapters': chapters,
            'thumbnails': thumbnails,
            'formats': formats,
        }
