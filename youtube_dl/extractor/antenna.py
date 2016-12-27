# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class AntennaIE(InfoExtractor):
    IE_NAME = 'antenna.gr'
    IE_DESC = 'ANT1 WEB TV'
    _VALID_URL = r'https?://(?:www\.)?antenna\.gr/minisites/[\w_\-0-9]+/watch/(?P<id>[\w_\-0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.antenna.gr/minisites/akros-ikogeniakon/watch/akros-ikogeniakon-epis-47',
            'info_dict': {
                'id': 'akros-ikogeniakon-epis-47',
                'ext': 'mp4',
                'title': 'Άκρως Οικογενειακόν (Επεισ: 47)',
                'thumbnail': 're:^https?://.*\.jpg\?w=[0-9]+&h=[0-9]+&mode=crop&scale=both&anchor=topcenter&quality=91&legacy=1',
                'description': 'Άκρως Οικογενειακόν (Επεισ: 47)',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Content not available outside Greece.'
        },
        {
            'url': 'http://www.antenna.gr/minisites/tis-ellados-ta-pedia/watch/tis-ellados-ta-pedia-epis38-ifigenia-en-tatoio',
            'info_dict': {
                'id': 'tis-ellados-ta-pedia-epis38-ifigenia-en-tatoio',
                'ext': 'mp4',
                'title': 'Της Ελλάδος τα παιδιά (επεισ.38 - Ιφιγένεια εν Τατοϊω)',
                'thumbnail': 're:^https?://.*\.jpg\?w=[0-9]+&h=[0-9]+&mode=crop&scale=both&anchor=topcenter&quality=91&legacy=1',
                'description': 'Της Ελλάδος τα παιδιά (επεισ.38 - Ιφιγένεια εν Τατοϊω)',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Content not available outside Greece.'
        }]

    class MediaSelectionError(Exception):
        def __init__(self, error_id):
            self.id = error_id

    def _raise_extractor_error(self, media_selection_error):
        raise ExtractorError('{0} returned error: {1}'.format(self.IE_NAME,
                                                              media_selection_error.id), expected=True)

    def _extract_info_json(self, mid, video_id, webpage):
        formats = []
        json_url = 'http://www.antenna.gr/Services/jwplayer/getplaylistJson.ashx?mid='
        meta = self._download_json(json_url + mid, video_id)
        manifest_url = meta.get('url')
        if manifest_url == 'http://extranet.antenna.gr/flvsteaming/GR.mp4':
            raise AntennaIE.MediaSelectionError('Content not available outside Greece.')
        formats.extend(self._extract_akamai_formats(manifest_url, video_id))
        if not formats:
            raise AntennaIE.MediaSelectionError('No formats available')
        title = meta.get('title') or self._og_search_title(webpage)
        thumbnail = meta.get('thumb') or self._og_search_thumbnail(webpage)
        desc = self._html_search_meta('description', webpage) or self._og_search_description(webpage)
        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': thumbnail,
            'description': desc.split(' | ')[-1],
        }

    def _real_extract(self, url):
        extractor = self._extract_info_json
        last_exception = None
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        mid = self._search_regex(r'getplaylistJson\.ashx\?mid=(.+)&show', webpage, 'mid')
        try:
            return extractor(mid, video_id, webpage)
        except AntennaIE.MediaSelectionError as e:
            if e.id in ('No formats available', 'Content not available outside Greece.'):
                last_exception = e
            self._raise_extractor_error(e)
        self._raise_extractor_error(last_exception)
