import re

from .common import InfoExtractor

class AddAnimeIE(InfoExtractor):

    _VALID_URL = r'^(?:http?://)?(?:\w+\.)?add-anime\.net/watch_video.php\?(?:.*?)v=(?P<video_id>[\w_]+)(?:.*)'
    IE_NAME = u'AddAnime'
    _TEST = {
        u'url': u'http://www.add-anime.net/watch_video.php?v=24MR3YO5SAS9',
        u'file': u'137499050692ced.flv',
        u'md5': u'0813c2430bea7a46bf13acf3406992f4',
        u'info_dict': {
            u"description": u"One Piece 606", 
            u"title": u"One Piece 606"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)


	def find_between( webpage, first, last ):
  	    try:
        	start = webpage.index( first ) + len( first )
        	end = webpage.index( last, start )
        	return webpage[start:end]
    	    except ValueError:
       		return ""

	video_url = find_between( webpage, "var normal_video_file = '", "';" )

        video_title = self._og_search_title(webpage)

        video_description = self._og_search_description(webpage)

        info = {
            'id':  video_id,
            'url': video_url,
            'ext': 'flv',
            'title': video_title,
            'description': video_description
        }

        return [info]
