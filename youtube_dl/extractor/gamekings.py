import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class GamekingsIE(InfoExtractor):
    _VALID_URL = r'http?://www\.gamekings\.tv/videos/(?P<name>[0-9a-z\-])'
    _TEST = {
        u"url": u"http://www.gamekings.tv/videos/phoenix-wright-ace-attorney-dual-destinies-review/",
        u'file': u'20130811_PhoenixWright.mp4',
        u'md5': u'8d42d15381e2dfa81dee86c7956d35ff',
        u'info_dict': {
            u"title": u"Phoenix Wright: Ace Attorney &#8211; Dual Destinies Review",
            u"description": u"Melle en Steven hebben voor de review een week in de rechtbank doorbracht met Phoenix Wright: Ace Attorney - Dual Destinies.",
        }
    }

    def _real_extract(self, url):

        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)
        gamekings_url = self._og_search_video_url(webpage)

        video = re.search(r'[0-9]+',gamekings_url)
        video_id = video.group(0)

        # Todo: add medium format 
        gamekings_url = gamekings_url.replace(video_id,'large/' + video_id)

        return {'id': video_id,
                'ext': 'mp4',
                'url': gamekings_url,
                'title': self._og_search_title(webpage),
                'description': self._og_search_description(webpage),
                }
