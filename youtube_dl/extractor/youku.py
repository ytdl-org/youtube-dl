# coding: utf-8
from __future__ import unicode_literals

import re
import time
import base64

from .common import InfoExtractor
from ..utils import ExtractorError

from ..compat import compat_urllib_parse

class YoukuIE(InfoExtractor):
    IE_NAME = 'youku'
    _VALID_URL = r'''(?x)
        (?:
            http://(?:v|player)\.youku\.com/(?:v_show/id_|player\.php/sid/)|
            youku:)
        (?P<id>[A-Za-z0-9]+)(?:\.html|/v\.swf|)
    '''

    _TEST = {
            'url': 'http://v.youku.com/v_show/id_XMTc1ODE5Njcy.html',
            'md5': '5f3af4192eabacc4501508d54a8cabd7',
            'info_dict': {
                'id': 'XMTc1ODE5Njcy',
                'title': '★Smile﹗♡ Git Fresh -Booty Music舞蹈.',
                'ext': 'flv'
            }
    }

    # _generate_ep is from
    # https://github.com/soimort/you-get/blob/develop/src/you_get/extractors/youku.py#L22
    def _generate_ep(self, vid, ep):
        f_code_1 = 'becaf9be'
        f_code_2 = 'bf7e5f01'

        def trans_e(a, c):
            f = h = 0
            b = list(range(256))
            result = ''
            while h < 256:
                f = (f + b[h] + ord(a[h % len(a)])) % 256
                b[h], b[f] = b[f], b[h]
                h += 1
            q = f = h = 0
            while q < len(c):
                h = (h + 1) % 256
                f = (f + b[h]) % 256
                b[h], b[f] = b[f], b[h]
                if isinstance(c[q], int):
                    result += chr(c[q] ^ b[(b[h] + b[f]) % 256])
                else:
                    result += chr(ord(c[q]) ^ b[(b[h] + b[f]) % 256])
                q += 1

            return result

        e_code = trans_e(f_code_1, base64.b64decode(bytes(ep, 'ascii')))
        sid, token = e_code.split('_')
        new_ep = trans_e(f_code_2, '%s_%s_%s' % (sid, vid, token))
        return base64.b64encode(bytes(new_ep, 'latin')), sid, token

    def parse_m3u8(self, cm):
        raw_urls = re.findall(r'(https?:.+?)\?', cm)
        t_url = raw_urls[0]
        urls = []
        urls.append(t_url)
        for url in raw_urls:
            if url != t_url:
                urls.append(url)
                t_url = url
        return urls

    def parse_ext_l(self, fm, supported_format):
        if fm in ('hd3', 'hd2', 'flvhd', 'flv'):
            ext = 'flv'
        elif fm in ('mp4',):
            ext = 'mp4'
        elif fm[:3] == '3gp':
            ext = '3gp'
        return ext

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        json_url = 'http://v.youku.com/player/getPlayList/VideoIDS/%s/Pf/4/ctype/12/ev/1' % video_id

        w_info = self._download_json(json_url, video_id)
        data = w_info['data'][0]

        error_code = data.get('error_code')
        if error_code:
            # -8 means blocked outside China.
            # Chinese and English, separated by newline.
            error = data.get('error')
            raise ExtractorError(
                error or 'Server reported error %i' %
                error_code,
                expected=True)

        title = data['title']
        #seed = data['seed']

        format = self._downloader.params.get('format', None)
        supported_format = data['streamtypes']

        # DONE proper format selection
        if format not in supported_format:
            if format is None or format == 'best':
                format = supported_format[-1]
            elif format == 'worst':
                format = supported_format[0]
            else:
                format = supported_format[-2] \
                    if len(supported_format) > 1 \
                    else supported_format[0]
        self._downloader.params['format'] = format

        ep = data['ep']
        ip = data['ip']
        new_ep, sid, token = self._generate_ep(video_id, ep)
        m3u8_url_params = {
            "ctype": 12,
            "ep": new_ep,
            "ev": 1,
            "keyframe": 1,
            "oip": ip,
            "sid": sid,
            "token": token,
            "ts": int(time.time()),
            "type": format,
            "vid": video_id
        }
        m3u8_url = 'http://pl.youku.com/playlist/m3u8?' \
            + compat_urllib_parse.urlencode(m3u8_url_params)
        cm = self._download_webpage(m3u8_url, video_id, 'M3U8 DOWNLOAD')
        video_urls = self.parse_m3u8(cm)

        # construct info
        entries = []
        for i in range(len(video_urls)):
            formats = []
            for fm in supported_format:
                formats.append(
                    {
                        'url': video_urls[i],
                        'format_id': fm,
                        'ext': self.parse_ext_l(fm, supported_format),
                    }
                )
            entries.append(
                {
                    'id': '_part%d' % (i+1),
                    'title': title,
                    'formats': formats
                }
            )

        if len(entries) > 1:
            info = {
                '_type': 'multi_video',
                'id': video_id,
                'title': title,
                'entries': entries,
            }
        else:
            info = entries[0]
            info['id'] = video_id

        return info
