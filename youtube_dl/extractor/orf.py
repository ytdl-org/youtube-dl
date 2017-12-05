# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    float_or_none,
    HEADRequest,
    int_or_none,
    orderedSet,
    remove_end,
    strip_jsonp,
    unescapeHTML,
    unified_strdate,
)


class ORFTVthekIE(InfoExtractor):
    IE_NAME = 'orf:tvthek'
    IE_DESC = 'ORF TVthek'
    _VALID_URL = r'https?://tvthek\.orf\.at/(?:[^/]+/)+(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://tvthek.orf.at/program/Aufgetischt/2745173/Aufgetischt-Mit-der-Steirischen-Tafelrunde/8891389',
        'playlist': [{
            'md5': '2942210346ed779588f428a92db88712',
            'info_dict': {
                'id': '8896777',
                'ext': 'mp4',
                'title': 'Aufgetischt: Mit der Steirischen Tafelrunde',
                'description': 'md5:c1272f0245537812d4e36419c207b67d',
                'duration': 2668,
                'upload_date': '20141208',
            },
        }],
        'skip': 'Blocked outside of Austria / Germany',
    }, {
        'url': 'http://tvthek.orf.at/topic/Im-Wandel-der-Zeit/8002126/Best-of-Ingrid-Thurnher/7982256',
        'info_dict': {
            'id': '7982259',
            'ext': 'mp4',
            'title': 'Best of Ingrid Thurnher',
            'upload_date': '20140527',
            'description': 'Viele Jahre war Ingrid Thurnher das "Gesicht" der ZIB 2. Vor ihrem Wechsel zur ZIB 2 im Jahr 1995 moderierte sie unter anderem "Land und Leute", "Österreich-Bild" und "Niederösterreich heute".',
        },
        'params': {
            'skip_download': True,  # rtsp downloads
        },
        'skip': 'Blocked outside of Austria / Germany',
    }, {
        'url': 'http://tvthek.orf.at/topic/Fluechtlingskrise/10463081/Heimat-Fremde-Heimat/13879132/Senioren-betreuen-Migrantenkinder/13879141',
        'only_matching': True,
    }, {
        'url': 'http://tvthek.orf.at/profile/Universum/35429',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        data_jsb = self._parse_json(
            self._search_regex(
                r'<div[^>]+class=(["\']).*?VideoPlaylist.*?\1[^>]+data-jsb=(["\'])(?P<json>.+?)\2',
                webpage, 'playlist', group='json'),
            playlist_id, transform_source=unescapeHTML)['playlist']['videos']

        def quality_to_int(s):
            m = re.search('([0-9]+)', s)
            if m is None:
                return -1
            return int(m.group(1))

        entries = []
        for sd in data_jsb:
            video_id, title = sd.get('id'), sd.get('title')
            if not video_id or not title:
                continue
            video_id = compat_str(video_id)
            formats = [{
                'preference': -10 if fd['delivery'] == 'hls' else None,
                'format_id': '%s-%s-%s' % (
                    fd['delivery'], fd['quality'], fd['quality_string']),
                'url': fd['src'],
                'protocol': fd['protocol'],
                'quality': quality_to_int(fd['quality']),
            } for fd in sd['sources']]

            # Check for geoblocking.
            # There is a property is_geoprotection, but that's always false
            geo_str = sd.get('geoprotection_string')
            if geo_str:
                try:
                    http_url = next(
                        f['url']
                        for f in formats
                        if re.match(r'^https?://.*\.mp4$', f['url']))
                except StopIteration:
                    pass
                else:
                    req = HEADRequest(http_url)
                    self._request_webpage(
                        req, video_id,
                        note='Testing for geoblocking',
                        errnote=((
                            'This video seems to be blocked outside of %s. '
                            'You may want to try the streaming-* formats.')
                            % geo_str),
                        fatal=False)

            self._check_formats(formats, video_id)
            self._sort_formats(formats)

            subtitles = {}
            for sub in sd.get('subtitles', []):
                sub_src = sub.get('src')
                if not sub_src:
                    continue
                subtitles.setdefault(sub.get('lang', 'de-AT'), []).append({
                    'url': sub_src,
                })

            upload_date = unified_strdate(sd.get('created_date'))
            entries.append({
                '_type': 'video',
                'id': video_id,
                'title': title,
                'formats': formats,
                'subtitles': subtitles,
                'description': sd.get('description'),
                'duration': int_or_none(sd.get('duration_in_seconds')),
                'upload_date': upload_date,
                'thumbnail': sd.get('image_full_url'),
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': playlist_id,
        }


class ORFRadioIE(InfoExtractor):
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        station = mobj.group('station')
        show_date = mobj.group('date')
        show_id = mobj.group('show')

        if station == 'fm4':
            show_id = '4%s' % show_id

        data = self._download_json(
            'http://audioapi.orf.at/%s/api/json/current/broadcast/%s/%s' % (station, show_id, show_date),
            show_id
        )

        def extract_entry_dict(info, title, subtitle):
            return {
                'id': info['loopStreamId'].replace('.mp3', ''),
                'url': 'http://loopstream01.apa.at/?channel=%s&id=%s' % (station, info['loopStreamId']),
                'title': title,
                'description': subtitle,
                'duration': (info['end'] - info['start']) / 1000,
                'timestamp': info['start'] / 1000,
                'ext': 'mp3'
            }

        entries = [extract_entry_dict(t, data['title'], data['subtitle']) for t in data['streams']]

        return {
            '_type': 'playlist',
            'id': show_id,
            'title': data['title'],
            'description': data['subtitle'],
            'entries': entries
        }


class ORFFM4IE(ORFRadioIE):
    IE_NAME = 'orf:fm4'
    IE_DESC = 'radio FM4'
    _VALID_URL = r'https?://(?P<station>fm4)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'

    _TEST = {
        'url': 'http://fm4.orf.at/player/20170107/CC',
        'md5': '2b0be47375432a7ef104453432a19212',
        'info_dict': {
            'id': '2017-01-07_2100_tl_54_7DaysSat18_31295',
            'ext': 'mp3',
            'title': 'Solid Steel Radioshow',
            'description': 'Die Mixshow von Coldcut und Ninja Tune.',
            'duration': 3599,
            'timestamp': 1483819257,
            'upload_date': '20170107',
        },
        'skip': 'Shows from ORF radios are only available for 7 days.'
    }


class ORFOE1IE(ORFRadioIE):
    IE_NAME = 'orf:oe1'
    IE_DESC = 'Radio Österreich 1'
    _VALID_URL = r'https?://(?P<station>oe1)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'

    _TEST = {
        'url': 'http://oe1.orf.at/player/20170108/456544',
        'md5': '34d8a6e67ea888293741c86a099b745b',
        'info_dict': {
            'id': '2017-01-08_0759_tl_51_7DaysSun6_256141',
            'ext': 'mp3',
            'title': 'Morgenjournal',
            'duration': 609,
            'timestamp': 1483858796,
            'upload_date': '20170108',
        },
        'skip': 'Shows from ORF radios are only available for 7 days.'
    }


class ORFIPTVIE(InfoExtractor):
    IE_NAME = 'orf:iptv'
    IE_DESC = 'iptv.ORF.at'
    _VALID_URL = r'https?://iptv\.orf\.at/(?:#/)?stories/(?P<id>\d+)'

    _TEST = {
        'url': 'http://iptv.orf.at/stories/2275236/',
        'md5': 'c8b22af4718a4b4af58342529453e3e5',
        'info_dict': {
            'id': '350612',
            'ext': 'flv',
            'title': 'Weitere Evakuierungen um Vulkan Calbuco',
            'description': 'md5:d689c959bdbcf04efeddedbf2299d633',
            'duration': 68.197,
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20150425',
        },
    }

    def _real_extract(self, url):
        story_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://iptv.orf.at/stories/%s' % story_id, story_id)

        video_id = self._search_regex(
            r'data-video(?:id)?="(\d+)"', webpage, 'video id')

        data = self._download_json(
            'http://bits.orf.at/filehandler/static-api/json/current/data.json?file=%s' % video_id,
            video_id)[0]

        duration = float_or_none(data['duration'], 1000)

        video = data['sources']['default']
        load_balancer_url = video['loadBalancerUrl']
        abr = int_or_none(video.get('audioBitrate'))
        vbr = int_or_none(video.get('bitrate'))
        fps = int_or_none(video.get('videoFps'))
        width = int_or_none(video.get('videoWidth'))
        height = int_or_none(video.get('videoHeight'))
        thumbnail = video.get('preview')

        rendition = self._download_json(
            load_balancer_url, video_id, transform_source=strip_jsonp)

        f = {
            'abr': abr,
            'vbr': vbr,
            'fps': fps,
            'width': width,
            'height': height,
        }

        formats = []
        for format_id, format_url in rendition['redirect'].items():
            if format_id == 'rtmp':
                ff = f.copy()
                ff.update({
                    'url': format_url,
                    'format_id': format_id,
                })
                formats.append(ff)
            elif determine_ext(format_url) == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    format_url, video_id, f4m_id=format_id))
            elif determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', m3u8_id=format_id))
            else:
                continue
        self._sort_formats(formats)

        title = remove_end(self._og_search_title(webpage), ' - iptv.ORF.at')
        description = self._og_search_description(webpage)
        upload_date = unified_strdate(self._html_search_meta(
            'dc.date', webpage, 'upload date'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'formats': formats,
        }


class ORFFM4StoryIE(InfoExtractor):
    IE_NAME = 'orf:fm4:story'
    IE_DESC = 'fm4.orf.at stories'
    _VALID_URL = r'https?://fm4\.orf\.at/stories/(?P<id>\d+)'

    _TEST = {
        'url': 'http://fm4.orf.at/stories/2865738/',
        'playlist': [{
            'md5': 'e1c2c706c45c7b34cf478bbf409907ca',
            'info_dict': {
                'id': '547792',
                'ext': 'flv',
                'title': 'Manu Delago und Inner Tongue live',
                'description': 'Manu Delago und Inner Tongue haben bei der FM4 Soundpark Session live alles gegeben. Hier gibt es Fotos und die gesamte Session als Video.',
                'duration': 1748.52,
                'thumbnail': r're:^https?://.*\.jpg$',
                'upload_date': '20170913',
            },
        }, {
            'md5': 'c6dd2179731f86f4f55a7b49899d515f',
            'info_dict': {
                'id': '547798',
                'ext': 'flv',
                'title': 'Manu Delago und Inner Tongue live (2)',
                'duration': 1504.08,
                'thumbnail': r're:^https?://.*\.jpg$',
                'upload_date': '20170913',
                'description': 'Manu Delago und Inner Tongue haben bei der FM4 Soundpark Session live alles gegeben. Hier gibt es Fotos und die gesamte Session als Video.',
            },
        }],
    }

    def _real_extract(self, url):
        story_id = self._match_id(url)
        webpage = self._download_webpage(url, story_id)

        entries = []
        all_ids = orderedSet(re.findall(r'data-video(?:id)?="(\d+)"', webpage))
        for idx, video_id in enumerate(all_ids):
            data = self._download_json(
                'http://bits.orf.at/filehandler/static-api/json/current/data.json?file=%s' % video_id,
                video_id)[0]

            duration = float_or_none(data['duration'], 1000)

            video = data['sources']['q8c']
            load_balancer_url = video['loadBalancerUrl']
            abr = int_or_none(video.get('audioBitrate'))
            vbr = int_or_none(video.get('bitrate'))
            fps = int_or_none(video.get('videoFps'))
            width = int_or_none(video.get('videoWidth'))
            height = int_or_none(video.get('videoHeight'))
            thumbnail = video.get('preview')

            rendition = self._download_json(
                load_balancer_url, video_id, transform_source=strip_jsonp)

            f = {
                'abr': abr,
                'vbr': vbr,
                'fps': fps,
                'width': width,
                'height': height,
            }

            formats = []
            for format_id, format_url in rendition['redirect'].items():
                if format_id == 'rtmp':
                    ff = f.copy()
                    ff.update({
                        'url': format_url,
                        'format_id': format_id,
                    })
                    formats.append(ff)
                elif determine_ext(format_url) == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        format_url, video_id, f4m_id=format_id))
                elif determine_ext(format_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4', m3u8_id=format_id))
                else:
                    continue
            self._sort_formats(formats)

            title = remove_end(self._og_search_title(webpage), ' - fm4.ORF.at')
            if idx >= 1:
                # Titles are duplicates, make them unique
                title += ' (' + str(idx + 1) + ')'
            description = self._og_search_description(webpage)
            upload_date = unified_strdate(self._html_search_meta(
                'dc.date', webpage, 'upload date'))

            entries.append({
                'id': video_id,
                'title': title,
                'description': description,
                'duration': duration,
                'thumbnail': thumbnail,
                'upload_date': upload_date,
                'formats': formats,
            })

        return self.playlist_result(entries)
