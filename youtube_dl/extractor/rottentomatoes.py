from __future__ import unicode_literals

from .videodetective import VideoDetectiveIE


# It just uses the same method as videodetective.com,
# the internetvideoarchive.com is extracted from the og:video property
class RottenTomatoesIE(VideoDetectiveIE):
    _VALID_URL = r'https?://www\.rottentomatoes\.com/m/[^/]+/trailers/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.rottentomatoes.com/m/toy_story_3/trailers/11028566/',
        'info_dict': {
            'id': '613340',
            'ext': 'mp4',
            'title': 'TOY STORY 3',
            'description': 'From the creators of the beloved TOY STORY films, comes a story that will reunite the gang in a whole new way.',
        },
    }
