# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class StreamzzIE(InfoExtractor):
    """
    Handles downloading video from streamzz.to
    """
    _VALID_URL = r'https?://(?:\w+\.)?streamzz\.to/[0-9a-zA-Z]+'
    _TESTS = [
        {
            'url': 'https://streamzz.to/fc3l1ZXk4anp0a2pmWFhY',
            'info_dict': {
                'id': 'fc3l1ZXk4anp0a2pmWFhY',
                'ext': 'mp4',
                'title': 'Dark Phoenix (2019) - Movie Trailer 2'
            },
        }
    ]

    def _real_extract(self, url):
        """
        Parses the URL into the video's URL.
        """
        # Parse the video id out of the URL
        video_id = self._search_regex(r'https?://(?:\w+\.)?streamzz\.(?:vg|to)/([0-9a-zA-Z]+)',
                                      url, 'video_id', fatal=False) or ''

        # Get the hosted webpage
        webpage = self._download_webpage(url, video_id)

        # Get the identifer of the video
        identifier = self._search_regex(r"streamz\.vg/download(.*?)[\"\']", webpage, video_id, fatal=False)

        # It can be either none or empty, either way it's bad
        if not identifier:
            raise ExtractorError('Streamz: Failed to find the download button on the website')

        # Now create the download URL using the identifier
        url = r'https://streamz.vg/getlink-{0}.dll'.format(identifier)

        # Get the title of the video, remove the prepended site name
        title = self._search_regex('<title>(.*?)(</title>)', webpage, name='title', fatal=False) or ''
        if title.startswith('StreamZ.vg '):
            title = title[len('StreamZ.vg '):].strip()

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'ext': 'mp4'
        }
