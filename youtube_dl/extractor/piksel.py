# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    dict_get,
    int_or_none,
    unescapeHTML,
    parse_iso8601,
)


class PikselIE(InfoExtractor):
    _VALID_URL = r'https?://player\.piksel\.com/v/(?P<id>[a-z0-9]+)'
    _TEST = {
        'url': 'http://player.piksel.com/v/nv60p12f',
        'md5': 'd9c17bbe9c3386344f9cfd32fad8d235',
        'info_dict': {
            'id': 'nv60p12f',
            'ext': 'mp4',
            'title': 'فن الحياة  - الحلقة 1',
            'description': 'احدث برامج الداعية الاسلامي " مصطفي حسني " فى رمضان 2016علي النهار نور',
            'timestamp': 1465231790,
            'upload_date': '20160606',
        }
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=["\'](?P<url>(?:https?:)?//player\.piksel\.com/v/[a-z0-9]+)',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        app_token = self._search_regex(
            r'clientAPI\s*:\s*"([^"]+)"', webpage, 'app token')
        response = self._download_json(
            'http://player.piksel.com/ws/ws_program/api/%s/mode/json/apiv/5' % app_token,
            video_id, query={
                'v': video_id
            })['response']
        failure = response.get('failure')
        if failure:
            raise ExtractorError(response['failure']['reason'], expected=True)
        video_data = response['WsProgramResponse']['program']['asset']
        title = video_data['title']

        formats = []

        m3u8_url = dict_get(video_data, [
            'm3u8iPadURL',
            'ipadM3u8Url',
            'm3u8AndroidURL',
            'm3u8iPhoneURL',
            'iphoneM3u8Url'])
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        asset_type = dict_get(video_data, ['assetType', 'asset_type'])
        for asset_file in video_data.get('assetFiles', []):
            # TODO: extract rtmp formats
            http_url = asset_file.get('http_url')
            if not http_url:
                continue
            tbr = None
            vbr = int_or_none(asset_file.get('videoBitrate'), 1024)
            abr = int_or_none(asset_file.get('audioBitrate'), 1024)
            if asset_type == 'video':
                tbr = vbr + abr
            elif asset_type == 'audio':
                tbr = abr

            format_id = ['http']
            if tbr:
                format_id.append(compat_str(tbr))

            formats.append({
                'format_id': '-'.join(format_id),
                'url': unescapeHTML(http_url),
                'vbr': vbr,
                'abr': abr,
                'width': int_or_none(asset_file.get('videoWidth')),
                'height': int_or_none(asset_file.get('videoHeight')),
                'filesize': int_or_none(asset_file.get('filesize')),
                'tbr': tbr,
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnailUrl'),
            'timestamp': parse_iso8601(video_data.get('dateadd')),
            'formats': formats,
        }
