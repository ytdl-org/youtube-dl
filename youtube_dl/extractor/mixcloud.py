from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
)
from ..utils import (
    ExtractorError,
    HEADRequest,
    str_to_int,
    parse_iso8601,
)

class MixcloudIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([^/]+)/([^/]+)'
    IE_NAME = 'mixcloud'
    STREAM_PART_RE = r'\bstream(\d+)\b'
    SERVER_NUMBERS_BOUNDARIES = (1, 30)

    _TESTS = [{
        'url': 'http://www.mixcloud.com/dholbach/cryptkeeper/',
        'info_dict': {
            'id': 'dholbach-cryptkeeper',
            'ext': 'mp3',
            'title': 'Cryptkeeper',
            'description': 'After quite a long silence from myself, finally another Drum\'n\'Bass mix with my favourite current dance floor bangers.',
            'uploader': 'Daniel Holbach',
            'uploader_id': 'dholbach',
            'upload_date': '20111115',
            'timestamp': 1321359578,
            'thumbnail': 're:https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
        },
    }, {
        'url': 'http://www.mixcloud.com/gillespeterson/caribou-7-inch-vinyl-mix-chat/',
        'info_dict': {
            'id': 'gillespeterson-caribou-7-inch-vinyl-mix-chat',
            'ext': 'm4a',
            'title': 'Electric Relaxation vol. 3',
            'description': 'md5:2b8aec6adce69f9d41724647c65875e8',
            'uploader': 'Daniel Drumz',
            'uploader_id': 'gillespeterson',
            'thumbnail': 're:https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
        },
    }]

    def _get_url(self, track_id, song_url):
        mobj = re.search(self.STREAM_PART_RE, song_url)
        if mobj is None:
          raise ExtractorError('Unexpected preview URL format: no stream%d')
        server_nr = int(mobj.group(1))
        for nr in server_numbers(server_nr, self.SERVER_NUMBERS_BOUNDARIES):
            url = re.sub(self.STREAM_PART_RE, 'stream%d' % nr, song_url)
            try:
                # We only want to know if the request succeed
                # don't download the whole file
                self._request_webpage(
                    HEADRequest(url), track_id,
                    'Checking URL %d/%d ...' % (nr, self.SERVER_NUMBERS_BOUNDARIES[-1]))
                return url
            except ExtractorError:
                pass
        return None

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group(1)
        cloudcast_name = mobj.group(2)
        track_id = compat_urllib_parse.unquote('-'.join((uploader, cloudcast_name)))

        webpage = self._download_webpage(url, track_id)

        preview_url = self._search_regex(
            r'\bm-play-on-spacebar\b.*\n?.*\bm-preview="([^"]+).mp3"',
            webpage, 'preview url')
        song_url = preview_url.replace('/previews/', '/c/m4a/64/') + '.m4a'
        final_song_url = self._get_url(track_id, song_url)
        if final_song_url is None:
            raise ExtractorError('Unable to extract track url')

        PREFIX = (
            r'<span class="play-button[^"]*?"'
            r'(?:\s+[a-zA-Z0-9-]+(?:="[^"]+")?)*?\s+')
        title = self._html_search_regex(
            PREFIX + r'm-title="([^"]+)"', webpage, 'title')
        thumbnail = self._proto_relative_url(self._html_search_regex(
            PREFIX + r'm-thumbnail-url="([^"]+)"', webpage, 'thumbnail',
            fatal=False))
        uploader = self._html_search_regex(
            PREFIX + r'm-owner-name="([^"]+)"',
            webpage, 'uploader', fatal=False)
        uploader_id = self._search_regex(
            r'\s+"profile": "([^"]+)",', webpage, 'uploader id', fatal=False)
        description = self._og_search_description(webpage)
        like_count = str_to_int(self._search_regex(
            r'\bbutton-favorite\b.+m-ajax-toggle-count="([^"]+)"',
            webpage, 'like count', fatal=False))
        view_count = str_to_int(self._search_regex(
            [r'<meta itemprop="interactionCount" content="UserPlays:([0-9]+)"',
             r'/listeners/?">([0-9,.]+)</a>'],
            webpage, 'play count', fatal=False))
        timestamp = parse_iso8601(self._search_regex(
            r'<time itemprop="dateCreated" datetime="([^"]+)">',
            webpage, 'upload date', default=None))

        return {
            'id': track_id,
            'title': title,
            'url': final_song_url,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': like_count,
        }

def server_numbers(first, boundaries):
    """ Server numbers to try in descending order of probable availability.
    Starting from first (i.e. the number of the server hosting the preview file)
    and going further and further up to the higher boundary and down to the
    lower one in an alternating fashion. Namely:

        server_numbers(2, (1, 5))

        # Where the preview server is 2, min number is 1 and max is 5.
        # Yields: 2, 3, 1, 4, 5

    Why not random numbers or increasing sequences? Since from what I've seen,
    full length files seem to be hosted on servers whose number is closer to
    that of the preview; to be confirmed.
    """

    if len(boundaries) != 2:
        raise ValueError("boundaries should be a two-element tuple")
    min, max = boundaries
    highs = range(first + 1, max + 1)
    lows = range(first - 1, min - 1, -1)
    rest = filter(None,
        itertools.chain.from_iterable(itertools.izip_longest(highs, lows)))
    yield first
    for n in rest:
        yield n
