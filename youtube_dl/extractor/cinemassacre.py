# encoding: utf-8
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)

class CinemassacreIE(InfoExtractor):
    """Information Extractor for Cinemassacre"""
    _VALID_URL = r'(?:http://)?(?:www\.)?(?P<url>cinemassacre\.com/(?P<date_Y>[0-9]{4})/(?P<date_m>[0-9]{2})/(?P<date_d>[0-9]{2})/.+?)(?:[/?].*)?'
    _TESTS = [{
        u'url': u'http://cinemassacre.com/2012/11/10/avgn-the-movie-trailer/',
        u'file': u'19911.mp4',
        u'info_dict': {
            u'upload_date': u'20121110', 
            u'title': u'“Angry Video Game Nerd: The Movie” – Trailer',
            #u'description': u'“Angry Video Game Nerd: The Movie” is...', # Description is too long
        },
        u'params': {
            u'skip_download': True,
        },
    }]

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)

        webpage_url = u'http://' + mobj.group('url')
        webpage = self._download_webpage(webpage_url, None) # Don't know video id yet
        video_date = mobj.group('date_Y') + mobj.group('date_m') + mobj.group('date_d')
        video_id = self._html_search_regex(r'src="http://player\.screenwavemedia\.com/play/embed\.php\?id=(?P<video_id>.+?)"',
            webpage, u'video_id')
        video_title = self._html_search_regex(r'<h1 class="entry-title">(?P<title>.+?)</h1>[^<]*</div>',
            webpage, u'title')
        video_description = self._html_search_regex(r'<div class="entry-content">(?P<description>.+?)</div>',
            webpage, u'description', flags=re.DOTALL, fatal=False)
        
        playerdata_url = u'http://player.screenwavemedia.com/play/player.php?id=' + video_id
        playerdata = self._download_webpage(playerdata_url, video_id)
        base_url = self._html_search_regex(r'\'streamer\': \'(?P<base_url>rtmp://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})/vod\'',
            playerdata, u'base_url')
        base_url += '/Cinemassacre/'
         # The file names in playerdata are wrong for some videos???
        sd_file = 'Cinemassacre-%s_high.mp4' % video_id
        hd_file = 'Cinemassacre-%s.mp4' % video_id
        video_thumbnail = 'http://image.screenwavemedia.com/Cinemassacre/Cinemassacre-%s_thumb_640x360.jpg' % video_id
        
        formats = [{
            'id':          video_id,
            'url':         base_url + hd_file,
            'format':      'hd',
            'ext':         'mp4',
            'title':       video_title,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail':   video_thumbnail,
        },
        {
            'id':          video_id,
            'url':         base_url + sd_file,
            'ext':         'mp4',
            'format':      'sd',
            'title':       video_title,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail':   video_thumbnail,
        }]
        
        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        req_format = self._downloader.params.get('format', 'best')
        self.to_screen(u'Format: %s' % req_format)

        if req_format is None or req_format == 'best':
            return [formats[0]]
        elif req_format == 'worst':
            return [formats[-1]]
        elif req_format in ('-1', 'all'):
            return formats
        else:
            format = self._specific( req_format, formats )
            if format is None:
                raise ExtractorError(u'Requested format not available')
            return [format]

    def _print_formats(self, formats):
        """Print all available formats"""
        print(u'Available formats:')
        print(u'ext\t\tformat')
        print(u'---------------------------------')
        for format in formats:
            print(u'%s\t\t%s'  % (format['ext'], format['format']))

    def _specific(self, req_format, formats):
        for x in formats:
            if x["format"] == req_format:
                return x
        return None
