# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    float_or_none,
    js_to_json,
    parse_iso8601,
    remove_end,
)


class TV2IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tv2\.no/v/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.tv2.no/v/916509/',
        'info_dict': {
            'id': '916509',
            'ext': 'mp4',
            'title': 'Se Frode Gryttens hyllest av Steven Gerrard',
            'description': 'TV 2 Sportens huspoet tar avskjed med Liverpools kaptein Steven Gerrard.',
            'timestamp': 1431715610,
            'upload_date': '20150515',
            'duration': 156.967,
            'view_count': int,
            'categories': list,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        formats = []
        format_urls = []
        for protocol in ('HDS', 'HLS'):
            data = self._download_json(
                'http://sumo.tv2.no/api/web/asset/%s/play.json?protocol=%s&videoFormat=SMIL+ISMUSP' % (video_id, protocol),
                video_id, 'Downloading play JSON')['playback']
            for item in data['items']['item']:
                video_url = item.get('url')
                if not video_url or video_url in format_urls:
                    continue
                format_id = '%s-%s' % (protocol.lower(), item.get('mediaFormat'))
                if not self._is_valid_url(video_url, video_id, format_id):
                    continue
                format_urls.append(video_url)
                ext = determine_ext(video_url)
                if ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        video_url, video_id, f4m_id=format_id, fatal=False))
                elif ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=format_id, fatal=False))
                elif ext == 'ism' or video_url.endswith('.ism/Manifest'):
                    pass
                else:
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                        'tbr': int_or_none(item.get('bitrate')),
                        'filesize': int_or_none(item.get('fileSize')),
                    })
        self._sort_formats(formats)

        asset = self._download_json(
            'http://sumo.tv2.no/api/web/asset/%s.json' % video_id,
            video_id, 'Downloading metadata JSON')['asset']

        title = asset['title']
        description = asset.get('description')
        timestamp = parse_iso8601(asset.get('createTime'))
        duration = float_or_none(asset.get('accurateDuration') or asset.get('duration'))
        view_count = int_or_none(asset.get('views'))
        categories = asset.get('keywords', '').split(',')

        thumbnails = [{
            'id': thumbnail.get('@type'),
            'url': thumbnail.get('url'),
        } for _, thumbnail in asset.get('imageVersions', {}).items()]

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'categories': categories,
            'formats': formats,
        }


class TV2ArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tv2\.no/(?:a|\d{4}/\d{2}/\d{2}(/[^/]+)+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.tv2.no/2015/05/16/nyheter/alesund/krim/pingvin/6930542',
        'info_dict': {
            'id': '6930542',
            'title': 'Russen hetses etter pingvintyveri - innrømmer å ha åpnet luken på buret',
            'description': 'md5:339573779d3eea3542ffe12006190954',
        },
        'playlist_count': 2,
    }, {
        'url': 'http://www.tv2.no/a/6930542',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        # Old embed pattern (looks unused nowadays)
        assets = re.findall(r'data-assetid=["\'](\d+)', webpage)

        if not assets:
            # New embed pattern
            for v in re.findall(r'TV2ContentboxVideo\(({.+?})\)', webpage):
                video = self._parse_json(
                    v, playlist_id, transform_source=js_to_json, fatal=False)
                if not video:
                    continue
                asset = video.get('assetId')
                if asset:
                    assets.append(asset)

        entries = [
            self.url_result('http://www.tv2.no/v/%s' % asset_id, 'TV2')
            for asset_id in assets]

        title = remove_end(self._og_search_title(webpage), ' - TV2.no')
        description = remove_end(self._og_search_description(webpage), ' - TV2.no')

        return self.playlist_result(entries, playlist_id, title, description)
