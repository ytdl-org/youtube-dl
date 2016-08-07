# coding: utf-8
from __future__ import unicode_literals

import re
import urllib #DEBUG

from .common import InfoExtractor


class Go90IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?go90\.com/profiles/va_(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'https://www.go90.com/profiles/va_07d47f43a7b04eb5b693252f2bd1086b',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '07d47f43a7b04eb5b693252f2bd1086b',
            'ext': 'mp4',
            'title': 't@gged S1:E1 #shotgun',
            'thumbnail': 're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        #title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        
        series_title = self._html_search_regex(r'<h1\b[^>]* data-reactid="90">(.+?)</h1>', webpage, 'series_title')
        season_episode_numbers = self._html_search_regex(r'<!-- react-text: 92 -->(.+?)<!-- /react-text -->', webpage, 'season_episode_numbers')
        episode_title = self._html_search_regex(r'<!-- react-text: 93 -->(.+?)<!-- /react-text -->', webpage, 'episode_title')
        
        title = series_title + " " + season_episode_numbers + " " + episode_title
        #print "[!!!] " + title
        
        #page_data_json = self._search_regex(r'<script\b[^>]*>window\.__data=(.+?);\s*</script>', webpage, 'page_data', flags=re.DOTALL)
        #print self.transform_source(page_data_json)
        #page_data = self._parse_json(page_data_json, video_id, transform_source=self.transform_source)
        
        
        
        video_api = "https://www.go90.com/api/metadata/video/" + video_id
        
        video_api_data = self._download_json(video_api, video_id)  #TODO: overwrite `note=` to output better explanation
        #print "[!!!] " + video_api_data['url']
        
        video_token_url = re.sub(r'^//', 'https://', video_api_data['url'])  #TODO: use utils.sanitize_url()
        #print "[!!!] " + video_token_url
        
        video_token_data = self._download_json(video_token_url, video_id)  #TODO: overwrite `note=` to output better explanation
        #print "[!!!] " + video_token_data['playURL']
        
        m3u8_url = video_token_data['playURL']
        
        #DEBUG
        testfile = urllib.URLopener()
        testfile.retrieve(m3u8_url, video_id + ".m3u8")
        #/DEBUG
        
        formats = []
        formats.extend(self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'formats': formats,
            #'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
    
    #def transform_source(self, json_string):
    #    return re.sub(re.sub(r':function.*?},([\[{"])', ':"",\g<1>', json_string, flags=re.DOTALL)