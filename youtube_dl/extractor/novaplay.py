# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NovaPlayIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?play.nova\.bg\/video\/.*\/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://play.nova.bg/video/vremeto/season-7/vreme-ob-2021-03-27/544702',
        'md5': 'bc9f79ce1d884551c75635badc91971e',
        'info_dict': {
            'id': '544702',
            'ext': 'mp4',
            'title': 'Прогноза за времето (27.03.2021 - обедна емисия)',
            'thumbnail': 'https://nbg-img.fite.tv/img/544702_460x260.jpg',
            'description': '27 March'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        thumbnail = self._og_search_property('image', webpage)
        api_url = 'https://nbg-api.fite.tv/api/v2/videos/' + video_id + '/streams'
        m3u8_url = self._download_json(api_url, video_id, headers={
            'x-flipps-user-agent': 'Flipps/75/9.7'
        })[0]['url']
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'url': m3u8_url,
            'title': title,
            'thumbnail': thumbnail,
            'description': self._og_search_description(webpage),
            'formats': formats
        }
