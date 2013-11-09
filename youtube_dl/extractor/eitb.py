# encoding: utf-8
import re

from .common import InfoExtractor
from .brightcove import BrightcoveIE
from ..utils import ExtractorError


class EitbIE(InfoExtractor):
    IE_NAME = u'eitb.tv'
    _VALID_URL = r'https?://www\.eitb\.tv/(eu/bideoa|es/video)/[^/]+/(?P<playlist_id>\d+)/(?P<chapter_id>\d+)'

    _TEST = {
        u'add_ie': ['Brightcove'],
        u'url': u'http://www.eitb.tv/es/video/60-minutos-60-minutos-2013-2014/2677100210001/2743577154001/lasa-y-zabala-30-anos/',
        u'md5': u'edf4436247185adee3ea18ce64c47998',
        u'info_dict': {
            u'id': u'2743577154001',
            u'ext': u'mp4',
            u'title': u'60 minutos (Lasa y Zabala, 30 años)',
            # All videos from eitb has this description in the brightcove info
            u'description': u'.',
            u'uploader': u'Euskal Telebista',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        chapter_id = mobj.group('chapter_id')
        webpage = self._download_webpage(url, chapter_id)
        bc_url = BrightcoveIE._extract_brightcove_url(webpage)
        if bc_url is None:
            raise ExtractorError(u'Could not extract the Brightcove url')
        # The BrightcoveExperience object doesn't contain the video id, we set
        # it manually
        bc_url += '&%40videoPlayer={0}'.format(chapter_id)
        return self.url_result(bc_url, BrightcoveIE.ie_key())
