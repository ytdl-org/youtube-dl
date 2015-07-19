# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import get_element_by_attribute


class SportschauIE(InfoExtractor):
    IE_NAME = 'Sportschau'
    _VALID_URL = r'https?://(?:www\.)?sportschau\.de/\w+(?:/\w+)?/video(?P<id>\w+)\.html'
    _TEST = {
        'url': 'http://www.sportschau.de/tourdefrance/videoseppeltkokainhatnichtsmitklassischemdopingzutun100.html',
        'info_dict': {
            'id': 'seppeltkokainhatnichtsmitklassischemdopingzutun100',
            'ext': 'mp4',
            'title': 'Seppelt: "Kokain hat nichts mit klassischem Doping zu tun"',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'Der ARD-Doping Experte Hajo Seppelt gibt seine Einschätzung zum ersten Dopingfall der diesjährigen Tour de France um den Italiener Luca Paolini ab.',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        ext = '-mc_defaultQuality-h.json'
        json_url = url[:-5] + ext

        json = self._download_json(json_url, video_id)
        thumb_url = json['_previewImage']

        m3u8_url = json['_mediaArray'][1]['_mediaStreamArray'][0]['_stream'][0]
        m3u8_formats = self._extract_m3u8_formats(m3u8_url, video_id, ext="mp4")

        webpage = self._download_webpage(url, video_id)
        title = get_element_by_attribute('class', 'headline', webpage)
        desc = self._html_search_meta('description', webpage)

        return {
            'id': video_id,
            'title': title,
            'formats': m3u8_formats,
            'description': desc,
            'thumbnail': thumb_url,
        }
