from __future__ import unicode_literals

from .mtv import MTVIE
from ..utils import ExtractorError


class CMTIE(MTVIE):
    IE_NAME = 'cmt.com'
    _VALID_URL = r'https?://(?:www\.)?cmt\.com/(?:videos|shows)/(?:[^/]+/)*(?P<videoid>\d+)'
    _FEED_URL = 'http://www.cmt.com/sitewide/apps/player/embed/rss/'

    _TESTS = [{
        'url': 'http://www.cmt.com/videos/garth-brooks/989124/the-call-featuring-trisha-yearwood.jhtml#artist=30061',
        'md5': 'e6b7ef3c4c45bbfae88061799bbba6c2',
        'info_dict': {
            'id': '989124',
            'ext': 'mp4',
            'title': 'Garth Brooks - "The Call (featuring Trisha Yearwood)"',
            'description': 'Blame It All On My Roots',
        },
        'skip': 'Video not available',
    }, {
        'url': 'http://www.cmt.com/videos/misc/1504699/still-the-king-ep-109-in-3-minutes.jhtml#id=1739908',
        'md5': 'e61a801ca4a183a466c08bd98dccbb1c',
        'info_dict': {
            'id': '1504699',
            'ext': 'mp4',
            'title': 'Still The King Ep. 109 in 3 Minutes',
            'description': 'Relive or catch up with Still The King by watching this recap of season 1, episode 9.',
            'timestamp': 1469421000.0,
            'upload_date': '20160725',
        },
    }, {
        'url': 'http://www.cmt.com/shows/party-down-south/party-down-south-ep-407-gone-girl/1738172/playlist/#id=1738172',
        'only_matching': True,
    }]

    @classmethod
    def _transform_rtmp_url(cls, rtmp_video_url):
        if 'error_not_available.swf' in rtmp_video_url:
            raise ExtractorError(
                '%s said: video is not available' % cls.IE_NAME, expected=True)

        return super(CMTIE, cls)._transform_rtmp_url(rtmp_video_url)

    def _extract_mgid(self, webpage):
        return self._search_regex(
            r'MTVN\.VIDEO\.contentUri\s*=\s*([\'"])(?P<mgid>.+?)\1',
            webpage, 'mgid', group='mgid')
