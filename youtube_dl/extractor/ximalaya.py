# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
import re


class XimalayaBaseIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ximalaya\.com/(?P<artist>[0-9]+)/sound/(?P<id>[0-9]+)'

    _GEO_COUNTRIES = ['CN']

    def _extract_track(self, item_id):
        # http://www.ximalaya.com/tracks/44404156.json

        item_info = self._download_json(
            'http://www.ximalaya.com/tracks/' + item_id + '.json', item_id, encoding='utf-8')
        return {
            'id': item_info.get('id'),
            'url': item_info.get('play_path'),
            'title': item_info.get('title'),
            'creator': item_info.get('nickname'),
            'album': item_info.get('album_title') or item_info.get('title'),
            'artist': item_info.get('nickname'),
        }


class XimalayaSongIE(XimalayaBaseIE):
    IE_NAME = 'Ximalaya:song'
    IE_DEST = '喜马拉雅 - 声音'

    _VALID_URL = r'https?://www\.ximalaya\.com/[0-9]+/sound/(?P<id>[0-9]+)'

    _TEST = [{
        'url': 'http://www.ximalaya.com/20924760/sound/44404156',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            "id": 44404156,
            "play_path_64": "http://audio.xmcdn.com/group31/M07/17/FF/wKgJX1lvHLWyLhhQAD-yGZR0pZM415.m4a",
            "play_path_32": "http://audio.xmcdn.com/group30/M0B/2D/8F/wKgJXllvIQ7SaqGFABhdLSg2RAk021.m4a",
            "play_path": "http://audio.xmcdn.com/group31/M07/17/FF/wKgJX1lvHLWyLhhQAD-yGZR0pZM415.m4a",
            "duration": 515,
            "title": "\u6210\u4e3a\u8427\u5cf0\uff1a\u91d1\u5eb8\u7b14\u4e0b\u7684\u7537\u6027\u8fdb\u5316\u53f2",
            "nickname": "\u4e09\u8054\u751f\u6d3b\u5468\u520a",
            "uid": 20924760,
            "waveform": "group31/M07/17/FF/wKgJX1lvHLCjOxmLAAAKOKKeWgA0908.js",
            "upload_id": "u_45633516",
            "cover_url": "http://fdfs.xmcdn.com/group25/M07/4C/C2/wKgJNlguXkmxdj2zAACSQPpffck622.jpg",
            "cover_url_142": "http://fdfs.xmcdn.com/group25/M07/4C/C2/wKgJNlguXkmxdj2zAACSQPpffck622_web_large.jpg",
            "formatted_created_at": "7\u670819\u65e5 16:53",
            "is_favorited": 'false',
            "play_count": 30628,
            "comments_count": 8,
            "shares_count": 2,
            "favorites_count": 42,
            "album_id": 376177,
            "album_title": "\u4e09\u8054\u2022\u542c\u5468\u520a",
            "intro": 'null',
            "have_more_intro": 'false',
            "time_until_now": "4\u5929\u524d",
            "category_name": "news",
            "category_title": "\u5934\u6761",
            "played_secs": 'null',
            "is_paid": 'false',
            "is_free": 'null',
            "price": 'null',
            "discounted_price": 'null'
        }
    }]

    def _real_extract(self, url):
        return self._extract_track(self._match_id(url))


class XimalayaAlbumIE(XimalayaBaseIE):
    IE_NAME = 'Ximalaya:album'
    IE_DEST = '喜马拉雅 - 专辑'

    _VALID_URL = r'http://www\.ximalaya\.com/[0-9]+/album/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'http://www.ximalaya.com/10936615/album/7651313',
        'info_dict': {
            'id': '7651313',
            'title': '晓说2017',
        },
    }]

    def next_page(self, url):
        webpage = self._download_webpage(url, self._match_id(url))

        entries = re.findall(
            r'<li sound_id="([0-9]+)" class="">',
            webpage)

        # next page
        # r'<a href="(.*)" data-page="[0-9]+" class="pagingBar_page" hashlink="" unencode="" rel="next">'
        next_page_url = self._search_regex(
            r'<a href=\'([0-9a-zA-Z\/?=/]+)\' data-page=\'[0-9]+\' class=\'pagingBar_page\' hashlink=\'\' unencode rel=\'next\'', webpage,
            'next page URL', default=None)

        if next_page_url is not None:
            next_page_url = 'http://www.ximalaya.com' + next_page_url
            entries += self.next_page(next_page_url)

        return entries

    def _real_extract(self, url):
        entries = []
        album_id = self._match_id(url)

        webpage = self._download_webpage(
            url, album_id, note='Download album info',
            errnote='Unable to get album info')

        album_name = self._html_search_regex(
            r'<div class=\"detailContent_title\"[>]<h1[>](.*)</h1[>]</div[>]', webpage,
            'album name')

        entries = re.findall(
            r'<li sound_id="([0-9]+)" class="">',
            webpage)

        # next page
        next_page_url = self._search_regex(
            r'<a href=\'([0-9a-zA-Z\/?=/]+)\' data-page=\'[0-9]+\' class=\'pagingBar_page\' hashlink=\'\' unencode rel=\'next\'', webpage,
            'next page URL', default=None)

        if next_page_url is not None:
            next_page_url = 'http://www.ximalaya.com' + next_page_url
            entries += self.next_page(next_page_url)

        # entries list stores id of tracks
        ret = []
        for track in entries:
            ret.append(self._extract_track(track))

        return self.playlist_result(ret, album_id, album_name)
