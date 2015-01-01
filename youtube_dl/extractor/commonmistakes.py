from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class CommonMistakesIE(InfoExtractor):
    IE_DESC = False  # Do not list
    _VALID_URL = r'''(?x)
        (?:url|URL)
    '''

    _TESTS = [{
        'url': 'url',
        'only_matching': True,
    }, {
        'url': 'URL',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        msg = (
            'You\'ve asked youtube-dl to download the URL "%s". '
            'That doesn\'t make any sense. '
            'Simply remove the parameter in your command or configuration.'
        ) % url
        if self._downloader.params.get('verbose'):
            msg += ' Add -v to the command line to see what arguments and configuration youtube-dl got.'
        raise ExtractorError(msg, expected=True)
