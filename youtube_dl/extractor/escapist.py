import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    compat_urllib_parse,

    ExtractorError,
)


class EscapistIE(InfoExtractor):
    _VALID_URL = r'^https?://?(www\.)?escapistmagazine\.com/videos/view/(?P<showname>[^/]+)/(?P<episode>[^/?]+)[/?]?.*$'
    _TEST = {
        u'url': u'http://www.escapistmagazine.com/videos/view/the-escapist-presents/6618-Breaking-Down-Baldurs-Gate',
        u'file': u'6618-Breaking-Down-Baldurs-Gate.mp4',
        u'md5': u'ab3a706c681efca53f0a35f1415cf0d1',
        u'info_dict': {
            u"description": u"Baldur's Gate: Original, Modded or Enhanced Edition? I'll break down what you can expect from the new Baldur's Gate: Enhanced Edition.", 
            u"uploader": u"the-escapist-presents", 
            u"title": u"Breaking Down Baldur's Gate"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        showName = mobj.group('showname')
        videoId = mobj.group('episode')

        self.report_extraction(videoId)
        webpage = self._download_webpage(url, videoId)

        videoDesc = self._html_search_regex(
            r'<meta name="description" content="([^"]*)"',
            webpage, u'description', fatal=False)

        playerUrl = self._og_search_video_url(webpage, name=u'player URL')

        title = self._html_search_regex(
            r'<meta name="title" content="([^"]*)"',
            webpage, u'title').split(' : ')[-1]

        configUrl = self._search_regex('config=(.*)$', playerUrl, u'config URL')
        configUrl = compat_urllib_parse.unquote(configUrl)

        formats = []

        def _add_format(name, cfgurl):
            configJSON = self._download_webpage(
                cfgurl, videoId,
                u'Downloading ' + name + ' configuration',
                u'Unable to download ' + name + ' configuration')

            # Technically, it's JavaScript, not JSON
            configJSON = configJSON.replace("'", '"')

            try:
                config = json.loads(configJSON)
            except (ValueError,) as err:
                raise ExtractorError(u'Invalid JSON in configuration file: ' + compat_str(err))
            playlist = config['playlist']
            formats.append({
                'url': playlist[1]['url'],
                'format_id': name,
            })

        _add_format(u'normal', configUrl)
        hq_url = (configUrl +
                  ('&hq=1' if '?' in configUrl else configUrl + '?hq=1'))
        try:
            _add_format(u'hq', hq_url)
        except ExtractorError:
            pass  # That's fine, we'll just use normal quality

        return {
            'id': videoId,
            'formats': formats,
            'uploader': showName,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': videoDesc,
            'player_url': playerUrl,
        }
