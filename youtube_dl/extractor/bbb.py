# coding: utf-8

# Contributed by Olivier Berger <olivier.berger@telecom-sudparis.eu>

# Extract material from recordings made inside BigBlueButton

# BigBlueButton records multiple videos :
#  - speaker speech & webcam
#  - screesharing
# for slides, annotations, etc. the playback app typically renders them on the fly upon playback
# so it may not be easy to capture that with youtube-dl

# Extract a merged video, without the slides with
# youtube-dl --merge-output-format mkv -f slides+speaker "https://mybbb.example.com/playback/presentation/2.0/playback.html?meetingId=12345679a50a715e8d6dc692df996dceb8d788f8-1234566973639"

from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    unified_timestamp,
    xpath_text,
    xpath_with_ns,
)

_s = lambda p: xpath_with_ns(p, {'svg': 'http://www.w3.org/2000/svg'})
_x = lambda p: xpath_with_ns(p, {'xlink': 'http://www.w3.org/1999/xlink'})

class BigBlueButtonIE(InfoExtractor):
    _VALID_URL = r'(?P<website>https?://[^/]+)/playback/presentation/2.0/playback.html\?meetingId=(?P<id>[0-9a-f\-]+)'
    _TEST = {
        'url': 'https://mybbb.example.com/playback/presentation/2.0/playback.html?meetingId=12345679a50a715e8d6dc692df996dceb8d788f8-1234566973639',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        m = self._VALID_URL_RE.match(url)
        website = m.group('website')

        webpage = self._download_webpage(url, video_id)

        # Extract basic metadata (more available in metadata.xml)
        metadata_url = website + '/presentation/' + video_id + '/metadata.xml'
        metadata = self._download_xml(metadata_url, video_id)

        id = xpath_text(metadata, 'id')
        meta = metadata.find('./meta')
        meeting_name = xpath_text(meta, 'meetingName')
        start_time = xpath_text(metadata, 'start_time')

        title = meeting_name

        # This code unused : have to grasp what to do with thumbnails
        thumbnails = []
        images = metadata.find('./playback/extensions/preview/images')
        for image in images:
            thumbnails += {
                'url': image.text.strip(),
                'width': image.get('width'),
                'height': image.get('height')
                }

        # This code mostly useless unless one know how to process slides
        shapes_url = website + '/presentation/' + video_id + '/shapes.svg'
        shapes = self._download_xml(shapes_url, video_id)
        images = shapes.findall(_s("./svg:image[@class='slide']"))
        slides = []
        for image in images:
            slides.append(image.get(_x('xlink:href')))

        # We produce 2 formats :
        # - the 'webcams.webm' one, for speaker (can be used for merging its audio)
        # - the 'deskshare.webm' one, for screen sharing (can be used
        #   for merging its video) - it lacks the slides unfortunately
        formats = []

        sources = { 'speaker': '/video/webcams.webm', 'slides': '/deskshare/deskshare.webm' }
        for format_id, source in sources.items():
            video_url = website + '/presentation/' + video_id + source
            formats.append({
                'url': video_url,
                'format_id': format_id
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'timestamp': int(start_time),
#            'thumbnails': thumbnails
        }
