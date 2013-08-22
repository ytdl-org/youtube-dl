import re

from .common import InfoExtractor


class TrailerAddictIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?traileraddict\.com/(?:trailer|clip)/(?P<movie>.+?)/(?P<trailer_name>.+)'
    _TEST = {
        u'url': u'http://www.traileraddict.com/trailer/prince-avalanche/trailer',
        u'file': u'76184.mp4',
        u'md5': u'57e39dbcf4142ceb8e1f242ff423fd71',
        u'info_dict': {
            u"title": u"Prince Avalanche Trailer",
            u"description": u"Trailer for Prince Avalanche.Two highway road workers spend the summer of 1988 away from their city lives. The isolated landscape becomes a place of misadventure as the men find themselves at odds with each other and the women they left behind."
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('movie') + '/' + mobj.group('trailer_name')
        webpage = self._download_webpage(url, name)

        title = self._search_regex(r'<title>(.+?)</title>',
                webpage, 'video title').replace(' - Trailer Addict','')
        view_count = self._search_regex(r'Views: (.+?)<br />',
                webpage, 'Views Count')
        video_id = self._og_search_property('video', webpage, 'Video id').split('=')[1]

        # Presence of (no)watchplus function indicates HD quality is available
        if re.search(r'function (no)?watchplus()', webpage):
            fvar = "fvarhd"
        else:
            fvar = "fvar"

        info_url = "http://www.traileraddict.com/%s.php?tid=%s" % (fvar, str(video_id))
        info_webpage = self._download_webpage(info_url, video_id , "Downloading the info webpage")

        final_url = self._search_regex(r'&fileurl=(.+)',
                info_webpage, 'Download url').replace('%3F','?')
        thumbnail_url = self._search_regex(r'&image=(.+?)&',
                info_webpage, 'thumbnail url')
        ext = final_url.split('.')[-1].split('?')[0]

        return [{
            'id'          : video_id,
            'url'         : final_url,
            'ext'         : ext,
            'title'       : title,
            'thumbnail'   : thumbnail_url,
            'description' : self._og_search_description(webpage),
            'view_count'  : view_count,
        }]
