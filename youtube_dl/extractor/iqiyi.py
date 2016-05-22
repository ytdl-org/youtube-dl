# coding: utf-8
from __future__ import unicode_literals

import hashlib
import itertools
import math
import os
import random
import re
import time
import uuid

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    decode_packed_codes,
    ExtractorError,
    ohdave_rsa_encrypt,
    remove_start,
    sanitized_Request,
    urlencode_postdata,
    url_basename,
)


def md5_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


class IqiyiSDK(object):
    def __init__(self, target, ip, timestamp):
        self.target = target
        self.ip = ip
        self.timestamp = timestamp

    @staticmethod
    def split_sum(data):
        return compat_str(sum(map(lambda p: int(p, 16), list(data))))

    @staticmethod
    def digit_sum(num):
        if isinstance(num, int):
            num = compat_str(num)
        return compat_str(sum(map(int, num)))

    def even_odd(self):
        even = self.digit_sum(compat_str(self.timestamp)[::2])
        odd = self.digit_sum(compat_str(self.timestamp)[1::2])
        return even, odd

    def preprocess(self, chunksize):
        self.target = md5_text(self.target)
        chunks = []
        for i in range(32 // chunksize):
            chunks.append(self.target[chunksize * i:chunksize * (i + 1)])
        if 32 % chunksize:
            chunks.append(self.target[32 - 32 % chunksize:])
        return chunks, list(map(int, self.ip.split('.')))

    def mod(self, modulus):
        chunks, ip = self.preprocess(32)
        self.target = chunks[0] + ''.join(map(lambda p: compat_str(p % modulus), ip))

    def split(self, chunksize):
        modulus_map = {
            4: 256,
            5: 10,
            8: 100,
        }

        chunks, ip = self.preprocess(chunksize)
        ret = ''
        for i in range(len(chunks)):
            ip_part = compat_str(ip[i] % modulus_map[chunksize]) if i < 4 else ''
            if chunksize == 8:
                ret += ip_part + chunks[i]
            else:
                ret += chunks[i] + ip_part
        self.target = ret

    def handle_input16(self):
        self.target = md5_text(self.target)
        self.target = self.split_sum(self.target[:16]) + self.target + self.split_sum(self.target[16:])

    def handle_input8(self):
        self.target = md5_text(self.target)
        ret = ''
        for i in range(4):
            part = self.target[8 * i:8 * (i + 1)]
            ret += self.split_sum(part) + part
        self.target = ret

    def handleSum(self):
        self.target = md5_text(self.target)
        self.target = self.split_sum(self.target) + self.target

    def date(self, scheme):
        self.target = md5_text(self.target)
        d = time.localtime(self.timestamp)
        strings = {
            'y': compat_str(d.tm_year),
            'm': '%02d' % d.tm_mon,
            'd': '%02d' % d.tm_mday,
        }
        self.target += ''.join(map(lambda c: strings[c], list(scheme)))

    def split_time_even_odd(self):
        even, odd = self.even_odd()
        self.target = odd + md5_text(self.target) + even

    def split_time_odd_even(self):
        even, odd = self.even_odd()
        self.target = even + md5_text(self.target) + odd

    def split_ip_time_sum(self):
        chunks, ip = self.preprocess(32)
        self.target = compat_str(sum(ip)) + chunks[0] + self.digit_sum(self.timestamp)

    def split_time_ip_sum(self):
        chunks, ip = self.preprocess(32)
        self.target = self.digit_sum(self.timestamp) + chunks[0] + compat_str(sum(ip))


class IqiyiSDKInterpreter(object):
    def __init__(self, sdk_code):
        self.sdk_code = sdk_code

    def run(self, target, ip, timestamp):
        self.sdk_code = decode_packed_codes(self.sdk_code)

        functions = re.findall(r'input=([a-zA-Z0-9]+)\(input', self.sdk_code)

        sdk = IqiyiSDK(target, ip, timestamp)

        other_functions = {
            'handleSum': sdk.handleSum,
            'handleInput8': sdk.handle_input8,
            'handleInput16': sdk.handle_input16,
            'splitTimeEvenOdd': sdk.split_time_even_odd,
            'splitTimeOddEven': sdk.split_time_odd_even,
            'splitIpTimeSum': sdk.split_ip_time_sum,
            'splitTimeIpSum': sdk.split_time_ip_sum,
        }
        for function in functions:
            if re.match(r'mod\d+', function):
                sdk.mod(int(function[3:]))
            elif re.match(r'date[ymd]{3}', function):
                sdk.date(function[4:])
            elif re.match(r'split\d+', function):
                sdk.split(int(function[5:]))
            elif function in other_functions:
                other_functions[function]()
            else:
                raise ExtractorError('Unknown funcion %s' % function)

        return sdk.target


class IqiyiIE(InfoExtractor):
    IE_NAME = 'iqiyi'
    IE_DESC = '爱奇艺'

    _VALID_URL = r'https?://(?:(?:[^.]+\.)?iqiyi\.com|www\.pps\.tv)/.+\.html'

    _NETRC_MACHINE = 'iqiyi'

    _TESTS = [{
        'url': 'http://www.iqiyi.com/v_19rrojlavg.html',
        'md5': '2cb594dc2781e6c941a110d8f358118b',
        'info_dict': {
            'id': '9c1fb1b99d192b21c559e5a1a2cb3c73',
            'title': '美国德州空中惊现奇异云团 酷似UFO',
            'ext': 'f4v',
        }
    }, {
        'url': 'http://www.iqiyi.com/v_19rrhnnclk.html',
        'info_dict': {
            'id': 'e3f585b550a280af23c98b6cb2be19fb',
            'title': '名侦探柯南第752集',
        },
        'playlist': [{
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part1',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part2',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part3',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part4',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part5',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part6',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part7',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }, {
            'info_dict': {
                'id': 'e3f585b550a280af23c98b6cb2be19fb_part8',
                'ext': 'f4v',
                'title': '名侦探柯南第752集',
            },
        }],
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.iqiyi.com/w_19rt6o8t9p.html',
        'only_matching': True,
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhbc6kt.html',
        'only_matching': True,
    }, {
        'url': 'http://yule.iqiyi.com/pcb.html',
        'only_matching': True,
    }, {
        # VIP-only video. The first 2 parts (6 minutes) are available without login
        # MD5 sums omitted as values are different on Travis CI and my machine
        'url': 'http://www.iqiyi.com/v_19rrny4w8w.html',
        'info_dict': {
            'id': 'f3cf468b39dddb30d676f89a91200dc1',
            'title': '泰坦尼克号',
        },
        'playlist': [{
            'info_dict': {
                'id': 'f3cf468b39dddb30d676f89a91200dc1_part1',
                'ext': 'f4v',
                'title': '泰坦尼克号',
            },
        }, {
            'info_dict': {
                'id': 'f3cf468b39dddb30d676f89a91200dc1_part2',
                'ext': 'f4v',
                'title': '泰坦尼克号',
            },
        }],
        'expected_warnings': ['Needs a VIP account for full video'],
    }, {
        'url': 'http://www.iqiyi.com/a_19rrhb8ce1.html',
        'info_dict': {
            'id': '202918101',
            'title': '灌篮高手 国语版',
        },
        'playlist_count': 101,
    }, {
        'url': 'http://www.pps.tv/w_19rrbav0ph.html',
        'only_matching': True,
    }]

    _FORMATS_MAP = [
        ('1', 'h6'),
        ('2', 'h5'),
        ('3', 'h4'),
        ('4', 'h3'),
        ('5', 'h2'),
        ('10', 'h1'),
    ]

    AUTH_API_ERRORS = {
        # No preview available (不允许试看鉴权失败)
        'Q00505': 'This video requires a VIP account',
        # End of preview time (试看结束鉴权失败)
        'Q00506': 'Needs a VIP account for full video',
    }

    def _real_initialize(self):
        self._login()

    @staticmethod
    def _rsa_fun(data):
        # public key extracted from http://static.iqiyi.com/js/qiyiV2/20160129180840/jobs/i18n/i18nIndex.js
        N = 0xab86b6371b5318aaa1d3c9e612a9f1264f372323c8c0f19875b5fc3b3fd3afcc1e5bec527aa94bfa85bffc157e4245aebda05389a5357b75115ac94f074aefcd
        e = 65537

        return ohdave_rsa_encrypt(data, e, N)

    def _login(self):
        (username, password) = self._get_login_info()

        # No authentication to be performed
        if not username:
            return True

        data = self._download_json(
            'http://kylin.iqiyi.com/get_token', None,
            note='Get token for logging', errnote='Unable to get token for logging')
        sdk = data['sdk']
        timestamp = int(time.time())
        target = '/apis/reglogin/login.action?lang=zh_TW&area_code=null&email=%s&passwd=%s&agenttype=1&from=undefined&keeplogin=0&piccode=&fromurl=&_pos=1' % (
            username, self._rsa_fun(password.encode('utf-8')))

        interp = IqiyiSDKInterpreter(sdk)
        sign = interp.run(target, data['ip'], timestamp)

        validation_params = {
            'target': target,
            'server': 'BEA3AA1908656AABCCFF76582C4C6660',
            'token': data['token'],
            'bird_src': 'f8d91d57af224da7893dd397d52d811a',
            'sign': sign,
            'bird_t': timestamp,
        }
        validation_result = self._download_json(
            'http://kylin.iqiyi.com/validate?' + compat_urllib_parse_urlencode(validation_params), None,
            note='Validate credentials', errnote='Unable to validate credentials')

        MSG_MAP = {
            'P00107': 'please login via the web interface and enter the CAPTCHA code',
            'P00117': 'bad username or password',
        }

        code = validation_result['code']
        if code != 'A00000':
            msg = MSG_MAP.get(code)
            if not msg:
                msg = 'error %s' % code
                if validation_result.get('msg'):
                    msg += ': ' + validation_result['msg']
            self._downloader.report_warning('unable to log in: ' + msg)
            return False

        return True

    def _authenticate_vip_video(self, api_video_url, video_id, tvid, _uuid, do_report_warning):
        auth_params = {
            # version and platform hard-coded in com/qiyi/player/core/model/remote/AuthenticationRemote.as
            'version': '2.0',
            'platform': 'b6c13e26323c537d',
            'aid': tvid,
            'tvid': tvid,
            'uid': '',
            'deviceId': _uuid,
            'playType': 'main',  # XXX: always main?
            'filename': os.path.splitext(url_basename(api_video_url))[0],
        }

        qd_items = compat_parse_qs(compat_urllib_parse_urlparse(api_video_url).query)
        for key, val in qd_items.items():
            auth_params[key] = val[0]

        auth_req = sanitized_Request(
            'http://api.vip.iqiyi.com/services/ckn.action',
            urlencode_postdata(auth_params))
        # iQiyi server throws HTTP 405 error without the following header
        auth_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        auth_result = self._download_json(
            auth_req, video_id,
            note='Downloading video authentication JSON',
            errnote='Unable to download video authentication JSON')

        code = auth_result.get('code')
        msg = self.AUTH_API_ERRORS.get(code) or auth_result.get('msg') or code
        if code == 'Q00506':
            if do_report_warning:
                self.report_warning(msg)
            return False
        if 'data' not in auth_result:
            if msg is not None:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, msg), expected=True)
            raise ExtractorError('Unexpected error from Iqiyi auth API')

        return auth_result['data']

    def construct_video_urls(self, data, video_id, _uuid, tvid):
        def do_xor(x, y):
            a = y % 3
            if a == 1:
                return x ^ 121
            if a == 2:
                return x ^ 72
            return x ^ 103

        def get_encode_code(l):
            a = 0
            b = l.split('-')
            c = len(b)
            s = ''
            for i in range(c - 1, -1, -1):
                a = do_xor(int(b[c - i - 1], 16), i)
                s += chr(a)
            return s[::-1]

        def get_path_key(x, format_id, segment_index):
            mg = ')(*&^flash@#$%a'
            tm = self._download_json(
                'http://data.video.qiyi.com/t?tn=' + str(random.random()), video_id,
                note='Download path key of segment %d for format %s' % (segment_index + 1, format_id)
            )['t']
            t = str(int(math.floor(int(tm) / (600.0))))
            return md5_text(t + mg + x)

        video_urls_dict = {}
        need_vip_warning_report = True
        for format_item in data['vp']['tkl'][0]['vs']:
            if 0 < int(format_item['bid']) <= 10:
                format_id = self.get_format(format_item['bid'])
            else:
                continue

            video_urls = []

            video_urls_info = format_item['fs']
            if not format_item['fs'][0]['l'].startswith('/'):
                t = get_encode_code(format_item['fs'][0]['l'])
                if t.endswith('mp4'):
                    video_urls_info = format_item['flvs']

            for segment_index, segment in enumerate(video_urls_info):
                vl = segment['l']
                if not vl.startswith('/'):
                    vl = get_encode_code(vl)
                is_vip_video = '/vip/' in vl
                filesize = segment['b']
                base_url = data['vp']['du'].split('/')
                if not is_vip_video:
                    key = get_path_key(
                        vl.split('/')[-1].split('.')[0], format_id, segment_index)
                    base_url.insert(-1, key)
                base_url = '/'.join(base_url)
                param = {
                    'su': _uuid,
                    'qyid': uuid.uuid4().hex,
                    'client': '',
                    'z': '',
                    'bt': '',
                    'ct': '',
                    'tn': str(int(time.time()))
                }
                api_video_url = base_url + vl
                if is_vip_video:
                    api_video_url = api_video_url.replace('.f4v', '.hml')
                    auth_result = self._authenticate_vip_video(
                        api_video_url, video_id, tvid, _uuid, need_vip_warning_report)
                    if auth_result is False:
                        need_vip_warning_report = False
                        break
                    param.update({
                        't': auth_result['t'],
                        # cid is hard-coded in com/qiyi/player/core/player/RuntimeData.as
                        'cid': 'afbe8fd3d73448c9',
                        'vid': video_id,
                        'QY00001': auth_result['u'],
                    })
                api_video_url += '?' if '?' not in api_video_url else '&'
                api_video_url += compat_urllib_parse_urlencode(param)
                js = self._download_json(
                    api_video_url, video_id,
                    note='Download video info of segment %d for format %s' % (segment_index + 1, format_id))
                video_url = js['l']
                video_urls.append(
                    (video_url, filesize))

            video_urls_dict[format_id] = video_urls
        return video_urls_dict

    def get_format(self, bid):
        matched_format_ids = [_format_id for _bid, _format_id in self._FORMATS_MAP if _bid == str(bid)]
        return matched_format_ids[0] if len(matched_format_ids) else None

    def get_bid(self, format_id):
        matched_bids = [_bid for _bid, _format_id in self._FORMATS_MAP if _format_id == format_id]
        return matched_bids[0] if len(matched_bids) else None

    def get_raw_data(self, tvid, video_id, enc_key, _uuid):
        tm = str(int(time.time()))
        tail = tm + tvid
        param = {
            'key': 'fvip',
            'src': md5_text('youtube-dl'),
            'tvId': tvid,
            'vid': video_id,
            'vinfo': 1,
            'tm': tm,
            'enc': md5_text(enc_key + tail),
            'qyid': _uuid,
            'tn': random.random(),
            # In iQiyi's flash player, um is set to 1 if there's a logged user
            # Some 1080P formats are only available with a logged user.
            # Here force um=1 to trick the iQiyi server
            'um': 1,
            'authkey': md5_text(md5_text('') + tail),
            'k_tag': 1,
        }

        api_url = 'http://cache.video.qiyi.com/vms' + '?' + \
            compat_urllib_parse_urlencode(param)
        raw_data = self._download_json(api_url, video_id)
        return raw_data

    def get_enc_key(self, video_id):
        # TODO: automatic key extraction
        # last update at 2016-01-22 for Zombie::bite
        enc_key = '4a1caba4b4465345366f28da7c117d20'
        return enc_key

    def _extract_playlist(self, webpage):
        PAGE_SIZE = 50

        links = re.findall(
            r'<a[^>]+class="site-piclist_pic_link"[^>]+href="(http://www\.iqiyi\.com/.+\.html)"',
            webpage)
        if not links:
            return

        album_id = self._search_regex(
            r'albumId\s*:\s*(\d+),', webpage, 'album ID')
        album_title = self._search_regex(
            r'data-share-title="([^"]+)"', webpage, 'album title', fatal=False)

        entries = list(map(self.url_result, links))

        # Start from 2 because links in the first page are already on webpage
        for page_num in itertools.count(2):
            pagelist_page = self._download_webpage(
                'http://cache.video.qiyi.com/jp/avlist/%s/%d/%d/' % (album_id, page_num, PAGE_SIZE),
                album_id,
                note='Download playlist page %d' % page_num,
                errnote='Failed to download playlist page %d' % page_num)
            pagelist = self._parse_json(
                remove_start(pagelist_page, 'var tvInfoJs='), album_id)
            vlist = pagelist['data']['vlist']
            for item in vlist:
                entries.append(self.url_result(item['vurl']))
            if len(vlist) < PAGE_SIZE:
                break

        return self.playlist_result(entries, album_id, album_title)

    def _real_extract(self, url):
        webpage = self._download_webpage(
            url, 'temp_id', note='download video page')

        # There's no simple way to determine whether an URL is a playlist or not
        # So detect it
        playlist_result = self._extract_playlist(webpage)
        if playlist_result:
            return playlist_result

        tvid = self._search_regex(
            r'data-player-tvid\s*=\s*[\'"](\d+)', webpage, 'tvid')
        video_id = self._search_regex(
            r'data-player-videoid\s*=\s*[\'"]([a-f\d]+)', webpage, 'video_id')
        _uuid = uuid.uuid4().hex

        enc_key = self.get_enc_key(video_id)

        raw_data = self.get_raw_data(tvid, video_id, enc_key, _uuid)

        if raw_data['code'] != 'A000000':
            raise ExtractorError('Unable to load data. Error code: ' + raw_data['code'])

        data = raw_data['data']

        title = data['vi']['vn']

        # generate video_urls_dict
        video_urls_dict = self.construct_video_urls(
            data, video_id, _uuid, tvid)

        # construct info
        entries = []
        for format_id in video_urls_dict:
            video_urls = video_urls_dict[format_id]
            for i, video_url_info in enumerate(video_urls):
                if len(entries) < i + 1:
                    entries.append({'formats': []})
                entries[i]['formats'].append(
                    {
                        'url': video_url_info[0],
                        'filesize': video_url_info[-1],
                        'format_id': format_id,
                        'preference': int(self.get_bid(format_id))
                    }
                )

        for i in range(len(entries)):
            self._sort_formats(entries[i]['formats'])
            entries[i].update(
                {
                    'id': '%s_part%d' % (video_id, i + 1),
                    'title': title,
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
            info['title'] = title

        return info
