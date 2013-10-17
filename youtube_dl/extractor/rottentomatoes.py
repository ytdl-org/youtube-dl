from .videodetective import VideoDetectiveIE


# It just uses the same method as videodetective.com,
# the internetvideoarchive.com is extracted from the og:video property
class RottenTomatoesIE(VideoDetectiveIE):
    _VALID_URL = r'https?://www\.rottentomatoes\.com/m/[^/]+/trailers/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.rottentomatoes.com/m/toy_story_3/trailers/11028566/',
        u'file': '613340.mp4',
        u'info_dict': {
            u'title': u'TOY STORY 3',
            u'description': u'From the creators of the beloved TOY STORY films, comes a story that will reunite the gang in a whole new way.',
        },
    }
