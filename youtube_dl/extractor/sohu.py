# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_request
)
from ..utils import ExtractorError


class SohuIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<mytv>my\.)?tv\.sohu\.com/.+?/(?(mytv)|n)(?P<id>\d+)\.shtml.*?'

    _TESTS = [{
        'note': 'This video is available only in Mainland China',
        'url': 'http://tv.sohu.com/20130724/n382479172.shtml#super',
        'md5': '29175c8cadd8b5cc4055001e85d6b372',
        'info_dict': {
            'id': '382479172',
            'ext': 'mp4',
            'title': 'MV：Far East Movement《The Illest》',
        },
        'skip': 'On available in China',
    }, {
        'url': 'http://tv.sohu.com/20150305/n409385080.shtml',
        'md5': 'ac9a5d322b4bf9ae184d53e4711e4f1a',
        'info_dict': {
            'id': '409385080',
            'ext': 'mp4',
            'title': '《2015湖南卫视羊年元宵晚会》唐嫣《花好月圆》',
        }
    }, {
        'url': 'http://my.tv.sohu.com/us/232799889/78693464.shtml',
        'md5': '49308ff6dafde5ece51137d04aec311e',
        'info_dict': {
            'id': '78693464',
            'ext': 'mp4',
            'title': '【爱范品】第31期：MWC见不到的奇葩手机',
        }
    }, {
        'note': 'Multipart video',
        'url': 'http://my.tv.sohu.com/pl/8384802/78910339.shtml',
        'info_dict': {
            'id': '78910339',
            'title': '【神探苍实战秘籍】第13期 战争之影 赫卡里姆',
        },
        'playlist': [{
            'md5': '492923eac023ba2f13ff69617c32754a',
            'info_dict': {
                'id': '78910339_part1',
                'ext': 'mp4',
                'duration': 294,
                'title': '【神探苍实战秘籍】第13期 战争之影 赫卡里姆',
            }
        }, {
            'md5': 'de604848c0e8e9c4a4dde7e1347c0637',
            'info_dict': {
                'id': '78910339_part2',
                'ext': 'mp4',
                'duration': 300,
                'title': '【神探苍实战秘籍】第13期 战争之影 赫卡里姆',
            }
        }, {
            'md5': '93584716ee0657c0b205b8aa3d27aa13',
            'info_dict': {
                'id': '78910339_part3',
                'ext': 'mp4',
                'duration': 150,
                'title': '【神探苍实战秘籍】第13期 战争之影 赫卡里姆',
            }
        }]
    }, {
        'note': 'Video with title containing dash',
        'url': 'http://my.tv.sohu.com/us/249884221/78932792.shtml',
        'info_dict': {
            'id': '78932792',
            'ext': 'mp4',
            'title': 'youtube-dl testing video',
        },
        'params': {
            'skip_download': True
        }
    }]

    def _real_extract(self, url):

        def _fetch_data(vid_id, mytv=False):
            if mytv:
                base_data_url = 'http://my.tv.sohu.com/play/videonew.do?vid='
            else:
                base_data_url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid='

            req = compat_urllib_request.Request(base_data_url + vid_id)

            cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
            if cn_verification_proxy:
                req.add_header('Ytdl-request-proxy', cn_verification_proxy)

            return self._download_json(
                req, video_id,
                'Downloading JSON data for %s' % vid_id)

        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        mytv = mobj.group('mytv') is not None

        webpage = self._download_webpage(url, video_id)

        title = re.sub(r' - 搜狐视频$', '', self._og_search_title(webpage))

        vid = self._html_search_regex(
            r'var vid ?= ?["\'](\d+)["\']',
            webpage, 'video path')
        vid_data = _fetch_data(vid, mytv)
        if vid_data['play'] != 1:
            if vid_data.get('status') == 12:
                raise ExtractorError(
                    'Sohu said: There\'s something wrong in the video.',
                    expected=True)
            else:
                raise ExtractorError(
                    'Sohu said: The video is only licensed to users in Mainland China.',
                    expected=True)

        formats_json = {}
        for format_id in ('nor', 'high', 'super', 'ori', 'h2644k', 'h2654k'):
            vid_id = vid_data['data'].get('%sVid' % format_id)
            if not vid_id:
                continue
            vid_id = compat_str(vid_id)
            formats_json[format_id] = vid_data if vid == vid_id else _fetch_data(vid_id, mytv)

        part_count = vid_data['data']['totalBlocks']

        playlist = []
        for i in range(part_count):
            formats = []
            for format_id, format_data in formats_json.items():
                data = format_data['data']

                # URLs starts with http://newflv.sohu.ccgslb.net/ is not usable
                # so retry until got a working URL
                video_url = 'newflv.sohu.ccgslb.net'
                retries = 0
                while 'newflv.sohu.ccgslb.net' in video_url and retries < 5:
                    download_note = 'Download information from CDN gateway for format ' + format_id
                    if retries > 0:
                        download_note += ' (retry #%d)' % retries
                    retries += 1
                    cdn_info = self._download_json(
                        'http://data.vod.itc.cn/cdnList?new=' + data['su'][i],
                        video_id, download_note)
                    video_url = cdn_info['url']

                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'filesize': data['clipsBytes'][i],
                    'width': data['width'],
                    'height': data['height'],
                    'fps': data['fps'],
                })
            self._sort_formats(formats)

            playlist.append({
                'id': '%s_part%d' % (video_id, i + 1),
                'title': title,
                'duration': vid_data['data']['clipsDuration'][i],
                'formats': formats,
            })

        if len(playlist) == 1:
            info = playlist[0]
            info['id'] = video_id
        else:
            info = {
                '_type': 'multi_video',
                'entries': playlist,
                'id': video_id,
                'title': title,
            }

        return info
