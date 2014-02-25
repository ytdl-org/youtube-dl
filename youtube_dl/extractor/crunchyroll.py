# encoding: utf-8
from __future__ import unicode_literals

import re
import json
import base64
import zlib

from hashlib import sha1
from math import pow, sqrt, floor
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    compat_urllib_request,
    bytes_to_intlist,
    intlist_to_bytes,
    unified_strdate,
    clean_html,
)
from ..aes import (
    aes_cbc_decrypt,
    inc,
)


class CrunchyrollIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?P<prefix>www|m)\.)?(?P<url>crunchyroll\.com/(?:[^/]*/[^/?&]*?|media/\?id=)(?P<video_id>[0-9]+))(?:[/?&]|$)'
    _TEST = {
        'url': 'http://www.crunchyroll.com/wanna-be-the-strongest-in-the-world/episode-1-an-idol-wrestler-is-born-645513',
        #'md5': 'b1639fd6ddfaa43788c85f6d1dddd412',
        'info_dict': {
            'id': '645513',
            'ext': 'flv',
            'title': 'Wanna be the Strongest in the World Episode 1 – An Idol-Wrestler is Born!',
            'description': 'md5:2d17137920c64f2f49981a7797d275ef',
            'thumbnail': 'http://img1.ak.crunchyroll.com/i/spire1-tmb/20c6b5e10f1a47b10516877d3c039cae1380951166_full.jpg',
            'uploader': 'Yomiuri Telecasting Corporation (YTV)',
            'upload_date': '20131013',
        },
        'params': {
            # rtmp
            'skip_download': True,
        },
    }

    _FORMAT_IDS = {
        '360': ('60', '106'),
        '480': ('61', '106'),
        '720': ('62', '106'),
        '1080': ('80', '108'),
    }

    def _decrypt_subtitles(self, data, iv, id):
        data = bytes_to_intlist(data)
        iv = bytes_to_intlist(iv)
        id = int(id)

        def obfuscate_key_aux(count, modulo, start):
            output = list(start)
            for _ in range(count):
                output.append(output[-1] + output[-2])
            # cut off start values
            output = output[2:]
            output = list(map(lambda x: x % modulo + 33, output))
            return output

        def obfuscate_key(key):
            num1 = int(floor(pow(2, 25) * sqrt(6.9)))
            num2 = (num1 ^ key) << 5
            num3 = key ^ num1
            num4 = num3 ^ (num3 >> 3) ^ num2
            prefix = intlist_to_bytes(obfuscate_key_aux(20, 97, (1, 2)))
            shaHash = bytes_to_intlist(sha1(prefix + str(num4).encode('ascii')).digest())
            # Extend 160 Bit hash to 256 Bit
            return shaHash + [0] * 12

        key = obfuscate_key(id)
        class Counter:
            __value = iv
            def next_value(self):
                temp = self.__value
                self.__value = inc(self.__value)
                return temp
        decrypted_data = intlist_to_bytes(aes_cbc_decrypt(data, key, iv))
        return zlib.decompress(decrypted_data)

    def _convert_subtitles_to_srt(self, subtitles):
        output = ''
        for i, (start, end, text) in enumerate(re.findall(r'<event [^>]*?start="([^"]+)" [^>]*?end="([^"]+)" [^>]*?text="([^"]+)"[^>]*?>', subtitles), 1):
            start = start.replace('.', ',')
            end = end.replace('.', ',')
            text = clean_html(text)
            text = text.replace('\\N', '\n')
            if not text:
                continue
            output += '%d\n%s --> %s\n%s\n\n' % (i, start, end, text)
        return output

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        if mobj.group('prefix') == 'm':
            mobile_webpage = self._download_webpage(url, video_id, 'Downloading mobile webpage')
            webpage_url = self._search_regex(r'<link rel="canonical" href="([^"]+)" />', mobile_webpage, 'webpage_url')
        else:
            webpage_url = 'http://www.' + mobj.group('url')

        webpage = self._download_webpage(webpage_url, video_id, 'Downloading webpage')
        note_m = self._html_search_regex(r'<div class="showmedia-trailer-notice">(.+?)</div>', webpage, 'trailer-notice', default='')
        if note_m:
            raise ExtractorError(note_m)

        mobj = re.search(r'Page\.messaging_box_controller\.addItems\(\[(?P<msg>{.+?})\]\)', webpage)
        if mobj:
            msg = json.loads(mobj.group('msg'))
            if msg.get('type') == 'error':
                raise ExtractorError('crunchyroll returned error: %s' % msg['message_body'], expected=True)

        video_title = self._html_search_regex(r'<h1[^>]*>(.+?)</h1>', webpage, 'video_title', flags=re.DOTALL)
        video_title = re.sub(r' {2,}', ' ', video_title)
        video_description = self._html_search_regex(r'"description":"([^"]+)', webpage, 'video_description', default='')
        if not video_description:
            video_description = None
        video_upload_date = self._html_search_regex(r'<div>Availability for free users:(.+?)</div>', webpage, 'video_upload_date', fatal=False, flags=re.DOTALL)
        if video_upload_date:
            video_upload_date = unified_strdate(video_upload_date)
        video_uploader = self._html_search_regex(r'<div>\s*Publisher:(.+?)</div>', webpage, 'video_uploader', fatal=False, flags=re.DOTALL)

        playerdata_url = compat_urllib_parse.unquote(self._html_search_regex(r'"config_url":"([^"]+)', webpage, 'playerdata_url'))
        playerdata_req = compat_urllib_request.Request(playerdata_url)
        playerdata_req.data = compat_urllib_parse.urlencode({'current_page': webpage_url})
        playerdata_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        playerdata = self._download_webpage(playerdata_req, video_id, note='Downloading media info')

        stream_id = self._search_regex(r'<media_id>([^<]+)', playerdata, 'stream_id')
        video_thumbnail = self._search_regex(r'<episode_image_url>([^<]+)', playerdata, 'thumbnail', fatal=False)

        formats = []
        for fmt in re.findall(r'\?p([0-9]{3,4})=1', webpage):
            stream_quality, stream_format = self._FORMAT_IDS[fmt]
            video_format = fmt+'p'
            streamdata_req = compat_urllib_request.Request('http://www.crunchyroll.com/xml/')
            # urlencode doesn't work!
            streamdata_req.data = 'req=RpcApiVideoEncode%5FGetStreamInfo&video%5Fencode%5Fquality='+stream_quality+'&media%5Fid='+stream_id+'&video%5Fformat='+stream_format
            streamdata_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            streamdata_req.add_header('Content-Length', str(len(streamdata_req.data)))
            streamdata = self._download_webpage(streamdata_req, video_id, note='Downloading media info for '+video_format)
            video_url = self._search_regex(r'<host>([^<]+)', streamdata, 'video_url')
            video_play_path = self._search_regex(r'<file>([^<]+)', streamdata, 'video_play_path')
            formats.append({
                'url': video_url,
                'play_path':   video_play_path,
                'ext': 'flv',
                'format': video_format,
                'format_id': video_format,
            })

        subtitles = {}
        for sub_id, sub_name in re.findall(r'\?ssid=([0-9]+)" title="([^"]+)', webpage):
            sub_page = self._download_webpage('http://www.crunchyroll.com/xml/?req=RpcApiSubtitle_GetXml&subtitle_script_id='+sub_id,\
                                              video_id, note='Downloading subtitles for '+sub_name)
            id = self._search_regex(r'id=\'([0-9]+)', sub_page, 'subtitle_id', fatal=False)
            iv = self._search_regex(r'<iv>([^<]+)', sub_page, 'subtitle_iv', fatal=False)
            data = self._search_regex(r'<data>([^<]+)', sub_page, 'subtitle_data', fatal=False)
            if not id or not iv or not data:
                continue
            id = int(id)
            iv = base64.b64decode(iv)
            data = base64.b64decode(data)

            subtitle = self._decrypt_subtitles(data, iv, id).decode('utf-8')
            lang_code = self._search_regex(r'lang_code=["\']([^"\']+)', subtitle, 'subtitle_lang_code', fatal=False)
            if not lang_code:
                continue
            subtitles[lang_code] = self._convert_subtitles_to_srt(subtitle)

        return {
            'id':          video_id,
            'title':       video_title,
            'description': video_description,
            'thumbnail':   video_thumbnail,
            'uploader':    video_uploader,
            'upload_date': video_upload_date,
            'subtitles':   subtitles,
            'formats':     formats,
        }
