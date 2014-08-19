# coding: utf-8
from __future__ import unicode_literals

import re
from datetime import datetime

from .common import InfoExtractor
from ..utils import determine_ext, ExtractorError


class JoveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jove\.com/video/(?P<id>[0-9]+)'
    _CHAPTERS_URL = 'http://www.jove.com/video-chapters?videoid={video_id:}'
    _TEST = {
        'url': 'http://www.jove.com/video/2744/electrode-positioning-montage-transcranial-direct-current',
        'md5': '93723888d82dbd6ba8b3d7d0cd65dd2b',
        'info_dict': {
            'id': '2744',
            'ext': 'mp4',
            'title': 'Electrode Positioning and Montage in Transcranial Direct Current Stimulation',
            'description': 'Transcranial direct current stimulation (tDCS) is an established technique to modulate cortical excitability1,2. It has been ...',
            'thumbnail': 're:^https?://.*\.png$',
            'upload_date': '20110523',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_meta('citation_title', webpage, 'title')
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._html_search_meta(
            'description', webpage, 'description', fatal=False)
        publish_date = self._html_search_meta(
            'citation_publication_date', webpage, 'publish date', fatal=False)
        if publish_date:
            publish_date = datetime.strptime(publish_date,
                                             '%Y/%m/%d').strftime('%Y%m%d')

        # Not the same as video_id.
        chapters_id = self._html_search_regex(
            r'/video-chapters\?videoid=([0-9]+)', webpage, 'chapters id')
        chapters_xml = self._download_xml(
            self._CHAPTERS_URL.format(video_id=chapters_id),
            video_id, note='Downloading chapter XML',
            errnote='Failed to download chapter XML'
        )
        video_url = chapters_xml.attrib.get('video')
        if not video_url:
            raise ExtractorError('Failed to get the video URL')

        ext = determine_ext(video_url)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': ext,
            'thumbnail': thumbnail,
            'description': description,
            'upload_date': publish_date,
        }
