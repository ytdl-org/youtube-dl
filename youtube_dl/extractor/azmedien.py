# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import (
    get_element_by_class,
    get_element_by_id,
    strip_or_none,
    urljoin,
)


class AZMedienBaseIE(InfoExtractor):
    def _kaltura_video(self, partner_id, entry_id):
        return self.url_result(
            'kaltura:%s:%s' % (partner_id, entry_id), ie=KalturaIE.ie_key(),
            video_id=entry_id)


class AZMedienIE(AZMedienBaseIE):
    IE_DESC = 'AZ Medien videos'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            telezueri\.ch|
                            telebaern\.tv|
                            telem1\.ch
                        )/
                        [0-9]+-show-[^/\#]+
                        (?:
                            /[0-9]+-episode-[^/\#]+
                            (?:
                                /[0-9]+-segment-(?:[^/\#]+\#)?|
                                \#
                            )|
                            \#
                        )
                        (?P<id>[^\#]+)
                    '''

    _TESTS = [{
        # URL with 'segment'
        'url': 'http://www.telezueri.ch/62-show-zuerinews/13772-episode-sonntag-18-dezember-2016/32419-segment-massenabweisungen-beim-hiltl-club-wegen-pelzboom',
        'info_dict': {
            'id': '1_2444peh4',
            'ext': 'mov',
            'title': 'Massenabweisungen beim Hiltl Club wegen Pelzboom',
            'description': 'md5:9ea9dd1b159ad65b36ddcf7f0d7c76a8',
            'uploader_id': 'TeleZ?ri',
            'upload_date': '20161218',
            'timestamp': 1482084490,
        },
        'params': {
            'skip_download': True,
        },
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

        partner_id = self._search_regex(
            r'<script[^>]+src=["\'](?:https?:)?//(?:[^/]+\.)?kaltura\.com(?:/[^/]+)*/(?:p|partner_id)/([0-9]+)',
            webpage, 'kaltura partner id')
        entry_id = self._html_search_regex(
            r'<a[^>]+data-id=(["\'])(?P<id>(?:(?!\1).)+)\1[^>]+data-slug=["\']%s'
            % re.escape(video_id), webpage, 'kaltura entry id', group='id')

        return self._kaltura_video(partner_id, entry_id)


class AZMedienPlaylistIE(AZMedienBaseIE):
    IE_DESC = 'AZ Medien playlists'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            telezueri\.ch|
                            telebaern\.tv|
                            telem1\.ch
                        )/
                        (?P<id>[0-9]+-
                            (?:
                                show|
                                topic|
                                themen
                            )-[^/\#]+
                            (?:
                                /[0-9]+-episode-[^/\#]+
                            )?
                        )$
                    '''

    _TESTS = [{
        # URL with 'episode'
        'url': 'http://www.telebaern.tv/118-show-news/13735-episode-donnerstag-15-dezember-2016',
        'info_dict': {
            'id': '118-show-news/13735-episode-donnerstag-15-dezember-2016',
            'title': 'News - Donnerstag, 15. Dezember 2016',
        },
        'playlist_count': 9,
    }, {
        # URL with 'themen'
        'url': 'http://www.telem1.ch/258-themen-tele-m1-classics',
        'info_dict': {
            'id': '258-themen-tele-m1-classics',
            'title': 'Tele M1 Classics',
        },
        'playlist_mincount': 15,
    }, {
        # URL with 'topic', contains nested playlists
        'url': 'http://www.telezueri.ch/219-topic-aera-trump-hat-offiziell-begonnen',
        'only_matching': True,
    }, {
        # URL with 'show' only
        'url': 'http://www.telezueri.ch/86-show-talktaeglich',
        'only_matching': True
    }]

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        entries = []

        partner_id = self._search_regex(
            r'src=["\'](?:https?:)?//(?:[^/]+\.)kaltura\.com/(?:[^/]+/)*(?:p|partner_id)/(\d+)',
            webpage, 'kaltura partner id', default=None)

        if partner_id:
            entries = [
                self._kaltura_video(partner_id, m.group('id'))
                for m in re.finditer(
                    r'data-id=(["\'])(?P<id>(?:(?!\1).)+)\1', webpage)]

        if not entries:
            entries = [
                self.url_result(m.group('url'), ie=AZMedienIE.ie_key())
                for m in re.finditer(
                    r'<a[^>]+data-real=(["\'])(?P<url>http.+?)\1', webpage)]

        if not entries:
            entries = [
                # May contain nested playlists (e.g. [1]) thus no explicit
                # ie_key
                # 1. http://www.telezueri.ch/219-topic-aera-trump-hat-offiziell-begonnen)
                self.url_result(urljoin(url, m.group('url')))
                for m in re.finditer(
                    r'<a[^>]+name=[^>]+href=(["\'])(?P<url>/.+?)\1', webpage)]

        title = self._search_regex(
            r'episodeShareTitle\s*=\s*(["\'])(?P<title>(?:(?!\1).)+)\1',
            webpage, 'title',
            default=strip_or_none(get_element_by_id(
                'video-title', webpage)), group='title')

        return self.playlist_result(entries, show_id, title)


class AZMedienShowPlaylistIE(AZMedienBaseIE):
    IE_DESC = 'AZ Medien show playlists'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            telezueri\.ch|
                            telebaern\.tv|
                            telem1\.ch
                        )/
                        (?:
                            all-episodes|
                            alle-episoden
                        )/
                        (?P<id>[^/?#&]+)
                    '''

    _TEST = {
        'url': 'http://www.telezueri.ch/all-episodes/astrotalk',
        'info_dict': {
            'id': 'astrotalk',
            'title': 'TeleZüri: AstroTalk - alle episoden',
            'description': 'md5:4c0f7e7d741d906004266e295ceb4a26',
        },
        'playlist_mincount': 13,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        episodes = get_element_by_class('search-mobile-box', webpage)
        entries = [self.url_result(
            urljoin(url, m.group('url'))) for m in re.finditer(
                r'<a[^>]+href=(["\'])(?P<url>(?:(?!\1).)+)\1', episodes)]
        title = self._og_search_title(webpage, fatal=False)
        description = self._og_search_description(webpage)
        return self.playlist_result(entries, playlist_id, title, description)
