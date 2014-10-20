import re
from .common import InfoExtractor

class VidziIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidzi\.tv/(?P<id>\w+)'
    _TEST = {
        'url': 'http://vidzi.tv/h8gbz2rn51vk.html',
        'md5': '4a48137d9fa8a7d848a64485aed68889',
        'info_dict': {
            'id': 'h8gbz2rn51vk',
            'ext': 'mp4',
            'title': 'Watch my4 mp4',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        
        webpage = self._download_webpage('http://vidzi.tv/' + video_id, video_id)
        video_url = self._html_search_regex(r'{\s*file\s*:\s*"([^"]+)"\s*}', webpage, u'vidzi url')
        title = self._html_search_regex(r'<Title>([^<]+)<\/Title>', webpage, u'vidzi title')
        
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
        }
        