from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate
)


class JoveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jove\.com/v/(?P<id>[0-9]+)'
    _CHAPTERS_URL = 'http://www.jove.com/video-chapters?videoid={video_id:}'
    _TESTS = [
        {
            'url': 'http://www.jove.com/v/2744/electrode-positioning-montage-transcranial-direct-current',
            'only_matching': True,
        },
        {
            'url': 'http://www.jove.com/v/51796/culturing-caenorhabditis-elegans-axenic-liquid-media-creation',
            'md5': 'a5b4cb47d97208ee24c8e1044c61e393',
            'info_dict': {
                'id': '51796',
                'ext': 'mp4',
                'title': 'Culturing Caenorhabditis elegans in Axenic Liquid Media and Creation of Transgenic Worms by Microparticle Bombardment',
                'description': 'md5:35ff029261900583970c4023b70f1dc9',
                'thumbnail': r're:^https?://.*\.jpg$',
                'upload_date': '20140802',
            }
        },

    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        chapters_id = self._html_search_regex(
            r'/video-chapters\?videoid=([0-9]+)', webpage, 'chapters id')

        chapters_xml = self._download_xml(
            self._CHAPTERS_URL.format(video_id=chapters_id),
            video_id, note='Downloading chapters XML',
            errnote='Failed to download chapters XML')

        video_url = chapters_xml.attrib.get('video')
        if not video_url:
            raise ExtractorError('Failed to get the video URL')

        if "mp4" not in video_url:
            raise ExtractorError('This video is DRM protected.', expected=True)

        title = self._html_search_meta('citation_title', webpage, 'title')
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._html_search_regex(
            r'<p class="jove_content">(.+?)</p>',
            webpage, 'description', fatal=False)
        publish_date = unified_strdate(self._html_search_meta(
            'citation_publication_date', webpage, 'publish date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': description,
            'upload_date': publish_date,
        }
