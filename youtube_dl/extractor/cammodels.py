from __future__ import unicode_literals
from .common import InfoExtractor
from .common import ExtractorError
import json
import re


class CamModelsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cammodels\.com/cam/(?P<id>\w+)'
    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        # Needed because server doesn't return links to video URLs if a browser-like User-Agent is not used
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            url,
            video_id,
            headers=self._HEADERS)
        manifest_url_root = self._html_search_regex(
            r'manifestUrlRoot=(?P<id>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))',
            webpage,
            'manifest',
            fatal=False)
        if not manifest_url_root:
            offline = self._html_search_regex(
                r'(?P<id>I\'m offline, but let\'s stay connected!)',
                webpage,
                'offline indicator',
                None,
                False)
            if offline:
                raise ExtractorError(
                    'This user is currently offline, so nothing can be downloaded.',
                    expected=True,
                    video_id=video_id)
            private = self._html_search_regex(
                r'(?P<id>I’m in a private show right now)',
                webpage,
                'private show indicator',
                None,
                False)
            if private:
                raise ExtractorError(
                    'This user is doing a private show, which requires payment. This extractor currently does not support private streams.',
                    expected=True,
                    video_id=video_id)
            raise ExtractorError(
                'Unable to find link to stream info on webpage. Room is not offline, so something else is wrong.',
                expected=False,
                video_id=video_id)
        manifest_url = manifest_url_root + video_id + '.json'
        manifest = self._download_json(
            manifest_url,
            video_id,
            'Downloading links to streams.',
            'Link to stream URLs was found, but we couldn\'t access it.',
            headers=self._HEADERS)
        try:
            rtmp_formats = manifest['formats']['mp4-rtmp']['encodings']
            formats = []
            for format in rtmp_formats:
                formats.append({
                    'ext': 'flv',
                    'url': format.get('location'),
                    'width': format.get('videoWidth'),
                    'height': format.get('videoHeight'),
                    'vbr': format.get('videoKbps'),
                    'abr': format.get('audioKbps'),
                    'format_id': str(format.get('videoWidth'))
                })
        # If they change the JSON format, then fallback to parsing out RTMP links via regex.
        except:
            manifest_json = json.dumps(manifest)
            manifest_links = re.finditer(
                r'(?P<id>rtmp?:\/\/[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#&//=]*))',
                manifest_json)
            if not manifest_links:
                raise ExtractorError(
                    'Link to stream info was found, but we couldn\'t read the response. This is probably a bug.',
                    expected=False,
                    video_id=video_id)
            formats = []
            for manifest_link in manifest_links:
                url = manifest_link.group('id')
                formats.append({
                    'ext': 'flv',
                    'url': url,
                    'format_id': url.split(sep='/')[-1]
                })
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'formats': formats
        }
