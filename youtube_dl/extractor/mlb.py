from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MlbIE(InfoExtractor):
    _VALID_URL = r'http?://m\.mlb\.com/video/topic/[0-9]+/v(?P<id>n?\d+)/.*$'
    _TEST = {
        'url': 'http://m.mlb.com/video/topic/81536970/v34496663/mianym-stanton-practices-for-the-home-run-derby',
        'md5': u'd9c022c10d21f849f49c05ae12a8a7e9',
        'info_dict': {
            'id': '34496663',
            'ext': 'mp4',
            'format': 'mp4',
            'description': "7/11/14: Giancarlo Stanton practices for the Home Run Derby prior to the game against the Mets",
            'title': "Stanton prepares for Derby",
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, default=video_id)
        description = self._html_search_regex(r'<meta name="description" (?:content|value)="(.*?)"/>', webpage, 'description', fatal=False)
        thumbnail = self._html_search_regex(r'<meta itemprop="image" (?:content|value)="(.*?)" />', webpage, 'image', fatal=False)
        
        # use the thumbnail URL to find the folder that contains the videos
        _image_url = r'http://mediadownloads.mlb.com/mlbam/(?P<_date>n?.+)/images/.*$'
        bobj = re.match(_image_url, thumbnail)
        datestr = bobj.group('_date')
        base_url = 'http://mediadownloads.mlb.com/mlbam/' + datestr
        filespage = self._download_webpage(base_url, video_id)
        
        # Try 1800K, 1500K, 1200K, 600K, then 300K videos
        video = self._html_search_regex(r'<li><a href="(.*?)_'+video_id+'_1800K.mp4"', filespage, '1800K', fatal=False)
        if video is not None:
            video_url = base_url+'/'+video+'_'+video_id+'_1800K.mp4'
        else:
            video = self._html_search_regex(r'<li><a href="(.*?)_'+video_id+'_1500K.mp4"', filespage, '1500K', fatal=False)
            if video is not None:
                video_url = base_url+'/'+video+'_'+video_id+'_1500K.mp4'
            else:
                video = self._html_search_regex(r'<li><a href="(.*?)_'+video_id+'_600K.mp4"', filespage, '600K', fatal=False)
                if video is not None:
                    video_url = base_url+'/'+video+'_'+video_id+'_600K.mp4'
                else:
                    video = self._html_search_regex(r'<li><a href="(.*?)_'+video_id+'_300K.mp4"', filespage, 'MLB', fatal=False)
                    if video is not None:
                        video_url = base_url+'/'+video+'_'+video_id+'_300K.mp4'
                    else:
                        # nothing valuable to return
                        return None
                
        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': 'mp4',
            'format': 'mp4',
            'description': description,
            'thumbnail': thumbnail,
        }
