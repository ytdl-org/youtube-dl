import binascii
import base64
import hashlib
import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_ord,
    compat_urllib_parse,
    compat_urllib_request,

    ExtractorError,
)



class MyVideoIE(InfoExtractor):
    """Information Extractor for myvideo.de."""

    _VALID_URL = r'(?:http://)?(?:www\.)?myvideo\.de/(?:[^/]+/)?watch/([0-9]+)/([^?/]+).*'
    IE_NAME = u'myvideo'
    _TEST = {
        u'url': u'http://www.myvideo.de/watch/8229274/bowling_fail_or_win',
        u'file': u'8229274.flv',
        u'md5': u'2d2753e8130479ba2cb7e0a37002053e',
        u'info_dict': {
            u"title": u"bowling-fail-or-win"
        }
    }

    # Original Code from: https://github.com/dersphere/plugin.video.myvideo_de.git
    # Released into the Public Domain by Tristan Fischer on 2013-05-19
    # https://github.com/rg3/youtube-dl/pull/842
    def __rc4crypt(self,data, key):
        x = 0
        box = list(range(256))
        for i in list(range(256)):
            x = (x + box[i] + compat_ord(key[i % len(key)])) % 256
            box[i], box[x] = box[x], box[i]
        x = 0
        y = 0
        out = ''
        for char in data:
            x = (x + 1) % 256
            y = (y + box[x]) % 256
            box[x], box[y] = box[y], box[x]
            out += chr(compat_ord(char) ^ box[(box[x] + box[y]) % 256])
        return out

    def __md5(self,s):
        return hashlib.md5(s).hexdigest().encode()

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'invalid URL: %s' % url)

        video_id = mobj.group(1)

        GK = (
          b'WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakpt'
          b'TW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3'
          b'TnpsbA0KTVRkbU1tSTRNdz09'
        )

        # Get video webpage
        webpage_url = 'http://www.myvideo.de/watch/%s' % video_id
        webpage = self._download_webpage(webpage_url, video_id)

        mobj = re.search('source src=\'(.+?)[.]([^.]+)\'', webpage)
        if mobj is not None:
            self.report_extraction(video_id)
            video_url = mobj.group(1) + '.flv'

            video_title = self._html_search_regex('<title>([^<]+)</title>',
                webpage, u'title')

            video_ext = self._search_regex('[.](.+?)$', video_url, u'extension')

            return [{
                'id':       video_id,
                'url':      video_url,
                'uploader': None,
                'upload_date':  None,
                'title':    video_title,
                'ext':      video_ext,
            }]

        mobj = re.search(r'data-video-service="/service/data/video/%s/config' % video_id, webpage)
        if mobj is not None:
            request = compat_urllib_request.Request('http://www.myvideo.de/service/data/video/%s/config' % video_id, '')
            response = self._download_webpage(request, video_id,
                                              u'Downloading video info')
            info = json.loads(base64.b64decode(response).decode('utf-8'))
            return {'id': video_id,
                    'title': info['title'],
                    'url': info['streaming_url'].replace('rtmpe', 'rtmpt'),
                    'play_path': info['filename'],
                    'ext': 'flv',
                    'thumbnail': info['thumbnail'][0]['url'],
                    }

        # try encxml
        mobj = re.search('var flashvars={(.+?)}', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract video')

        params = {}
        encxml = ''
        sec = mobj.group(1)
        for (a, b) in re.findall('(.+?):\'(.+?)\',?', sec):
            if not a == '_encxml':
                params[a] = b
            else:
                encxml = compat_urllib_parse.unquote(b)
        if not params.get('domain'):
            params['domain'] = 'www.myvideo.de'
        xmldata_url = '%s?%s' % (encxml, compat_urllib_parse.urlencode(params))
        if 'flash_playertype=MTV' in xmldata_url:
            self._downloader.report_warning(u'avoiding MTV player')
            xmldata_url = (
                'http://www.myvideo.de/dynamic/get_player_video_xml.php'
                '?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes'
            ) % video_id

        # get enc data
        enc_data = self._download_webpage(xmldata_url, video_id).split('=')[1]
        enc_data_b = binascii.unhexlify(enc_data)
        sk = self.__md5(
            base64.b64decode(base64.b64decode(GK)) +
            self.__md5(
                str(video_id).encode('utf-8')
            )
        )
        dec_data = self.__rc4crypt(enc_data_b, sk)

        # extracting infos
        self.report_extraction(video_id)

        video_url = None
        mobj = re.search('connectionurl=\'(.*?)\'', dec_data)
        if mobj:
            video_url = compat_urllib_parse.unquote(mobj.group(1))
            if 'myvideo2flash' in video_url:
                self._downloader.report_warning(u'forcing RTMPT ...')
                video_url = video_url.replace('rtmpe://', 'rtmpt://')

        if not video_url:
            # extract non rtmp videos
            mobj = re.search('path=\'(http.*?)\' source=\'(.*?)\'', dec_data)
            if mobj is None:
                raise ExtractorError(u'unable to extract url')
            video_url = compat_urllib_parse.unquote(mobj.group(1)) + compat_urllib_parse.unquote(mobj.group(2))

        video_file = self._search_regex('source=\'(.*?)\'', dec_data, u'video file')
        video_file = compat_urllib_parse.unquote(video_file)

        if not video_file.endswith('f4m'):
            ppath, prefix = video_file.split('.')
            video_playpath = '%s:%s' % (prefix, ppath)
            video_hls_playlist = ''
        else:
            video_playpath = ''
            video_hls_playlist = (
                video_file
            ).replace('.f4m', '.m3u8')

        video_swfobj = self._search_regex('swfobject.embedSWF\(\'(.+?)\'', webpage, u'swfobj')
        video_swfobj = compat_urllib_parse.unquote(video_swfobj)

        video_title = self._html_search_regex("<h1(?: class='globalHd')?>(.*?)</h1>",
            webpage, u'title')

        return [{
            'id':                 video_id,
            'url':                video_url,
            'tc_url':             video_url,
            'uploader':           None,
            'upload_date':        None,
            'title':              video_title,
            'ext':                u'flv',
            'play_path':          video_playpath,
            'video_file':         video_file,
            'video_hls_playlist': video_hls_playlist,
            'player_url':         video_swfobj,
        }]

