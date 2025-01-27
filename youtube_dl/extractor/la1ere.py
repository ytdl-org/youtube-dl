# coding: utf-8
from __future__ import unicode_literals

from urllib.parse import quote

from .common import InfoExtractor


class La1ereExrtractorBaseIE(InfoExtractor):

    def _extract_given_title(self, webpage, title):

        # get the ID
        video_id = self._html_search_regex(r'data-id="([^"]+)"', webpage, 'id')

        # request the mpd-request url
        json_request_url = 'https://k7.ftven.fr/videos/%s?country_code=FR&w=937&h=527&screen_w=1920&screen_h=1200&player_version=5.116.1&domain=la1ere.francetvinfo.fr&device_type=desktop&browser=chrome&browser_version=126&os=linux&diffusion_mode=tunnel&gmt=-0400&capabilities=drm' % video_id
        json_request = self._download_json(json_request_url, video_id)
        mpd_request_url = json_request['video']['url']

        # using the mpd-request url, auth to get the full mpd URL with auth params
        auth_request_url = 'https://hdfauth.ftven.fr/esi/TA?format=json&url=%s' % quote(mpd_request_url)
        auth_request = self._download_json(auth_request_url, video_id)

        # this is the full playlist URL with auth params
        playlist_url = auth_request['url']
        return video_id, playlist_url


class La1ereExtractorPageIE(La1ereExrtractorBaseIE):
    _VALID_URL = r'https://la1ere.francetvinfo.fr/(?P<region>[^/]+)/programme-video/diffusion/(?P<page>[^\.]+).html'
    _TEST = {
        'skip': 'Only available in FR',
        'url': 'https://la1ere.francetvinfo.fr/martinique/programme-video/diffusion/4774522-origine-kongo.html',
        'info_dict': {
            'ext': 'mp4',
            'title': 'Origine Kongo',
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'la1ere')

        title = self._html_search_regex(r'<h1 .*title.*>(.+?)</h1>', webpage, 'title')

        video_id, playlist_url = self._extract_given_title(webpage, title)

        # get the mpd playlist
        formats = self._extract_mpd_formats(playlist_url, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class La1ereExtractorShowPageIE(La1ereExrtractorBaseIE):
    _VALID_URL = r'https://la1ere.francetvinfo.fr/(?P<region>[^/]+)/programme-video/(?P<show>[^/]+)/diffusion/(?P<page>[^\.]+).html'
    _TEST = {
        'skip': 'Only available in FR',
        'url': 'https://la1ere.francetvinfo.fr/guadeloupe/programme-video/la1ere_guadeloupe_le-13h-en-guadeloupe/diffusion/5643549-emission-du-lundi-29-janvier-2024.html',
        'info_dict': {
            'ext': 'mp4',
            'title': '13H en Guadeloupe - Émission du lundi 29 janvier 2024',
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'la1ere')

        series_name = self._html_search_regex(r'<span class="m-dtv-player-title__subtitle">(.+?)</span>', webpage, 'series_name')
        episode_name = self._html_search_regex(r'<h1 .*title.*>(.+?)</h1>', webpage, 'episode_name')
        title = f'{series_name} - {episode_name}'

        video_id, playlist_url = self._extract_given_title(webpage, title)

        # get the m3u8 playlist
        formats = self._extract_m3u8_formats(playlist_url, video_id)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }



