# coding: utf-8
from __future__ import unicode_literals

import random
import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_age_limit,
    parse_duration,
)


class NRKBaseIE(InfoExtractor):
    _faked_ip = None

    def _download_webpage_handle(self, *args, **kwargs):
        # NRK checks X-Forwarded-For HTTP header in order to figure out the
        # origin of the client behind proxy. This allows to bypass geo
        # restriction by faking this header's value to some Norway IP.
        # We will do so once we encounter any geo restriction error.
        if self._faked_ip:
            # NB: str is intentional
            kwargs.setdefault(str('headers'), {})['X-Forwarded-For'] = self._faked_ip
        return super(NRKBaseIE, self)._download_webpage_handle(*args, **kwargs)

    def _fake_ip(self):
        # Use fake IP from 37.191.128.0/17 in order to workaround geo
        # restriction
        def octet(lb=0, ub=255):
            return random.randint(lb, ub)
        self._faked_ip = '37.191.%d.%d' % (octet(128), octet())

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'http://%s/mediaelement/%s' % (self._API_HOST, video_id),
            video_id, 'Downloading mediaelement JSON')

        title = data.get('fullTitle') or data.get('mainTitle') or data['title']
        video_id = data.get('id') or video_id

        http_headers = {'X-Forwarded-For': self._faked_ip} if self._faked_ip else {}

        entries = []

        conviva = data.get('convivaStatistics') or {}
        live = (data.get('mediaElementType') == 'Live' or
                data.get('isLive') is True or conviva.get('isLive'))

        def make_title(t):
            return self._live_title(t) if live else t

        media_assets = data.get('mediaAssets')
        if media_assets and isinstance(media_assets, list):
            def video_id_and_title(idx):
                return ((video_id, title) if len(media_assets) == 1
                        else ('%s-%d' % (video_id, idx), '%s (Part %d)' % (title, idx)))
            for num, asset in enumerate(media_assets, 1):
                asset_url = asset.get('url')
                if not asset_url:
                    continue
                formats = self._extract_akamai_formats(asset_url, video_id)
                if not formats:
                    continue
                self._sort_formats(formats)

                # Some f4m streams may not work with hdcore in fragments' URLs
                for f in formats:
                    extra_param = f.get('extra_param_to_segment_url')
                    if extra_param and 'hdcore' in extra_param:
                        del f['extra_param_to_segment_url']

                entry_id, entry_title = video_id_and_title(num)
                duration = parse_duration(asset.get('duration'))
                subtitles = {}
                for subtitle in ('webVtt', 'timedText'):
                    subtitle_url = asset.get('%sSubtitlesUrl' % subtitle)
                    if subtitle_url:
                        subtitles.setdefault('no', []).append({
                            'url': compat_urllib_parse_unquote(subtitle_url)
                        })
                entries.append({
                    'id': asset.get('carrierId') or entry_id,
                    'title': make_title(entry_title),
                    'duration': duration,
                    'subtitles': subtitles,
                    'formats': formats,
                    'http_headers': http_headers,
                })

        if not entries:
            media_url = data.get('mediaUrl')
            if media_url:
                formats = self._extract_akamai_formats(media_url, video_id)
                self._sort_formats(formats)
                duration = parse_duration(data.get('duration'))
                entries = [{
                    'id': video_id,
                    'title': make_title(title),
                    'duration': duration,
                    'formats': formats,
                }]

        if not entries:
            message_type = data.get('messageType', '')
            # Can be ProgramIsGeoBlocked or ChannelIsGeoBlocked*
            if 'IsGeoBlocked' in message_type and not self._faked_ip:
                self.report_warning(
                    'Video is geo restricted, trying to fake IP')
                self._fake_ip()
                return self._real_extract(url)

            MESSAGES = {
                'ProgramRightsAreNotReady': 'Du kan dessverre ikke se eller høre programmet',
                'ProgramRightsHasExpired': 'Programmet har gått ut',
                'ProgramIsGeoBlocked': 'NRK har ikke rettigheter til å vise dette programmet utenfor Norge',
            }
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, MESSAGES.get(
                    message_type, message_type)),
                expected=True)

        series = conviva.get('seriesName') or data.get('seriesTitle')
        episode = conviva.get('episodeName') or data.get('episodeNumberOrDate')

        thumbnails = None
        images = data.get('images')
        if images and isinstance(images, dict):
            web_images = images.get('webImages')
            if isinstance(web_images, list):
                thumbnails = [{
                    'url': image['imageUrl'],
                    'width': int_or_none(image.get('width')),
                    'height': int_or_none(image.get('height')),
                } for image in web_images if image.get('imageUrl')]

        description = data.get('description')

        common_info = {
            'description': description,
            'series': series,
            'episode': episode,
            'age_limit': parse_age_limit(data.get('legalAge')),
            'thumbnails': thumbnails,
        }

        vcodec = 'none' if data.get('mediaType') == 'Audio' else None

        # TODO: extract chapters when https://github.com/rg3/youtube-dl/pull/9409 is merged

        for entry in entries:
            entry.update(common_info)
            for f in entry['formats']:
                f['vcodec'] = vcodec

        return self.playlist_result(entries, video_id, title, description)


class NRKIE(NRKBaseIE):
    _VALID_URL = r'''(?x)
                        (?:
                            nrk:|
                            https?://
                                (?:
                                    (?:www\.)?nrk\.no/video/PS\*|
                                    v8-psapi\.nrk\.no/mediaelement/
                                )
                            )
                            (?P<id>[^/?#&]+)
                        '''
    _API_HOST = 'v8.psapi.nrk.no'
    _TESTS = [{
        # video
        'url': 'http://www.nrk.no/video/PS*150533',
        'md5': '2f7f6eeb2aacdd99885f355428715cfa',
        'info_dict': {
            'id': '150533',
            'ext': 'mp4',
            'title': 'Dompap og andre fugler i Piip-Show',
            'description': 'md5:d9261ba34c43b61c812cb6b0269a5c8f',
            'duration': 263,
        }
    }, {
        # audio
        'url': 'http://www.nrk.no/video/PS*154915',
        # MD5 is unstable
        'info_dict': {
            'id': '154915',
            'ext': 'flv',
            'title': 'Slik høres internett ut når du er blind',
            'description': 'md5:a621f5cc1bd75c8d5104cb048c6b8568',
            'duration': 20,
        }
    }, {
        'url': 'nrk:ecc1b952-96dc-4a98-81b9-5296dc7a98d9',
        'only_matching': True,
    }, {
        'url': 'https://v8-psapi.nrk.no/mediaelement/ecc1b952-96dc-4a98-81b9-5296dc7a98d9',
        'only_matching': True,
    }]


class NRKTVIE(NRKBaseIE):
    IE_DESC = 'NRK TV and NRK Radio'
    _EPISODE_RE = r'(?P<id>[a-zA-Z]{4}\d{8})'
    _VALID_URL = r'''(?x)
                        https?://
                            (?:tv|radio)\.nrk(?:super)?\.no/
                            (?:serie/[^/]+|program)/
                            (?![Ee]pisodes)%s
                            (?:/\d{2}-\d{2}-\d{4})?
                            (?:\#del=(?P<part_id>\d+))?
                    ''' % _EPISODE_RE
    _API_HOST = 'psapi-we.nrk.no'

    _TESTS = [{
        'url': 'https://tv.nrk.no/serie/20-spoersmaal-tv/MUHH48000314/23-05-2014',
        'md5': '4e9ca6629f09e588ed240fb11619922a',
        'info_dict': {
            'id': 'MUHH48000314AA',
            'ext': 'mp4',
            'title': '20 spørsmål 23.05.2014',
            'description': 'md5:bdea103bc35494c143c6a9acdd84887a',
            'duration': 1741,
        },
    }, {
        'url': 'https://tv.nrk.no/program/mdfp15000514',
        'md5': '43d0be26663d380603a9cf0c24366531',
        'info_dict': {
            'id': 'MDFP15000514CA',
            'ext': 'mp4',
            'title': 'Grunnlovsjubiléet - Stor ståhei for ingenting 24.05.2014',
            'description': 'md5:89290c5ccde1b3a24bb8050ab67fe1db',
            'duration': 4605,
        },
    }, {
        # single playlist video
        'url': 'https://tv.nrk.no/serie/tour-de-ski/MSPO40010515/06-01-2015#del=2',
        'md5': 'adbd1dbd813edaf532b0a253780719c2',
        'info_dict': {
            'id': 'MSPO40010515-part2',
            'ext': 'flv',
            'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn 06.01.2015 (del 2:2)',
            'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
        },
        'skip': 'Only works from Norway',
    }, {
        'url': 'https://tv.nrk.no/serie/tour-de-ski/MSPO40010515/06-01-2015',
        'playlist': [{
            'md5': '9480285eff92d64f06e02a5367970a7a',
            'info_dict': {
                'id': 'MSPO40010515-part1',
                'ext': 'flv',
                'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn 06.01.2015 (del 1:2)',
                'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
            },
        }, {
            'md5': 'adbd1dbd813edaf532b0a253780719c2',
            'info_dict': {
                'id': 'MSPO40010515-part2',
                'ext': 'flv',
                'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn 06.01.2015 (del 2:2)',
                'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
            },
        }],
        'info_dict': {
            'id': 'MSPO40010515',
            'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn',
            'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
            'duration': 6947.52,
        },
        'skip': 'Only works from Norway',
    }, {
        'url': 'https://radio.nrk.no/serie/dagsnytt/NPUB21019315/12-07-2015#',
        'only_matching': True,
    }]


class NRKTVDirekteIE(NRKTVIE):
    IE_DESC = 'NRK TV Direkte and NRK Radio Direkte'
    _VALID_URL = r'https?://(?:tv|radio)\.nrk\.no/direkte/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://tv.nrk.no/direkte/nrk1',
        'only_matching': True,
    }, {
        'url': 'https://radio.nrk.no/direkte/p1_oslo_akershus',
        'only_matching': True,
    }]


class NRKPlaylistBaseIE(InfoExtractor):
    def _extract_description(self, webpage):
        pass

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [
            self.url_result('nrk:%s' % video_id, NRKIE.ie_key())
            for video_id in re.findall(self._ITEM_RE, webpage)
        ]

        playlist_title = self. _extract_title(webpage)
        playlist_description = self._extract_description(webpage)

        return self.playlist_result(
            entries, playlist_id, playlist_title, playlist_description)


class NRKPlaylistIE(NRKPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?nrk\.no/(?!video|skole)(?:[^/]+/)+(?P<id>[^/]+)'
    _ITEM_RE = r'class="[^"]*\brich\b[^"]*"[^>]+data-video-id="([^"]+)"'
    _TESTS = [{
        'url': 'http://www.nrk.no/troms/gjenopplev-den-historiske-solformorkelsen-1.12270763',
        'info_dict': {
            'id': 'gjenopplev-den-historiske-solformorkelsen-1.12270763',
            'title': 'Gjenopplev den historiske solformørkelsen',
            'description': 'md5:c2df8ea3bac5654a26fc2834a542feed',
        },
        'playlist_count': 2,
    }, {
        'url': 'http://www.nrk.no/kultur/bok/rivertonprisen-til-karin-fossum-1.12266449',
        'info_dict': {
            'id': 'rivertonprisen-til-karin-fossum-1.12266449',
            'title': 'Rivertonprisen til Karin Fossum',
            'description': 'Første kvinne på 15 år til å vinne krimlitteraturprisen.',
        },
        'playlist_count': 5,
    }]

    def _extract_title(self, webpage):
        return self._og_search_title(webpage, fatal=False)

    def _extract_description(self, webpage):
        return self._og_search_description(webpage)


class NRKTVEpisodesIE(NRKPlaylistBaseIE):
    _VALID_URL = r'https?://tv\.nrk\.no/program/[Ee]pisodes/[^/]+/(?P<id>\d+)'
    _ITEM_RE = r'data-episode=["\']%s' % NRKTVIE._EPISODE_RE
    _TESTS = [{
        'url': 'https://tv.nrk.no/program/episodes/nytt-paa-nytt/69031',
        'info_dict': {
            'id': '69031',
            'title': 'Nytt på nytt, sesong: 201210',
        },
        'playlist_count': 4,
    }]

    def _extract_title(self, webpage):
        return self._html_search_regex(
            r'<h1>([^<]+)</h1>', webpage, 'title', fatal=False)


class NRKSkoleIE(InfoExtractor):
    IE_DESC = 'NRK Skole'
    _VALID_URL = r'https?://(?:www\.)?nrk\.no/skole/?\?.*\bmediaId=(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://www.nrk.no/skole/?page=search&q=&mediaId=14099',
        'md5': '6bc936b01f9dd8ed45bc58b252b2d9b6',
        'info_dict': {
            'id': '6021',
            'ext': 'mp4',
            'title': 'Genetikk og eneggede tvillinger',
            'description': 'md5:3aca25dcf38ec30f0363428d2b265f8d',
            'duration': 399,
        },
    }, {
        'url': 'https://www.nrk.no/skole/?page=objectives&subject=naturfag&objective=K15114&mediaId=19355',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://mimir.nrk.no/plugin/1.0/static?mediaId=%s' % video_id,
            video_id)

        nrk_id = self._parse_json(
            self._search_regex(
                r'<script[^>]+type=["\']application/json["\'][^>]*>({.+?})</script>',
                webpage, 'application json'),
            video_id)['activeMedia']['psId']

        return self.url_result('nrk:%s' % nrk_id)
