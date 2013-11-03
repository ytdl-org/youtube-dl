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
from ..aes import (
    aes_decrypt_text
)

class YouPornIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>youporn\.com/watch/(?P<videoid>[0-9]+)/(?P<title>[^/]+))'
    _TEST = {
        u'url': u'http://www.youporn.com/watch/505835/sex-ed-is-it-safe-to-masturbate-daily/',
        u'file': u'505835.mp4',
        u'md5': u'71ec5fcfddacf80f495efa8b6a8d9a89',
        u'info_dict': {
            u"upload_date": u"20101221", 
            u"description": u"Love & Sex Answers: http://bit.ly/DanAndJenn -- Is It Unhealthy To Masturbate Daily?", 
            u"uploader": u"Ask Dan And Jennifer", 
            u"title": u"Sex Ed: Is It Safe To Masturbate Daily?",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)
        age_limit = self._rta_search(webpage)

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

        # Get all of the links from the page
        DOWNLOAD_LIST_RE = r'(?s)<ul class="downloadList">(?P<download_list>.*?)</ul>'
        download_list_html = self._search_regex(DOWNLOAD_LIST_RE,
            webpage, u'download list').strip()
        LINK_RE = r'<a href="([^"]+)">'
        links = re.findall(LINK_RE, download_list_html)

        # Get all encrypted links
        encrypted_links = re.findall(r'var encryptedQuality[0-9]{3}URL = \'([a-zA-Z0-9+/]+={0,2})\';', webpage)
        for encrypted_link in encrypted_links:
            link = aes_decrypt_text(encrypted_link, video_title, 32).decode('utf-8')
            links.append(link)
        
        if not links:
            raise ExtractorError(u'ERROR: no known formats available for video')

        formats = []
        for link in links:

            # A link looks like this:
            # http://cdn1.download.youporn.phncdn.com/201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4?nvb=20121113051249&nva=20121114051249&ir=1200&sr=1200&hash=014b882080310e95fb6a0
            # A path looks like this:
            # /201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4
            video_url = unescapeHTML(link)
            path = compat_urllib_parse_urlparse(video_url).path
            extension = os.path.splitext(path)[1][1:]
            format = path.split('/')[4].split('_')[:2]

            # size = format[0]
            # bitrate = format[1]
            format = "-".join(format)
            # title = u'%s-%s-%s' % (video_title, size, bitrate)

            formats.append({
                'url': video_url,
                'ext': extension,
                'format': format,
                'format_id': format,
            })

        # Sort and remove doubles
        formats.sort(key=lambda format: list(map(lambda s: s.zfill(6), format['format'].split('-'))))
        for i in range(len(formats)-1,0,-1):
            if formats[i]['format_id'] == formats[i-1]['format_id']:
                del formats[i]
        
        return {
            'id': video_id,
            'uploader': video_uploader,
            'upload_date': upload_date,
            'title': video_title,
            'thumbnail': thumbnail,
            'description': video_description,
            'age_limit': age_limit,
            'formats': formats,
        }
