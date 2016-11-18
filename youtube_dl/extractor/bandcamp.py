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
    parse_filesize,
    unescapeHTML,
    update_url_query,
)


class BandcampIE(InfoExtractor):
    _VALID_URL = r'https?://.*?\.bandcamp\.com/track/(?P<title>.*)'
    _TESTS = [{
        'url': 'http://youtube-dl.bandcamp.com/track/youtube-dl-test-song',
        'md5': 'c557841d5e50261777a6585648adf439',
        'info_dict': {
            'id': '1812978515',
            'ext': 'mp3',
            'title': "youtube-dl  \"'/\\\u00e4\u21ad - youtube-dl test song \"'/\\\u00e4\u21ad",
            'duration': 9.8485,
        },
        '_skip': 'There is a limit of 200 free downloads / month for the test song'
    }, {
        'url': 'http://benprunty.bandcamp.com/track/lanius-battle',
        'md5': '73d0b3171568232574e45652f8720b5c',
        'info_dict': {
            'id': '2650410135',
            'ext': 'mp3',
            'title': 'Lanius (Battle)',
            'uploader': 'Ben Prunty Music',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        m_download = re.search(r'freeDownloadPage: "(.*?)"', webpage)
        if not m_download:
            m_trackinfo = re.search(r'trackinfo: (.+),\s*?\n', webpage)
            if m_trackinfo:
                json_code = m_trackinfo.group(1)
                data = json.loads(json_code)[0]
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
                    'title': data['title'],
                    'formats': formats,
                    'duration': float_or_none(data.get('duration')),
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

        info = blob['digital_items'][0]

        downloads = info['downloads']
        track = info['title']

        artist = info.get('artist')
        title = '%s - %s' % (artist, track) if artist else track

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
            'title': title,
            'thumbnail': info.get('thumb_url'),
            'uploader': info.get('artist'),
            'artist': artist,
            'track': track,
            'formats': formats,
        }


class BandcampAlbumIE(InfoExtractor):
    IE_NAME = 'Bandcamp:album'
    _VALID_URL = r'https?://(?:(?P<subdomain>[^.]+)\.)?bandcamp\.com(?:/album/(?P<album_id>[^?#]+)|/?(?:$|[?#]))'

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
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader_id = mobj.group('subdomain')
        album_id = mobj.group('album_id')
        playlist_id = album_id or uploader_id
        webpage = self._download_webpage(url, playlist_id)
        tracks_paths = re.findall(r'<a href="(.*?)" itemprop="url">', webpage)
        if not tracks_paths:
            raise ExtractorError('The page doesn\'t contain any tracks')
        entries = [
            self.url_result(compat_urlparse.urljoin(url, t_path), ie=BandcampIE.ie_key())
            for t_path in tracks_paths]
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
