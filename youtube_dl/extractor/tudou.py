# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    float_or_none,
    unescapeHTML,
)


class TudouIE(InfoExtractor):
    IE_NAME = 'tudou'
    _VALID_URL = r'https?://(?:www\.)?tudou\.com/(?:(?:programs|wlplay)/view|(?:listplay|albumplay)/[\w-]{11})/(?P<id>[\w-]{11})'
    _TESTS = [{
        'url': 'http://www.tudou.com/listplay/zzdE77v6Mmo/2xN2duXMxmw.html',
        'md5': '140a49ed444bd22f93330985d8475fcb',
        'info_dict': {
            'id': '159448201',
            'ext': 'f4v',
            'title': '卡马乔国足开大脚长传冲吊集锦',
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1372113489000,
            'description': '卡马乔卡家军，开大脚先进战术不完全集锦！',
            'duration': 289.04,
            'view_count': int,
            'filesize': int,
        }
    }, {
        'url': 'http://www.tudou.com/programs/view/ajX3gyhL0pc/',
        'info_dict': {
            'id': '117049447',
            'ext': 'f4v',
            'title': 'La Sylphide-Bolshoi-Ekaterina Krysanova & Vyacheslav Lopatin 2012',
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1349207518000,
            'description': 'md5:294612423894260f2dcd5c6c04fe248b',
            'duration': 5478.33,
            'view_count': int,
            'filesize': int,
        }
    }]

    _PLAYER_URL = 'http://js.tudouui.com/bin/lingtong/PortalPlayer_177.swf'

    def _url_for_id(self, video_id, quality=None):
        info_url = 'http://v2.tudou.com/f?id=' + compat_str(video_id)
        if quality:
            info_url += '&hd' + quality
        xml_data = self._download_xml(info_url, video_id, 'Opening the info XML page')
        final_url = xml_data.text
        return final_url

    def _real_extract(self, url):
        video_id = self._match_id(url)
        item_data = self._download_json(
            'http://www.tudou.com/tvp/getItemInfo.action?ic=%s' % video_id, video_id)

        youku_vcode = item_data.get('vcode')
        if youku_vcode:
            return self.url_result('youku:' + youku_vcode, ie='Youku')

        title = unescapeHTML(item_data['kw'])
        description = item_data.get('desc')
        thumbnail_url = item_data.get('pic')
        view_count = int_or_none(item_data.get('playTimes'))
        timestamp = int_or_none(item_data.get('pt'))

        segments = self._parse_json(item_data['itemSegs'], video_id)
        # It looks like the keys are the arguments that have to be passed as
        # the hd field in the request url, we pick the higher
        # Also, filter non-number qualities (see issue #3643).
        quality = sorted(filter(lambda k: k.isdigit(), segments.keys()),
                         key=lambda k: int(k))[-1]
        parts = segments[quality]
        result = []
        len_parts = len(parts)
        if len_parts > 1:
            self.to_screen('%s: found %s parts' % (video_id, len_parts))
        for part in parts:
            part_id = part['k']
            final_url = self._url_for_id(part_id, quality)
            ext = (final_url.split('?')[0]).split('.')[-1]
            part_info = {
                'id': '%s' % part_id,
                'url': final_url,
                'ext': ext,
                'title': title,
                'thumbnail': thumbnail_url,
                'description': description,
                'view_count': view_count,
                'timestamp': timestamp,
                'duration': float_or_none(part.get('seconds'), 1000),
                'filesize': int_or_none(part.get('size')),
                'http_headers': {
                    'Referer': self._PLAYER_URL,
                },
            }
            result.append(part_info)

        return {
            '_type': 'multi_video',
            'entries': result,
            'id': video_id,
            'title': title,
        }


class TudouPlaylistIE(InfoExtractor):
    IE_NAME = 'tudou:playlist'
    _VALID_URL = r'https?://(?:www\.)?tudou\.com/listplay/(?P<id>[\w-]{11})\.html'
    _TESTS = [{
        'url': 'http://www.tudou.com/listplay/zzdE77v6Mmo.html',
        'info_dict': {
            'id': 'zzdE77v6Mmo',
        },
        'playlist_mincount': 209,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        playlist_data = self._download_json(
            'http://www.tudou.com/tvp/plist.action?lcode=%s' % playlist_id, playlist_id)
        entries = [self.url_result(
            'http://www.tudou.com/programs/view/%s' % item['icode'],
            'Tudou', item['icode'],
            item['kw']) for item in playlist_data['items']]
        return self.playlist_result(entries, playlist_id)


class TudouAlbumIE(InfoExtractor):
    IE_NAME = 'tudou:album'
    _VALID_URL = r'https?://(?:www\.)?tudou\.com/album(?:cover|play)/(?P<id>[\w-]{11})'
    _TESTS = [{
        'url': 'http://www.tudou.com/albumplay/v5qckFJvNJg.html',
        'info_dict': {
            'id': 'v5qckFJvNJg',
        },
        'playlist_mincount': 45,
    }]

    def _real_extract(self, url):
        album_id = self._match_id(url)
        album_data = self._download_json(
            'http://www.tudou.com/tvp/alist.action?acode=%s' % album_id, album_id)
        entries = [self.url_result(
            'http://www.tudou.com/programs/view/%s' % item['icode'],
            'Tudou', item['icode'],
            item['kw']) for item in album_data['items']]
        return self.playlist_result(entries, album_id)
