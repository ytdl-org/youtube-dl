# coding: utf-8
from __future__ import unicode_literals

import re
from ..compat import compat_urllib_request
from .common import InfoExtractor


class StopGameIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stopgame\.ru/(gamemovie/show|videoplayer|show)/(?P<id>[0-9a-zA-Z]+)'

    _TESTS = [{
        'url': 'https://stopgame.ru/gamemovie/show/390',
        'file': 'После\ титров.\ Бриолин-390.mp4',
        'md5': 'a4d89bd7dc8f5db500b00894444e1bea',
        'info_dict': {
            'id': '390',
            'ext': 'mp4',
            'title': 'После титров. «Бриолин»',
            'description': 'Вот и добрались наши голоса до трудов группировки мультипликаторов, прославившейся благодаря сериалу How It Should Have Ended. В «После титров» смысл несколько иной (о чём само название и сообщает), но менее забавными видеоролики из-за этого не становятся.',
            'thumbnail': r'https://images.stopgame.ru/video/logos/84140.jpg'
        }
    }, {
        'url': 'https://stopgame.ru/show/84140/posle_titrov_briolin',
        'file': 'После титров. Бриолин-84140.mp4',
        'md5': 'a4d89bd7dc8f5db500b00894444e1bea',
        'info_dict': {
            'id': '84140',
            'ext': 'mp4',
            'title': 'После титров. «Бриолин»',
            'description': None,
            'thumbnail': None
        }
    }, {
        'url': 'https://stopgame.ru/videoplayer/84250',
        'file': 'gamescom\ 2016.\ Геймплей-84250.mp4',
        'md5': '1cc53dea8a6ac86eea9aa7a5d235a2f2',
        'info_dict': {
            'id': '84250',
            'ext': 'mp4',
            'title': 'gamescom 2016. Геймплей',
            'description': None,
            'thumbnail': None
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'<h1>(.+?)</h1>', webpage, 'title', default=None)
        description = self._html_search_regex(
            r'<div itemprop="description">(.+?)</div>',
            webpage, 'description', default=None)
        thumbnail = self._html_search_meta(
            'thumbnail', webpage, 'thumbnail', default=None)
        if title is None:
            title = self._html_search_regex(
                r'title: \"(.+?)\"', webpage, 'title', default=None)

        video_url = self._html_search_regex(
            r'\[360p\](.+?),', webpage, 'video URL', default=None)
        if video_url is None:
            video_url = self._html_search_regex(
                r'file:\"(.+?)\"', webpage, 'video URL', default=None)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'ext': 'mp4',
            'url': video_url
        }


class StopGamePlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stopgame\.ru/(gamemovie/genre)/(?P<id>[0-9a-zA-Z]+)'

    _TESTS = [{
        'url': 'http://stopgame.ru/gamemovie/genre/vghs',
        'playlist_mincount': 21,
        'info_dict': {
            'id': 'vghs',
            'title': 'Гимназия Видеоигр / Машинима',
        }
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        playlist_title = self._html_search_regex(
            r'<h1>(.+?)</h1>', webpage, 'title')

        entries = []
        for mobj in re.findall(
            r'<div class=\"title lent-title\"><a href=\"(.+?)\">(.+?)</a>',
                webpage):
            mobj0 = "https://stopgame.ru" + mobj[0]
            entry_webpage = compat_urllib_request.urlopen(mobj0).read()
            try:
                video_url = re.search(r'\[360p\](.+?),', entry_webpage)
                video_url = video_url.group(0).split("]")[1].split(",")[0]
            except BaseException:
                video_url = re.search(r'file:\"(.+?)\"', entry_webpage)
                video_url = video_url.group(0).split('\"')[1]
            entry = dict(
                url=video_url,
                ie_key=None,
                id=mobj[0].split("/")[3],
                title=mobj[1])
            entries.append(entry)
        return self.playlist_result(entries, playlist_id, playlist_title)
