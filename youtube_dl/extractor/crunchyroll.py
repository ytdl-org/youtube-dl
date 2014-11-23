# encoding: utf-8
from __future__ import unicode_literals

import re
import json
import base64
import zlib
import xml.etree.ElementTree

from hashlib import sha1
from math import pow, sqrt, floor
from .subtitles import SubtitlesInfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    compat_urllib_request,
    bytes_to_intlist,
    intlist_to_bytes,
    unified_strdate,
    urlencode_postdata,
)
from ..aes import (
    aes_cbc_decrypt,
    inc,
)
from .common import InfoExtractor


class CrunchyrollIE(SubtitlesInfoExtractor):
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
            'url': 're:(?!.*&amp)',
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

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        self.report_login()
        login_url = 'https://www.crunchyroll.com/?a=formhandler'
        data = urlencode_postdata({
            'formname': 'RpcApiUser_Login',
            'name': username,
            'password': password,
        })
        login_request = compat_urllib_request.Request(login_url, data)
        login_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        self._download_webpage(login_request, None, False, 'Wrong login info')

    def _real_initialize(self):
        self._login()

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

    def _convert_subtitles_to_srt(self, sub_root):
        output = ''

        for i, event in enumerate(sub_root.findall('./events/event'), 1):
            start = event.attrib['start'].replace('.', ',')
            end = event.attrib['end'].replace('.', ',')
            text = event.attrib['text'].replace('\\N', '\n')
            output += '%d\n%s --> %s\n%s\n\n' % (i, start, end, text)
        return output

    def _convert_subtitles_to_ass(self, sub_root):
        output = ''

        def ass_bool(strvalue):
            assvalue = '0'
            if strvalue == '1':
                assvalue = '-1'
            return assvalue

        output = '[Script Info]\n'
        output += 'Title: %s\n' % sub_root.attrib["title"]
        output += 'ScriptType: v4.00+\n'
        output += 'WrapStyle: %s\n' % sub_root.attrib["wrap_style"]
        output += 'PlayResX: %s\n' % sub_root.attrib["play_res_x"]
        output += 'PlayResY: %s\n' % sub_root.attrib["play_res_y"]
        output += """ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
        for style in sub_root.findall('./styles/style'):
            output += 'Style: ' + style.attrib["name"]
            output += ',' + style.attrib["font_name"]
            output += ',' + style.attrib["font_size"]
            output += ',' + style.attrib["primary_colour"]
            output += ',' + style.attrib["secondary_colour"]
            output += ',' + style.attrib["outline_colour"]
            output += ',' + style.attrib["back_colour"]
            output += ',' + ass_bool(style.attrib["bold"])
            output += ',' + ass_bool(style.attrib["italic"])
            output += ',' + ass_bool(style.attrib["underline"])
            output += ',' + ass_bool(style.attrib["strikeout"])
            output += ',' + style.attrib["scale_x"]
            output += ',' + style.attrib["scale_y"]
            output += ',' + style.attrib["spacing"]
            output += ',' + style.attrib["angle"]
            output += ',' + style.attrib["border_style"]
            output += ',' + style.attrib["outline"]
            output += ',' + style.attrib["shadow"]
            output += ',' + style.attrib["alignment"]
            output += ',' + style.attrib["margin_l"]
            output += ',' + style.attrib["margin_r"]
            output += ',' + style.attrib["margin_v"]
            output += ',' + style.attrib["encoding"]
            output += '\n'

        output += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        for event in sub_root.findall('./events/event'):
            output += 'Dialogue: 0'
            output += ',' + event.attrib["start"]
            output += ',' + event.attrib["end"]
            output += ',' + event.attrib["style"]
            output += ',' + event.attrib["name"]
            output += ',' + event.attrib["margin_l"]
            output += ',' + event.attrib["margin_r"]
            output += ',' + event.attrib["margin_v"]
            output += ',' + event.attrib["effect"]
            output += ',' + event.attrib["text"]
            output += '\n'

        return output

    def _real_extract(self, url):
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
            video_format = fmt + 'p'
            streamdata_req = compat_urllib_request.Request('http://www.crunchyroll.com/xml/')
            # urlencode doesn't work!
            streamdata_req.data = 'req=RpcApiVideoEncode%5FGetStreamInfo&video%5Fencode%5Fquality=' + stream_quality + '&media%5Fid=' + stream_id + '&video%5Fformat=' + stream_format
            streamdata_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            streamdata_req.add_header('Content-Length', str(len(streamdata_req.data)))
            streamdata = self._download_xml(
                streamdata_req, video_id,
                note='Downloading media info for %s' % video_format)
            video_url = streamdata.find('.//host').text
            video_play_path = streamdata.find('.//file').text
            formats.append({
                'url': video_url,
                'play_path': video_play_path,
                'ext': 'flv',
                'format': video_format,
                'format_id': video_format,
            })

        subtitles = {}
        sub_format = self._downloader.params.get('subtitlesformat', 'srt')
        for sub_id, sub_name in re.findall(r'\?ssid=([0-9]+)" title="([^"]+)', webpage):
            sub_page = self._download_webpage(
                'http://www.crunchyroll.com/xml/?req=RpcApiSubtitle_GetXml&subtitle_script_id=' + sub_id,
                video_id, note='Downloading subtitles for ' + sub_name)
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
            sub_root = xml.etree.ElementTree.fromstring(subtitle)
            if sub_format == 'ass':
                subtitles[lang_code] = self._convert_subtitles_to_ass(sub_root)
            else:
                subtitles[lang_code] = self._convert_subtitles_to_srt(sub_root)

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'thumbnail': video_thumbnail,
            'uploader': video_uploader,
            'upload_date': video_upload_date,
            'subtitles': subtitles,
            'formats': formats,
        }


class CrunchyrollShowPlaylistIE(InfoExtractor):
    IE_NAME = "crunchyroll:playlist"
    _VALID_URL = r'https?://(?:(?P<prefix>www|m)\.)?(?P<url>crunchyroll\.com/(?!(?:news|anime-news|library|forum|launchcalendar|lineup|store|comics|freetrial|login))(?P<id>[\w\-]+))/?$'

    _TESTS = [{
        'url': 'http://www.crunchyroll.com/a-bridge-to-the-starry-skies-hoshizora-e-kakaru-hashi',
        'info_dict': {
            'id': 'a-bridge-to-the-starry-skies-hoshizora-e-kakaru-hashi',
            'title': 'A Bridge to the Starry Skies - Hoshizora e Kakaru Hashi'
        },
        'playlist_count': 13,
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)

        webpage = self._download_webpage(url, show_id)
        title = self._html_search_regex(
            r'(?s)<h1[^>]*>\s*<span itemprop="name">(.*?)</span>',
            webpage, 'title')
        episode_paths = re.findall(
            r'(?s)<li id="showview_videos_media_[0-9]+"[^>]+>.*?<a href="([^"]+)"',
            webpage)
        entries = [
            self.url_result('http://www.crunchyroll.com' + ep, 'Crunchyroll')
            for ep in episode_paths
        ]
        entries.reverse()

        return {
            '_type': 'playlist',
            'id': show_id,
            'title': title,
            'entries': entries,
        }
