# coding: utf-8

import json
import math
import random
import re
import time
from struct import unpack

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request
)


class YoukuIE(InfoExtractor):
    _VALID_URL =  r'(?:(?:http://)?(?:v|player)\.youku\.com/(?:v_show/id_|player\.php/sid/)|youku:)(?P<ID>[A-Za-z0-9]+)(?:\.html|/v\.swf|)'
    _TEST =   {
        u"url": u"http://v.youku.com/v_show/id_XNDgyMDQ2NTQw.html",
        u"file": u"XNDgyMDQ2NTQw_part00.flv",
        u"md5": u"ffe3f2e435663dc2d1eea34faeff5b5b",
        u"params": {u"test": False},
        u"info_dict": {
            u"title": u"youtube-dl test video \"'/\\ä↭𝕐"
        }
    }


    def _gen_sid(self):
        nowTime = int(time.time() * 1000)
        random1 = random.randint(1000,1998)
        random2 = random.randint(1000,9999)

        return "%d%d%d" %(nowTime,random1,random2)

    def _get_file_ID_mix_string(self, seed):
        mixed = []
        source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\:._-1234567890")
        seed = float(seed)
        for i in range(len(source)):
            seed  =  (seed * 211 + 30031) % 65536
            index  =  math.floor(seed / 65536 * len(source))
            mixed.append(source[int(index)])
            source.remove(source[int(index)])
        #return ''.join(mixed)
        return mixed

    def _get_file_id(self, fileId, seed):
        mixed = self._get_file_ID_mix_string(seed)
        ids = fileId.split('*')
        realId = []
        for ch in ids:
            if ch:
                realId.append(mixed[int(ch)])
        return ''.join(realId)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('ID')

        info_url = 'http://v.youku.com/player/getPlayList/VideoIDS/' + video_id

        jsondata = self._download_webpage(info_url, video_id)

        self.report_extraction(video_id)
        try:
            config = json.loads(jsondata)
            error_code = config['data'][0].get('error_code')
            # -8 means blocked outside China.
            if error_code == -8:
                proxy_handler = compat_urllib_request.ProxyHandler({
                    'http': 'h0.edu.bj.ie.sogou.com'
                })
                opener = compat_urllib_request.build_opener(proxy_handler)
                old_opener = compat_urllib_request.install_opener(opener)
                t = hex(int(time.time()))[2:].rstrip('L').zfill(8)
                proxied_request = compat_urllib_request.Request(info_url)
                proxied_request.add_header('X-Sogou-Auth', self.x_sogou_auth)
                proxied_request.add_header('X-Sogou-Tag', self.calc_sogou_hash(t, 'v.youku.com'))
                proxied_request.add_header('X-Sogou-Timestamp', t)
                jsondata = self._download_webpage(proxied_request, video_id)
                config = json.loads(jsondata)
                error_code = config['data'][0].get('error_code')
                # XXX: needs a way to restore the original proxy settings
                compat_urllib_request.install_opener(compat_urllib_request.build_opener(compat_urllib_request.ProxyHandler({})))
            else:
                print 'hahaha'

            if error_code:
                error = config['data'][0].get('error')  # Chinese and English, separated by newline.
                raise ExtractorError(error or u'Server reported error %i' % error_code,
                    expected=True)

            video_title =  config['data'][0]['title']
            seed = config['data'][0]['seed']

            format = self._downloader.params.get('format', None)
            supported_format = list(config['data'][0]['streamfileids'].keys())

            if format is None or format == 'best':
                if 'hd2' in supported_format:
                    format = 'hd2'
                else:
                    format = 'flv'
                ext = u'flv'
            elif format == 'worst':
                format = 'mp4'
                ext = u'mp4'
            else:
                format = 'flv'
                ext = u'flv'


            fileid = config['data'][0]['streamfileids'][format]
            keys = [s['k'] for s in config['data'][0]['segs'][format]]
            # segs is usually a dictionary, but an empty *list* if an error occured.
        except (UnicodeDecodeError, ValueError, KeyError):
            raise ExtractorError(u'Unable to extract info section')

        files_info=[]
        sid = self._gen_sid()
        fileid = self._get_file_id(fileid, seed)

        #column 8,9 of fileid represent the segment number
        #fileid[7:9] should be changed
        for index, key in enumerate(keys):

            temp_fileid = '%s%02X%s' % (fileid[0:8], index, fileid[10:])
            download_url = 'http://f.youku.com/player/getFlvPath/sid/%s_%02X/st/flv/fileid/%s?k=%s' % (sid, index, temp_fileid, key)

            info = {
                'id': '%s_part%02d' % (video_id, index),
                'url': download_url,
                'uploader': None,
                'upload_date': None,
                'title': video_title,
                'ext': ext,
            }
            files_info.append(info)

        return files_info

    x_sogou_auth = "9CD285F1E7ADB0BD403C22AD1D545F40/30/853edc6d49ba4e27"

    # http://xiaoxia.org/2011/11/14/update-sogou-proxy-program-with-https-support/
    def calc_sogou_hash(self, t, host):  
        s = (t + host + 'SogouExplorerProxy').encode('ascii')  
        code = len(s)  
        dwords = int(len(s)/4)  
        rest = len(s) % 4  
        v = unpack(str(dwords) + 'i'+str(rest)+'s', s)  
        for vv in v:  
            if(type(vv)==type('i')):  
                break  
            a = (vv & 0xFFFF)  
            b = (vv >> 16)  
            code += a  
            code = code ^ (((code<<5)^b) << 0xb)  
            # To avoid overflows  
            code &= 0xffffffff  
            code += code >> 0xb  
        if rest == 3:  
            code += ord(s[len(s)-2]) * 256 + ord(s[len(s)-3])  
            code = code ^ ((code ^ (ord(s[len(s)-1])*4)) << 0x10)  
            code &= 0xffffffff  
            code += code >> 0xb  
        elif rest == 2:  
            code += ord(s[len(s)-1]) * 256 + ord(s[len(s)-2])  
            code ^= code << 0xb  
            code &= 0xffffffff  
            code += code >> 0x11  
        elif rest == 1:  
            code += ord(s[len(s)-1])  
            code ^= code << 0xa  
            code &= 0xffffffff  
            code += code >> 0x1  
        code ^= code * 8  
        code &= 0xffffffff  
        code += code >> 5  
        code ^= code << 4  
        code = code & 0xffffffff  
        code += code >> 0x11  
        code ^= code << 0x19  
        code = code & 0xffffffff  
        code += code >> 6  
        code = code & 0xffffffff  
        return hex(code)[2:].rstrip('L').zfill(8)  

