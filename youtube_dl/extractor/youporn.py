import json
import os
import re
import sys

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urllib_request,

    ExtractorError,
    unescapeHTML,
    unified_strdate,
)


class YouPornIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?youporn\.com/watch/(?P<videoid>[0-9]+)/(?P<title>[^/]+)'
    _TEST = {
        u'url': u'http://www.youporn.com/watch/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        u'file': u'505835.mp4',
        u'md5': u'c37ddbaaa39058c76a7e86c6813423c1',
        u'info_dict': {
            u"upload_date": u"20101221", 
            u"description": u"Love & Sex Answers: http://bit.ly/DanAndJenn -- Is It Unhealthy To Masturbate Daily?", 
            u"uploader": u"Ask Dan And Jennifer", 
            u"title": u"Sex Ed: Is It Safe To Masturbate Daily?"
        }
    }

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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        # Get JSON parameters
        json_params = self._search_regex(r'var currentVideo = new Video\((.*)\);', webpage, u'JSON parameters')
        try:
            params = json.loads(json_params)
        except:
            raise ExtractorError(u'Invalid JSON')

        self.report_extraction(video_id)
        try:
            video_title = params['title']
            upload_date = unified_strdate(params['release_date_f'])
            video_description = params['description']
            video_uploader = params['submitted_by']
            thumbnail = params['thumbnails'][0]['image']
        except KeyError:
            raise ExtractorError('Missing JSON parameter: ' + sys.exc_info()[1])

        # Get all of the formats available
        DOWNLOAD_LIST_RE = r'(?s)<ul class="downloadList">(?P<download_list>.*?)</ul>'
        download_list_html = self._search_regex(DOWNLOAD_LIST_RE,
            webpage, u'download list').strip()

        # Get all of the links from the page
        LINK_RE = r'(?s)<a href="(?P<url>[^"]+)">'
        links = re.findall(LINK_RE, download_list_html)
        if(len(links) == 0):
            raise ExtractorError(u'ERROR: no known formats available for video')

        self.to_screen(u'Links found: %d' % len(links))

        formats = []
        for link in links:

            # A link looks like this:
            # http://cdn1.download.youporn.phncdn.com/201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4?nvb=20121113051249&nva=20121114051249&ir=1200&sr=1200&hash=014b882080310e95fb6a0
            # A path looks like this:
            # /201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4
            video_url = unescapeHTML( link )
            path = compat_urllib_parse_urlparse( video_url ).path
            extension = os.path.splitext( path )[1][1:]
            format = path.split('/')[4].split('_')[:2]
            # size = format[0]
            # bitrate = format[1]
            format = "-".join( format )
            # title = u'%s-%s-%s' % (video_title, size, bitrate)

            formats.append({
                'id': video_id,
                'url': video_url,
                'uploader': video_uploader,
                'upload_date': upload_date,
                'title': video_title,
                'ext': extension,
                'format': format,
                'thumbnail': thumbnail,
                'description': video_description
            })

        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        req_format = self._downloader.params.get('format', None)
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
