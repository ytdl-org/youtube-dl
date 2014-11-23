# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
    unified_strdate,
    parse_duration,
    int_or_none,
    ExtractorError,
)


class NiconicoIE(InfoExtractor):
    IE_NAME = 'niconico'
    IE_DESC = 'ニコニコ動画'

    _TEST = {
        'url': 'http://www.nicovideo.jp/watch/sm22312215',
        'md5': 'd1a75c0823e2f629128c43e1212760f9',
        'info_dict': {
            'id': 'sm22312215',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'uploader': 'takuya0301',
            'uploader_id': '2698420',
            'upload_date': '20131123',
            'description': '(c) copyright 2008, Blender Foundation / www.bigbuckbunny.org',
            'duration': 33,
        },
        'params': {
            'username': 'ydl.niconico@gmail.com',
            'password': 'youtube-dl',
        },
    }

    _VALID_URL = r'https?://(?:www\.|secure\.)?nicovideo\.jp/watch/((?:[a-z]{2})?[0-9]+)'
    _NETRC_MACHINE = 'niconico'
    # Determine whether the downloader used authentication to download video
    _AUTHENTICATED = False

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        # No authentication to be performed
        if not username:
            return True

        # Log in
        login_form_strs = {
            'mail': username,
            'password': password,
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k, v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('utf-8')
        request = compat_urllib_request.Request(
            'https://secure.nicovideo.jp/secure/login', login_data)
        login_results = self._download_webpage(
            request, None, note='Logging in', errnote='Unable to log in')
        if re.search(r'(?i)<h1 class="mb8p4">Log in error</h1>', login_results) is not None:
            self._downloader.report_warning('unable to log in: bad username or password')
            return False
        # Successful login
        self._AUTHENTICATED = True
        return True

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        # Get video webpage. We are not actually interested in it, but need
        # the cookies in order to be able to download the info webpage
        self._download_webpage('http://www.nicovideo.jp/watch/' + video_id, video_id)

        video_info = self._download_xml(
            'http://ext.nicovideo.jp/api/getthumbinfo/' + video_id, video_id,
            note='Downloading video info page')

        if self._AUTHENTICATED:
            # Get flv info
            flv_info_webpage = self._download_webpage(
                'http://flapi.nicovideo.jp/api/getflv?v=' + video_id,
                video_id, 'Downloading flv info')
        else:
            # Get external player info
            ext_player_info = self._download_webpage(
                'http://ext.nicovideo.jp/thumb_watch/' + video_id, video_id)
            thumb_play_key = self._search_regex(
                r'\'thumbPlayKey\'\s*:\s*\'(.*?)\'', ext_player_info, 'thumbPlayKey')

            # Get flv info
            flv_info_data = compat_urllib_parse.urlencode({
                'k': thumb_play_key,
                'v': video_id
            })
            flv_info_request = compat_urllib_request.Request(
                'http://ext.nicovideo.jp/thumb_watch', flv_info_data,
                {'Content-Type': 'application/x-www-form-urlencoded'})
            flv_info_webpage = self._download_webpage(
                flv_info_request, video_id,
                note='Downloading flv info', errnote='Unable to download flv info')

        if 'deleted=' in flv_info_webpage:
            raise ExtractorError('The video has been deleted.',
                                 expected=True)
        video_real_url = compat_urlparse.parse_qs(flv_info_webpage)['url'][0]

        # Start extracting information
        title = video_info.find('.//title').text
        extension = video_info.find('.//movie_type').text
        video_format = extension.upper()
        thumbnail = video_info.find('.//thumbnail_url').text
        description = video_info.find('.//description').text
        upload_date = unified_strdate(video_info.find('.//first_retrieve').text.split('+')[0])
        view_count = int_or_none(video_info.find('.//view_counter').text)
        comment_count = int_or_none(video_info.find('.//comment_num').text)
        duration = parse_duration(video_info.find('.//length').text)
        webpage_url = video_info.find('.//watch_url').text

        if video_info.find('.//ch_id') is not None:
            uploader_id = video_info.find('.//ch_id').text
            uploader = video_info.find('.//ch_name').text
        elif video_info.find('.//user_id') is not None:
            uploader_id = video_info.find('.//user_id').text
            uploader = video_info.find('.//user_nickname').text
        else:
            uploader_id = uploader = None

        return {
            'id': video_id,
            'url': video_real_url,
            'title': title,
            'ext': extension,
            'format': video_format,
            'thumbnail': thumbnail,
            'description': description,
            'uploader': uploader,
            'upload_date': upload_date,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'comment_count': comment_count,
            'duration': duration,
            'webpage_url': webpage_url,
        }


class NiconicoPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://www\.nicovideo\.jp/mylist/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.nicovideo.jp/mylist/27411728',
        'info_dict': {
            'id': '27411728',
            'title': 'AKB48のオールナイトニッポン',
        },
        'playlist_mincount': 225,
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self._download_webpage(url, list_id)

        entries_json = self._search_regex(r'Mylist\.preload\(\d+, (\[.*\])\);',
                                          webpage, 'entries')
        entries = json.loads(entries_json)
        entries = [{
            '_type': 'url',
            'ie_key': NiconicoIE.ie_key(),
            'url': ('http://www.nicovideo.jp/watch/%s' %
                    entry['item_data']['video_id']),
        } for entry in entries]

        return {
            '_type': 'playlist',
            'title': self._search_regex(r'\s+name: "(.*?)"', webpage, 'title'),
            'id': list_id,
            'entries': entries,
        }
