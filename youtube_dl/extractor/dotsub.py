import re
import json
import time

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
            u'thumbnail': u'http://dotsub.com/media/aed3b8b2-1889-4df5-ae63-ad85f5572f27/p',
            u'upload_date': u'20101213',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        info_url = "https://dotsub.com/api/media/%s/metadata" %(video_id)
        webpage = self._download_webpage(info_url, video_id)
        info = json.loads(webpage)
        date = time.gmtime(info['dateCreated']/1000) # The timestamp is in miliseconds

        return [{
            'id':          video_id,
            'url':         info['mediaURI'],
            'ext':         'flv',
            'title':       info['title'],
            'thumbnail':   info['screenshotURI'],
            'description': info['description'],
            'uploader':    info['user'],
            'view_count':  info['numberOfViews'],
            'upload_date': u'%04i%02i%02i' % (date.tm_year, date.tm_mon, date.tm_mday),
        }]
