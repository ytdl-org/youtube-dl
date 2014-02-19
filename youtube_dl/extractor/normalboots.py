import re

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    unified_strdate,
)

class NormalbootsIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?normalboots\.com/video/(?P<videoid>[0-9a-z-]*)/?$'
    _TEST = {
        u'url': u'http://normalboots.com/video/home-alone-games-jontron/',
        u'file': u'home-alone-games-jontron.mp4',
        u'md5': u'8bf6de238915dd501105b44ef5f1e0f6',
        u'info_dict': {
            u'title': u'Home Alone Games - JonTron - NormalBoots',
            u'description': u'Jon is late for Christmas. Typical. Thanks to: Paul Ritchey for Co-Writing/Filming: http://www.youtube.com/user/ContinueShow Michael Azzi for Christmas Intro Animation: http://michafrar.tumblr.com/ Jerrod Waters for Christmas Intro Music: http://www.youtube.com/user/xXJerryTerryXx Casey Ormond for \u2018Tense Battle Theme\u2019:\xa0http://www.youtube.com/Kiamet/',
            u'uploader': u'JonTron',
            u'upload_date': u'20140125',
        }
    }
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('videoid')
        
        info = {
            'id': video_id,
            'uploader': None,
            'upload_date': None,
        }
        
        if url[:4] != 'http':
            url = 'http://' + url
        
        webpage = self._download_webpage(url, video_id)
        video_title = self._og_search_title(webpage)
        video_description = self._og_search_description(webpage)
        video_thumbnail = self._og_search_thumbnail(webpage)
        video_uploader = self._html_search_regex(r'Posted\sby\s<a\shref="[A-Za-z0-9/]*">(?P<uploader>[A-Za-z]*)\s</a>',
            webpage, 'uploader')
        raw_upload_date = self._html_search_regex('<span style="text-transform:uppercase; font-size:inherit;">[A-Za-z]+, (?P<date>.*)</span>', 
            webpage, 'date')
        video_upload_date = unified_strdate(raw_upload_date)
        video_upload_date = unified_strdate(raw_upload_date)
            
        player_url = self._html_search_regex(r'<iframe\swidth="[0-9]+"\sheight="[0-9]+"\ssrc="(?P<url>[\S]+)"', webpage, 'url')
        player_page = self._download_webpage(player_url, video_id)
        video_url = u'http://player.screenwavemedia.com/' + self._html_search_regex(r"'file':\s'(?P<file>[0-9A-Za-z-_\.]+)'", player_page, 'file')
        
        info['url'] = video_url
        info['title'] = video_title
        info['description'] = video_description
        info['thumbnail'] = video_thumbnail
        info['uploader'] = video_uploader
        info['upload_date'] = video_upload_date
        
        return info
