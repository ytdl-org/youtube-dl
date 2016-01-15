# coding: utf-8
from __future__ import unicode_literals

import base64
import random
import string
import time

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_ord,
)
from ..utils import (
    ExtractorError,
    sanitized_Request,
    int_or_none,
    float_or_none,
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
            'id': 'XMTc1ODE5Njcy_part1',
            'title': '★Smile﹗♡ Git Fresh -Booty Music舞蹈.',
            'ext': 'flv'
        }
    }, {
        'url': 'http://player.youku.com/player.php/sid/XNDgyMDQ2NTQw/v.swf',
        'only_matching': True,
    }, {
        'url': 'http://v.youku.com/v_show/id_XODgxNjg1Mzk2_ev_1.html',
        'info_dict': {
            'id': 'XODgxNjg1Mzk2',
            'title': '武媚娘传奇 85',
        },
        'playlist_count': 11,
        'skip': 'Available in China only',
    }, {
        'url': 'http://v.youku.com/v_show/id_XMTI1OTczNDM5Mg==.html',
        'info_dict': {
            'id': 'XMTI1OTczNDM5Mg',
            'title': '花千骨 04',
        },
        'playlist_count': 13,
    }, {
        'url': 'http://v.youku.com/v_show/id_XNjA1NzA2Njgw.html',
        'note': 'Video protected with password',
        'info_dict': {
            'id': 'XNjA1NzA2Njgw',
            'title': '邢義田复旦讲座之想象中的胡人—从“左衽孔子”说起',
        },
        'playlist_count': 19,
        'params': {
            'videopassword': '100600',
        },
    }]

    def construct_formats(self, data):
        # get sid, token
        def yk_t(s1, s2):
            ls = list(range(256))
            t = 0
            for i in range(256):
                t = (t + ls[i] + compat_ord(s1[i % len(s1)])) % 256
                ls[i], ls[t] = ls[t], ls[i]
            s = bytearray()
            x, y = 0, 0
            for i in range(len(s2)):
                y = (y + 1) % 256
                x = (x + ls[y]) % 256
                ls[x], ls[y] = ls[y], ls[x]
                s.append(compat_ord(s2[i]) ^ ls[(ls[x] + ls[y]) % 256])
            return bytes(s)

        sid, token = yk_t(
            b'becaf9be', base64.b64decode(data['security']['encrypt_string'].encode('ascii'))
        ).decode('ascii').split('_')

        # get oip
        oip = data['security']['ip']

        fileid_dict = {}
        for stream in data['stream']:
            format = stream.get('stream_type')
            fileid = stream['stream_fileid']
            fileid_dict[format] = fileid

        def get_fileid(format, n):
            number = hex(int(str(n), 10))[2:].upper()
            if len(number) == 1:
                number = '0' + number
            streamfileids = fileid_dict[format]
            fileid = streamfileids[0:8] + number + streamfileids[10:]
            return fileid

        # get ep
        def generate_ep(format, n):
            fileid = get_fileid(format, n)
            ep_t = yk_t(
                b'bf7e5f01',
                ('%s_%s_%s' % (sid, fileid, token)).encode('ascii')
            )
            ep = base64.b64encode(ep_t).decode('ascii')
            return ep

        formats = []
        for stream in data['stream']:
            format = stream.get('stream_type')
            parts = []
            for dt in stream['segs']:
                n = str(stream['segs'].index(dt))
                param = {
                    'K': dt['key'],
                    'hd': self.get_hd(format),
                    'myp': 0,
                    'ypp': 0,
                    'ctype': 12,
                    'ev': 1,
                    'token': token,
                    'oip': oip,
                    'ep': generate_ep(format, n)
                }
                video_url = \
                    'http://k.youku.com/player/getFlvPath/' + \
                    'sid/' + sid + \
                    '_00' + \
                    '/st/' + self.parse_ext_l(format) + \
                    '/fileid/' + get_fileid(format, n) + '?' + \
                    compat_urllib_parse.urlencode(param)
                parts.append({
                    'url': video_url,
                    'filesize': int_or_none(dt.get('size')),
                })
            formats.append({
                'format_id': self.get_format_name(format),
                'parts': parts,
                'width': int_or_none(stream.get('width')),
                'height': int_or_none(stream.get('height')),
                'filesize': int_or_none(stream.get('size')),
                'ext': self.parse_ext_l(format),
            })
        self._sort_formats(formats)
        return formats

    @staticmethod
    def get_ysuid():
        return '%d%s' % (int(time.time()), ''.join([
            random.choice(string.ascii_letters) for i in range(3)]))

    def get_hd(self, fm):
        hd_id_dict = {
            '3gp': '0',
            '3gphd': '1',
            'flv': '0',
            'flvhd': '0',
            'mp4': '1',
            'mp4hd': '1',
            'mp4hd2': '1',
            'mp4hd3': '1',
            'hd2': '2',
            'hd3': '3',
        }
        return hd_id_dict[fm]

    def parse_ext_l(self, fm):
        ext_dict = {
            '3gp': 'flv',
            '3gphd': 'mp4',
            'flv': 'flv',
            'flvhd': 'flv',
            'mp4': 'mp4',
            'mp4hd': 'mp4',
            'mp4hd2': 'flv',
            'mp4hd3': 'flv',
            'hd2': 'flv',
            'hd3': 'flv',
        }
        return ext_dict[fm]

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
        return _dict[fm]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        self._set_cookie('youku.com', '__ysuid', self.get_ysuid())

        def retrieve_data(req_url, note):
            headers = {
                'Referer': req_url,
            }
            self._set_cookie('youku.com', 'xreferrer', 'http://www.youku.com')
            req = sanitized_Request(req_url, headers=headers)

            cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
            if cn_verification_proxy:
                req.add_header('Ytdl-request-proxy', cn_verification_proxy)

            raw_data = self._download_json(req, video_id, note=note)

            return raw_data['data']

        video_password = self._downloader.params.get('videopassword', None)

        # request basic data
        basic_data_url = "http://play.youku.com/play/get.json?vid=%s&ct=12" % video_id
        if video_password:
            basic_data_url += '&pwd=%s' % video_password

        data = retrieve_data(basic_data_url, 'Downloading JSON metadata')

        error = data.get('error')
        if error:
            error_note = error.get('note')
            if error_note is not None and '因版权原因无法观看此视频' in error_note:
                raise ExtractorError(
                    'Youku said: Sorry, this video is available in China only', expected=True)
            else:
                msg = 'Youku server reported error %i' % error.get('code')
                if error_note is not None:
                    msg += ': ' + error_note
                raise ExtractorError(msg)

        video_data = data['video']

        return {
            'id': video_id,
            'title': video_data['title'],
            'duration': float_or_none(video_data.get('seconds')),
            'uploader': video_data.get('username'),
            'uploader_id': video_data.get('userid'),
            'formats': self.construct_formats(data),
        }
