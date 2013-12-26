# encoding: utf-8
import re, base64, zlib
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
    _VALID_URL = r'(?:https?://)?(?:www\.)?(?P<url>crunchyroll\.com/[^/]*/[^/?&]*?(?P<video_id>[0-9]+))(?:[/?&]|$)'
    _TESTS = [{
        u'url': u'http://www.crunchyroll.com/wanna-be-the-strongest-in-the-world/episode-1-an-idol-wrestler-is-born-645513',
        u'file': u'645513.flv',
        #u'md5': u'b1639fd6ddfaa43788c85f6d1dddd412',
        u'info_dict': {
            u'title': u'Wanna be the Strongest in the World Episode 1 – An Idol-Wrestler is Born!',
            u'description': u'md5:2d17137920c64f2f49981a7797d275ef',
            u'thumbnail': u'http://img1.ak.crunchyroll.com/i/spire1-tmb/20c6b5e10f1a47b10516877d3c039cae1380951166_full.jpg',
            u'uploader': u'Yomiuri Telecasting Corporation (YTV)',
            u'upload_date': u'20131013',
        },
        u'params': {
            # rtmp
            u'skip_download': True,
        },
    }]

    _FORMAT_IDS = {
        u'360': (u'60', u'106'),
        u'480': (u'61', u'106'),
        u'720': (u'62', u'106'),
        u'1080': (u'80', u'108'),
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
            shaHash = bytes_to_intlist(sha1(prefix + str(num4).encode(u'ascii')).digest())
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
        i=1
        output = u''
        for start, end, text in re.findall(r'<event [^>]*?start="([^"]+)" [^>]*?end="([^"]+)" [^>]*?text="([^"]+)"[^>]*?>', subtitles):
            start = start.replace(u'.', u',')
            end = end.replace(u'.', u',')
            text = clean_html(text)
            text = text.replace(u'\\N', u'\n')
            if not text:
                continue
            output += u'%d\n%s --> %s\n%s\n\n' % (i, start, end, text)
            i+=1
        return output

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)

        webpage_url = u'http://www.' + mobj.group('url')
        video_id = mobj.group(u'video_id')
        webpage = self._download_webpage(webpage_url, video_id)
        note_m = self._html_search_regex(r'<div class="showmedia-trailer-notice">(.+?)</div>', webpage, u'trailer-notice', default=u'')
        if note_m:
            raise ExtractorError(note_m)

        video_title = self._html_search_regex(r'<h1[^>]*>(.+?)</h1>', webpage, u'video_title', flags=re.DOTALL)
        video_title = re.sub(r' {2,}', u' ', video_title)
        video_description = self._html_search_regex(r'"description":"([^"]+)', webpage, u'video_description', default=u'')
        if not video_description:
            video_description = None
        video_upload_date = self._html_search_regex(r'<div>Availability for free users:(.+?)</div>', webpage, u'video_upload_date', fatal=False, flags=re.DOTALL)
        if video_upload_date:
            video_upload_date = unified_strdate(video_upload_date)
        video_uploader = self._html_search_regex(r'<div>\s*Publisher:(.+?)</div>', webpage, u'video_uploader', fatal=False, flags=re.DOTALL)

        playerdata_url = compat_urllib_parse.unquote(self._html_search_regex(r'"config_url":"([^"]+)', webpage, u'playerdata_url'))
        playerdata_req = compat_urllib_request.Request(playerdata_url)
        playerdata_req.data = compat_urllib_parse.urlencode({u'current_page': webpage_url})
        playerdata_req.add_header(u'Content-Type', u'application/x-www-form-urlencoded')
        playerdata = self._download_webpage(playerdata_req, video_id, note=u'Downloading media info')
        
        stream_id = self._search_regex(r'<media_id>([^<]+)', playerdata, u'stream_id')
        video_thumbnail = self._search_regex(r'<episode_image_url>([^<]+)', playerdata, u'thumbnail', fatal=False)

        formats = []
        for fmt in re.findall(r'\?p([0-9]{3,4})=1', webpage):
            stream_quality, stream_format = self._FORMAT_IDS[fmt]
            video_format = fmt+u'p'
            streamdata_req = compat_urllib_request.Request(u'http://www.crunchyroll.com/xml/')
            # urlencode doesn't work!
            streamdata_req.data = u'req=RpcApiVideoEncode%5FGetStreamInfo&video%5Fencode%5Fquality='+stream_quality+u'&media%5Fid='+stream_id+u'&video%5Fformat='+stream_format
            streamdata_req.add_header(u'Content-Type', u'application/x-www-form-urlencoded')
            streamdata_req.add_header(u'Content-Length', str(len(streamdata_req.data)))
            streamdata = self._download_webpage(streamdata_req, video_id, note=u'Downloading media info for '+video_format)
            video_url = self._search_regex(r'<host>([^<]+)', streamdata, u'video_url')
            video_play_path = self._search_regex(r'<file>([^<]+)', streamdata, u'video_play_path')
            formats.append({
                u'url': video_url,
                u'play_path':   video_play_path,
                u'ext': 'flv',
                u'format': video_format,
                u'format_id': video_format,
            })

        subtitles = {}
        for sub_id, sub_name in re.findall(r'\?ssid=([0-9]+)" title="([^"]+)', webpage):
            sub_page = self._download_webpage(u'http://www.crunchyroll.com/xml/?req=RpcApiSubtitle_GetXml&subtitle_script_id='+sub_id,\
                                              video_id, note=u'Downloading subtitles for '+sub_name)
            id = self._search_regex(r'id=\'([0-9]+)', sub_page, u'subtitle_id', fatal=False)
            iv = self._search_regex(r'<iv>([^<]+)', sub_page, u'subtitle_iv', fatal=False)
            data = self._search_regex(r'<data>([^<]+)', sub_page, u'subtitle_data', fatal=False)
            if not id or not iv or not data:
                continue
            id = int(id)
            iv = base64.b64decode(iv)
            data = base64.b64decode(data)

            subtitle = self._decrypt_subtitles(data, iv, id).decode(u'utf-8')
            lang_code = self._search_regex(r'lang_code=\'([^\']+)', subtitle, u'subtitle_lang_code', fatal=False)
            if not lang_code:
                continue
            subtitles[lang_code] = self._convert_subtitles_to_srt(subtitle)

        return {
            u'id':          video_id,
            u'title':       video_title,
            u'description': video_description,
            u'thumbnail':   video_thumbnail,
            u'uploader':    video_uploader,
            u'upload_date': video_upload_date,
            u'subtitles':   subtitles,
            u'formats':     formats,
        }
