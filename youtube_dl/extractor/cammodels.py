from __future__ import unicode_literals
from .common import InfoExtractor
from .common import ExtractorError
import json
import re


class CamModelsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cammodels\.com/cam/(?P<id>\w+)'
    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url_or_request=url, video_id=video_id, headers=self._HEADERS)
        manifest_url = self._get_manifest_url_from_webpage(video_id=video_id, webpage=webpage)
        manifest = self._get_manifest_from_manifest_url(manifest_url=manifest_url, video_id=video_id, webpage=webpage)
        formats = self._get_formats_from_manifest(manifest=manifest, video_id=video_id)
        return {
            'id': video_id,
            'title': self._live_title(video_id),
            'formats': formats
        }

    def _get_manifest_url_from_webpage(self, video_id, webpage):
        manifest_url_root = self._html_search_regex(
            pattern=r'manifestUrlRoot=(?P<id>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))',
            string=webpage,
            name='manifest',
            fatal=False)
        if not manifest_url_root:
            offline = self._html_search_regex(
                pattern=r'(?P<id>I\'m offline, but let\'s stay connected!)',
                string=webpage,
                name='offline indicator',
                fatal=False)
            if offline:
                raise ExtractorError(
                    msg='This user is currently offline, so nothing can be downloaded.',
                    expected=True,
                    video_id=video_id)
            private = self._html_search_regex(
                pattern=r'(?P<id>I’m in a private show right now)',
                string=webpage,
                name='private show indicator',
                fatal=False)
            if private:
                raise ExtractorError(
                    msg='This user is doing a private show, which requires payment. This extractor currently does not support private streams.',
                    expected=True,
                    video_id=video_id)
            raise ExtractorError(
                msg='Unable to find link to stream info on webpage. Room is not offline, so something else is wrong.',
                expected=False,
                video_id=video_id)
        manifest_url = manifest_url_root + video_id + '.json'
        return manifest_url

    def _get_manifest_from_manifest_url(self, manifest_url, video_id, webpage):
        manifest = self._download_json(url_or_request=manifest_url, video_id=video_id, headers=self._HEADERS, fatal=False)
        if not manifest:
            raise ExtractorError(
                msg='Link to stream URLs was found, but we couldn\'t access it.',
                expected=False,
                video_id=video_id)
        return manifest

    def _get_formats_from_manifest(self, manifest, video_id):
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
                pattern=r'(?P<id>rtmp?:\/\/[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#&//=]*))',
                string=manifest_json)
            if not manifest_links:
                raise ExtractorError(
                    msg='Link to stream info was found, but we couldn\'t read the response. This is probably a bug.',
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
        return formats
