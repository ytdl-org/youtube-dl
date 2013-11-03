import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    RegexNotFoundError,
)


class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<url_title>.*)'
    _TEST = {
        u'url': u'http://teamcoco.com/video/louis-ck-interview-george-w-bush',
        u'file': u'19705.mp4',
        u'md5': u'cde9ba0fa3506f5f017ce11ead928f9a',
        u'info_dict': {
            u"description": u"Louis C.K. got starstruck by George W. Bush, so what? Part one.", 
            u"title": u"Louis C.K. Interview Pt. 1 11/3/11"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        url_title = mobj.group('url_title')
        webpage = self._download_webpage(url, url_title)

        video_id = self._html_search_regex(r'<article class="video" data-id="(\d+?)"',
            webpage, u'video id')

        self.report_extraction(video_id)

        data_url = 'http://teamcoco.com/cvp/2.0/%s.xml' % video_id
        data = self._download_webpage(data_url, video_id, 'Downloading data webpage')


        qualities = [ '1080p', '720p', '1000k', '480p', '500k' ]
        best_quality_idx = len(qualities)+1  # First regex match may not be optimal
        for idx, quality in enumerate(qualities):
            regex = r'<file [^>]*type="(?:high|standard)".*?>(.*%s.*)</file>' % quality
            try:
                url = self._html_search_regex(regex, data, u'video URL')
                if idx < best_quality_idx:
                    video_url = url
                    best_quality_idx = idx
            except RegexNotFoundError:
                # Just catch fatal exc. Don't want the fatal=False warning
                continue
        if not video_url:
            raise RegexNotFoundError(u'Unable to extract video URL')

        return [{
            'id':          video_id,
            'url':         video_url,
            'ext':         'mp4',
            'title':       self._og_search_title(webpage),
            'thumbnail':   self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
        }]
