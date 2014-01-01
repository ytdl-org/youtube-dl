from .mtv import MTVIE

class CMTIE(MTVIE):
    IE_NAME = u'cmt.com'
    _VALID_URL = r'https?://www\.cmt\.com/videos/.+?/(?P<videoid>[^/]+)\.jhtml'
    _FEED_URL = 'http://www.cmt.com/sitewide/apps/player/embed/rss/'

    _TESTS = [
        {
            u'url': u'http://www.cmt.com/videos/garth-brooks/989124/the-call-featuring-trisha-yearwood.jhtml#artist=30061',
            u'md5': u'e6b7ef3c4c45bbfae88061799bbba6c2',
            u'info_dict': {
                u'id': u'989124',
                u'ext': u'mp4',
                u'title': u'Garth Brooks - "The Call (featuring Trisha Yearwood)"',
                u'description': u'Blame It All On My Roots',
            },
        },
    ]
