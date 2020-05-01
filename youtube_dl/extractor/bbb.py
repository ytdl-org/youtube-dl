# coding: utf-8

# Extract material from recordings made inside BigBlueButton

# BigBlueButton records multiple videos :
#  - speaker speech & webcam
#  - screesharing
# for slides, annotations, etc. the playback app typically renders them on the fly upon playback
# so it may not be easy to capture that with youtube-dl


from __future__ import unicode_literals

from .common import InfoExtractor

from .openload import PhantomJSwrapper

# TODO : thumbnails

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
        #print(video_id)
        print(website)

        webpage = self._download_webpage(url, video_id)

        # print(webpagejs)

        # TODO more code goes here, for example ...
        #title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        title = video_id

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
 #           'description': self._og_search_description(webpage),
#            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
    
