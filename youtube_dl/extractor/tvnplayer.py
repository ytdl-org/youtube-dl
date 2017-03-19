# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import determine_ext


class TVNIE(InfoExtractor):
    IE_NAME = 'tvn'
    _VALID_URL = r'https?://(?:[^/]+\.)?tvn\.pl/.*?,(?P<id>\d+),o\.html'

    _TEST = {
        'url': 'http://nawspolnej.tvn.pl/odcinki-online/odcinek-2440,71587,o.html',
        'md5': '1de06bc87774c334ac473f79ee4a5719',
        'info_dict': {
            'id': '70618',
            'ext': 'mp4',
            'title': 'Na Wspólnej, odc. 2440',
            'description': 'md5:73b915646094286a6b3c159c79c67e38',
        },
    }

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        video_id = self._search_regex([
            r'/player.pl/.*?,(\d+),autoplay.html',
            r'var\s+var_id\s+=\s+[\'"](\d+)'], webpage, 'video id')
        return self.url_result('http://player.pl/,%s.html' % video_id, ie=TVNPlayerIE.ie_key())


class TVNPlayerIE(InfoExtractor):
    IE_NAME = 'tvnplayer'
    _VALID_URL = r'https?://player\.pl/.*?,(?P<id>\d+)(?:,\w+)?\.html'

    _TEST = {
        'url': 'http://player.pl/seriale-online/na-wspolnej-odcinki,144/odcinek-2436,S00E2436,70614.html',
        'md5': '1e1457420045d36c488c94cf35d8e9cb',
        'info_dict': {
            'id': '70614',
            'ext': 'mp4',
            'title': 'Na Wspólnej, odc. 2436',
            'description': 'md5:651cbbc050c3716200cb3f61c24e85b5',
        },
    }


    def determine_bitrate(self, url):
        str_bitrate = url.partition("?")[0].rpartition('.')[0].rpartition("_")[-1]
        return int(str_bitrate)/1000

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_url = 'http://player.pl/api/?platform=ConnectedTV&terminal=Panasonic&format=json&authKey=064fda5ab26dc1dd936f5c6e84b7d3c2&v=3.1&m=getItem&id='
        json_data = self._download_json(json_url + video_id, video_id)
        item = json_data['item']
        title = item['serie_title']
        description = item['lead']
        if item['season'] > 0:
            title += ', sezon ' + str(item['season'])
        if item['episode'] > 0:
            title += ', odc. ' + str(item['episode'])
        formats = []
        for video in item['videos']['main']['video_content']:
            video_url = video['url']
            formats.append({
                'format_id': video['profile_name'],
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
                'tbr': self.determine_bitrate(video_url),
                'description': description
            })

        self._sort_formats(formats)

        # ISM manifest, doesn't work
        '''
        json_data = self._download_json('http://player.pl/playlist-vod/' + video_id + '.json', video_id)
        for movie in json_data['playlist']['movies'].values():
          if type(movie).__name__ == 'dict' and 'episode_id' in movie and video_id == movie['episode_id']:
            title = movie['title']
            if not movie['one_episode']:
              title += ", odc. " + movie['episode']
            formats = self._extract_ism_formats(movie['profiles']['wv']['url'], video_id)
            formats = self._extract_ism_formats(movie['profiles']['row']['url'], video_id)
        '''

        extracted_info = {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'season_id': item['season'],
            'episode_id': item['episode'],
        }

        return extracted_info


class TVNPlayerSeriesIE(InfoExtractor):
    IE_NAME = 'tvnplayer:series'
    _VALID_URL = r'https?://player\.pl/.*?-odcinki,(?P<id>\d+)/(?:\?.*)?$'

    _TESTS = [{
        'url': 'http://player.pl/seriale-online/brzydula-odcinki,52/?player&pl_source=pop-up&pl_campaign=logCRM#',
        'info_dict': {
            'title': 'Brzydula',
            'id': '52',
        },
        'playlist_count': 235,
    }, {
        'url': 'http://player.pl/seriale-online/singielka-odcinki,3784/',
        'info_dict': {
            'title': 'Singielka',
            'id': '3784',
        },
        'playlist_count': 198,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage('http://player.pl/informacje,p,%s.html?noAds=1&ajax=1' % playlist_id, playlist_id)

        playlist_title = self._html_search_regex(r'<h1>([^<]+)</h1>', webpage, 'series title')

        videos_ids = re.findall(r'data-article-id\s*=\s*["\'](\d+).*?class\s*=\s*["\']play', webpage)
        entries = [self.url_result('http://player.pl/,%s.html' % video_id, ie=TVNPlayerIE.ie_key()) for video_id in videos_ids]

        return self.playlist_result(entries, playlist_id, playlist_title)