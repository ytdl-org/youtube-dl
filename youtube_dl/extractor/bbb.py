# coding: utf-8

# Contributed by Olivier Berger <olivier.berger@telecom-sudparis.eu>

# Extract material from recordings made inside BigBlueButton

# BigBlueButton records multiple videos :
#  - webcams feed : sound & webcam views : useful for extracting sound
#  - deskshare captures : screensharing, but not the slides

# For slides, annotations, polls and other stuff displayed to the
# audience the playback app typically renders them on the fly upon
# playback (SVG) so it may not be easy to capture that with youtube-dl

# To extract a merged video, which will miss the slides and webcam views, proceed with :
# youtube-dl --merge-output-format mkv -f deskshare+webcams "https://mybbb.example.com/playback/presentation/2.0/playback.html?meetingId=12345679a50a715e8d6dc692df996dceb8d788f8-1234566973639"

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
    _TESTS = [
        {
            'url': 'https://webconf.imtbs-tsp.eu/playback/presentation/2.0/playback.html?meetingId=522d1d51bee82a57b535ced7091addeecb074d47-1588254659509',
            'md5': 'dc98924b35c2234a8c7b3a61b30d968e',
            'info_dict': {
                'id': '522d1d51bee82a57b535ced7091addeecb074d47-1588254659509',
                'ext': 'webm',
                'title': 'PRO 3600',
                'timestamp': 1588254659509,
                'format': 'webcams - unknown'
            },
            'params': {
                'format': 'webcams',
            }
        },
        {
            'url': 'https://webconf.imtbs-tsp.eu/playback/presentation/2.0/playback.html?meetingId=522d1d51bee82a57b535ced7091addeecb074d47-1588254659509',
            'md5': '99c9191dbe03dd5eab34ba02352f1742',
            'info_dict': {
                'id': '522d1d51bee82a57b535ced7091addeecb074d47-1588254659509',
                'ext': 'webm',
                'title': 'PRO 3600',
                'timestamp': 1588254659509,
                'format': 'deskshare - unknown'
            },
            'params': {
                'format': 'deskshare',
            }
        }]

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
        # - the 'webcams.webm' one, for webcams (can be used for merging its audio)
        # - the 'deskshare.webm' one, for screen sharing (can be used
        #   for merging its video) - it lacks the slides, unfortunately
        formats = []

        sources = { 'webcams': '/video/webcams.webm', 'deskshare': '/deskshare/deskshare.webm' }
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
