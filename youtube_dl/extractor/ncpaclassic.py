# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError

class NcpaClassicVideoIE(InfoExtractor):
    _VALID_URL = r'http://www\.ncpa-classic\.com/[0-9]{4}/[0-9]{2}/[0-9]{2}/VID[E A](?P<id>\w*)\.shtml'
    _TESTS = [{
        'url': 'http://www.ncpa-classic.com/2013/05/22/VIDE1369219508996867.shtml',
        'info_dict': {
            'id': '1369219508996867',
            'title': '小泽征尔音乐塾 音乐梦想无国界_古典音乐频道'
        },
        'playlist_count': 8,
    },{
        'url': 'http://ncpa-classic.cntv.cn/2013/05/22/VIDE1369219508996867.shtml',
        'info_dict': {
            'id': '1369219508996867',
            'title': '小泽征尔音乐塾 音乐梦想无国界_古典音乐频道'
        },
        'playlist_count': 8,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url,playlist_id)
        entries = []
        if 'VIDE' in url:
            videoCenterId = self._html_search_regex(r'var initMyAray=\s *\'(?P<videoCenterId>\w*)\'',webpage,'videoCenterId', group='videoCenterId')
            playlist_title = self._html_search_regex(
                r'<title>(?P<title>.*)</title>', webpage,
                'title', group='title')
            api_result = self._download_json(
                'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid=%s&tz=-8&from=000dajuyuan&url=%s&idl=32&idlr=32&modifyed=false' % (
                videoCenterId,url),playlist_id, 'Get playlist links')
            entries = [{'_type': 'video',
                'id':'%s' % idx,
                'title':playlist_title,
                'url': video.get('url')
            }  for idx,video in enumerate(api_result['video']['chapters2'])]

        elif 'VIDA' in url:
            playlist_title = self._html_search_regex(
                r'<title>(?P<title>.*)</title>', webpage,
                'title', group='title')
            sub_titles = re.findall(r'<td.*changeAudio_url.*>(.*)</td>',webpage)
            vida_ids = re.findall(r'"(\w{32})"',webpage)
            for idx,vida_id in enumerate(vida_ids):
                title = sub_titles[idx]
                api_result = self._download_json(
                    'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid=%s&tz=-8&from=000dajuyuan&url=%s&idl=32&idlr=32&modifyed=false' % (
                    vida_id,url),playlist_id, 'Get playlist links')
                video_json = api_result['video']['chapters']
                real_url = video_json[0]['url']
                entries.append({'_type': 'video',
                       'id':'%s' % idx,
                       'title':title,
                       'url': real_url})
        else:
            raise ExtractorError('Unexpected url %s' % url, expected=True)

        return self.playlist_result(
            entries, playlist_id, playlist_title)


class NcpaClassicAudioIE(InfoExtractor):
    _VALID_URL = r'http://www\.ncpa-classic\.com/clt/more/(?P<id>[0-9]*)/index.shtml'
    _TESTS = [{
        'url': 'http://www.ncpa-classic.com/clt/more/416/index.shtml',
        'info_dict': {
            'id': '416',
            'title': '来自维也纳的新年贺礼'
        },
        'playlist_count': 1,
    },{
        'url': 'http://ncpa-classic.cntv.cn/clt/more/416/index.shtml',
        'info_dict': {
            'id': '416',
            'title': '来自维也纳的新年贺礼'
        },
        'playlist_count': 1,
    }]

    def _real_extract(self, url):
         playlist_id = self._match_id(url)
         webpage = self._download_webpage(url,playlist_id)
         videoCenterId = self._html_search_regex(r'\"(?P<videoCenterId>\w{32})\"',webpage,'videoCenterId', group='videoCenterId')
         playlist_title = self._html_search_regex(
             r'<title>(?P<title>.*)</title>', webpage,
             'title', group='title')
         api_result = self._download_json(
             'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid=%s&tz=-8&tai=dajuyuanaudio' % (
             videoCenterId),playlist_id, 'Get playlist links')
         entries = [{'_type': 'video',
             'id': '%s' % idx,
             'title':playlist_title,
             'url': video.get('url')
         }  for idx,video in enumerate(api_result['video']['chapters'])]

         return self.playlist_result(
            entries, playlist_id, playlist_title)
