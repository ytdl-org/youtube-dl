# encoding: utf-8

from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    int_or_none,
    str_to_int,
    xpath_text,
    unescapeHTML,
)


class DaumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:m\.)?tvpot\.daum\.net/v/|videofarm\.daum\.net/controller/player/VodPlayer\.swf\?vid=)(?P<id>[^?#&]+)'
    IE_NAME = 'daum.net'

    _TESTS = [{
        'url': 'http://tvpot.daum.net/v/vab4dyeDBysyBssyukBUjBz',
        'info_dict': {
            'id': 'vab4dyeDBysyBssyukBUjBz',
            'ext': 'mp4',
            'title': '마크 헌트 vs 안토니오 실바',
            'description': 'Mark Hunt vs Antonio Silva',
            'upload_date': '20131217',
            'thumbnail': 're:^https?://.*\.(?:jpg|png)',
            'duration': 2117,
            'view_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'http://m.tvpot.daum.net/v/65139429',
        'info_dict': {
            'id': '65139429',
            'ext': 'mp4',
            'title': '1297회, \'아빠 아들로 태어나길 잘 했어\' 민수, 감동의 눈물[아빠 어디가] 20150118',
            'description': 'md5:79794514261164ff27e36a21ad229fc5',
            'upload_date': '20150604',
            'thumbnail': 're:^https?://.*\.(?:jpg|png)',
            'duration': 154,
            'view_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'http://tvpot.daum.net/v/07dXWRka62Y%24',
        'only_matching': True,
    }, {
        'url': 'http://videofarm.daum.net/controller/player/VodPlayer.swf?vid=vwIpVpCQsT8%24&ref=',
        'info_dict': {
            'id': 'vwIpVpCQsT8$',
            'ext': 'flv',
            'title': '01-Korean War ( Trouble on the horizon )',
            'description': '\nKorean War 01\nTrouble on the horizon\n전쟁의 먹구름',
            'upload_date': '20080223',
            'thumbnail': 're:^https?://.*\.(?:jpg|png)',
            'duration': 249,
            'view_count': int,
            'comment_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = compat_urllib_parse_unquote(self._match_id(url))
        query = compat_urllib_parse_urlencode({'vid': video_id})
        movie_data = self._download_json(
            'http://videofarm.daum.net/controller/api/closed/v1_2/IntegratedMovieData.json?' + query,
            video_id, 'Downloading video formats info')

        # For urls like http://m.tvpot.daum.net/v/65139429, where the video_id is really a clipid
        if not movie_data.get('output_list', {}).get('output_list') and re.match(r'^\d+$', video_id):
            return self.url_result('http://tvpot.daum.net/clip/ClipView.do?clipid=%s' % video_id)

        info = self._download_xml(
            'http://tvpot.daum.net/clip/ClipInfoXml.do?' + query, video_id,
            'Downloading video info')

        formats = []
        for format_el in movie_data['output_list']['output_list']:
            profile = format_el['profile']
            format_query = compat_urllib_parse_urlencode({
                'vid': video_id,
                'profile': profile,
            })
            url_doc = self._download_xml(
                'http://videofarm.daum.net/controller/api/open/v1_2/MovieLocation.apixml?' + format_query,
                video_id, note='Downloading video data for %s format' % profile)
            format_url = url_doc.find('result/url').text
            formats.append({
                'url': format_url,
                'format_id': profile,
                'width': int_or_none(format_el.get('width')),
                'height': int_or_none(format_el.get('height')),
                'filesize': int_or_none(format_el.get('filesize')),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info.find('TITLE').text,
            'formats': formats,
            'thumbnail': xpath_text(info, 'THUMB_URL'),
            'description': xpath_text(info, 'CONTENTS'),
            'duration': int_or_none(xpath_text(info, 'DURATION')),
            'upload_date': info.find('REGDTTM').text[:8],
            'view_count': str_to_int(xpath_text(info, 'PLAY_CNT')),
            'comment_count': str_to_int(xpath_text(info, 'COMMENT_CNT')),
        }


class DaumClipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tvpot\.daum\.net/(?:clip/ClipView.(?:do|tv)|mypot/View.do)\?.*?clipid=(?P<id>\d+)'
    IE_NAME = 'daum.net:clip'
    _URL_TEMPLATE = 'http://tvpot.daum.net/clip/ClipView.do?clipid=%s'

    _TESTS = [{
        'url': 'http://tvpot.daum.net/clip/ClipView.do?clipid=52554690',
        'info_dict': {
            'id': '52554690',
            'ext': 'mp4',
            'title': 'DOTA 2GETHER 시즌2 6회 - 2부',
            'description': 'DOTA 2GETHER 시즌2 6회 - 2부',
            'upload_date': '20130831',
            'thumbnail': 're:^https?://.*\.(?:jpg|png)',
            'duration': 3868,
            'view_count': int,
        },
    }, {
        'url': 'http://m.tvpot.daum.net/clip/ClipView.tv?clipid=54999425',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if DaumPlaylistIE.suitable(url) or DaumUserIE.suitable(url) else super(DaumClipIE, cls).suitable(url)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        clip_info = self._download_json(
            'http://tvpot.daum.net/mypot/json/GetClipInfo.do?clipid=%s' % video_id,
            video_id, 'Downloading clip info')['clip_bean']

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': 'http://tvpot.daum.net/v/%s' % clip_info['vid'],
            'title': unescapeHTML(clip_info['title']),
            'thumbnail': clip_info.get('thumb_url'),
            'description': clip_info.get('contents'),
            'duration': int_or_none(clip_info.get('duration')),
            'upload_date': clip_info.get('up_date')[:8],
            'view_count': int_or_none(clip_info.get('play_count')),
            'ie_key': 'Daum',
        }


class DaumListIE(InfoExtractor):
    def _get_entries(self, list_id, list_id_type):
        name = None
        entries = []
        for pagenum in itertools.count(1):
            list_info = self._download_json(
                'http://tvpot.daum.net/mypot/json/GetClipInfo.do?size=48&init=true&order=date&page=%d&%s=%s' % (
                    pagenum, list_id_type, list_id), list_id, 'Downloading list info - %s' % pagenum)

            entries.extend([
                self.url_result(
                    'http://tvpot.daum.net/v/%s' % clip['vid'])
                for clip in list_info['clip_list']
            ])

            if not name:
                name = list_info.get('playlist_bean', {}).get('name') or \
                    list_info.get('potInfo', {}).get('name')

            if not list_info.get('has_more'):
                break

        return name, entries

    def _check_clip(self, url, list_id):
        query_dict = compat_parse_qs(compat_urlparse.urlparse(url).query)
        if 'clipid' in query_dict:
            clip_id = query_dict['clipid'][0]
            if self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading just video %s because of --no-playlist' % clip_id)
                return self.url_result(DaumClipIE._URL_TEMPLATE % clip_id, 'DaumClip')
            else:
                self.to_screen('Downloading playlist %s - add --no-playlist to just download video' % list_id)


class DaumPlaylistIE(DaumListIE):
    _VALID_URL = r'https?://(?:m\.)?tvpot\.daum\.net/mypot/(?:View\.do|Top\.tv)\?.*?playlistid=(?P<id>[0-9]+)'
    IE_NAME = 'daum.net:playlist'
    _URL_TEMPLATE = 'http://tvpot.daum.net/mypot/View.do?playlistid=%s'

    _TESTS = [{
        'note': 'Playlist url with clipid',
        'url': 'http://tvpot.daum.net/mypot/View.do?playlistid=6213966&clipid=73806844',
        'info_dict': {
            'id': '6213966',
            'title': 'Woorissica Official',
        },
        'playlist_mincount': 181
    }, {
        'note': 'Playlist url with clipid - noplaylist',
        'url': 'http://tvpot.daum.net/mypot/View.do?playlistid=6213966&clipid=73806844',
        'info_dict': {
            'id': '73806844',
            'ext': 'mp4',
            'title': '151017 Airport',
            'upload_date': '20160117',
        },
        'params': {
            'noplaylist': True,
            'skip_download': True,
        }
    }]

    @classmethod
    def suitable(cls, url):
        return False if DaumUserIE.suitable(url) else super(DaumPlaylistIE, cls).suitable(url)

    def _real_extract(self, url):
        list_id = self._match_id(url)

        clip_result = self._check_clip(url, list_id)
        if clip_result:
            return clip_result

        name, entries = self._get_entries(list_id, 'playlistid')

        return self.playlist_result(entries, list_id, name)


class DaumUserIE(DaumListIE):
    _VALID_URL = r'https?://(?:m\.)?tvpot\.daum\.net/mypot/(?:View|Top)\.(?:do|tv)\?.*?ownerid=(?P<id>[0-9a-zA-Z]+)'
    IE_NAME = 'daum.net:user'

    _TESTS = [{
        'url': 'http://tvpot.daum.net/mypot/View.do?ownerid=o2scDLIVbHc0',
        'info_dict': {
            'id': 'o2scDLIVbHc0',
            'title': '마이 리틀 텔레비전',
        },
        'playlist_mincount': 213
    }, {
        'url': 'http://tvpot.daum.net/mypot/View.do?ownerid=o2scDLIVbHc0&clipid=73801156',
        'info_dict': {
            'id': '73801156',
            'ext': 'mp4',
            'title': '[미공개] 김구라, 오만석이 부릅니다 \'오케피\' - 마이 리틀 텔레비전 20160116',
            'upload_date': '20160117',
            'description': 'md5:5e91d2d6747f53575badd24bd62b9f36'
        },
        'params': {
            'noplaylist': True,
            'skip_download': True,
        }
    }, {
        'note': 'Playlist url has ownerid and playlistid, playlistid takes precedence',
        'url': 'http://tvpot.daum.net/mypot/View.do?ownerid=o2scDLIVbHc0&playlistid=6196631',
        'info_dict': {
            'id': '6196631',
            'title': '마이 리틀 텔레비전 - 20160109',
        },
        'playlist_count': 11
    }, {
        'url': 'http://tvpot.daum.net/mypot/Top.do?ownerid=o2scDLIVbHc0',
        'only_matching': True,
    }, {
        'url': 'http://m.tvpot.daum.net/mypot/Top.tv?ownerid=45x1okb1If50&playlistid=3569733',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        list_id = self._match_id(url)

        clip_result = self._check_clip(url, list_id)
        if clip_result:
            return clip_result

        query_dict = compat_parse_qs(compat_urlparse.urlparse(url).query)
        if 'playlistid' in query_dict:
            playlist_id = query_dict['playlistid'][0]
            return self.url_result(DaumPlaylistIE._URL_TEMPLATE % playlist_id, 'DaumPlaylist')

        name, entries = self._get_entries(list_id, 'ownerid')

        return self.playlist_result(entries, list_id, name)
