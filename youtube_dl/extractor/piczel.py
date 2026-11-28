 
# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,    
    compat_urllib_request
)
from ..utils import (    
    ExtractorError    
)


class PiczelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www.)?piczel\.tv/watch/(?P<id>[a-zA-Z0-9]+)'    
    _TESTS = [{
        'url': 'https://piczel.tv/watch/Schwoo',        
        'info_dict': {
            'id': 'Schwoo',
            'uploader_id': '43564',
            'ext': 'mp4',
            'title': 'Schwoo - Piczel.tv',
            'description': 'Horni Vibin\'',
            'is_live': bool,            
        },
        'skip': 'Stream is offline',
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://piczel.tv/watch/GeneralButchTv',
        'info_dict': {
            'id': 'GeneralButchTv',
            'uploader_id': '39042',
            'ext': 'mp4',
            'title': 'GeneralButchTv - Piczel.tv',
            'description': 'GENERAL BUTCH',
            'is_live': bool,            
        },
        'skip': 'Stream is offline',
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://piczel.tv/watch/Nifffi',        
        'info_dict': {
            'id': 'Nifffi',
            'uploader_id': '60996',
            'ext': 'mp4',
            'title': 'Nifffi - Piczel.tv',
            'description': u'(ﾉ´ヮ`)ﾉ*: ･ﾟ',
            'is_live': bool, 
        },
        'skip': 'Stream is offline',
        'params': {
            'skip_download': True,
        },
    }]
    
    
    def _real_extract(self, url):
        video_id = self._match_id(url)        
        
        webpage = self._download_webpage(url, video_id)               
        title = self._html_search_regex(r'<title data-react-helmet=\"true\">(.+?)<\/title>', webpage, 'title')
        
        api_data = self._download_json('https://piczel.tv/api/streams/%s' % video_id, video_id)
        uploader_id = api_data['data'][0]['id']
        is_live = api_data['data'][0]['live']
        
        if not is_live:
            # There is a bug where the api says user is not streaming when they are.
            # So checing user's index.m3u8 file for 404 errors
            try:                
                req = compat_urllib_request.urlopen('https://piczel.tv/hls/%i/index.m3u8' % uploader_id)
                print(req.code)
            except:               
                raise ExtractorError('Stream is offline', expected=True)
            
                
        formats = []        
        formats.append({
            'url': 'https://piczel.tv/hls/%i/index.m3u8' % uploader_id,
            'ext': 'mp4',            
        })
        
        return {
            'id': video_id,
            'uploader_id': str(uploader_id),
            'title': title,
            'description': self._og_search_description(webpage),            
            'is_live': is_live,
            'formats': formats,            
        }
