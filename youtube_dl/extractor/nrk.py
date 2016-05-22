# encoding: utf-8
from __future__ import unicode_literals

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
    def _extract_formats(self, manifest_url, video_id, fatal=True):
        formats = []
        formats.extend(self._extract_f4m_formats(
            manifest_url + '?hdcore=3.5.0&plugin=aasp-3.5.0.151.81',
            video_id, f4m_id='hds', fatal=fatal))
        formats.extend(self._extract_m3u8_formats(manifest_url.replace(
            'akamaihd.net/z/', 'akamaihd.net/i/').replace('/manifest.f4m', '/master.m3u8'),
            video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=fatal))
        return formats

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'http://%s/mediaelement/%s' % (self._API_HOST, video_id),
            video_id, 'Downloading mediaelement JSON')

        title = data.get('fullTitle') or data.get('mainTitle') or data['title']
        video_id = data.get('id') or video_id

        entries = []

        media_assets = data.get('mediaAssets')
        if media_assets and isinstance(media_assets, list):
            def video_id_and_title(idx):
                return ((video_id, title) if len(media_assets) == 1
                        else ('%s-%d' % (video_id, idx), '%s (Part %d)' % (title, idx)))
            for num, asset in enumerate(media_assets, 1):
                asset_url = asset.get('url')
                if not asset_url:
                    continue
                formats = self._extract_formats(asset_url, video_id, fatal=False)
                if not formats:
                    continue
                self._sort_formats(formats)
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
                    'title': entry_title,
                    'duration': duration,
                    'subtitles': subtitles,
                    'formats': formats,
                })

        if not entries:
            media_url = data.get('mediaUrl')
            if media_url:
                formats = self._extract_formats(media_url, video_id)
                self._sort_formats(formats)
                duration = parse_duration(data.get('duration'))
                entries = [{
                    'id': video_id,
                    'title': title,
                    'duration': duration,
                    'formats': formats,
                }]

        if not entries:
            if data.get('usageRights', {}).get('isGeoBlocked'):
                raise ExtractorError(
                    'NRK har ikke rettigheter til å vise dette programmet utenfor Norge',
                    expected=True)

        conviva = data.get('convivaStatistics') or {}
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
    _VALID_URL = r'(?:nrk:|https?://(?:www\.)?nrk\.no/video/PS\*)(?P<id>\d+)'
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
    }]


class NRKTVIE(NRKBaseIE):
    IE_DESC = 'NRK TV and NRK Radio'
    _VALID_URL = r'https?://(?:tv|radio)\.nrk(?:super)?\.no/(?:serie/[^/]+|program)/(?P<id>[a-zA-Z]{4}\d{8})(?:/\d{2}-\d{2}-\d{4})?(?:#del=(?P<part_id>\d+))?'
    _API_HOST = 'psapi-we.nrk.no'

    _TESTS = [{
        'url': 'https://tv.nrk.no/serie/20-spoersmaal-tv/MUHH48000314/23-05-2014',
        'md5': '4e9ca6629f09e588ed240fb11619922a',
        'info_dict': {
            'id': 'MUHH48000314AA',
            'ext': 'mp4',
            'title': '20 spørsmål 23.05.2014',
            'description': 'md5:bdea103bc35494c143c6a9acdd84887a',
            'duration': 1741.52,
        },
    }, {
        'url': 'https://tv.nrk.no/program/mdfp15000514',
        'md5': '43d0be26663d380603a9cf0c24366531',
        'info_dict': {
            'id': 'MDFP15000514CA',
            'ext': 'mp4',
            'title': 'Grunnlovsjubiléet - Stor ståhei for ingenting 24.05.2014',
            'description': 'md5:89290c5ccde1b3a24bb8050ab67fe1db',
            'duration': 4605.08,
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


class NRKPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nrk\.no/(?!video|skole)(?:[^/]+/)+(?P<id>[^/]+)'

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

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [
            self.url_result('nrk:%s' % video_id, 'NRK')
            for video_id in re.findall(
                r'class="[^"]*\brich\b[^"]*"[^>]+data-video-id="([^"]+)"',
                webpage)
        ]

        playlist_title = self._og_search_title(webpage)
        playlist_description = self._og_search_description(webpage)

        return self.playlist_result(
            entries, playlist_id, playlist_title, playlist_description)


class NRKSkoleIE(InfoExtractor):
    IE_DESC = 'NRK Skole'
    _VALID_URL = r'https?://(?:www\.)?nrk\.no/skole/klippdetalj?.*\btopic=(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://nrk.no/skole/klippdetalj?topic=nrk:klipp/616532',
        'md5': '04cd85877cc1913bce73c5d28a47e00f',
        'info_dict': {
            'id': '6021',
            'ext': 'flv',
            'title': 'Genetikk og eneggede tvillinger',
            'description': 'md5:3aca25dcf38ec30f0363428d2b265f8d',
            'duration': 399,
        },
    }, {
        'url': 'http://www.nrk.no/skole/klippdetalj?topic=nrk%3Aklipp%2F616532#embed',
        'only_matching': True,
    }, {
        'url': 'http://www.nrk.no/skole/klippdetalj?topic=urn:x-mediadb:21379',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = compat_urllib_parse_unquote(self._match_id(url))

        webpage = self._download_webpage(url, video_id)

        nrk_id = self._search_regex(r'data-nrk-id=["\'](\d+)', webpage, 'nrk id')
        return self.url_result('nrk:%s' % nrk_id)
