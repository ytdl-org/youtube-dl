from __future__ import unicode_literals

import json
import random
import re
import time

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    KNOWN_EXTENSIONS,
    parse_filesize,
    unescapeHTML,
    update_url_query,
    unified_strdate,
)


class BandcampIE(InfoExtractor):
    _VALID_URL = r'https?://.*?\.bandcamp\.com/track/(?P<title>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://youtube-dl.bandcamp.com/track/youtube-dl-test-song',
        'md5': 'c557841d5e50261777a6585648adf439',
        'info_dict': {
            'id': '1812978515',
            'ext': 'mp3',
            'track': "youtube-dl  \"'/\\\u00e4\u21ad - youtube-dl test song \"'/\\\u00e4\u21ad",
            'title': "youtube-dl  \\ - youtube-dl  \"'/\\\u00e4\u21ad - youtube-dl test song \"'/\\\u00e4\u21ad",
            'duration': 9.8485,
            'uploader': 'youtube-dl  \\',
            'artist': 'youtube-dl  \\',
        },
        '_skip': 'There is a limit of 200 free downloads / month for the test song'
    }, {
        'url': 'http://benprunty.bandcamp.com/track/lanius-battle',
        'md5': '0369ace6b939f0927e62c67a1a8d9fa7',
        'info_dict': {
            'id': '2650410135',
            'ext': 'aiff',
            'album': 'FTL: Advanced Edition Soundtrack',
            'artist': 'Ben Prunty',
            'uploader': 'Ben Prunty',
            'release_date': '20140403',
            'release_year': 2014,
            'track_number': 1,
            'track': 'Lanius (Battle)',
            'title': 'Ben Prunty - Lanius (Battle)',
        },
    }, {
        'url': 'https://billbaxter.bandcamp.com/track/drone-city-pt-3-3',
        'md5': 'e8e24365cb38ff841b4e5df014f988ed',
        'info_dict': {
            'id': '3755531036',
            'ext': 'mp3',
            'album': 'Drone City',
            'artist': 'The ambient drones of Bill Baxter',
            'uploader': 'The ambient drones of Bill Baxter',
            'release_date': '20160326',
            'release_year': 2016,
            'track_number': 3,
            'track': 'Drone City, Pt. 3',
            'title': 'The ambient drones of Bill Baxter - Drone City, Pt. 3',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        thumbnail = self._html_search_meta('og:image', webpage, default=None)
        m_download = re.search(r'freeDownloadPage: "(.*?)"', webpage)
        m_trackinfo = re.search(r'trackinfo: (.+),\s*?\n', webpage)
        json_code = m_trackinfo.group(1) if m_trackinfo else None
        data = self._parse_json(json_code, title)[0]

        artist = self._search_regex(r'artist\s*:\s*"([^"]+)"', webpage, 'artist', default=None)
        album_title = self._search_regex(r'album_title\s*:\s*"([^"]+)"', webpage, 'album title', default=None)
        release_date = self._search_regex(r'album_release_date\s*:\s*"([^"]+)"', webpage, 'release', default=None)
        release_date = unified_strdate(release_date) if release_date else None
        release_year = int(release_date[0:4]) if release_date else None
        track = data.get('title') if data else None
        title = '%s - %s' % (artist, track) if artist else (track or title)
        track_number = data.get('track_num') if data else None
        duration = float_or_none(data.get('duration'))

        if not m_download:
            if data:
                track_id = compat_str(data['id'])

                if not data.get('file'):
                    raise ExtractorError('Not streamable', video_id=track_id, expected=True)

                formats = []
                for format_id, format_url in data['file'].items():
                    ext, abr_str = format_id.split('-', 1)
                    formats.append({
                        'format_id': format_id,
                        'url': self._proto_relative_url(format_url, 'http:'),
                        'ext': ext,
                        'vcodec': 'none',
                        'acodec': ext,
                        'abr': int_or_none(abr_str),
                    })

                self._sort_formats(formats)

                return {
                    'id': track_id,
                    'album': album_title,
                    'uploader': artist,
                    'artist': artist,
                    'track_id': track_id,
                    'track_number': track_number,
                    'release_date': release_date,
                    'release_year': release_year,
                    'track': track,
                    'title': title,
                    'thumbnail': thumbnail,
                    'formats': formats,
                    'duration': duration,
                }
            else:
                raise ExtractorError('No free songs found')

        download_link = m_download.group(1)
        video_id = self._search_regex(
            r'(?ms)var TralbumData = .*?[{,]\s*id: (?P<id>\d+),?$',
            webpage, 'video id')

        download_webpage = self._download_webpage(
            download_link, video_id, 'Downloading free downloads page')

        blob = self._parse_json(
            self._search_regex(
                r'data-blob=(["\'])(?P<blob>{.+?})\1', download_webpage,
                'blob', group='blob'),
            video_id, transform_source=unescapeHTML)

        digital_items = blob['digital_items'][0]

        downloads = digital_items['downloads']

        download_formats = {}
        for f in blob['download_formats']:
            name, ext = f.get('name'), f.get('file_extension')
            if all(isinstance(x, compat_str) for x in (name, ext)):
                download_formats[name] = ext.strip('.')

        formats = []
        for format_id, f in downloads.items():
            format_url = f.get('url')
            if not format_url:
                continue
            # Stat URL generation algorithm is reverse engineered from
            # download_*_bundle_*.js
            stat_url = update_url_query(
                format_url.replace('/download/', '/statdownload/'), {
                    '.rand': int(time.time() * 1000 * random.random()),
                })
            format_id = f.get('encoding_name') or format_id
            stat = self._download_json(
                stat_url, video_id, 'Downloading %s JSON' % format_id,
                transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1],
                fatal=False)
            if not stat:
                continue
            retry_url = stat.get('retry_url')
            if not isinstance(retry_url, compat_str):
                continue
            formats.append({
                'url': self._proto_relative_url(retry_url, 'http:'),
                'ext': download_formats.get(format_id),
                'format_id': format_id,
                'format_note': f.get('description'),
                'filesize': parse_filesize(f.get('size_mb')),
                'vcodec': 'none',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'album': album_title,
            'uploader': artist,
            'artist': artist,
            'track_id': video_id,
            'track_number': track_number,
            'release_date': release_date,
            'release_year': release_year,
            'track': track,
            'title': title,
            'thumbnail': digital_items.get('thumb_url') or thumbnail,
            'track': track,
            'formats': formats,
            'duration': duration,
        }


class BandcampAlbumIE(InfoExtractor):
    IE_NAME = 'Bandcamp:album'
    _VALID_URL = r'https?://(?:(?P<subdomain>[^.]+)\.)?bandcamp\.com(?:/album/(?P<album_id>[^/?#&]+))?'

    _TESTS = [{
        'url': 'http://blazo.bandcamp.com/album/jazz-format-mixtape-vol-1',
        'playlist': [
            {
                'md5': '39bc1eded3476e927c724321ddf116cf',
                'info_dict': {
                    'id': '1353101989',
                    'ext': 'mp3',
                    'title': 'Intro',
                }
            },
            {
                'md5': '1a2c32e2691474643e912cc6cd4bffaa',
                'info_dict': {
                    'id': '38097443',
                    'ext': 'mp3',
                    'title': 'Kero One - Keep It Alive (Blazo remix)',
                }
            },
        ],
        'info_dict': {
            'title': 'Jazz Format Mixtape vol.1',
            'id': 'jazz-format-mixtape-vol-1',
            'uploader_id': 'blazo',
        },
        'params': {
            'playlistend': 2
        },
        'skip': 'Bandcamp imposes download limits.'
    }, {
        'url': 'http://nightbringer.bandcamp.com/album/hierophany-of-the-open-grave',
        'info_dict': {
            'title': 'Hierophany of the Open Grave',
            'uploader_id': 'nightbringer',
            'id': 'hierophany-of-the-open-grave',
        },
        'playlist_mincount': 9,
    }, {
        'url': 'http://dotscale.bandcamp.com',
        'info_dict': {
            'title': 'Loom',
            'id': 'dotscale',
            'uploader_id': 'dotscale',
        },
        'playlist_mincount': 7,
    }, {
        # with escaped quote in title
        'url': 'https://jstrecords.bandcamp.com/album/entropy-ep',
        'info_dict': {
            'title': '"Entropy" EP',
            'uploader_id': 'jstrecords',
            'id': 'entropy-ep',
        },
        'playlist_mincount': 3,
    }, {
        # not all tracks have songs
        'url': 'https://insulters.bandcamp.com/album/we-are-the-plague',
        'info_dict': {
            'id': 'we-are-the-plague',
            'title': 'WE ARE THE PLAGUE',
            'uploader_id': 'insulters',
        },
        'playlist_count': 2,
    }]

    @classmethod
    def suitable(cls, url):
        return (False
                if BandcampWeeklyIE.suitable(url) or BandcampIE.suitable(url)
                else super(BandcampAlbumIE, cls).suitable(url))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader_id = mobj.group('subdomain')
        album_id = mobj.group('album_id')
        playlist_id = album_id or uploader_id
        webpage = self._download_webpage(url, playlist_id)
        track_elements = re.findall(
            r'(?s)<div[^>]*>(.*?<a[^>]+href="([^"]+?)"[^>]+itemprop="url"[^>]*>.*?)</div>', webpage)
        if not track_elements:
            raise ExtractorError('The page doesn\'t contain any tracks')
        # Only tracks with duration info have songs
        entries = [
            self.url_result(
                compat_urlparse.urljoin(url, t_path),
                ie=BandcampIE.ie_key(),
                video_title=self._search_regex(
                    r'<span\b[^>]+\bitemprop=["\']name["\'][^>]*>([^<]+)',
                    elem_content, 'track title', fatal=False))
            for elem_content, t_path in track_elements
            if self._html_search_meta('duration', elem_content, default=None)]

        title = self._html_search_regex(
            r'album_title\s*:\s*"((?:\\.|[^"\\])+?)"',
            webpage, 'title', fatal=False)
        if title:
            title = title.replace(r'\"', '"')
        return {
            '_type': 'playlist',
            'uploader_id': uploader_id,
            'id': playlist_id,
            'title': title,
            'entries': entries,
        }


class BandcampWeeklyIE(InfoExtractor):
    IE_NAME = 'Bandcamp:weekly'
    _VALID_URL = r'https?://(?:www\.)?bandcamp\.com/?\?(?:.*?&)?show=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://bandcamp.com/?show=224',
        'md5': 'b00df799c733cf7e0c567ed187dea0fd',
        'info_dict': {
            'id': '224',
            'ext': 'opus',
            'title': 'BC Weekly April 4th 2017 - Magic Moments',
            'description': 'md5:5d48150916e8e02d030623a48512c874',
            'duration': 5829.77,
            'release_date': '20170404',
            'series': 'Bandcamp Weekly',
            'episode': 'Magic Moments',
            'episode_number': 208,
            'episode_id': '224',
        }
    }, {
        'url': 'https://bandcamp.com/?blah/blah@&show=228',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        blob = self._parse_json(
            self._search_regex(
                r'data-blob=(["\'])(?P<blob>{.+?})\1', webpage,
                'blob', group='blob'),
            video_id, transform_source=unescapeHTML)

        show = blob['bcw_show']

        # This is desired because any invalid show id redirects to `bandcamp.com`
        # which happens to expose the latest Bandcamp Weekly episode.
        show_id = int_or_none(show.get('show_id')) or int_or_none(video_id)

        formats = []
        for format_id, format_url in show['audio_stream'].items():
            if not isinstance(format_url, compat_str):
                continue
            for known_ext in KNOWN_EXTENSIONS:
                if known_ext in format_id:
                    ext = known_ext
                    break
            else:
                ext = None
            formats.append({
                'format_id': format_id,
                'url': format_url,
                'ext': ext,
                'vcodec': 'none',
            })
        self._sort_formats(formats)

        title = show.get('audio_title') or 'Bandcamp Weekly'
        subtitle = show.get('subtitle')
        if subtitle:
            title += ' - %s' % subtitle

        episode_number = None
        seq = blob.get('bcw_seq')

        if seq and isinstance(seq, list):
            try:
                episode_number = next(
                    int_or_none(e.get('episode_number'))
                    for e in seq
                    if isinstance(e, dict) and int_or_none(e.get('id')) == show_id)
            except StopIteration:
                pass

        return {
            'id': video_id,
            'title': title,
            'description': show.get('desc') or show.get('short_desc'),
            'duration': float_or_none(show.get('audio_duration')),
            'is_live': False,
            'release_date': unified_strdate(show.get('published_date')),
            'series': 'Bandcamp Weekly',
            'episode': show.get('subtitle'),
            'episode_number': episode_number,
            'episode_id': compat_str(video_id),
            'formats': formats
        }
