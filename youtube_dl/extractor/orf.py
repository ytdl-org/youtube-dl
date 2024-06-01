# coding: utf-8
from __future__ import unicode_literals

import base64
import functools
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    float_or_none,
    int_or_none,
    merge_dicts,
    orderedSet,
    parse_age_limit,
    parse_iso8601,
    remove_end,
    str_or_none,
    strip_jsonp,
    txt_or_none,
    unified_strdate,
    url_or_none,
)
from ..traversal import T, traverse_obj

k_float_or_none = functools.partial(float_or_none, scale=1000)


class ORFRadioIE(InfoExtractor):
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_date = mobj.group('date')
        show_id = mobj.group('show')

        data = self._download_json(
            'http://audioapi.orf.at/%s/api/json/current/broadcast/%s/%s'
            % (self._API_STATION, show_id, show_date), show_id)

        entries = []
        for info in data['streams']:
            loop_stream_id = str_or_none(info.get('loopStreamId'))
            if not loop_stream_id:
                continue
            title = str_or_none(data.get('title'))
            if not title:
                continue
            start = int_or_none(info.get('start'), scale=1000)
            end = int_or_none(info.get('end'), scale=1000)
            duration = end - start if end and start else None
            entries.append({
                'id': loop_stream_id.replace('.mp3', ''),
                'url': 'https://loopstream01.apa.at/?channel=%s&id=%s' % (self._LOOP_STATION, loop_stream_id),
                'title': title,
                'description': clean_html(data.get('subtitle')),
                'duration': duration,
                'timestamp': start,
                'ext': 'mp3',
                'series': data.get('programTitle'),
            })

        return {
            '_type': 'playlist',
            'id': show_id,
            'title': data.get('title'),
            'description': clean_html(data.get('subtitle')),
            'entries': entries,
        }


class ORFFM4IE(ORFRadioIE):
    IE_NAME = 'orf:fm4'
    IE_DESC = 'radio FM4'
    _VALID_URL = r'https?://(?P<station>fm4)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>4\w+)'
    _API_STATION = 'fm4'
    _LOOP_STATION = 'fm4'

    _TEST = {
        'url': 'http://fm4.orf.at/player/20170107/4CC',
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
        'skip': 'Shows from ORF radios are only available for 7 days.',
        'only_matching': True,
    }


class ORFNOEIE(ORFRadioIE):
    IE_NAME = 'orf:noe'
    IE_DESC = 'Radio Niederösterreich'
    _VALID_URL = r'https?://(?P<station>noe)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'noe'
    _LOOP_STATION = 'oe2n'

    _TEST = {
        'url': 'https://noe.orf.at/player/20200423/NGM',
        'only_matching': True,
    }


class ORFWIEIE(ORFRadioIE):
    IE_NAME = 'orf:wien'
    IE_DESC = 'Radio Wien'
    _VALID_URL = r'https?://(?P<station>wien)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'wie'
    _LOOP_STATION = 'oe2w'

    _TEST = {
        'url': 'https://wien.orf.at/player/20200423/WGUM',
        'only_matching': True,
    }


class ORFBGLIE(ORFRadioIE):
    IE_NAME = 'orf:burgenland'
    IE_DESC = 'Radio Burgenland'
    _VALID_URL = r'https?://(?P<station>burgenland)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'bgl'
    _LOOP_STATION = 'oe2b'

    _TEST = {
        'url': 'https://burgenland.orf.at/player/20200423/BGM',
        'only_matching': True,
    }


class ORFOOEIE(ORFRadioIE):
    IE_NAME = 'orf:oberoesterreich'
    IE_DESC = 'Radio Oberösterreich'
    _VALID_URL = r'https?://(?P<station>ooe)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'ooe'
    _LOOP_STATION = 'oe2o'

    _TEST = {
        'url': 'https://ooe.orf.at/player/20200423/OGMO',
        'only_matching': True,
    }


class ORFSTMIE(ORFRadioIE):
    IE_NAME = 'orf:steiermark'
    IE_DESC = 'Radio Steiermark'
    _VALID_URL = r'https?://(?P<station>steiermark)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'stm'
    _LOOP_STATION = 'oe2st'

    _TEST = {
        'url': 'https://steiermark.orf.at/player/20200423/STGMS',
        'only_matching': True,
    }


class ORFKTNIE(ORFRadioIE):
    IE_NAME = 'orf:kaernten'
    IE_DESC = 'Radio Kärnten'
    _VALID_URL = r'https?://(?P<station>kaernten)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'ktn'
    _LOOP_STATION = 'oe2k'

    _TEST = {
        'url': 'https://kaernten.orf.at/player/20200423/KGUMO',
        'only_matching': True,
    }


class ORFSBGIE(ORFRadioIE):
    IE_NAME = 'orf:salzburg'
    IE_DESC = 'Radio Salzburg'
    _VALID_URL = r'https?://(?P<station>salzburg)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'sbg'
    _LOOP_STATION = 'oe2s'

    _TEST = {
        'url': 'https://salzburg.orf.at/player/20200423/SGUM',
        'only_matching': True,
    }


class ORFTIRIE(ORFRadioIE):
    IE_NAME = 'orf:tirol'
    IE_DESC = 'Radio Tirol'
    _VALID_URL = r'https?://(?P<station>tirol)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'tir'
    _LOOP_STATION = 'oe2t'

    _TEST = {
        'url': 'https://tirol.orf.at/player/20200423/TGUMO',
        'only_matching': True,
    }


class ORFVBGIE(ORFRadioIE):
    IE_NAME = 'orf:vorarlberg'
    IE_DESC = 'Radio Vorarlberg'
    _VALID_URL = r'https?://(?P<station>vorarlberg)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'vbg'
    _LOOP_STATION = 'oe2v'

    _TEST = {
        'url': 'https://vorarlberg.orf.at/player/20200423/VGUM',
        'only_matching': True,
    }


class ORFOE3IE(ORFRadioIE):
    IE_NAME = 'orf:oe3'
    IE_DESC = 'Radio Österreich 3'
    _VALID_URL = r'https?://(?P<station>oe3)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'oe3'
    _LOOP_STATION = 'oe3'

    _TEST = {
        'url': 'https://oe3.orf.at/player/20200424/3WEK',
        'only_matching': True,
    }


class ORFOE1IE(ORFRadioIE):
    IE_NAME = 'orf:oe1'
    IE_DESC = 'Radio Österreich 1'
    _VALID_URL = r'https?://(?P<station>oe1)\.orf\.at/player/(?P<date>[0-9]+)/(?P<show>\w+)'
    _API_STATION = 'oe1'
    _LOOP_STATION = 'oe1'

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
    _WORKING = False  # URLs redirect to orf.at/
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


class ORFONBase(InfoExtractor):
    _ENC_PFX = '3dSlfek03nsLKdj4Jsd'
    _API_PATH = 'episode'

    def _call_api(self, video_id, **kwargs):
        encrypted_id = base64.b64encode('{0}{1}'.format(
            self._ENC_PFX, video_id).encode('utf-8')).decode('ascii')
        return self._download_json(
            'https://api-tvthek.orf.at/api/v4.3/public/{0}/encrypted/{1}'.format(
                self._API_PATH, encrypted_id),
            video_id, **kwargs)

    @classmethod
    def _parse_metadata(cls, api_json):
        return traverse_obj(api_json, {
            'id': ('id', T(int), T(txt_or_none)),
            'age_limit': ('age_classification', T(parse_age_limit)),
            'duration': ((('exact_duration', T(k_float_or_none)),
                          ('duration_second', T(float_or_none))),),
            'title': (('title', 'headline'), T(txt_or_none)),
            'description': (('description', 'teaser_text'), T(txt_or_none)),
            # 'media_type': ('video_type', T(txt_or_none)),
            'thumbnail': ('_embedded', 'image', 'public_urls', 'highlight_teaser', 'url', T(url_or_none)),
            'timestamp': (('date', 'episode_date'), T(parse_iso8601)),
            'release_timestamp': ('release_date', T(parse_iso8601)),
            # 'modified_timestamp': ('updated_at', T(parse_iso8601)),
        }, get_all=False)

    def _extract_video(self, video_id, segment_id):
        # Not a segmented episode: return single video
        # Segmented episode without valid segment id: return entire playlist
        # Segmented episode with valid segment id and yes-playlist: return entire playlist
        # Segmented episode with valid segment id and no-playlist: return single video corresponding to segment id
        # If a multi_video playlist would be returned, but an unsegmented source exists, that source is chosen instead.

        api_json = self._call_api(video_id)

        if traverse_obj(api_json, 'is_drm_protected'):
            self.report_drm(video_id)

        # updates formats, subtitles
        def extract_sources(src_json, video_id):
            for manifest_type in traverse_obj(src_json, ('sources', T(dict.keys), Ellipsis)):
                for manifest_url in traverse_obj(src_json, ('sources', manifest_type, Ellipsis, 'src', T(url_or_none))):
                    if manifest_type == 'hls':
                        fmts, subs = self._extract_m3u8_formats(
                            manifest_url, video_id, fatal=False, m3u8_id='hls',
                            ext='mp4', entry_protocol='m3u8_native'), {}
                        for f in fmts:
                            if '_vo.' in f['url']:
                                f['acodec'] = 'none'
                    elif manifest_type == 'dash':
                        fmts, subs = self._extract_mpd_formats_and_subtitles(
                            manifest_url, video_id, fatal=False, mpd_id='dash')
                    else:
                        continue
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)

        formats, subtitles = [], {}
        if segment_id is None:
            extract_sources(api_json, video_id)
        if not formats:
            segments = traverse_obj(api_json, (
                '_embedded', 'segments', lambda _, v: v['id']))
            if len(segments) > 1 and segment_id is not None:
                if not self._yes_playlist(video_id, segment_id, playlist_label='collection', video_label='segment'):
                    segments = [next(s for s in segments if txt_or_none(s['id']) == segment_id)]

            entries = []
            for seg in segments:
                formats, subtitles = [], {}
                extract_sources(seg, segment_id)
                self._sort_formats(formats)
                entries.append(merge_dicts({
                    'formats': formats,
                    'subtitles': subtitles,
                }, self._parse_metadata(seg), rev=True))
            result = merge_dicts(
                {'_type': 'multi_video' if len(entries) > 1 else 'playlist'},
                self._parse_metadata(api_json),
                self.playlist_result(entries, video_id))
            # not yet processed in core for playlist/multi
            self._downloader._fill_common_fields(result)
            return result
        else:
            self._sort_formats(formats)

        for sub_url in traverse_obj(api_json, (
                '_embedded', 'subtitle',
                ('xml_url', 'sami_url', 'stl_url', 'ttml_url', 'srt_url', 'vtt_url'),
                T(url_or_none))):
            self._merge_subtitles({'de': [{'url': sub_url}]}, target=subtitles)

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            # '_old_archive_ids': [self._downloader._make_archive_id({'ie_key': 'ORFTVthek', 'id': video_id})],
        }, self._parse_metadata(api_json), rev=True)

    def _real_extract(self, url):
        video_id, segment_id = self._match_valid_url(url).group('id', 'segment')
        webpage = self._download_webpage(url, video_id)

        # ORF doesn't like 410 or 404
        if self._search_regex(r'<div\b[^>]*>\s*(Nicht mehr verfügbar)\s*</div>', webpage, 'Availability', default=False):
            raise ExtractorError('Content is no longer available', expected=True, video_id=video_id)

        return merge_dicts({
            'id': video_id,
            'title': self._html_search_meta(['og:title', 'twitter:title'], webpage, default=None),
            'description': self._html_search_meta(
                ['description', 'og:description', 'twitter:description'], webpage, default=None),
        }, self._search_json_ld(webpage, video_id, default={}),
            self._extract_video(video_id, segment_id),
            rev=True)


class ORFONIE(ORFONBase):
    IE_NAME = 'orf:on'
    _VALID_URL = r'https?://on\.orf\.at/video/(?P<id>\d+)(?:/(?P<segment>\d+))?'
    _TESTS = [{
        'url': 'https://on.orf.at/video/14210000/school-of-champions-48',
        'info_dict': {
            'id': '14210000',
            'ext': 'mp4',
            'duration': 2651.08,
            'thumbnail': 'https://api-tvthek.orf.at/assets/segments/0167/98/thumb_16697671_segments_highlight_teaser.jpeg',
            'title': 'School of Champions (4/8)',
            'description': r're:(?s)Luca hat sein ganzes Leben in den Bergen Südtirols verbracht und ist bei seiner Mutter aufgewachsen, .{1029} Leo$',
            # 'media_type': 'episode',
            'timestamp': 1706558922,
            'upload_date': '20240129',
            'release_timestamp': 1706472362,
            'release_date': '20240128',
            # 'modified_timestamp': 1712756663,
            # 'modified_date': '20240410',
            # '_old_archive_ids': ['orftvthek 14210000'],
        },
        'params': {
            'format': 'bestvideo',
        },
    }, {
        'url': 'https://on.orf.at/video/3220355',
        'md5': '925a93b2b9a37da5c9b979d7cf71aa2e',
        'info_dict': {
            'id': '3220355',
            'ext': 'mp4',
            'duration': 445.04,
            'thumbnail': 'https://api-tvthek.orf.at/assets/segments/0002/60/thumb_159573_segments_highlight_teaser.png',
            'title': '50 Jahre Burgenland: Der Festumzug',
            'description': r're:(?s)Aus allen Landesteilen zogen festlich geschmückte Wagen und Musikkapellen .{270} Jenakowitsch$',
            # 'media_type': 'episode',
            'timestamp': 52916400,
            'upload_date': '19710905',
            'release_timestamp': 52916400,
            'release_date': '19710905',
            # 'modified_timestamp': 1498536049,
            # 'modified_date': '20170627',
            # '_old_archive_ids': ['orftvthek 3220355'],
        },
    }, {
        # Video with multiple segments selecting the second segment
        'url': 'https://on.orf.at/video/14226549/15639808/jugendbande-einbrueche-aus-langeweile',
        'md5': 'fc151bba8c05ea77ab5693617e4a33d3',
        'info_dict': {
            'id': '15639808',
            'ext': 'mp4',
            'duration': 97.707,
            'thumbnail': 'https://api-tvthek.orf.at/assets/segments/0175/43/thumb_17442704_segments_highlight_teaser.jpg',
            'title': 'Jugendbande: Einbrüche aus Langeweile',
            'description': r're:Jugendbande: Einbrüche aus Langeweile \| Neuer Kinder- und .{259} Wanda$',
            # 'media_type': 'segment',
            'timestamp': 1715792400,
            'upload_date': '20240515',
            # 'modified_timestamp': 1715794394,
            # 'modified_date': '20240515',
            # '_old_archive_ids': ['orftvthek 15639808'],
        },
        'params': {
            'noplaylist': True,
            'format': 'bestvideo',
        },
    }, {
        # Video with multiple segments and no combined version
        'url': 'https://on.orf.at/video/14227864/formel-1-grosser-preis-von-monaco-2024',
        'info_dict': {
            '_type': 'multi_video',
            'id': '14227864',
            'duration': 18410.52,
            'thumbnail': 'https://api-tvthek.orf.at/assets/segments/0176/04/thumb_17503881_segments_highlight_teaser.jpg',
            'title': 'Formel 1: Großer Preis von Monaco 2024',
            'description': 'md5:aeeb010710ccf70ce28ccb4482243d4f',
            # 'media_type': 'episode',
            'timestamp': 1716721200,
            'upload_date': '20240526',
            'release_timestamp': 1716721802,
            'release_date': '20240526',
            # 'modified_timestamp': 1716884702,
            # 'modified_date': '20240528',
        },
        'playlist_count': 42,
        'skip': 'Gone: Nicht mehr verfügbar',
    }, {
        # Video with multiple segments, but with combined version
        'url': 'https://on.orf.at/video/14228172',
        'info_dict': {
            'id': '14228172',
            'ext': 'mp4',
            'duration': 3294.878,
            'thumbnail': 'https://api-tvthek.orf.at/assets/segments/0176/29/thumb_17528242_segments_highlight_teaser.jpg',
            'title': 'Willkommen Österreich mit Stermann & Grissemann',
            'description': r're:Zum Saisonfinale freuen sich die urlaubsreifen Gastgeber Stermann und .{1863} Geschichten\.$',
            # 'media_type': 'episode',
            'timestamp': 1716926584,
            'upload_date': '20240528',
            'release_timestamp': 1716919202,
            'release_date': '20240528',
            # 'modified_timestamp': 1716968045,
            # 'modified_date': '20240529',
            # '_old_archive_ids': ['orftvthek 14228172'],
        },
        'params': {
            'format': 'bestvideo',
        },
        'skip': 'Gone: Nicht mehr verfügbar',
    }]


class ORFONLiveIE(ORFONBase):
    _ENC_PFX = '8876324jshjd7293ktd'
    _API_PATH = 'livestream'
    _VALID_URL = r'https?://on\.orf\.at/livestream/(?P<id>\d+)(?:/(?P<segment>\d+))?'
    _TESTS = [{
        'url': 'https://on.orf.at/livestream/14320204/pressekonferenz-neos-zu-aktuellen-entwicklungen',
        'info_dict': {
            'id': '14320204',
            'ext': 'mp4',
            'title': 'Pressekonferenz: Neos zu aktuellen Entwicklungen',
            'description': r're:(?s)Neos-Chefin Beate Meinl-Reisinger informi.{598}ng\."',
            'timestamp': 1716886335,
            'upload_date': '20240528',
            # 'modified_timestamp': 1712756663,
            # 'modified_date': '20240410',
            # '_old_archive_ids': ['orftvthek 14210000'],
        },
        'params': {
            'format': 'bestvideo',
        },
    }]

    @classmethod
    def _parse_metadata(cls, api_json):
        return merge_dicts(
            super(ORFONLiveIE, cls)._parse_metadata(api_json),
            traverse_obj(api_json, {
                'timestamp': ('updated_at', T(parse_iso8601)),
                'release_timestamp': ('start', T(parse_iso8601)),
                'is_live': True,
            }))
