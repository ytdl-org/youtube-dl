# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class AntennaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?antenna\.gr/webtv/watch\?cid=(?P<id>[\w_%]+)(&p=[0-9]+)?'
    _TESTS = [
        {
            'url': 'http://www.antenna.gr/webtv/watch?cid=otn_f_jvi5_e_z_i%3d&p=1',
            'info_dict': {
                'id': 'otn_f_jvi5_e_z_i%3d',
                'ext': 'mp4',
                'title': 'Αραχτοί και λάιτ (επεισ.16)',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': '"Αραχτές και... λάιτ" καταστάσεις στον Ant1.',
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

    def _real_extract(self, url):
        error = 'Content not available outside Greece.'
        desc = r'<description><!\[CDATA\[(.+?)\]\]></description>'
        thumb = r'<jwplayer:image>(.+?)</jwplayer:image>'
        formats = []
        link = 'http://www.antenna.gr/templates/data/jplayer?d=m&cid='
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        rsspage = self._download_webpage(link + video_id, video_id)
        title = self._og_search_title(webpage) or self._search_regex(r'<title>(.+?)</title>', rsspage, 'title')[9:-3]
        video_url = self._search_regex(r'file="(.+?)"', rsspage, 'url')
        if video_url == 'http://extranet.antenna.gr/flvsteaming/GR.flv':
            raise ExtractorError('%s returned error: %s' % (self.IE_NAME, error), expected=True)
        thumbnail = self._og_search_thumbnail(webpage) or self._search_regex(thumb, webpage, 'thumb', fatal=False)
        description = self._og_search_description(webpage) or self._search_regex(desc, webpage, 'description', fatal=False)
        formats.extend(self._extract_m3u8_formats(video_url, video_id, ext='mp4', entry_protocol='m3u8_native',
                                                  m3u8_id='hls', fatal=False))
        for video_format in formats:
            if video_format.get('format_note') == 'Quality selection URL':
                formats.remove(video_format)
        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
        }
