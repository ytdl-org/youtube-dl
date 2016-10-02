# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    get_element_by_class,
    int_or_none,
    js_to_json,
    parse_iso8601,
    remove_start,
    strip_or_none,
    url_basename,
)


class OnetBaseIE(InfoExtractor):
    def _search_mvp_id(self, webpage):
        return self._search_regex(
            r'id=(["\'])mvp:(?P<id>.+?)\1', webpage, 'mvp id', group='id')

    def _extract_from_id(self, video_id, webpage):
        response = self._download_json(
            'http://qi.ckm.onetapi.pl/', video_id,
            query={
                'body[id]': video_id,
                'body[jsonrpc]': '2.0',
                'body[method]': 'get_asset_detail',
                'body[params][ID_Publikacji]': video_id,
                'body[params][Service]': 'www.onet.pl',
                'content-type': 'application/jsonp',
                'x-onet-app': 'player.front.onetapi.pl',
            })

        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error['message']), expected=True)

        video = response['result'].get('0')

        formats = []
        for _, formats_dict in video['formats'].items():
            if not isinstance(formats_dict, dict):
                continue
            for format_id, format_list in formats_dict.items():
                if not isinstance(format_list, list):
                    continue
                for f in format_list:
                    video_url = f.get('url')
                    if not video_url:
                        continue
                    ext = determine_ext(video_url)
                    if format_id == 'ism':
                        # TODO: Support Microsoft Smooth Streaming
                        continue
                    elif ext == 'mpd':
                        formats.extend(self._extract_mpd_formats(
                            video_url, video_id, mpd_id='dash', fatal=False))
                    else:
                        formats.append({
                            'url': video_url,
                            'format_id': format_id,
                            'height': int_or_none(f.get('vertical_resolution')),
                            'width': int_or_none(f.get('horizontal_resolution')),
                            'abr': float_or_none(f.get('audio_bitrate')),
                            'vbr': float_or_none(f.get('video_bitrate')),
                        })
        self._sort_formats(formats)

        meta = video.get('meta', {})

        title = self._og_search_title(webpage, default=None) or meta['title']
        description = self._og_search_description(webpage, default=None) or meta.get('description')
        duration = meta.get('length') or meta.get('lenght')
        timestamp = parse_iso8601(meta.get('addDate'), ' ')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }


class OnetIE(OnetBaseIE):
    _VALID_URL = r'https?://(?:www\.)?onet\.tv/[a-z]/[a-z]+/(?P<display_id>[0-9a-z-]+)/(?P<id>[0-9a-z]+)'
    IE_NAME = 'onet.tv'

    _TEST = {
        'url': 'http://onet.tv/k/openerfestival/open-er-festival-2016-najdziwniejsze-wymagania-gwiazd/qbpyqc',
        'md5': 'e3ffbf47590032ac3f27249204173d50',
        'info_dict': {
            'id': 'qbpyqc',
            'display_id': 'open-er-festival-2016-najdziwniejsze-wymagania-gwiazd',
            'ext': 'mp4',
            'title': 'Open\'er Festival 2016: najdziwniejsze wymagania gwiazd',
            'description': 'Trzy samochody, których nigdy nie użyto, prywatne spa, hotel dekorowany czarnym suknem czy nielegalne używki. Organizatorzy koncertów i festiwali muszą stawać przed nie lada wyzwaniem zapraszając gwia...',
            'upload_date': '20160705',
            'timestamp': 1467721580,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id, video_id = mobj.group('display_id', 'id')

        webpage = self._download_webpage(url, display_id)

        mvp_id = self._search_mvp_id(webpage)

        info_dict = self._extract_from_id(mvp_id, webpage)
        info_dict.update({
            'id': video_id,
            'display_id': display_id,
        })

        return info_dict


class OnetChannelIE(OnetBaseIE):
    _VALID_URL = r'https?://(?:www\.)?onet\.tv/[a-z]/(?P<id>[a-z]+)(?:[?#]|$)'
    IE_NAME = 'onet.tv:channel'

    _TEST = {
        'url': 'http://onet.tv/k/openerfestival',
        'info_dict': {
            'id': 'openerfestival',
            'title': 'Open\'er Festival Live',
            'description': 'Dziękujemy, że oglądaliście transmisje. Zobaczcie nasze relacje i wywiady z artystami.',
        },
        'playlist_mincount': 46,
    }

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        webpage = self._download_webpage(url, channel_id)

        current_clip_info = self._parse_json(self._search_regex(
            r'var\s+currentClip\s*=\s*({[^}]+})', webpage, 'video info'), channel_id,
            transform_source=lambda s: js_to_json(re.sub(r'\'\s*\+\s*\'', '', s)))
        video_id = remove_start(current_clip_info['ckmId'], 'mvp:')
        video_name = url_basename(current_clip_info['url'])

        if self._downloader.params.get('noplaylist'):
            self.to_screen(
                'Downloading just video %s because of --no-playlist' % video_name)
            return self._extract_from_id(video_id, webpage)

        self.to_screen(
            'Downloading channel %s - add --no-playlist to just download video %s' % (
                channel_id, video_name))
        matches = re.findall(
            r'<a[^>]+href=[\'"](https?://(?:www\.)?onet\.tv/[a-z]/[a-z]+/[0-9a-z-]+/[0-9a-z]+)',
            webpage)
        entries = [
            self.url_result(video_link, OnetIE.ie_key())
            for video_link in matches]

        channel_title = strip_or_none(get_element_by_class('o_channelName', webpage))
        channel_description = strip_or_none(get_element_by_class('o_channelDesc', webpage))
        return self.playlist_result(entries, channel_id, channel_title, channel_description)
