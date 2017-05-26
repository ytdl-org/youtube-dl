# coding: utf-8
from __future__ import unicode_literals

import itertools
import random
import re
import string
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    get_element_by_attribute,
)


class YoukuIE(InfoExtractor):
    IE_NAME = 'youku'
    IE_DESC = '优酷'
    _VALID_URL = r'''(?x)
        (?:
            http://(?:v|player)\.youku\.com/(?:v_show/id_|player\.php/sid/)|
            youku:)
        (?P<id>[A-Za-z0-9]+)(?:\.html|/v\.swf|)
    '''

    _TESTS = [{
        # MD5 is unstable
        'url': 'http://v.youku.com/v_show/id_XMTc1ODE5Njcy.html',
        'info_dict': {
            'id': 'XMTc1ODE5Njcy',
            'title': '★Smile﹗♡ Git Fresh -Booty Music舞蹈.',
            'ext': 'mp4',
        }
    }, {
        'url': 'http://player.youku.com/player.php/sid/XNDgyMDQ2NTQw/v.swf',
        'only_matching': True,
    }, {
        'url': 'http://v.youku.com/v_show/id_XODgxNjg1Mzk2_ev_1.html',
        'info_dict': {
            'id': 'XODgxNjg1Mzk2',
            'ext': 'mp4',
            'title': '武媚娘传奇 85',
        },
    }, {
        'url': 'http://v.youku.com/v_show/id_XMTI1OTczNDM5Mg==.html',
        'info_dict': {
            'id': 'XMTI1OTczNDM5Mg',
            'ext': 'mp4',
            'title': '花千骨 04',
        },
    }, {
        'url': 'http://v.youku.com/v_show/id_XNjA1NzA2Njgw.html',
        'note': 'Video protected with password',
        'info_dict': {
            'id': 'XNjA1NzA2Njgw',
            'ext': 'mp4',
            'title': '邢義田复旦讲座之想象中的胡人—从“左衽孔子”说起',
        },
        'params': {
            'videopassword': '100600',
        },
    }, {
        # /play/get.json contains streams with "channel_type":"tail"
        'url': 'http://v.youku.com/v_show/id_XOTUxMzg4NDMy.html',
        'info_dict': {
            'id': 'XOTUxMzg4NDMy',
            'ext': 'mp4',
            'title': '我的世界☆明月庄主☆车震猎杀☆杀人艺术Minecraft',
        },
    }]

    @staticmethod
    def get_ysuid():
        return '%d%s' % (int(time.time()), ''.join([
            random.choice(string.ascii_letters) for i in range(3)]))

    def get_format_name(self, fm):
        _dict = {
            '3gp': 'h6',
            '3gphd': 'h5',
            'flv': 'h4',
            'flvhd': 'h4',
            'mp4': 'h3',
            'mp4hd': 'h3',
            'mp4hd2': 'h4',
            'mp4hd3': 'h4',
            'hd2': 'h2',
            'hd3': 'h1',
        }
        return _dict.get(fm)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        self._set_cookie('youku.com', '__ysuid', self.get_ysuid())
        self._set_cookie('youku.com', 'xreferrer', 'http://www.youku.com')

        _, urlh = self._download_webpage_handle(
            'https://log.mmstat.com/eg.js', video_id, 'Retrieving cna info')
        # The etag header is '"foobar"'; let's remove the double quotes
        cna = urlh.headers['etag'][1:-1]

        # request basic data
        basic_data_params = {
            'vid': video_id,
            'ccode': '0401',
            'client_ip': '192.168.1.1',
            'utid': cna,
            'client_ts': time.time() / 1000,
        }

        video_password = self._downloader.params.get('videopassword')
        if video_password:
            basic_data_params['password'] = video_password

        headers = {
            'Referer': url,
        }
        headers.update(self.geo_verification_headers())
        data = self._download_json(
            'https://ups.youku.com/ups/get.json', video_id,
            'Downloading JSON metadata',
            query=basic_data_params, headers=headers)['data']

        error = data.get('error')
        if error:
            error_note = error.get('note')
            if error_note is not None and '因版权原因无法观看此视频' in error_note:
                raise ExtractorError(
                    'Youku said: Sorry, this video is available in China only', expected=True)
            elif error_note and '该视频被设为私密' in error_note:
                raise ExtractorError(
                    'Youku said: Sorry, this video is private', expected=True)
            else:
                msg = 'Youku server reported error %i' % error.get('code')
                if error_note is not None:
                    msg += ': ' + error_note
                raise ExtractorError(msg)

        # get video title
        title = data['video']['title']

        formats = [{
            'url': stream['m3u8_url'],
            'format_id': self.get_format_name(stream.get('stream_type')),
            'ext': 'mp4',
            'protocol': 'm3u8_native',
            'filesize': int(stream.get('size')),
            'width': stream.get('width'),
            'height': stream.get('height'),
        } for stream in data['stream'] if stream.get('channel_type') != 'tail']
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }


class YoukuShowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youku\.com/show_page/id_(?P<id>[0-9a-z]+)\.html'
    IE_NAME = 'youku:show'

    _TEST = {
        'url': 'http://www.youku.com/show_page/id_zc7c670be07ff11e48b3f.html',
        'info_dict': {
            'id': 'zc7c670be07ff11e48b3f',
            'title': '花千骨 未删减版',
            'description': 'md5:578d4f2145ae3f9128d9d4d863312910',
        },
        'playlist_count': 50,
    }

    _PAGE_SIZE = 40

    def _find_videos_in_page(self, webpage):
        videos = re.findall(
            r'<li><a[^>]+href="(?P<url>https?://v\.youku\.com/[^"]+)"[^>]+title="(?P<title>[^"]+)"', webpage)
        return [
            self.url_result(video_url, YoukuIE.ie_key(), title)
            for video_url, title in videos]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        entries = self._find_videos_in_page(webpage)

        playlist_title = self._html_search_regex(
            r'<span[^>]+class="name">([^<]+)</span>', webpage, 'playlist title', fatal=False)
        detail_div = get_element_by_attribute('class', 'detail', webpage) or ''
        playlist_description = self._html_search_regex(
            r'<span[^>]+style="display:none"[^>]*>([^<]+)</span>',
            detail_div, 'playlist description', fatal=False)

        for idx in itertools.count(1):
            episodes_page = self._download_webpage(
                'http://www.youku.com/show_episode/id_%s.html' % show_id,
                show_id, query={'divid': 'reload_%d' % (idx * self._PAGE_SIZE + 1)},
                note='Downloading episodes page %d' % idx)
            new_entries = self._find_videos_in_page(episodes_page)
            entries.extend(new_entries)
            if len(new_entries) < self._PAGE_SIZE:
                break

        return self.playlist_result(entries, show_id, playlist_title, playlist_description)
