# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse


class BaiduVideoIE(InfoExtractor):
    IE_DESC = '百度视频'
    _VALID_URL = r'http://v\.baidu\.com/(?P<type>[a-z]+)/(?P<id>\d+)\.htm'
    _TESTS = [{
        'url': 'http://v.baidu.com/comic/1069.htm?frp=bdbrand&q=%E4%B8%AD%E5%8D%8E%E5%B0%8F%E5%BD%93%E5%AE%B6',
        'info_dict': {
            'id': '1069',
            'title': '中华小当家 TV版 (全52集)',
            'description': 'md5:395a419e41215e531c857bb037bbaf80',
        },
        'playlist_count': 52,
    }, {
        'url': 'http://v.baidu.com/show/11595.htm?frp=bdbrand',
        'info_dict': {
            'id': '11595',
            'title': 're:^奔跑吧兄弟',
            'description': 'md5:1bf88bad6d850930f542d51547c089b8',
        },
        'playlist_mincount': 3,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        category = category2 = mobj.group('type')
        if category == 'show':
            category2 = 'tvshow'

        webpage = self._download_webpage(url, playlist_id)

        playlist_title = self._html_search_regex(
            r'title\s*:\s*(["\'])(?P<title>[^\']+)\1', webpage,
            'playlist title', group='title')
        playlist_description = self._html_search_regex(
            r'<input[^>]+class="j-data-intro"[^>]+value="([^"]+)"/>', webpage,
            playlist_id, 'playlist description')

        site = self._html_search_regex(
            r'filterSite\s*:\s*["\']([^"]*)["\']', webpage,
            'primary provider site')
        api_result = self._download_json(
            'http://v.baidu.com/%s_intro/?dtype=%sPlayUrl&id=%s&site=%s' % (
                category, category2, playlist_id, site),
            playlist_id, 'Get playlist links')

        entries = []
        for episode in api_result[0]['episodes']:
            episode_id = '%s_%s' % (playlist_id, episode['episode'])

            redirect_page = self._download_webpage(
                compat_urlparse.urljoin(url, episode['url']), episode_id,
                note='Download Baidu redirect page')
            real_url = self._html_search_regex(
                r'location\.replace\("([^"]+)"\)', redirect_page, 'real URL')

            entries.append(self.url_result(
                real_url, video_title=episode['single_title']))

        return self.playlist_result(
            entries, playlist_id, playlist_title, playlist_description)
