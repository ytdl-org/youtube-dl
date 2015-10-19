# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor


class StitcherIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stitcher\.com/podcast/[\/a-z\-]+(?P<id>\d+)|\?[a-z=]+'
    _TEST = {
        'url': 'http://www.stitcher.com/podcast/the-talking-machines/e/40789481?autoplay=true',
        'md5': '391dd4e021e6edeb7b8e68fbf2e9e940',
        'info_dict': {
            'id': '40789481',
            'ext': 'mp3',
            'title': 'Machine Learning Mastery and Cancer Clusters from Talking Machines',
        }
    }

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(url, audio_id)

        title = self._og_search_title(webpage)
        url = self._search_regex(r'episodeURL: "(.+?)"', webpage, 'url')
        episode_image = self._search_regex(r'episodeImage: "(.+?)"', webpage, 'episode_image', fatal=False)
        duration = self._search_regex(r'simpleDuration: "(\d+?) minutes"', webpage, 'duration', fatal=False)

        return {
            'id': audio_id,
            'url': url,
            'title': title,
            'duration': duration,
            'thumbnail': episode_image,
            'ext': 'mp3',
            'vcodec': 'none',
        }
