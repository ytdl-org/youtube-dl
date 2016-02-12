# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request

class CctvIE(InfoExtractor):
    IE_NAME = 'cctv'
    IE_DESC = '央视网'
    _VALID_URL = r'''(?x)
        (
            http://(?:ent|tv)\.(?:cntv|cctv)\.(?:com|cn)/
            ((video/(?P<content_id>[A-Za-z0-9]+))|(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+))
        )
        /(?P<id>[A-Za-z0-9]+)(?:\.shtml|)
    '''

    _TESTS = [{
        'url': 'http://tv.cntv.cn/video/C39296/e0210d949f113ddfb38d31f00a4e5c44',
        # 'md5': 'ec76aa9b1129e2e5b301a474e54fab74',##############
        'info_dict': {
            'id': 'e0210d949f113ddfb38d31f00a4e5c44',
            'ext': 'flv',
            'title': '《传奇故事》 20150409 金钱“魔术”（下）_传奇故事(纪录片)_视频_央视网'
        }
    },{
        'url': 'http://tv.cctv.com/2016/02/05/VIDEUS7apq3lKrHG9Dncm03B160205.shtml',
        # 'md5': 'ec76aa9b1129e2e5b301a474e54fab74',##############
        'info_dict': {
            'id': 'efc5d49e5b3b4ab2b34f3a502b73d3ae',
            'ext': 'flv',
            'title': '[赛车]“车王”舒马赫恢复情况成谜（快讯）'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.match(r'var guid[ ="]+(?P<video_id>[a-zA-Z0-9]+)"', webpage)

        if mobj is None:
            video_id = self._match_id(url)
        else:
            video_id = mobj.group('video_id')

        # reference to youku.py
        def retrieve_data(req_url, note):
            req = compat_urllib_request.Request(req_url)

            cn_verification_proxy = self._downloader.params.get('cn_verification_proxy')
            if cn_verification_proxy:
                req.add_header('Ytdl-request-proxy', cn_verification_proxy)

            raw_data = self._download_json(req, video_id, note=note)
            return raw_data

        get_info_url = \
            'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do' + \
            '?pid=%s' % video_id + \
            '&tz=-8' + \
            '&from=000tv' + \
            '&url=%s' % url + \
            '&idl=32' + \
            '&idlr=32' + \
            '&modifyed=false'

        data = retrieve_data(
            get_info_url,
            'Downloading JSON metadata')

        title = data.get('title')
        uploader = data.get('editer_name')
        hls_url = data.get('hls_url')
        formats = self._extract_m3u8_formats(hls_url, video_id, 'flv')
        self._sort_formats(formats)

        description = self._html_search_meta('description', webpage)
        thumbnail = self._html_search_regex(r'flvImgUrl="(.+?)"', webpage, 'thumbnail')
        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
        }
