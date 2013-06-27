import datetime
import json
import re

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
)

class PhotobucketIE(InfoExtractor):
    """Information extractor for photobucket.com."""

    # TODO: the original _VALID_URL was:
    # r'(?:http://)?(?:[a-z0-9]+\.)?photobucket\.com/.*[\?\&]current=(.*\.flv)'
    # Check if it's necessary to keep the old extracion process
    _VALID_URL = r'(?:http://)?(?:[a-z0-9]+\.)?photobucket\.com/.*(([\?\&]current=)|_)(?P<id>.*)\.(?P<ext>(flv)|(mp4))'
    IE_NAME = u'photobucket'
    _TEST = {
        u'url': u'http://media.photobucket.com/user/rachaneronas/media/TiredofLinkBuildingTryBacklinkMyDomaincom_zpsc0c3b9fa.mp4.html?filters[term]=search&filters[primary]=videos&filters[secondary]=images&sort=1&o=0',
        u'file': u'zpsc0c3b9fa.mp4',
        u'md5': u'7dabfb92b0a31f6c16cebc0f8e60ff99',
        u'info_dict': {
            u"upload_date": u"20130504", 
            u"uploader": u"rachaneronas", 
            u"title": u"Tired of Link Building? Try BacklinkMyDomain.com!"
        }
    }

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('id')

        video_extension = mobj.group('ext')

        # Retrieve video webpage to extract further information
        webpage = self._download_webpage(url, video_id)

        # Extract URL, uploader, and title from webpage
        self.report_extraction(video_id)
        # We try first by looking the javascript code:
        mobj = re.search(r'Pb\.Data\.Shared\.put\(Pb\.Data\.Shared\.MEDIA, (?P<json>.*?)\);', webpage)
        if mobj is not None:
            info = json.loads(mobj.group('json'))
            return [{
                'id':       video_id,
                'url':      info[u'downloadUrl'],
                'uploader': info[u'username'],
                'upload_date':  datetime.date.fromtimestamp(info[u'creationDate']).strftime('%Y%m%d'),
                'title':    info[u'title'],
                'ext':      video_extension,
                'thumbnail': info[u'thumbUrl'],
            }]

        # We try looking in other parts of the webpage
        video_url = self._search_regex(r'<link rel="video_src" href=".*\?file=([^"]+)" />',
            webpage, u'video URL')

        mobj = re.search(r'<title>(.*) video by (.*) - Photobucket</title>', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract title')
        video_title = mobj.group(1).decode('utf-8')
        video_uploader = mobj.group(2).decode('utf-8')

        return [{
            'id':       video_id.decode('utf-8'),
            'url':      video_url.decode('utf-8'),
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension.decode('utf-8'),
        }]
