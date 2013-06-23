import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_parse,

    ExtractorError,
)


class EscapistIE(InfoExtractor):
    _VALID_URL = r'^(https?://)?(www\.)?escapistmagazine\.com/videos/view/(?P<showname>[^/]+)/(?P<episode>[^/?]+)[/?]?.*$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        showName = mobj.group('showname')
        videoId = mobj.group('episode')

        self.report_extraction(videoId)
        webpage = self._download_webpage(url, videoId)

        videoDesc = self._html_search_regex('<meta name="description" content="([^"]*)"',
            webpage, u'description', fatal=False)

        imgUrl = self._html_search_regex('<meta property="og:image" content="([^"]*)"',
            webpage, u'thumbnail', fatal=False)

        playerUrl = self._html_search_regex('<meta property="og:video" content="([^"]*)"',
            webpage, u'player url')

        title = self._html_search_regex('<meta name="title" content="([^"]*)"',
            webpage, u'player url').split(' : ')[-1]

        configUrl = self._search_regex('config=(.*)$', playerUrl, u'config url')
        configUrl = compat_urllib_parse.unquote(configUrl)

        configJSON = self._download_webpage(configUrl, videoId,
                                            u'Downloading configuration',
                                            u'unable to download configuration')

        # Technically, it's JavaScript, not JSON
        configJSON = configJSON.replace("'", '"')

        try:
            config = json.loads(configJSON)
        except (ValueError,) as err:
            raise ExtractorError(u'Invalid JSON in configuration file: ' + compat_str(err))

        playlist = config['playlist']
        videoUrl = playlist[1]['url']

        info = {
            'id': videoId,
            'url': videoUrl,
            'uploader': showName,
            'upload_date': None,
            'title': title,
            'ext': 'mp4',
            'thumbnail': imgUrl,
            'description': videoDesc,
            'player_url': playerUrl,
        }

        return [info]
