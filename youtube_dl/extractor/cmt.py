from __future__ import unicode_literals
from .mtv import MTVIE


class CMTIE(MTVIE):
    IE_NAME = 'cmt.com'
    _VALID_URL = r'https?://www\.cmt\.com/(?:videos|shows)/(?:[^/]+/)*(?P<videoid>\d+)'
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
    }, {
        'url': 'http://www.cmt.com/shows/party-down-south/party-down-south-ep-407-gone-girl/1738172/playlist/#id=1738172',
        'only_matching': True,
    }]
