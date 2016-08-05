# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError

class ViuIE(InfoExtractor):
    IE_DESC = 'Viu.com'
    _VALID_URL = r'''(?x)^
                    (?:https?://|//)        # http(s):// or protocol-independent URL
                    (?:(?:www\.)?viu\.com)  # main hostname
                    .*                      # path components
                    /vod/                   # path anchor, make sure it is a video page
                    (?P<id>[0-9]+)          # product_id (=video_id)
                    /                       # trailing slash is required
                    .*                      # anything can follow
                    $'''
    _config_url = 'http://www.viu.com/ott/hk/v1/js/config.js'
    _js_var_pattern = r'var\s+%s\s*=\s*(.*)\s*;' # get a value from javascript variable declaration
    _subtitle_lang = {
        '1': 'zh_hk',
        '2': 'zh_cn',
        '3': 'en',
    }
    _TESTS = [
        {
            'url': 'http://www.viu.com/ott/hk/zh-hk/vod/17732/Doctors',
            'md5': '563f4efac43f62873bab47ba0e84d2f9',
            'info_dict': {
                'id': '17732',
                'title': 'Doctors 13 [我想念嫲嫲的湯飯]',
                'thumbnail': 're:(https?:)?//[0-9a-zA-Z]+\.cloudfront\.net/2849538801/bb28adaf740c168ecb9340e73ddc9c5b4e62e313',
            }
        },
        {
            'url': 'https://www.viu.com/ott/hk/zh-hk/vod/16061/',
            'info_dict': {
                'id': '16061',
                'title': 'Doctors 1 [我們的相遇是孽緣嗎？]',
                'thumbnail': 're:(https?:)?//[0-9a-zA-Z]+\.cloudfront\.net/3543435935/6696b3b32ec1213adbe4f251ba824b019f4c83c1'
            }
        },
        {
            'url': '//www.viu.com/ott/hk/zh-hk/vod/16915/%E3%80%8AW%EF%BC%8D%E5%85%A9%E5%80%8B%E4%B8%96%E7%95%8C%E3%80%8B%E9%A0%90%E5%91%8A',
            'info_dict': {
                'id': '16915',
                'title': '《W－兩個世界》預告 1 [漫畫人物姜哲來到現實！]',
                'thumbnail': 're:(https?:)?//[0-9a-zA-Z]+\.cloudfront\.net/1928834/02b2382ff1799c200f8f03500f9da1d87ea68d22'
            }
        },
        {
            'url': 'http://www.viu.com/ott/hk/zh-hk/vod/7379/%E6%88%91%E5%80%91%E7%B5%90%E5%A9%9A%E4%BA%86%20(2015)',
            'info_dict': {
                'id': '7379',
                'title': '我們結婚了 (2015) 301 [養眼夫婦百日合約到期]',
                'thumbnail': 're:(https?:)?//[0-9a-zA-Z]+\.cloudfront\.net/2521531018/04f4b8c5d94865cb46118e206b7ba5d5329d8064'
            }
        }
    ]
    
    def search_js_var(self, string, var_name):
        result = self._search_regex(self._js_var_pattern % var_name, string, var_name)
        result = re.sub(r'(^\')|(\'$)', '"', result)
        return json.loads(result) if result is not None else None
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        # confirm the product_id from the url with the one found in content script
        product_id = self.search_js_var(webpage, 'product_id')
        if video_id != product_id:
            raise ExtractorError('Video ID in webpage "%s" does not match URL "%s"' % (product_id, video_id))
        
        # fetch variables
        config_js = self._download_webpage(
            'http://www.viu.com/ott/hk/v1/js/config.js',
            product_id,
            'Downloading runtime variables from config.js',
            'Unable to download config.js')
        web_api_url = self.search_js_var(config_js, 'web_api_url')
        web_api_tail = self.search_js_var(config_js, 'web_api_tail')
        video_url = self.search_js_var(config_js, 'video_url')
        user_param = "";
        ut_param = '0';
        
        # video info
        url = web_api_url + 'vod/ajax-detail' + web_api_tail + user_param + '&product_id=' + product_id + "&ut=" + ut_param
        if url.startswith('//'):
            url = 'https:' + url
        info = self._download_json(
            url,
            product_id,
            'Downloading video info',
            'Unable to download video info')
        info = info['data']
        current_product = info['current_product']
        series = info.get('series')
        
        title = '%s %s [%s]' % (series.get('name'), current_product.get('number'), current_product['synopsis'])
        
        #stream info
        ccs_product_id = current_product['ccs_product_id']
        streams = self._download_json(
            video_url + ccs_product_id,
            product_id,
            'Downloading streams info',
            'Unable to download streams info')
        streams = streams['data']['stream']
        
        # populate formats
        formats = []
        sizes = streams.get('size')
        for key in streams['url']:
            height = self._search_regex(r'(\d+)', key, 'video_size', None, False)
            formats.append({
                'url': streams['url'][key],
                'protocol': 'm3u8',
                'ext': 'ts',
                'format': 'hls with mpeg2-ts segments',
                'format_id': key,
                'height': int(height) if height is not None else None,
                'filesize_approx': int(sizes.get(key)) if sizes.get(key) is not None else None
            })
        
        #populate subtitles
        subtitles = {}
        list = current_product.get('subtitle')
        if list is not None:
            for sub in list:
                if sub['product_subtitle_language_id'] in self._subtitle_lang:
                    subtitles[self._subtitle_lang[sub['product_subtitle_language_id']]] = [{
                        'url': sub['url'],
                        'ext': 'srt',
                    }]
        
        self._sort_formats(formats)
        
        return {
            'id': product_id,
            'title': title,
            'description': current_product.get('description'),
            'thumbnail': current_product.get('cover_image_url'),
            'duration': streams.get('duration'),
            'formats': formats,
            'subtitles': subtitles
            # TODO more properties (see youtube_dl/extractor/common.py)
        }