from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    smuggle_url,
    url_basename,
)


class NationalGeographicIE(InfoExtractor):
    _VALID_URL = r'http://video\.nationalgeographic\.com/video/.*?'

    _TEST = {
        'url': 'http://video.nationalgeographic.com/video/news/150210-news-crab-mating-vin?source=featuredvideo',
        'info_dict': {
            'id': '4DmDACA6Qtk_',
            'ext': 'flv',
            'title': 'Mating Crabs Busted by Sharks',
            'description': 'md5:16f25aeffdeba55aaa8ec37e093ad8b3',
        },
        'add_ie': ['ThePlatform'],
    }

    def _real_extract(self, url):
        name = url_basename(url)

        webpage = self._download_webpage(url, name)
        feed_url = self._search_regex(r'data-feed-url="([^"]+)"', webpage, 'feed url')
        guid = self._search_regex(r'data-video-guid="([^"]+)"', webpage, 'guid')

        feed = self._download_xml('%s?byGuid=%s' % (feed_url, guid), name)
        content = feed.find('.//{http://search.yahoo.com/mrss/}content')
        theplatform_id = url_basename(content.attrib.get('url'))

        return self.url_result(smuggle_url(
            'http://link.theplatform.com/s/ngs/%s?format=SMIL&formats=MPEG4&manifest=f4m' % theplatform_id,
            # For some reason, the normal links don't work and we must force the use of f4m
            {'force_smil_url': True}))
