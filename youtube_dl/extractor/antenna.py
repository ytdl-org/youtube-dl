# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class AntennaIE(InfoExtractor):
    IE_NAME = 'antenna.gr'
    IE_DESC = 'ANT1 WEB TV'
    _VALID_URL = r'https?://(?:www\.)?antenna\.gr/webtv/watch\?cid=(?P<id>[\w_%]+)(&p=[0-9]+)?'
    _TESTS = [
        {
            'url': 'http://www.antenna.gr/webtv/watch?cid=jbq_kgua8_jw_a%3d&p=1',
            'info_dict': {
                'id': 'jbq_kgua8_jw_a%3d',
                'ext': 'mp4',
                'title': 'ANT1 News 19-09-2016 στις 19:00',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': 'Μετά από αλλεπάλληλες αναβολές ξεκίνησε η δίκη για την τραγωδία της Marfin.',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Content not available outside Greece.'
        },
        {
            'url': 'http://www.antenna.gr/webtv/watch?cid=%2fn_u4_x_n79i_d_i%3d',
            'info_dict': {
                'id': '%2fn_u4_x_n79i_d_i%3d',
                'ext': 'mp4',
                'title': 'Της Ελλάδος τα παιδιά (επεισ.38 - Ιφιγένεια εν Τατοϊω)',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': 'Τρείς σμηνίτες, η κυρία Μπoυμπoύ και o Σμήvαρχoς τoυ γραφείoυ Κάκαλoς, συνθέτουν μια '
                               'από τις πιο αστείες συντροφιές της ελληνικής τηλεόρασης.',
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

    def _extract_info_rss(self, video_id, webpage):
        formats = []
        jplayer_url = 'http://www.antenna.gr/templates/data/jplayer?d=m&cid='
        desc_re = r'<description><!\[CDATA\[(.+?)\]\]></description>'
        rss = self._download_webpage(jplayer_url + video_id, video_id)
        video_url = self._search_regex(r'file="(.+?)"', rss, 'url')
        if video_url == 'http://extranet.antenna.gr/flvsteaming/GR.flv':
            raise AntennaIE.MediaSelectionError('Content not available outside Greece.')
        formats.extend(self._extract_akamai_formats(video_url, video_id))
        if not formats:
            raise AntennaIE.MediaSelectionError('No formats available')
        title = self._og_search_title(webpage).split(' | ')[-1] or self._search_regex(r'<title>(.+?)</title>', rss,
                                                                                      'title')[9:-3]
        thumbnail = self._og_search_thumbnail(webpage)
        desc = self._og_search_description(webpage).split(' | ')[-1] or self._search_regex(desc_re, rss, 'description', fatal=false)

        return {
            'id': video_id,
            'formats': formats,
            'title': title.strip(),
            'thumbnail': thumbnail,
            'description': desc,
        }

    def _extract_info_json(self, video_id, webpage):
        formats = []
        json_url = 'http://www.antenna.gr/templates/data/jsonPlayer?d=m&cid='
        meta = self._download_json(json_url + video_id, video_id)
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
        extractors = [self._extract_info_json, self._extract_info_rss]
        last_exception = None
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        for extractor in extractors:
            try:
                return extractor(video_id, webpage)
            except AntennaIE.MediaSelectionError as e:
                if e.id in ('No formats available', 'Content not available outside Greece.'):
                    last_exception = e
                    continue
                self._raise_extractor_error(e)
        self._raise_extractor_error(last_exception)
