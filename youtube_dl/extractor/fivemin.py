from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_parse_qs,
    compat_urllib_parse_urlparse,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    parse_duration,
    replace_extension,
)


class FiveMinIE(InfoExtractor):
    IE_NAME = '5min'
    _VALID_URL = r'''(?x)
        (?:https?://[^/]*?5min\.com/Scripts/PlayerSeed\.js\?(?:.*?&)?playList=|
            https?://(?:(?:massively|www)\.)?joystiq\.com/video/|
            5min:)
        (?P<id>\d+)
        '''

    _TESTS = [
        {
            # From http://www.engadget.com/2013/11/15/ipad-mini-retina-display-review/
            'url': 'http://pshared.5min.com/Scripts/PlayerSeed.js?sid=281&width=560&height=345&playList=518013791',
            'md5': '4f7b0b79bf1a470e5004f7112385941d',
            'info_dict': {
                'id': '518013791',
                'ext': 'mp4',
                'title': 'iPad Mini with Retina Display Review',
                'duration': 177,
            },
        },
        {
            # From http://on.aol.com/video/how-to-make-a-next-level-fruit-salad-518086247
            'url': '5min:518086247',
            'md5': 'e539a9dd682c288ef5a498898009f69e',
            'info_dict': {
                'id': '518086247',
                'ext': 'mp4',
                'title': 'How to Make a Next-Level Fruit Salad',
                'duration': 184,
            },
        },
    ]
    _ERRORS = {
        'ErrorVideoNotExist': 'We\'re sorry, but the video you are trying to watch does not exist.',
        'ErrorVideoNoLongerAvailable': 'We\'re sorry, but the video you are trying to watch is no longer available.',
        'ErrorVideoRejected': 'We\'re sorry, but the video you are trying to watch has been removed.',
        'ErrorVideoUserNotGeo': 'We\'re sorry, but the video you are trying to watch cannot be viewed from your current location.',
        'ErrorVideoLibraryRestriction': 'We\'re sorry, but the video you are trying to watch is currently unavailable for viewing at this domain.',
        'ErrorExposurePermission': 'We\'re sorry, but the video you are trying to watch is currently unavailable for viewing at this domain.',
    }
    _QUALITIES = {
        1: {
            'width': 640,
            'height': 360,
        },
        2: {
            'width': 854,
            'height': 480,
        },
        4: {
            'width': 1280,
            'height': 720,
        },
        8: {
            'width': 1920,
            'height': 1080,
        },
        16: {
            'width': 640,
            'height': 360,
        },
        32: {
            'width': 854,
            'height': 480,
        },
        64: {
            'width': 1280,
            'height': 720,
        },
        128: {
            'width': 640,
            'height': 360,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        embed_url = 'https://embed.5min.com/playerseed/?playList=%s' % video_id
        embed_page = self._download_webpage(embed_url, video_id,
                                            'Downloading embed page')
        sid = self._search_regex(r'sid=(\d+)', embed_page, 'sid')
        query = compat_urllib_parse.urlencode({
            'func': 'GetResults',
            'playlist': video_id,
            'sid': sid,
            'isPlayerSeed': 'true',
            'url': embed_url,
        })
        response = self._download_json(
            'https://syn.5min.com/handlers/SenseHandler.ashx?' + query,
            video_id)
        if not response['success']:
            raise ExtractorError(
                '%s said: %s' % (
                    self.IE_NAME,
                    self._ERRORS.get(response['errorMessage'], response['errorMessage'])),
                expected=True)
        info = response['binding'][0]

        formats = []
        parsed_video_url = compat_urllib_parse_urlparse(compat_parse_qs(
            compat_urllib_parse_urlparse(info['EmbededURL']).query)['videoUrl'][0])
        for rendition in info['Renditions']:
            if rendition['RenditionType'] == 'm3u8':
                formats.extend(self._extract_m3u8_formats(rendition['Url'], video_id, m3u8_id='hls'))
            elif rendition['RenditionType'] == 'aac':
                continue
            else:
                rendition_url = compat_urlparse.urlunparse(parsed_video_url._replace(path=replace_extension(parsed_video_url.path.replace('//', '/%s/' % rendition['ID']), rendition['RenditionType'])))
                quality = self._QUALITIES.get(rendition['ID'], {})
                formats.append({
                    'format_id': '%s-%d' % (rendition['RenditionType'], rendition['ID']),
                    'url': rendition_url,
                    'width': quality.get('width'),
                    'height': quality.get('height'),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['Title'],
            'thumbnail': info.get('ThumbURL'),
            'duration': parse_duration(info.get('Duration')),
            'formats': formats,
        }
