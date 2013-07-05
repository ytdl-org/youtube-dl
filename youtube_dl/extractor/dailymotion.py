import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,

    ExtractorError,
)

class DailymotionIE(InfoExtractor):
    """Information Extractor for Dailymotion"""

    _VALID_URL = r'(?i)(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/video/([^/]+)'
    IE_NAME = u'dailymotion'
    _TEST = {
        u'url': u'http://www.dailymotion.com/video/x33vw9_tutoriel-de-youtubeur-dl-des-video_tech',
        u'file': u'x33vw9.mp4',
        u'md5': u'392c4b85a60a90dc4792da41ce3144eb',
        u'info_dict': {
            u"uploader": u"Alex and Van .", 
            u"title": u"Tutoriel de Youtubeur\"DL DES VIDEO DE YOUTUBE\""
        }
    }

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group(1).split('_')[0].split('?')[0]

        video_extension = 'mp4'

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url)
        request.add_header('Cookie', 'family_filter=off')
        webpage = self._download_webpage(request, video_id)

        # Extract URL, uploader and title from webpage
        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'<meta property="og:title" content="(.*?)" />',
                                              webpage, 'title')

        video_uploader = self._search_regex([r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a>',
                                             # Looking for official user
                                             r'<(?:span|a) .*?rel="author".*?>([^<]+?)</'],
                                            webpage, 'video uploader')

        video_upload_date = None
        mobj = re.search(r'<div class="[^"]*uploaded_cont[^"]*" title="[^"]*">([0-9]{2})-([0-9]{2})-([0-9]{4})</div>', webpage)
        if mobj is not None:
            video_upload_date = mobj.group(3) + mobj.group(2) + mobj.group(1)

        embed_url = 'http://www.dailymotion.com/embed/video/%s' % video_id
        embed_page = self._download_webpage(embed_url, video_id,
                                            u'Downloading embed page')
        info = self._search_regex(r'var info = ({.*?}),', embed_page, 'video info')
        info = json.loads(info)

        # TODO: support choosing qualities

        for key in ['stream_h264_hd1080_url','stream_h264_hd_url',
                    'stream_h264_hq_url','stream_h264_url',
                    'stream_h264_ld_url']:
            if info.get(key):#key in info and info[key]:
                max_quality = key
                self.to_screen(u'Using %s' % key)
                break
        else:
            raise ExtractorError(u'Unable to extract video URL')
        video_url = info[max_quality]

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'upload_date':  video_upload_date,
            'title':    video_title,
            'ext':      video_extension,
            'thumbnail': info['thumbnail_url']
        }]
