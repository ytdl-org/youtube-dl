# coding: utf-8
from __future__ import unicode_literals

import base64
import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)
from ..utils import (
    int_or_none,
    bytes_to_intlist,
    intlist_to_bytes,
    parse_duration,
    parse_iso8601,
    ExtractorError,
)
from ..aes import (
    aes_cfb_decrypt,
    BLOCK_SIZE_BYTES,
)


class YLEAreenaIE(InfoExtractor):
    _VALID_URL = r'^https?://(?P<host>areena|arenan)\.yle\.fi/(?:|tv/(?P<live>suorat|direkt)/)(?P<id>[^/?#]+)(?:[?#].+)?$'
    _PROTOCOLS = ['RTMPE', 'HDS', 'HLS']
    _AES_KEY = 'yjuap4n5ok9wzg43'
    _LIMIT = 50

    _TESTS = [
        {
            'url': 'http://areena.yle.fi/1-2825412',
            'md5': 'c9a0d9cf91a0596126531d6e91114dff',
            'info_dict': {
                'id': '6-c0a4c751a4c84dbca2292d2dc4066957',
                'ext': 'mp4',
                'upload_date': '20150525',
                'description': 'md5:e71da182216dd2e350f9009872c7d72c',
                'title': 'Ylen aamu-tv: Näin liputat oikein',
                'timestamp': 1432529700,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://areena.yle.fi/1-3238941',
            'info_dict': {
                'id': '1-3238941',
                'title': 'Yle News',
                'description': 'md5:2f7abf6497f6c447c1a3f757b8b0851d',
            },
            'playlist_mincount': 25,
        },
        {
            'url': 'http://areena.yle.fi/tv/suorat/yle-tv1',
            'info_dict': {
                'title': 're:^Yle TV1 [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
                'id': '10-1',
                'ext': 'mp4',
                'is_live': True,
            },
            'params': {
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        lang = 'fi'
        if mobj.group('host') == 'arenan':
            lang = 'sv'

        if mobj.group('live'):
            program_url = 'http://player.yle.fi/api/v1/services.jsonp?id={pid}&region=fi'
            program_key = 'service'
            event_key = 'outlet'
            is_live = True
        else:
            program_url = 'http://player.yle.fi/api/v1/programs.jsonp?id={pid}'
            program_key = 'program'
            event_key = 'publicationEvent'
            is_live = False
            data = []

            for i in itertools.count():
                path = '/api/programs/v1/items.json?' \
                    'series=%s&type=program&availability=ondemand&' \
                    'order=publication.starttime%%3Adesc&app_id=89868a18&' \
                    'app_key=54bb4ea4d92854a2a45e98f961f0d7da&' \
                    'limit=%d&offset=%d&olang=fi' % (
                        display_id, self._LIMIT, i * self._LIMIT)

                series_url = compat_urlparse.urljoin(url, path)
                json_data = self._download_json(
                    series_url, display_id, 'Downloading page %d' % (i + 1),
                    fatal=False)

                if json_data is None:
                    break

                page_data = json_data.get('data', [])
                data.extend(page_data)

                if len(page_data) < self._LIMIT:
                    break
            if data:
                series = data[0].get('partOfSeries', {})
                urls = []
                for clip in data:
                    clip_id = clip.get('id')
                    title = clip.get('title', {}).get(lang, '')
                    item_title = clip.get('itemTitle', {}).get(lang, '')
                    if item_title:
                        title = '%s-%s' % (title, item_title)
                    urls.append(self.url_result(
                        compat_urlparse.urljoin(url, '/' + clip_id),
                        video_id=clip_id,
                        video_title=title))

                return self.playlist_result(
                    urls, playlist_id=display_id,
                    playlist_title=series.get('title', {}).get(lang),
                    playlist_description=series.get('description', {}).get(lang))

        clip_info = self._download_json(
            program_url.format(pid=display_id), display_id)
        program_info = clip_info.get('data', {}).get(program_key, {})
        events = program_info.get(event_key, [])
        events_with_media = [e for e in events if e.get('media', {})]

        if not events_with_media:
            return

        media_id = events_with_media[0]['media'].get('id')
        formats, subtitles = self._extract_formats(media_id)
        self._sort_formats(formats)
        title = program_info.get('title', {}).get(lang, '')

        if is_live:
            title = self._live_title(title)

        return {
            'id': media_id,
            'title': title,
            'episode': program_info.get('itemTitle', {}).get(lang),
            'episode_number': int_or_none(program_info.get('episodeNumber')),
            'season_number': int_or_none(program_info.get('partOfSeason', {}).get('seasonNumber')),
            'series': program_info.get('partOfSeries', {}).get('title', {}).get(lang),
            'description': program_info.get('description', {}).get(lang),
            'formats': formats,
            'duration': parse_duration(program_info.get('duration')),
            'timestamp': parse_iso8601(events_with_media[0].get('startTime')),
            'subtitles': subtitles,
            'age_limit': program_info.get('contentRating', {}).get('ageRestriction', 0),
            'is_live': is_live,
        }

    def _extract_formats(self, media_id):
        media_infos = []
        subtitles = []
        for protocol in self._PROTOCOLS:
            media_url = 'http://player.yle.fi/api/v1/media.jsonp?id=%s&' \
                'protocol=%s&client=areena-flash-player' % (
                    media_id, protocol)
            media_response = self._download_json(media_url, media_id)
            media_infos.extend(media_response['data']['media'][protocol])

        has_subtitles = [i for i in media_infos if i.get('subtitles')]

        formats = []
        for fmt in media_infos:
            if has_subtitles and 'hardsubtitle' in fmt:
                continue

            url = self._decrypt_data(fmt['url']).decode('utf-8')
            sub_list = fmt.get('subtitles', [])

            extracted_subtitles = self.extract_subtitles(sub_list)
            if subtitles:
                if subtitles != extracted_subtitles:
                    raise ExtractorError(
                        'Different formats return different subtitle urls')
            else:
                subtitles = extracted_subtitles
            if fmt['protocol'] == 'HDS':
                sep = '&' if '?' in url else '?'
                url += sep + 'hdcore=3.3.0&plugin=flowplayer-3.3.0.0'
                formats.extend(self._extract_f4m_formats(
                    url, media_id, f4m_id='hds', fatal=False))
                continue
            if fmt['protocol'] == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    url, media_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
                continue

            abr = fmt.get('audioBitrateKbps', 0)
            vbr = fmt.get('videoBitrateKbps', 0)
            tbr = vbr + abr

            formats.append({
                'format_id': 'rtmp-%d' % tbr if tbr else 'rtmp',
                'url': url,
                'ext': 'flv',
                'abr': abr if abr else None,
                'vbr': vbr if vbr else None,
                'tbr': tbr if tbr else None,
                'height': fmt.get('height'),
                'width': fmt.get('width'),
                'rtmp_live': fmt.get('live'),
                'protocol': 'rtmp',
                'preference': -1,
            })

        return formats, subtitles

    def _get_subtitles(self, sub_list):
        subtitles = {}
        for sub in sub_list:
            subtitles[sub['lang']] = [{
                'ext': 'srt',
                'url': sub['uri'],
            }]
        return subtitles

    def _decrypt_data(self, data):
        data = bytes_to_intlist(base64.b64decode(data))
        key = bytes_to_intlist(self._AES_KEY.encode('utf-8'))

        iv = data[:BLOCK_SIZE_BYTES]
        cipher = data[BLOCK_SIZE_BYTES:]
        decrypted_data = aes_cfb_decrypt(cipher, key, iv)

        plaintext = intlist_to_bytes(decrypted_data)

        return plaintext
