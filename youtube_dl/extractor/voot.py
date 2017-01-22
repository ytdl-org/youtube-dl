# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VootIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?voot\.com/shows/(?:.+?[/-]?)/1/(?:.+?[0-9]?)/(?:.+?[/-]?)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.voot.com/shows/ishq-ka-rang-safed/1/360558/is-this-the-end-of-kamini-/441353',
        'info_dict': {
            'id': '441353',
            'ext': 'mp4',
            'title': 'Ishq Ka Rang Safed - Season 01 - Episode 340',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    _GET_CONTENT_TEMPLATE = 'https://wapi.voot.com/ws/ott/getMediaInfo.json?platform=Web&pId=3&mediaId=%s'

    def _download_json(self, url_or_request, video_id, note='Downloading JSON metadata', fatal=True):
        json_data = super(VootIE, self)._download_json(url_or_request, video_id, note, fatal=fatal)
        if json_data['status']['code'] != 0:
            if fatal:
                raise ExtractorError(json_data['status']['message'])
            return None
        return json_data['assets']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            self._GET_CONTENT_TEMPLATE % video_id,
            video_id)

        thumbnail = ''
        formats = []

        if video_data:
            format_url = video_data.get('URL')
            formats.extend(self._extract_m3u8_formats(format_url, video_id, 'mp4', m3u8_id='hls', fatal=False))

        if video_data['Pictures']:
            for picture in video_data['Pictures']:
                #Get only first available thumbnail
                thumbnail = picture.get('URL')
                break

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_data.get('MediaName'),
            'thumbnail': thumbnail,
            'formats':formats,
        }
