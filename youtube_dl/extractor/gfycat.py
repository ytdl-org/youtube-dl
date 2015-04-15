from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    mimetype2ext,
    ExtractorError,
)

class GfycatIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?gfycat\.com/(?P<id>[a-zA-Z]+)(\.(?P<ext>gif|webm|mp4))?'
    _TESTS = [{
        'url': 'http://gfycat.com/RequiredUnkemptBuzzard',
        'info_dict': {
            'id': 'RequiredUnkemptBuzzard',
            'title': 'Headshot!',
            'ext': 'mp4'
        },
    }, {
        'url': 'https://giant.gfycat.com/RequiredUnkemptBuzzard.gif',
        'info_dict': {
            'id': 'RequiredUnkemptBuzzard',
            'title': 'Headshot!',
            'ext': 'gif'
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parse = re.search(self._VALID_URL, url)
        userExt = None
        if parse.group('ext'):
            userExt = parse.group('ext')
        
        url = 'http://gfycat.com/'+video_id
        webpage = self._download_webpage(url, video_id)
        
        width = int_or_none(self._search_regex(
            r'gfyWidth[\s=]*?"(?P<width>\d+?)"',
            webpage, 'width', fatal=False))
        height = int_or_none(self._search_regex(
            r'gfyHeight[\s=]*?"(?P<height>\d+?)"',
            webpage, 'height', fatal=False))
        framerate = int_or_none(self._search_regex(
            r'gfyFrameRate[\s=]*?"(?P<framerate>\d+?)"',
            webpage, 'framerate', fatal=False))
        frames = int_or_none(self._search_regex(
            r'gfyNumFrames[\s=]*?"(?P<frames>\d+?)"',
            webpage, 'frames', fatal=False))
        views = int_or_none(self._search_regex(
            r'gfyViews[\s=]*?"(?P<views>\d+?)"',
            webpage, 'views', fatal=False))
        title = self._search_regex(r'class="gfyTitle">(?P<title>[^<]*)',webpage, 'title', fatal=False)

        formats = []
        x=0
        for f in ['image/webm','image/gif','video/mp4']:
            preference = False
            fext = f.partition('/')[2]
            furl = re.search('gfy'+fext.title()+'Url[\s=]*?"(.*?)"', webpage)
            fsize = re.search('gfy'+fext.title()+'Size[\s=]*?"(.*?)"', webpage)
            
            if fext == userExt:
                preference=1000
            
            formats.append({
                'format_id': f.partition('/')[2],
                'url': self._proto_relative_url(furl.group(1)),
                'acodec': 'none',
                'ext':f.partition('/')[2],
                'width': width,
                'vbr':float(fsize.group(1))/(frames/framerate)/1024,
                'preference':x if not preference else preference,
                'fps':framerate,
                'height': height,
                'bytesize': fsize.group(1),
                'id':video_id,
                'http_headers': {
                    'User-Agent': 'youtube-dl (like wget)',
                },
            })
            x+=1
       
        if not len(formats):
            raise ExtractorError('No sources found for gfycat %s. be sure to link to the page with the embed on it.' % video_id, expected=True)
	
        self._sort_formats(formats)

        ret = {
            'id': video_id,
            'formats': formats,
            'title': title,
            'duration':(frames/framerate),
            'view_count':views 
        }
        
        # print json.dumps(ret, sort_keys=True, indent=4, separators=(',', ': '))
        
        
        return ret