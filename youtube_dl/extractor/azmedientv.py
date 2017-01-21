from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import get_element_by_class


class AZMedienTVIE(InfoExtractor):
    IE_DESC = 'telezueri.ch, telebaern.tv and telem1.ch videos'
    _VALID_URL = r'http://(?:www\.)?(?:telezueri\.ch|telebaern\.tv|telem1\.ch)/[0-9]+-show-[^/#]+(?:/[0-9]+-episode-[^/#]+(?:/[0-9]+-segment-(?:[^/#]+#)?|#)|#)(?P<id>[^#]+)'

    _TESTS = [{
        # URL with 'segment'
        'url': 'http://www.telezueri.ch/62-show-zuerinews/13772-episode-sonntag-18-dezember-2016/32419-segment-massenabweisungen-beim-hiltl-club-wegen-pelzboom',
        'md5': 'fda85ada1299cee517a622bfbc5f6b66',
        'info_dict': {
            'id': '1_2444peh4',
            'ext': 'mov',
            'title': 'Massenabweisungen beim Hiltl Club wegen Pelzboom',
            'description': 'md5:9ea9dd1b159ad65b36ddcf7f0d7c76a8',
            'uploader_id': 'TeleZ?ri',
            'upload_date': '20161218',
            'timestamp': 1482084490,
        }
    }, {
        # URL with 'segment' and fragment:
        'url': 'http://www.telebaern.tv/118-show-news/14240-episode-dienstag-17-januar-2017/33666-segment-achtung-gefahr#zu-wenig-pflegerinnen-und-pfleger',
        'only_matching': True
    }, {
        # URL with 'episode' and fragment:
        'url': 'http://www.telem1.ch/47-show-sonntalk/13986-episode-soldaten-fuer-grenzschutz-energiestrategie-obama-bilanz#soldaten-fuer-grenzschutz-energiestrategie-obama-bilanz',
        'only_matching': True
    }, {
        # URL with 'show' and fragment:
        'url': 'http://www.telezueri.ch/66-show-sonntalk#burka-plakate-trump-putin-china-besuch',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        kaltura_partner_id = self._html_search_regex(
            r'<script[^>]+src=["\']https?://www\.kaltura\.com/.*/partner_id/([0-9]+)',
            webpage, 'Kaltura partner ID')
        kaltura_entry_id = self._html_search_regex(
            r'<a[^>]+data-id=["\'](.*?)["\'][^>]+data-slug=["\']%s' % video_id,
            webpage, 'Kaltura entry ID')

        return self.url_result(
            'kaltura:%s:%s' % (kaltura_partner_id, kaltura_entry_id),
            ie=KalturaIE.ie_key())


class AZMedienTVShowIE(InfoExtractor):
    IE_DESC = 'telezueri.ch, telebaern.tv and telem1.ch shows'
    _VALID_URL = r'http://(?:www\.)?(?:telezueri\.ch|telebaern\.tv|telem1\.ch)/(?P<id>[0-9]+-show-[^/#]+(?:/[0-9]+-episode-[^/#]+)?)$'

    _TESTS = [{
        # URL with 'episode':
        'url': 'http://www.telebaern.tv/118-show-news/13735-episode-donnerstag-15-dezember-2016',
        'info_dict': {
            'id': '118-show-news/13735-episode-donnerstag-15-dezember-2016',
            'title': 'News',
        },
        'playlist_count': 9,
    }, {
        # URL with 'show' only:
        'url': 'http://www.telezueri.ch/86-show-talktaeglich',
        'only_matching': True
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        title = get_element_by_class('title-block-cell', webpage)
        if title:
            title = title.strip()

        entries = [self.url_result(m.group('url'), ie=AZMedienTVIE.ie_key()) for m in re.finditer(
            r'<a href=["\']#["\'][^>]+data-real=["\'](?P<url>.+?)["\']', webpage)]

        return self.playlist_result(
            entries, show_id, title)
