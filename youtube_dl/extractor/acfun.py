# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..compat import (
    compat_cookiejar,
    compat_urllib_parse_urlencode,
    compat_urllib_request,
)
from ..utils import (
    int_or_none,
    float_or_none,
    str_or_none,
    str_to_int,
    sanitized_Request,
    ExtractorError,
)

class BasicAcfunInfoExtractor(InfoExtractor):
    _FAKE_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
        'Accept-Charset': 'UTF-8,*;q=0.5',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',  # noqa
    }    
    def _extract_formats(self, currentVideoInfo):
        durationMillis = currentVideoInfo.get('durationMillis')
        if 'ksPlayJson' in currentVideoInfo:
            ksPlayJson = ksPlayJson = json.loads( currentVideoInfo['ksPlayJson'] )
            representation = ksPlayJson.get('adaptationSet')[0].get('representation')

        formats = []
        for stream in representation:
            size = float_or_none(durationMillis) * stream["avgBitrate"] / 8
            stream_id = stream["qualityLabel"]
            quality = stream["qualityType"]
            formats += [{
                'url': stream["url"],
                'ext': 'mp4',
                'width': stream.get('width'),
                'height': stream.get('height'),
                'filesize': size,
            }]
        formats = formats[::-1]  
        self._sort_formats(formats)
        return formats        

class AcfunIE(BasicAcfunInfoExtractor):
    _VALID_URL = r'https?://www\.acfun\.cn/v/ac(?P<id>[_\d]+)'
    _TESTS = [
        {
            'url': 'https://www.acfun.cn/v/ac18184362',
            'info_dict': {
                'id': '18184362',
                'ext': 'mp4',
                'duration': 192.042,
                'title': '【AC娘】魔性新单《极乐857》上线！来和AC娘一起云蹦迪吧！',
                'uploader': 'AC娘本体',
                'uploader_id': 23682490
            }
        },
        {
            'url': 'https://www.acfun.cn/v/ac17532274_3',
            'info_dict': {
                'id': '17532274_3',
                'ext': 'mp4',
                'duration': 233.770,
                'title': '【AC娘x竾颜音】【周六狂欢24小时】TRAP：七夕恋歌！落入本娘爱的陷阱！ - TRAP 阿婵',
                'uploader': 'AC娘本体',
                'uploader_id': 23682490
            }
        }
    ]  

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers=self._FAKE_HEADERS)

        json_text = self._html_search_regex(r'(?s)videoInfo\s*=\s*(\{.*?\});', webpage, 'json_text')
        json_data = json.loads(json_text)

        title = json_data['title']
        p_title = self._html_search_regex(r"<li\s[^<]*?class='[^']*active[^']*'.*?>(.*?)</li>", webpage, 'p_title', default=None)
        if p_title:
            title = '%s - %s' % (title, p_title)                  

        uploader = json_data.get('user').get('name')
        uploader_id = json_data.get('user').get('id')

        currentVideoInfo = json_data.get('currentVideoInfo')
        durationMillis = currentVideoInfo.get('durationMillis')
        duration = durationMillis / 1000    
    
        formats = self._extract_formats(currentVideoInfo)
        return {
            'id': video_id,
            'uploader_id': str_to_int(uploader_id),
            'title': title,
            'uploader': str_or_none(uploader),
            'duration': float_or_none(duration),
            'formats': formats
        }


class AcfunBangumiIE(BasicAcfunInfoExtractor):
    _VALID_URL = r'https?://www\.acfun\.cn/bangumi/aa(?P<id>[_\d]+)'
    _TEST = {
        'url': 'https://www.acfun.cn/bangumi/aa6002917_36188_1748679',
        'info_dict': {
            'id': '6002917_36188_1748679',
            'ext': 'mp4',
            'duration': 1437.076,
            'title': '租借女友 第12话 告白和女友',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers=self._FAKE_HEADERS)

        json_text = self._html_search_regex(r'(?s)bangumiData\s*=\s*(\{.*?\});', webpage, 'json_text')
        json_data = json.loads(json_text)

        title = json_data.get('showTitle') or json_data['bangumiTitle'] + " " + json_data['episodeName'] + " " + json_data['title']

        currentVideoInfo = json_data.get('currentVideoInfo')
        durationMillis = currentVideoInfo.get('durationMillis')
        duration = durationMillis / 1000    

        formats = self._extract_formats(currentVideoInfo)
        return {
            'id': video_id,
            'title': title,
            'duration': float_or_none(duration),
            'formats': formats
        }

class AcfunLiveIE(BasicAcfunInfoExtractor):
    _VALID_URL = r'https?://live\.acfun\.cn/live/(?P<id>\d+)'
    _TEST = {
        'url': 'https://live.acfun.cn/live/36782183',
        'only_matching': True,
        'info_dict': {
            'id': '36782183',
            'ext': 'mp4',
            # 'title': '看见兔兔就烦！',
            'is_live': True,
        } 
    }

    def _real_extract(self, url):
        live_id = self._match_id(url)
        self._FAKE_HEADERS.update({
            'Referer': url
        })

        # Firstly get _did cookie
        fisrt_req = sanitized_Request(url, headers=self._FAKE_HEADERS)
        first_res = compat_urllib_request.urlopen(fisrt_req)

        for header_name, header_value in first_res.info().items():
            if header_name.lower() == 'set-cookie':
                cookies = header_value
        if not cookies:
            raise ExtractorError('Fail to fetch cookies')

        cookies_dict = dict(c.strip(' ,').split('=', 1) for c in cookies.split(';'))
        did_cookie = cookies_dict['_did']        

        self._FAKE_HEADERS.update({
            'Cookie': '_did=%s' % did_cookie
        })        

        # Login to get userId and acfun.api.visitor_st
        login_data = compat_urllib_parse_urlencode({'sid': 'acfun.api.visitor'}).encode('ascii')
        login_json = self._download_json(
            'https://id.app.acfun.cn/rest/app/visitor/login', 
            live_id, 
            data=login_data, 
            headers=self._FAKE_HEADERS)

        streams_url = "https://api.kuaishouzt.com/rest/zt/live/web/startPlay?subBiz=mainApp&kpn=ACFUN_APP&kpf=PC_WEB&userId=%d&did=%s&acfun.api.visitor_st=%s" % (
            login_json['userId'], 
            did_cookie, login_json['acfun.api.visitor_st'])

        # Fetch stream lists
        fetch_streams_data = compat_urllib_parse_urlencode({
            'authorId':  int_or_none(live_id),
            'pullStreamType': 'FLV'    
        }).encode('ascii')

        streams_json = self._download_json(
            streams_url, 
            live_id,  
            data=fetch_streams_data, 
            headers=self._FAKE_HEADERS)

        # print(streams_json)
        title = streams_json['data']['caption']
        streams_info = json.loads(streams_json['data']['videoPlayRes']) # streams info
        representation = streams_info['liveAdaptiveManifest'][0]['adaptationSet']['representation']
        
        formats = []
        for stream in representation:
            quality = stream["qualityType"]
            formats += [{
                'url': stream["url"],
                'ext': 'mp4',
                'tbr': stream.get('bitrate'),
            }]  
        self._sort_formats(formats)
        return {
            'id': live_id,
            'title': self._live_title(title),
            'formats': formats,
            'is_live': True
        }