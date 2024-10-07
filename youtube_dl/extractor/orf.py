# coding: utf-8
from __future__ import unicode_literals

import base64
import functools
import re

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    float_or_none,
    int_or_none,
    merge_dicts,
    mimetype2ext,
    parse_age_limit,
    parse_iso8601,
    strip_jsonp,
    txt_or_none,
    unified_strdate,
    update_url_query,
    url_or_none,
)
from ..traversal import T, traverse_obj

k_float_or_none = functools.partial(float_or_none, scale=1000)


class ORFRadioBase(InfoExtractor):
    STATION_INFO = {
        'fm4': ('fm4', 'fm4', 'orffm4'),
        'noe': ('noe', 'oe2n', 'orfnoe'),
        'wien': ('wie', 'oe2w', 'orfwie'),
        'burgenland': ('bgl', 'oe2b', 'orfbgl'),
        'ooe': ('ooe', 'oe2o', 'orfooe'),
        'steiermark': ('stm', 'oe2st', 'orfstm'),
        'kaernten': ('ktn', 'oe2k', 'orfktn'),
        'salzburg': ('sbg', 'oe2s', 'orfsbg'),
        'tirol': ('tir', 'oe2t', 'orftir'),
        'vorarlberg': ('vbg', 'oe2v', 'orfvbg'),
        'oe3': ('oe3', 'oe3', 'orfoe3'),
        'oe1': ('oe1', 'oe1', 'orfoe1'),
    }
    _ID_NAMES = ('id', 'guid', 'program')

    @classmethod
    def _get_item_id(cls, data):
        return traverse_obj(data, *cls._ID_NAMES, expected_type=txt_or_none)

    @classmethod
    def _get_api_payload(cls, data, expected_id, in_payload=False):
        if expected_id not in traverse_obj(data, ('payload',)[:1 if in_payload else 0] + (cls._ID_NAMES, T(txt_or_none))):
            raise ExtractorError('Unexpected API data result', video_id=expected_id)
        return data['payload']

    @staticmethod
    def _extract_podcast_upload(data):
        return traverse_obj(data, {
            'url': ('enclosures', 0, 'url'),
            'ext': ('enclosures', 0, 'type', T(mimetype2ext)),
            'filesize': ('enclosures', 0, 'length', T(int_or_none)),
            'title': ('title', T(txt_or_none)),
            'description': ('description', T(clean_html)),
            'timestamp': (('published', 'postDate'), T(parse_iso8601)),
            'duration': ('duration', T(k_float_or_none)),
            'series': ('podcast', 'title'),
            'uploader': ((('podcast', 'author'), 'station'), T(txt_or_none)),
            'uploader_id': ('podcast', 'channel', T(txt_or_none)),
        }, get_all=False)

    @classmethod
    def _entries(cls, data, station, item_type=None):
        if item_type in ('upload', 'podcast-episode'):
            yield merge_dicts({
                'id': cls._get_item_id(data),
                'ext': 'mp3',
                'vcodec': 'none',
            }, cls._extract_podcast_upload(data), rev=True)
            return

        loop_station = cls.STATION_INFO[station][1]
        for info in traverse_obj(data, ((('streams', Ellipsis), 'stream'), T(lambda v: v if v['loopStreamId'] else None))):
            item_id = info['loopStreamId']
            host = info.get('host') or 'loopstream01.apa.at'
            yield merge_dicts({
                'id': item_id.replace('.mp3', ''),
                'ext': 'mp3',
                'url': update_url_query('https://{0}/'.format(host), {
                    'channel': loop_station,
                    'id': item_id,
                }),
                'vcodec': 'none',
                # '_old_archive_ids': [make_archive_id(old_ie, video_id)],
            }, traverse_obj(data, {
                'title': ('title', T(txt_or_none)),
                'description': ('subtitle', T(clean_html)),
                'uploader': 'station',
                'series': ('programTitle', T(txt_or_none)),
            }), traverse_obj(info, {
                'duration': (('duration',
                              (None, T(lambda x: x['end'] - x['start']))),
                             T(k_float_or_none), any),
                'timestamp': (('start', 'startISO'), T(parse_iso8601), any),
            }))


class ORFRadioIE(ORFRadioBase):
    IE_NAME = 'orf:sound'
    _STATION_RE = '|'.join(map(re.escape, ORFRadioBase.STATION_INFO.keys()))

    _VALID_URL = (
        r'https?://sound\.orf\.at/radio/(?P<station>{0})/sendung/(?P<id>\d+)(?:/(?P<show>\w+))?'.format(_STATION_RE),
        r'https?://(?P<station>{0})\.orf\.at/(?:player|programm)/(?P<date>\d{{8}})/(?P<id>\d+)'.format(_STATION_RE),
    )

    _TESTS = [{
        'url': 'https://sound.orf.at/radio/ooe/sendung/37802/guten-morgen-oberoesterreich-am-feiertag',
        'info_dict': {
            'id': '37802',
            'title': 'Guten Morgen Oberösterreich am Feiertag',
            'description': 'Oberösterreichs meistgehörte regionale Frühsendung.\nRegionale Nachrichten zu jeder halben Stunde.\nModeration: Wolfgang Lehner\nNachrichten:  Stephan Schnabl',
        },
        'playlist': [{
            'md5': 'f9ff8517dd681b642a2c900e2c9e6085',
            'info_dict': {
                'id': '2024-05-30_0559_tl_66_7DaysThu1_443862',
                'ext': 'mp3',
                'title': 'Guten Morgen Oberösterreich am Feiertag',
                'description': 'Oberösterreichs meistgehörte regionale Frühsendung.\nRegionale Nachrichten zu jeder halben Stunde.\nModeration: Wolfgang Lehner\nNachrichten:  Stephan Schnabl',
                'timestamp': 1717041587,
                'upload_date': '20240530',
                'uploader': 'ooe',
                'duration': 14413.0,
            }
        }],
        'skip': 'Shows from ORF Sound are only available for 30 days.'
    }, {
        'url': 'https://oe1.orf.at/player/20240531/758136',
        'md5': '2397717aaf3ae9c22a4f090ee3b8d374',
        'info_dict': {
            'id': '2024-05-31_1905_tl_51_7DaysFri35_2413387',
            'ext': 'mp3',
            'title': '"Who Cares?"',
            'description': 'Europas größte Netzkonferenz re:publica 2024',
            'timestamp': 1717175100,
            'upload_date': '20240531',
            'uploader': 'oe1',
            'duration': 1500,
        },
        'skip': 'Shows from ORF Sound are only available for 30 days.'
    }, {
        # yt-dlp/yt-dlp#11014
        'url': 'https://oe1.orf.at/programm/20240916/769302/Playgrounds',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        m = self._match_valid_url(url)
        station, show_id = m.group('station', 'id')
        api_station, _, _ = self.STATION_INFO[station]
        if 'date' in m.groupdict():
            data = self._download_json(
                'https://audioapi.orf.at/{0}/json/4.0/broadcast/{1}/{2}?_o={3}.orf.at'.format(
                    api_station, show_id, m.group('date'), station), show_id)
            show_id = data['id']
        else:
            data = self._download_json(
                'https://audioapi.orf.at/{0}/api/json/5.0/broadcast/{1}?_o=sound.orf.at'.format(
                    api_station, show_id), show_id)

            data = self._get_api_payload(data, show_id, in_payload=True)

        # site sends ISO8601 GMT date-times with separate TZ offset, ignored
        # TODO: should `..._date` be calculated relative to TZ?

        return merge_dicts(
            {'_type': 'multi_video'},
            self.playlist_result(
                self._entries(data, station), show_id,
                txt_or_none(data.get('title')),
                clean_html(data.get('subtitle'))))


class ORFRadioCollectionIE(ORFRadioBase):
    IE_NAME = 'orf:collection'
    _VALID_URL = r'https?://sound\.orf\.at/collection/(?P<coll_id>\d+)(?:/(?P<item_id>\d+))?'

    _TESTS = [{
        'url': 'https://sound.orf.at/collection/4/61908/was-das-uberschreiten-des-15-limits-bedeutet',
        'info_dict': {
            'id': '2577582',
        },
        'playlist': [{
            'md5': '5789cec7d75575ff58d19c0428c80eb3',
            'info_dict': {
                'id': '2024-06-06_1659_tl_54_7DaysThu6_153926',
                'ext': 'mp3',
                'title': 'Klimakrise: Was das Überschreiten des 1,5°-Limits bedeutet',
                'timestamp': 1717686674,
                'upload_date': '20240606',
                'uploader': 'fm4',
            },
        }],
        'skip': 'Shows from ORF Sound are only available for 30 days.'
    }, {
        # persistent playlist (FM4 Highlights)
        'url': 'https://sound.orf.at/collection/4/',
        'info_dict': {
            'id': '4',
        },
        'playlist_mincount': 10,
        'playlist_maxcount': 13,
    }]

    def _real_extract(self, url):
        coll_id, item_id = self._match_valid_url(url).group('coll_id', 'item_id')
        data = self._download_json(
            'https://collector.orf.at/api/frontend/collections/{0}?_o=sound.orf.at'.format(
                coll_id), coll_id)
        data = self._get_api_payload(data, coll_id, in_payload=True)

        def yield_items():
            for item in traverse_obj(data, (
                    'content', 'items', lambda _, v: any(k in v['target']['params'] for k in self._ID_NAMES))):
                if item_id is None or item_id == txt_or_none(item.get('id')):
                    target = item['target']
                    typed_item_id = self._get_item_id(target['params'])
                    station = target['params'].get('station')
                    item_type = target.get('type')
                    if typed_item_id and (station or item_type):
                        yield station, typed_item_id, item_type
                    if item_id is not None:
                        break
            else:
                if item_id is not None:
                    raise ExtractorError('Item not found in collection',
                                         video_id=coll_id, expected=True)

        def item_playlist(station, typed_item_id, item_type):
            if item_type == 'upload':
                item_data = self._download_json('https://audioapi.orf.at/radiothek/api/2.0/upload/{0}?_o=sound.orf.at'.format(
                    typed_item_id), typed_item_id)
            elif item_type == 'podcast-episode':
                item_data = self._download_json('https://audioapi.orf.at/radiothek/api/2.0/episode/{0}?_o=sound.orf.at'.format(
                    typed_item_id), typed_item_id)
            else:
                api_station, _, _ = self.STATION_INFO[station]
                item_data = self._download_json(
                    'https://audioapi.orf.at/{0}/api/json/5.0/{1}/{2}?_o=sound.orf.at'.format(
                        api_station, item_type or 'broadcastitem', typed_item_id), typed_item_id)

            item_data = self._get_api_payload(item_data, typed_item_id, in_payload=True)

            return merge_dicts(
                {'_type': 'multi_video'},
                self.playlist_result(
                    self._entries(item_data, station, item_type), typed_item_id,
                    txt_or_none(data.get('title')),
                    clean_html(data.get('subtitle'))))

        def yield_item_entries():
            for station, typed_id, item_type in yield_items():
                yield item_playlist(station, typed_id, item_type)

        if item_id is not None:
            # coll_id = '/'.join((coll_id, item_id))
            return next(yield_item_entries())

        return self.playlist_result(yield_item_entries(), coll_id, data.get('title'))


class ORFPodcastIE(ORFRadioBase):
    IE_NAME = 'orf:podcast'
    _STATION_RE = '|'.join(map(re.escape, (x[0] for x in ORFRadioBase.STATION_INFO.values()))) + '|tv'
    _VALID_URL = r'https?://sound\.orf\.at/podcast/(?P<station>{0})/(?P<show>[\w-]+)/(?P<id>[\w-]+)'.format(_STATION_RE)
    _TESTS = [{
        'url': 'https://sound.orf.at/podcast/stm/der-kraeutertipp-von-christine-lackner/rotklee',
        'md5': '1f2bab2ba90c2ce0c2754196ea78b35f',
        'info_dict': {
            'id': 'der-kraeutertipp-von-christine-lackner/rotklee',
            'ext': 'mp3',
            'title': 'Rotklee',
            'description': 'In der Natur weit verbreitet - in der Medizin längst anerkennt: Rotklee. Dieser Podcast begleitet die Sendung "Radio Steiermark am Vormittag", Radio Steiermark, 28. Mai 2024.',
            'timestamp': 1716891761,
            'upload_date': '20240528',
            'uploader_id': 'stm_kraeutertipp',
            'uploader': 'ORF Radio Steiermark',
            'duration': 101,
            'series': 'Der Kräutertipp von Christine Lackner',
        },
        'skip': 'ORF podcasts are only available for a limited time'
    }]

    _ID_NAMES = ('slug', 'guid')

    def _real_extract(self, url):
        station, show, show_id = self._match_valid_url(url).group('station', 'show', 'id')
        data = self._download_json(
            'https://audioapi.orf.at/radiothek/api/2.0/podcast/{0}/{1}/{2}'.format(
                station, show, show_id), show_id)
        data = self._get_api_payload(data, show_id, in_payload=True)

        return merge_dicts({
            'id': '/'.join((show, show_id)),
            'ext': 'mp3',
            'vcodec': 'none',
        }, self._extract_podcast_upload(data), rev=True)


class ORFIPTVBase(InfoExtractor):
    _TITLE_STRIP_RE = ''

    def _extract_video(self, video_id, webpage, fatal=False):

        data = self._download_json(
            'http://bits.orf.at/filehandler/static-api/json/current/data.json?file=%s' % video_id,
            video_id)[0]

        video = traverse_obj(data, (
            'sources', ('default', 'q8c'),
            T(lambda x: x if x['loadBalancerUrl'] else None),
            any))

        load_balancer_url = video['loadBalancerUrl']

        try:
            rendition = self._download_json(
                load_balancer_url, video_id, transform_source=strip_jsonp)
        except ExtractorError:
            rendition = None

        if not rendition:
            rendition = {
                'redirect': {
                    'smil': re.sub(
                        r'(/)jsonp(/.+\.)mp4$', r'\1dash\2smil/manifest.mpd',
                        load_balancer_url),
                },
            }

        f = traverse_obj(video, {
            'abr': ('audioBitrate', T(int_or_none)),
            'vbr': ('bitrate', T(int_or_none)),
            'fps': ('videoFps', T(int_or_none)),
            'width': ('videoWidth', T(int_or_none)),
            'height': ('videoHeight', T(int_or_none)),
        })

        formats = []
        for format_id, format_url in traverse_obj(rendition, (
                'redirect', T(dict.items), Ellipsis)):
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
                    format_url, video_id, 'mp4', m3u8_id=format_id,
                    entry_protocol='m3u8_native'))
            elif determine_ext(format_url) == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id=format_id))

        if formats or fatal:
            self._sort_formats(formats)
        else:
            return

        return merge_dicts({
            'id': video_id,
            'title': re.sub(self._TITLE_STRIP_RE, '', self._og_search_title(webpage)),
            'description': self._og_search_description(webpage),
            'upload_date': unified_strdate(self._html_search_meta(
                'dc.date', webpage, 'upload date', fatal=False)),
            'formats': formats,
        }, traverse_obj(data, {
            'duration': ('duration', T(k_float_or_none)),
            'thumbnail': ('sources', 'default', 'preview', T(url_or_none)),
        }), rev=True)


class ORFIPTVIE(ORFIPTVBase):
    IE_NAME = 'orf:iptv'
    IE_DESC = 'iptv.ORF.at'
    _WORKING = False  # URLs redirect to orf.at/
    _VALID_URL = r'https?://iptv\.orf\.at/(?:#/)?stories/(?P<id>\d+)'
    _TITLE_STRIP_RE = r'\s+-\s+iptv\.ORF\.at\S*$'

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

        return self._extract_video(video_id, webpage)


class ORFFM4StoryIE(ORFIPTVBase):
    IE_NAME = 'orf:fm4:story'
    IE_DESC = 'fm4.orf.at stories'
    _VALID_URL = r'https?://fm4\.orf\.at/stories/(?P<id>\d+)'
    _TITLE_STRIP_RE = r'\s+-\s+fm4\.ORF\.at\s*$'

    _TESTS = [{
        'url': 'https://fm4.orf.at/stories/3041554/',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': '3041554',
            'title': 'Is The EU Green Deal In Mortal Danger?',
        },
        'playlist_count': 4,
        'params': {
            'format': 'bestvideo',
        },
    }, {
        'url': 'http://fm4.orf.at/stories/2865738/',
        'info_dict': {
            'id': '2865738',
            'title': 'Manu Delago und Inner Tongue live',
        },
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
                'title': 'Manu Delago und Inner Tongue https://vod-ww.mdn.ors.at/cms-worldwide_episodes_nas/_definst_/nas/cms-worldwide_episodes/online/14228823_0005.smil/chunklist_b992000_vo.m3u8live (2)',
                'duration': 1504.08,
                'thumbnail': r're:^https?://.*\.jpg$',
                'upload_date': '20170913',
                'description': 'Manu Delago und Inner Tongue haben bei der FM4 Soundpark Session live alles gegeben. Hier gibt es Fotos und die gesamte Session als Video.',
            },
        }],
        'skip': 'Videos gone',
    }]

    def _real_extract(self, url):
        story_id = self._match_id(url)
        webpage = self._download_webpage(url, story_id)

        entries = []
        seen_ids = set()
        for idx, video_id in enumerate(re.findall(r'data-video(?:id)?="(\d+)"', webpage)):
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)
            entry = self._extract_video(video_id, webpage, fatal=False)
            if not entry:
                continue

            if idx >= 1:
                # Titles are duplicates, make them unique
                entry['title'] = '%s (%d)' % (entry['title'], idx)

            entries.append(entry)

        seen_ids = set()
        for yt_id in re.findall(
                r'data-id\s*=\s*["\']([\w-]+)[^>]+\bclass\s*=\s*["\']youtube\b',
                webpage):
            if yt_id in seen_ids:
                continue
            seen_ids.add(yt_id)
            if YoutubeIE.suitable(yt_id):
                entries.append(self.url_result(yt_id, ie='Youtube', video_id=yt_id))

        return self.playlist_result(
            entries, story_id,
            re.sub(self._TITLE_STRIP_RE, '', self._og_search_title(webpage, default='') or None))


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
        'skip': 'Available until 2024-08-12',
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
        'skip': 'Available until 2024-06-14',
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
