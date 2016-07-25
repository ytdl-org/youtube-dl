# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
    urlencode_postdata,
)
import re


class SdarotBaseIE(InfoExtractor):
    def get_request(self, form, url):
            request = sanitized_Request('http://www.sdarot.pm/ajax/watch', urlencode_postdata(form))
            request.add_header('Pragma', 'no-cache')
            request.add_header('Origin', 'Origin: http://www.sdarot.pm')
            request.add_header('Accept-Encoding', 'gzip, deflate')
            request.add_header('Accept-Language', 'en-US,en;q=0.8,he;q=0.6')
            request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36')
            request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
            request.add_header('Accept', '*/*')
            request.add_header('Cache-Control', 'no-cache')
            request.add_header('X-Requested-With', 'XMLHttpRequest')
            request.add_header('Connection', 'keep-alive')
            request.add_header('Referer', url)

            return request

    def get_token(self, url, serie, season, episode):
            video_id = '%s-%s-%s' % (serie, season, episode)

            form = {
                'preWatch': 'true',
                'SID': serie,
                'season': season,
                'ep': episode
            }

            request = self.get_request(form, url)

            token = self._download_webpage(request, video_id, None)

            return token

    def get_info(self, url, serie, season, episode, token, title):
            video_id = '%s-%s-%s' % (serie, season, episode)

            form = {
                'watch': 'false',
                'token': token,
                'serie': serie,
                'season': season,
                'episode': episode
            }

            # request.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
            request = self.get_request(form, url)

            response = self._download_json(request, video_id, None)

            url = 'http://%s/watch/sd/%s.mp4?token=%s&time=%s' % (response['url'], response['VID'], response['watch']['sd'], response['time'])
            return {
                'id': video_id,
                'url': url,
                'title': title
            }

    def get_key(self, serie, season, episode):
        return '%s-%s-%s' % (serie, season, episode)


class SdarotEpisodeIE(SdarotBaseIE):
    _VALID_URL = r'http://(?:www\.)?sdarot\.pm/watch/(?P<serie>\d+)-(?P<title>.*)?/season/(?P<season>[0-9]+)/episode/(?P<episode>[0-9]+)'
    _TEST = {
        'url': 'http://www.sdarot.pm/watch/27-%D7%9E%D7%93-%D7%9E%D7%9F-mad-men/season/1/episode/1',
        'info_dict': {
            'id': '27-1-1',
            'ext': 'mp4',
            'title': '%D7%9E%D7%93-%D7%9E%D7%9F-mad-men'
        }
    }

    def _real_extract(self, url):
        m = re.search(self._VALID_URL, url)
        serie = m.group(1)
        title = m.group(2)
        season = m.group(3)
        episode = m.group(4)

        video_id = '%s-%s-%s' % (serie, season, episode)
        token = self.get_token(url, serie, season, episode)

        # Free users need to wait 30 seconds before they can get the video link
        self._sleep(30, video_id, None)

        return self.get_info(url, serie, season, episode, token, title)


class SdarotSeasonIE(SdarotBaseIE):
    _VALID_URL = r'http:\//(?:www\.)?sdarot\.pm/watch/(?P<serie>\d+)-(?P<title>.*)?/season/(?P<season>[0-9]+)$'
    _TEST = {
        'url': 'http://www.sdarot.pm/watch/27-%D7%9E%D7%93-%D7%9E%D7%9F-mad-men/season/1',
        'info_dict': {
            'id': '27-1',
            'title': '%D7%9E%D7%93-%D7%9E%D7%9F-mad-men'
        },
        'playlist_count': 13
    }

    def _real_extract(self, url):
        m = re.search(self._VALID_URL, url)
        serie = m.group(1)
        title = m.group(2)
        season = m.group(3)

        video_id = '%s-%s' % (serie, season)
        webpage = self._download_webpage(url, video_id)
        episodes_count = len(re.findall(r'(data-episode)', webpage))
        entries = []
        tokens = {}
        for i in range(episodes_count):
            episode = i + 1
            key = self.get_key(serie, season, episode)
            token = self.get_token(url, serie, season, episode)
            tokens[key] = token

        # Free users need to wait 30 seconds before they can get the video link
        self._sleep(30, video_id, None)

        for i in range(episodes_count):
            episode = i + 1
            key = self.get_key(serie, season, episode)
            token = tokens[key]
            info = self.get_info(url, serie, season, episode, token, title)
            entries.append(info)

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': video_id,
            'title': title,
        }


class SdarotSerieIE(SdarotBaseIE):
    _VALID_URL = r'http:\//(?:www\.)?sdarot\.pm/watch/(?P<serie>\d+)-(?P<title>.*)?/$'
    _TEST = {
        'url': 'http://www.sdarot.pm/watch/27-%D7%9E%D7%93-%D7%9E%D7%9F-mad-men/',
        'info_dict': {
            'id': '27',
            'ext': 'mp4',
            'title': '%D7%9E%D7%93-%D7%9E%D7%9F-mad-men'
        },
        'playlist': [],
        'skip': 'too long for tests'
    }

    def _real_extract(self, url):
        m = re.search(self._VALID_URL, url)
        serie = m.group(1)
        title = m.group(2)

        video_id = '%s' % serie

        webpage = self._download_webpage(url, video_id)
        seasons_count = len(re.findall(r'(data-season)', webpage))

        entries = []
        tokens = {}

        for i in range(seasons_count):
            season = i + 1
            season_url = '%s/season/%s' % (url, season)
            season_webpage = self._download_webpage(season_url, video_id)
            episodes_count = len(re.findall(r'(data-episode)', season_webpage))
            for x in range(episodes_count):
                episode = x + 1
                token = self.get_token(url, serie, season, episode)
                key = self.get_key(serie, season, episode)
                tokens[key] = token

        # Free users need to wait 30 seconds before they can get the video link
        self._sleep(30, video_id, None)

        for i in range(seasons_count):
            season = i + 1
            season_url = '%s/season/%s' % (url, season)
            season_webpage = self._download_webpage(season_url, video_id)
            episodes_count = len(re.findall(r'(data-episode)', season_webpage))
            for x in range(episodes_count):
                episode = x + 1
                key = self.get_key(serie, season, episode)
                token = tokens[key]
                info = self.get_info(url, serie, season, episode, token, title)
                entries.append(info)

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': video_id,
            'title': title
        }
