# coding: utf-8

from __future__ import unicode_literals

import datetime

from .common import InfoExtractor

class GfycatIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gfycat\.com/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://gfycat.com/DeadlyDecisiveGermanpinscher',
        'info_dict': {
            'id':          'DeadlyDecisiveGermanpinscher',
            'title':       'Ghost in the Shell',
            'ext':         'mp4',
            'upload_date': '20140913'
        }
    },{
        'url': 'http://gfycat.com/pleasinghilariouskusimanse',
        'info_dict': {
            'id':          'pleasinghilariouskusimanse',
            'title':       'PleasingHilariousKusimanse',
            'ext':         'webm',
            'upload_date': '20150412'
        }
    },{
        'url': 'http://gfycat.com/requiredunkemptbuzzard',
        'info_dict': {
            'id':          'requiredunkemptbuzzard',
            'title':       'Headshot!',
            'ext':         'gif',
            'upload_date': '20150130'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json     = self._download_json("http://gfycat.com/cajax/get/" + video_id, video_id, 'Downloading video info')['gfyItem']
        
        # Title
        # Use user title first, else fallback to url formated name
        if json['title']:
            video_title = json['title']
        else:
            video_title = json['gfyName']
        
        # Formats
        # Pref: mp4, webm, gif
        formats = [{
            'format_id':  'mp4',
            'ext':        'mp4',
            'url':        json['mp4Url'],
            'width':      json['width'],
            'height':     json['height'],
            'fps':        json['frameRate'],
            'filesize':   json['mp4Size'],
            'preference': '-1'
        }, {
            'format_id': 'webm',
            'ext':       'webm',
            'url':        json['webmUrl'],
            'width':      json['width'],
            'height':     json['height'],
            'fps':        json['frameRate'],
            'filesize':   json['webmSize'],
            'preference': 0
        }, {
            'format_id':  'gif',
            'ext':        'gif',
            'url':        json['gifUrl'],
            'width':      json['width'],
            'height':     json['height'],
            'fps':        json['frameRate'],
            'filesize':   json['gifSize'],
            'preference': 1
        }]
        
        self._sort_formats(formats)
        
        # Date
        date = datetime.datetime.fromtimestamp(
            int(json['createDate'])
        ).strftime('%Y%m%d')
        
        # Length
        duration = json['numFrames'] / json['frameRate']
        
        # Age limit
        # 1 = nsfw / 0 = sfw
        if json['nsfw'] == 1:
            age_limit = 18
        else:
            age_limit = 0
        
        return {
            'id':          video_id,
            'title':       video_title,
            'formats':     formats,
            'creator':     json['userName'],
            'description': json['description'],
            'upload_date': date,
            'categories':  json['tags'],
            'age_limit':   age_limit,
            'duration':    duration,
            'view_count':  json['views']
        }
