import re
import json
from .common import InfoExtractor


class DotsubIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?dotsub\.com/view/([^/]+)'
    _TEST = {
        u'url': u'http://dotsub.com/view/aed3b8b2-1889-4df5-ae63-ad85f5572f27',
        u'file': u'aed3b8b2-1889-4df5-ae63-ad85f5572f27.flv',
        u'md5': u'0914d4d69605090f623b7ac329fea66e',
        u'info_dict': {
            u"title": u"Pyramids of Waste (2010), AKA The Lightbulb Conspiracy - Planned obsolescence documentary",
            u"uploader": u"4v4l0n42",
            u'description': u'Pyramids of Waste (2010) also known as "The lightbulb conspiracy" is a documentary about how our economic system based on consumerism  and planned obsolescence is breaking our planet down.\r\n\r\nSolutions to this can be found at:\r\nhttp://robotswillstealyourjob.com\r\nhttp://www.federicopistono.org\r\n\r\nhttp://opensourceecology.org\r\nhttp://thezeitgeistmovement.com',
            u'thumbnail': u'http://dotsub.com/media/aed3b8b2-1889-4df5-ae63-ad85f5572f27/p'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        info_url = "https://dotsub.com/api/media/%s/metadata" %(video_id)
        webpage = self._download_webpage(info_url, video_id)
        info = json.loads(webpage)
        video_url = info['mediaURI']
        uploader = info['user']
        description = info['description']
        view_count = info['numberOfViews']
        title = info['title']
        thumbnail_url = info['screenshotURI']
        ext = 'flv'
        return [{
            'id':          video_id,
            'url':         video_url,
            'ext':         ext,
            'title':       title,
            'thumbnail':   thumbnail_url,
            'description': description,
            'uploader':    uploader,
            'view_count':  view_count,
        }]
