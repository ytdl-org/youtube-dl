# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    float_or_none,
    parse_duration,
    unified_strdate,
)


class NRKIE(InfoExtractor):
    _VALID_URL = r'(?:nrk:|https?://(?:www\.)?nrk\.no/video/PS\*)(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'http://www.nrk.no/video/PS*150533',
            'md5': 'bccd850baebefe23b56d708a113229c2',
            'info_dict': {
                'id': '150533',
                'ext': 'flv',
                'title': 'Dompap og andre fugler i Piip-Show',
                'description': 'md5:d9261ba34c43b61c812cb6b0269a5c8f',
                'duration': 263,
            }
        },
        {
            'url': 'http://www.nrk.no/video/PS*154915',
            'md5': '0b1493ba1aae7d9579a5ad5531bc395a',
            'info_dict': {
                'id': '154915',
                'ext': 'flv',
                'title': 'Slik høres internett ut når du er blind',
                'description': 'md5:a621f5cc1bd75c8d5104cb048c6b8568',
                'duration': 20,
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'http://v8.psapi.nrk.no/mediaelement/%s' % video_id,
            video_id, 'Downloading media JSON')

        if data['usageRights']['isGeoBlocked']:
            raise ExtractorError(
                'NRK har ikke rettigheter til å vise dette programmet utenfor Norge',
                expected=True)

        video_url = data['mediaUrl'] + '?hdcore=3.5.0&plugin=aasp-3.5.0.151.81'

        duration = parse_duration(data.get('duration'))

        images = data.get('images')
        if images:
            thumbnails = images['webImages']
            thumbnails.sort(key=lambda image: image['pixelWidth'])
            thumbnail = thumbnails[-1]['imageUrl']
        else:
            thumbnail = None

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'flv',
            'title': data['title'],
            'description': data['description'],
            'duration': duration,
            'thumbnail': thumbnail,
        }


class NRKPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nrk\.no/(?!video)(?:[^/]+/)+(?P<id>[^/]+)'

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


class NRKTVIE(InfoExtractor):
    IE_DESC = 'NRK TV and NRK Radio'
    _VALID_URL = r'(?P<baseurl>https?://(?:tv|radio)\.nrk(?:super)?\.no/)(?:serie/[^/]+|program)/(?P<id>[a-zA-Z]{4}\d{8})(?:/\d{2}-\d{2}-\d{4})?(?:#del=(?P<part_id>\d+))?'

    _TESTS = [
        {
            'url': 'https://tv.nrk.no/serie/20-spoersmaal-tv/MUHH48000314/23-05-2014',
            'md5': 'adf2c5454fa2bf032f47a9f8fb351342',
            'info_dict': {
                'id': 'MUHH48000314',
                'ext': 'flv',
                'title': '20 spørsmål',
                'description': 'md5:bdea103bc35494c143c6a9acdd84887a',
                'upload_date': '20140523',
                'duration': 1741.52,
            },
        },
        {
            'url': 'https://tv.nrk.no/program/mdfp15000514',
            'md5': '383650ece2b25ecec996ad7b5bb2a384',
            'info_dict': {
                'id': 'mdfp15000514',
                'ext': 'flv',
                'title': 'Kunnskapskanalen: Grunnlovsjubiléet - Stor ståhei for ingenting',
                'description': 'md5:654c12511f035aed1e42bdf5db3b206a',
                'upload_date': '20140524',
                'duration': 4605.0,
            },
        },
        {
            # single playlist video
            'url': 'https://tv.nrk.no/serie/tour-de-ski/MSPO40010515/06-01-2015#del=2',
            'md5': 'adbd1dbd813edaf532b0a253780719c2',
            'info_dict': {
                'id': 'MSPO40010515-part2',
                'ext': 'flv',
                'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn 06.01.2015 (del 2:2)',
                'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
                'upload_date': '20150106',
            },
            'skip': 'Only works from Norway',
        },
        {
            'url': 'https://tv.nrk.no/serie/tour-de-ski/MSPO40010515/06-01-2015',
            'playlist': [
                {
                    'md5': '9480285eff92d64f06e02a5367970a7a',
                    'info_dict': {
                        'id': 'MSPO40010515-part1',
                        'ext': 'flv',
                        'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn 06.01.2015 (del 1:2)',
                        'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
                        'upload_date': '20150106',
                    },
                },
                {
                    'md5': 'adbd1dbd813edaf532b0a253780719c2',
                    'info_dict': {
                        'id': 'MSPO40010515-part2',
                        'ext': 'flv',
                        'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn 06.01.2015 (del 2:2)',
                        'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
                        'upload_date': '20150106',
                    },
                },
            ],
            'info_dict': {
                'id': 'MSPO40010515',
                'title': 'Tour de Ski: Sprint fri teknikk, kvinner og menn',
                'description': 'md5:238b67b97a4ac7d7b4bf0edf8cc57d26',
                'upload_date': '20150106',
                'duration': 6947.5199999999995,
            },
            'skip': 'Only works from Norway',
        },
        {
            'url': 'https://radio.nrk.no/serie/dagsnytt/NPUB21019315/12-07-2015#',
            'only_matching': True,
        }
    ]

    def _extract_f4m(self, manifest_url, video_id):
        return self._extract_f4m_formats(
            manifest_url + '?hdcore=3.1.1&plugin=aasp-3.1.1.69.124', video_id, f4m_id='hds')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        part_id = mobj.group('part_id')
        base_url = mobj.group('baseurl')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta(
            'title', webpage, 'title')
        description = self._html_search_meta(
            'description', webpage, 'description')

        thumbnail = self._html_search_regex(
            r'data-posterimage="([^"]+)"',
            webpage, 'thumbnail', fatal=False)
        upload_date = unified_strdate(self._html_search_meta(
            'rightsfrom', webpage, 'upload date', fatal=False))
        duration = float_or_none(self._html_search_regex(
            r'data-duration="([^"]+)"',
            webpage, 'duration', fatal=False))

        # playlist
        parts = re.findall(
            r'<a href="#del=(\d+)"[^>]+data-argument="([^"]+)">([^<]+)</a>', webpage)
        if parts:
            entries = []
            for current_part_id, stream_url, part_title in parts:
                if part_id and current_part_id != part_id:
                    continue
                video_part_id = '%s-part%s' % (video_id, current_part_id)
                formats = self._extract_f4m(stream_url, video_part_id)
                entries.append({
                    'id': video_part_id,
                    'title': part_title,
                    'description': description,
                    'thumbnail': thumbnail,
                    'upload_date': upload_date,
                    'formats': formats,
                })
            if part_id:
                if entries:
                    return entries[0]
            else:
                playlist = self.playlist_result(entries, video_id, title, description)
                playlist.update({
                    'thumbnail': thumbnail,
                    'upload_date': upload_date,
                    'duration': duration,
                })
                return playlist

        formats = []

        f4m_url = re.search(r'data-media="([^"]+)"', webpage)
        if f4m_url:
            formats.extend(self._extract_f4m(f4m_url.group(1), video_id))

        m3u8_url = re.search(r'data-hls-media="([^"]+)"', webpage)
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(m3u8_url.group(1), video_id, 'mp4', m3u8_id='hls'))
        self._sort_formats(formats)

        subtitles_url = self._html_search_regex(
            r'data-subtitlesurl\s*=\s*(["\'])(?P<url>.+?)\1',
            webpage, 'subtitle URL', default=None, group='url')
        subtitles = {}
        if subtitles_url:
            subtitles['no'] = [{
                'ext': 'ttml',
                'url': compat_urlparse.urljoin(base_url, subtitles_url),
            }]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }
