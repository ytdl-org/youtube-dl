from __future__ import unicode_literals

from .tnaflix import TNAFlixIE


class EMPFlixIE(TNAFlixIE):
    _VALID_URL = r'^https?://www\.empflix\.com/videos/(?P<display_id>[0-9a-zA-Z-]+)-(?P<id>[0-9]+)\.html'

    _TITLE_REGEX = r'name="title" value="(?P<title>[^"]*)"'
    _DESCRIPTION_REGEX = r'name="description" value="([^"]*)"'
    _CONFIG_REGEX = r'flashvars\.config\s*=\s*escape\("([^"]+)"'

    _TEST = {
        'url': 'http://www.empflix.com/videos/Amateur-Finger-Fuck-33051.html',
        'md5': 'b1bc15b6412d33902d6e5952035fcabc',
        'info_dict': {
            'id': '33051',
            'display_id': 'Amateur-Finger-Fuck',
            'ext': 'mp4',
            'title': 'Amateur Finger Fuck',
            'description': 'Amateur solo finger fucking.',
            'thumbnail': 're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }
