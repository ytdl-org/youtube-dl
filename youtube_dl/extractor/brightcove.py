import re
import json

from .common import InfoExtractor

class BrightcoveIE(InfoExtractor):
    _VALID_URL = r'http://.*brightcove\.com/.*\?(?P<query>.*videoPlayer=(?P<id>\d*).*)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query = mobj.group('query')
        video_id = mobj.group('id')

        request_url = 'http://c.brightcove.com/services/viewer/htmlFederated?%s' % query
        webpage = self._download_webpage(request_url, video_id)

        self.report_extraction(video_id)
        info = self._search_regex(r'var experienceJSON = ({.*?});', webpage, 'json')
        info = json.loads(info)['data']
        video_info = info['programmedContent']['videoPlayer']['mediaDTO']
        renditions = video_info['renditions']
        renditions = sorted(renditions, key=lambda r: r['size'])
        best_format = renditions[-1]
        
        return {'id': video_id,
                'title': video_info['displayName'],
                'url': best_format['defaultURL'], 
                'ext': 'mp4',
                'description': video_info.get('shortDescription'),
                'thumbnail': video_info.get('videoStillURL') or video_info.get('thumbnailURL'),
                'uploader': video_info.get('publisherName'),
                }
