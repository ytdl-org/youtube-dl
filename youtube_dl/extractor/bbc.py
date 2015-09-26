# coding: utf-8
from __future__ import unicode_literals

import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_duration,
    parse_iso8601,
)
from ..compat import compat_HTTPError


class BBCCoUkIE(InfoExtractor):
    IE_NAME = 'bbc.co.uk'
    IE_DESC = 'BBC iPlayer'
    _VALID_URL = r'https?://(?:www\.)?bbc\.co\.uk/(?:(?:(?:programmes|iplayer(?:/[^/]+)?/(?:episode|playlist))/)|music/clips[/#])(?P<id>[\da-z]{8})'

    _MEDIASELECTOR_URLS = [
        # Provides HQ HLS streams with even better quality that pc mediaset but fails
        # with geolocation in some cases when it's even not geo restricted at all (e.g.
        # http://www.bbc.co.uk/programmes/b06bp7lf)
        'http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s',
        'http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/%s',
    ]

    _TESTS = [
        {
            'url': 'http://www.bbc.co.uk/programmes/b039g8p7',
            'info_dict': {
                'id': 'b039d07m',
                'ext': 'flv',
                'title': 'Kaleidoscope, Leonard Cohen',
                'description': 'The Canadian poet and songwriter reflects on his musical career.',
                'duration': 1740,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            }
        },
        {
            'url': 'http://www.bbc.co.uk/iplayer/episode/b00yng5w/The_Man_in_Black_Series_3_The_Printed_Name/',
            'info_dict': {
                'id': 'b00yng1d',
                'ext': 'flv',
                'title': 'The Man in Black: Series 3: The Printed Name',
                'description': "Mark Gatiss introduces Nicholas Pierpan's chilling tale of a writer's devilish pact with a mysterious man. Stars Ewan Bailey.",
                'duration': 1800,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
            'skip': 'Episode is no longer available on BBC iPlayer Radio',
        },
        {
            'url': 'http://www.bbc.co.uk/iplayer/episode/b03vhd1f/The_Voice_UK_Series_3_Blind_Auditions_5/',
            'info_dict': {
                'id': 'b00yng1d',
                'ext': 'flv',
                'title': 'The Voice UK: Series 3: Blind Auditions 5',
                'description': "Emma Willis and Marvin Humes present the fifth set of blind auditions in the singing competition, as the coaches continue to build their teams based on voice alone.",
                'duration': 5100,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
            'skip': 'Currently BBC iPlayer TV programmes are available to play in the UK only',
        },
        {
            'url': 'http://www.bbc.co.uk/iplayer/episode/p026c7jt/tomorrows-worlds-the-unearthly-history-of-science-fiction-2-invasion',
            'info_dict': {
                'id': 'b03k3pb7',
                'ext': 'flv',
                'title': "Tomorrow's Worlds: The Unearthly History of Science Fiction",
                'description': '2. Invasion',
                'duration': 3600,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
            'skip': 'Currently BBC iPlayer TV programmes are available to play in the UK only',
        }, {
            'url': 'http://www.bbc.co.uk/programmes/b04v20dw',
            'info_dict': {
                'id': 'b04v209v',
                'ext': 'flv',
                'title': 'Pete Tong, The Essential New Tune Special',
                'description': "Pete has a very special mix - all of 2014's Essential New Tunes!",
                'duration': 10800,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            }
        }, {
            'url': 'http://www.bbc.co.uk/music/clips/p02frcc3',
            'note': 'Audio',
            'info_dict': {
                'id': 'p02frcch',
                'ext': 'flv',
                'title': 'Pete Tong, Past, Present and Future Special, Madeon - After Hours mix',
                'description': 'French house superstar Madeon takes us out of the club and onto the after party.',
                'duration': 3507,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            }
        }, {
            'url': 'http://www.bbc.co.uk/music/clips/p025c0zz',
            'note': 'Video',
            'info_dict': {
                'id': 'p025c103',
                'ext': 'flv',
                'title': 'Reading and Leeds Festival, 2014, Rae Morris - Closer (Live on BBC Three)',
                'description': 'Rae Morris performs Closer for BBC Three at Reading 2014',
                'duration': 226,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            }
        }, {
            'url': 'http://www.bbc.co.uk/iplayer/episode/b054fn09/ad/natural-world-20152016-2-super-powered-owls',
            'info_dict': {
                'id': 'p02n76xf',
                'ext': 'flv',
                'title': 'Natural World, 2015-2016: 2. Super Powered Owls',
                'description': 'md5:e4db5c937d0e95a7c6b5e654d429183d',
                'duration': 3540,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
            'skip': 'geolocation',
        }, {
            'url': 'http://www.bbc.co.uk/iplayer/episode/b05zmgwn/royal-academy-summer-exhibition',
            'info_dict': {
                'id': 'b05zmgw1',
                'ext': 'flv',
                'description': 'Kirsty Wark and Morgan Quaintance visit the Royal Academy as it prepares for its annual artistic extravaganza, meeting people who have come together to make the show unique.',
                'title': 'Royal Academy Summer Exhibition',
                'duration': 3540,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
            'skip': 'geolocation',
        }, {
            # iptv-all mediaset fails with geolocation however there is no geo restriction
            # for this programme at all
            'url': 'http://www.bbc.co.uk/programmes/b06bp7lf',
            'info_dict': {
                'id': 'b06bp7kf',
                'ext': 'flv',
                'title': "Annie Mac's Friday Night, B.Traits sits in for Annie",
                'description': 'B.Traits sits in for Annie Mac with a Mini-Mix from Disclosure.',
                'duration': 10800,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        }, {
            'url': 'http://www.bbc.co.uk/iplayer/playlist/p01dvks4',
            'only_matching': True,
        }, {
            'url': 'http://www.bbc.co.uk/music/clips#p02frcc3',
            'only_matching': True,
        }, {
            'url': 'http://www.bbc.co.uk/iplayer/cbeebies/episode/b0480276/bing-14-atchoo',
            'only_matching': True,
        }
    ]

    class MediaSelectionError(Exception):
        def __init__(self, id):
            self.id = id

    def _extract_asx_playlist(self, connection, programme_id):
        asx = self._download_xml(connection.get('href'), programme_id, 'Downloading ASX playlist')
        return [ref.get('href') for ref in asx.findall('./Entry/ref')]

    def _extract_connection(self, connection, programme_id):
        formats = []
        protocol = connection.get('protocol')
        supplier = connection.get('supplier')
        if protocol == 'http':
            href = connection.get('href')
            transfer_format = connection.get('transferFormat')
            # ASX playlist
            if supplier == 'asx':
                for i, ref in enumerate(self._extract_asx_playlist(connection, programme_id)):
                    formats.append({
                        'url': ref,
                        'format_id': 'ref%s_%s' % (i, supplier),
                    })
            # Skip DASH until supported
            elif transfer_format == 'dash':
                pass
            elif transfer_format == 'hls':
                m3u8_formats = self._extract_m3u8_formats(
                    href, programme_id, ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id=supplier, fatal=False)
                if m3u8_formats:
                    formats.extend(m3u8_formats)
            # Direct link
            else:
                formats.append({
                    'url': href,
                    'format_id': supplier,
                })
        elif protocol == 'rtmp':
            application = connection.get('application', 'ondemand')
            auth_string = connection.get('authString')
            identifier = connection.get('identifier')
            server = connection.get('server')
            formats.append({
                'url': '%s://%s/%s?%s' % (protocol, server, application, auth_string),
                'play_path': identifier,
                'app': '%s?%s' % (application, auth_string),
                'page_url': 'http://www.bbc.co.uk',
                'player_url': 'http://www.bbc.co.uk/emp/releases/iplayer/revisions/617463_618125_4/617463_618125_4_emp.swf',
                'rtmp_live': False,
                'ext': 'flv',
                'format_id': supplier,
            })
        return formats

    def _extract_items(self, playlist):
        return playlist.findall('./{http://bbc.co.uk/2008/emp/playlist}item')

    def _extract_medias(self, media_selection):
        error = media_selection.find('./{http://bbc.co.uk/2008/mp/mediaselection}error')
        if error is not None:
            raise BBCCoUkIE.MediaSelectionError(error.get('id'))
        return media_selection.findall('./{http://bbc.co.uk/2008/mp/mediaselection}media')

    def _extract_connections(self, media):
        return media.findall('./{http://bbc.co.uk/2008/mp/mediaselection}connection')

    def _extract_video(self, media, programme_id):
        formats = []
        vbr = int_or_none(media.get('bitrate'))
        vcodec = media.get('encoding')
        service = media.get('service')
        width = int_or_none(media.get('width'))
        height = int_or_none(media.get('height'))
        file_size = int_or_none(media.get('media_file_size'))
        for connection in self._extract_connections(media):
            conn_formats = self._extract_connection(connection, programme_id)
            for format in conn_formats:
                format.update({
                    'format_id': '%s_%s' % (service, format['format_id']),
                    'width': width,
                    'height': height,
                    'vbr': vbr,
                    'vcodec': vcodec,
                    'filesize': file_size,
                })
            formats.extend(conn_formats)
        return formats

    def _extract_audio(self, media, programme_id):
        formats = []
        abr = int_or_none(media.get('bitrate'))
        acodec = media.get('encoding')
        service = media.get('service')
        for connection in self._extract_connections(media):
            conn_formats = self._extract_connection(connection, programme_id)
            for format in conn_formats:
                format.update({
                    'format_id': '%s_%s' % (service, format['format_id']),
                    'abr': abr,
                    'acodec': acodec,
                })
            formats.extend(conn_formats)
        return formats

    def _get_subtitles(self, media, programme_id):
        subtitles = {}
        for connection in self._extract_connections(media):
            captions = self._download_xml(connection.get('href'), programme_id, 'Downloading captions')
            lang = captions.get('{http://www.w3.org/XML/1998/namespace}lang', 'en')
            subtitles[lang] = [
                {
                    'url': connection.get('href'),
                    'ext': 'ttml',
                },
            ]
        return subtitles

    def _raise_extractor_error(self, media_selection_error):
        raise ExtractorError(
            '%s returned error: %s' % (self.IE_NAME, media_selection_error.id),
            expected=True)

    def _download_media_selector(self, programme_id):
        last_exception = None
        for mediaselector_url in self._MEDIASELECTOR_URLS:
            try:
                return self._download_media_selector_url(
                    mediaselector_url % programme_id, programme_id)
            except BBCCoUkIE.MediaSelectionError as e:
                if e.id in ('notukerror', 'geolocation'):
                    last_exception = e
                    continue
                self._raise_extractor_error(e)
        self._raise_extractor_error(last_exception)

    def _download_media_selector_url(self, url, programme_id=None):
        try:
            media_selection = self._download_xml(
                url, programme_id, 'Downloading media selection XML')
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 403:
                media_selection = xml.etree.ElementTree.fromstring(ee.cause.read().decode('utf-8'))
            else:
                raise
        return self._process_media_selector(media_selection, programme_id)

    def _process_media_selector(self, media_selection, programme_id):
        formats = []
        subtitles = None

        for media in self._extract_medias(media_selection):
            kind = media.get('kind')
            if kind == 'audio':
                formats.extend(self._extract_audio(media, programme_id))
            elif kind == 'video':
                formats.extend(self._extract_video(media, programme_id))
            elif kind == 'captions':
                subtitles = self.extract_subtitles(media, programme_id)
        return formats, subtitles

    def _download_playlist(self, playlist_id):
        try:
            playlist = self._download_json(
                'http://www.bbc.co.uk/programmes/%s/playlist.json' % playlist_id,
                playlist_id, 'Downloading playlist JSON')

            version = playlist.get('defaultAvailableVersion')
            if version:
                smp_config = version['smpConfig']
                title = smp_config['title']
                description = smp_config['summary']
                for item in smp_config['items']:
                    kind = item['kind']
                    if kind != 'programme' and kind != 'radioProgramme':
                        continue
                    programme_id = item.get('vpid')
                    duration = int_or_none(item.get('duration'))
                    formats, subtitles = self._download_media_selector(programme_id)
                return programme_id, title, description, duration, formats, subtitles
        except ExtractorError as ee:
            if not (isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 404):
                raise

        # fallback to legacy playlist
        return self._process_legacy_playlist(playlist_id)

    def _process_legacy_playlist_url(self, url, display_id):
        playlist = self._download_legacy_playlist_url(url, display_id)
        return self._extract_from_legacy_playlist(playlist, display_id)

    def _process_legacy_playlist(self, playlist_id):
        return self._process_legacy_playlist_url(
            'http://www.bbc.co.uk/iplayer/playlist/%s' % playlist_id, playlist_id)

    def _download_legacy_playlist_url(self, url, playlist_id=None):
        return self._download_xml(
            url, playlist_id, 'Downloading legacy playlist XML')

    def _extract_from_legacy_playlist(self, playlist, playlist_id):
        no_items = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}noItems')
        if no_items is not None:
            reason = no_items.get('reason')
            if reason == 'preAvailability':
                msg = 'Episode %s is not yet available' % playlist_id
            elif reason == 'postAvailability':
                msg = 'Episode %s is no longer available' % playlist_id
            elif reason == 'noMedia':
                msg = 'Episode %s is not currently available' % playlist_id
            else:
                msg = 'Episode %s is not available: %s' % (playlist_id, reason)
            raise ExtractorError(msg, expected=True)

        for item in self._extract_items(playlist):
            kind = item.get('kind')
            if kind != 'programme' and kind != 'radioProgramme':
                continue
            title = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}title').text
            description = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}summary').text

            def get_programme_id(item):
                def get_from_attributes(item):
                    for p in('identifier', 'group'):
                        value = item.get(p)
                        if value and re.match(r'^[pb][\da-z]{7}$', value):
                            return value
                get_from_attributes(item)
                mediator = item.find('./{http://bbc.co.uk/2008/emp/playlist}mediator')
                if mediator is not None:
                    return get_from_attributes(mediator)

            programme_id = get_programme_id(item)
            duration = int_or_none(item.get('duration'))
            # TODO: programme_id can be None and media items can be incorporated right inside
            # playlist's item (e.g. http://www.bbc.com/turkce/haberler/2015/06/150615_telabyad_kentin_cogu)
            # as f4m and m3u8
            formats, subtitles = self._download_media_selector(programme_id)

        return programme_id, title, description, duration, formats, subtitles

    def _real_extract(self, url):
        group_id = self._match_id(url)

        webpage = self._download_webpage(url, group_id, 'Downloading video page')

        programme_id = None

        tviplayer = self._search_regex(
            r'mediator\.bind\(({.+?})\s*,\s*document\.getElementById',
            webpage, 'player', default=None)

        if tviplayer:
            player = self._parse_json(tviplayer, group_id).get('player', {})
            duration = int_or_none(player.get('duration'))
            programme_id = player.get('vpid')

        if not programme_id:
            programme_id = self._search_regex(
                r'"vpid"\s*:\s*"([\da-z]{8})"', webpage, 'vpid', fatal=False, default=None)

        if programme_id:
            formats, subtitles = self._download_media_selector(programme_id)
            title = self._og_search_title(webpage)
            description = self._search_regex(
                r'<p class="[^"]*medium-description[^"]*">([^<]+)</p>',
                webpage, 'description', fatal=False)
        else:
            programme_id, title, description, duration, formats, subtitles = self._download_playlist(group_id)

        self._sort_formats(formats)

        return {
            'id': programme_id,
            'title': title,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }


class BBCIE(BBCCoUkIE):
    IE_NAME = 'bbc'
    IE_DESC = 'BBC'
    _VALID_URL = r'https?://(?:www\.)?bbc\.(?:com|co\.uk)/(?:[^/]+/)+(?P<id>[^/#?]+)'

    _MEDIASELECTOR_URLS = [
        # Provides more formats, namely direct mp4 links, but fails on some videos with
        # notukerror for non UK (?) users (e.g.
        # http://www.bbc.com/travel/story/20150625-sri-lankas-spicy-secret)
        'http://open.live.bbc.co.uk/mediaselector/4/mtis/stream/%s',
        # Provides fewer formats, but works everywhere for everybody (hopefully)
        'http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/journalism-pc/vpid/%s',
    ]

    _TESTS = [{
        # article with multiple videos embedded with data-media-meta containing
        # playlist.sxml, externalId and no direct video links
        'url': 'http://www.bbc.com/news/world-europe-32668511',
        'info_dict': {
            'id': 'world-europe-32668511',
            'title': 'Russia stages massive WW2 parade despite Western boycott',
            'description': 'md5:00ff61976f6081841f759a08bf78cc9c',
        },
        'playlist_count': 2,
    }, {
        # article with multiple videos embedded with data-media-meta (more videos)
        'url': 'http://www.bbc.com/news/business-28299555',
        'info_dict': {
            'id': 'business-28299555',
            'title': 'Farnborough Airshow: Video highlights',
            'description': 'BBC reports and video highlights at the Farnborough Airshow.',
        },
        'playlist_count': 9,
        'skip': 'Save time',
    }, {
        # article with multiple videos embedded with `new SMP()`
        'url': 'http://www.bbc.co.uk/blogs/adamcurtis/entries/3662a707-0af9-3149-963f-47bea720b460',
        'info_dict': {
            'id': '3662a707-0af9-3149-963f-47bea720b460',
            'title': 'BBC Blogs - Adam Curtis - BUGGER',
        },
        'playlist_count': 18,
    }, {
        # single video embedded with mediaAssetPage.init()
        'url': 'http://www.bbc.com/news/world-europe-32041533',
        'info_dict': {
            'id': 'p02mprgb',
            'ext': 'mp4',
            'title': 'Aerial footage showed the site of the crash in the Alps - courtesy BFM TV',
            'duration': 47,
            'timestamp': 1427219242,
            'upload_date': '20150324',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        # article with single video embedded with data-media-meta containing
        # direct video links (for now these are extracted) and playlist.xml (with
        # media items as f4m and m3u8 - currently unsupported)
        'url': 'http://www.bbc.com/turkce/haberler/2015/06/150615_telabyad_kentin_cogu',
        'info_dict': {
            'id': '150615_telabyad_kentin_cogu',
            'ext': 'mp4',
            'title': "YPG: Tel Abyad'ın tamamı kontrolümüzde",
            'duration': 47,
            'timestamp': 1434397334,
            'upload_date': '20150615',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # single video embedded with mediaAssetPage.init() (regional section)
        'url': 'http://www.bbc.com/mundo/video_fotos/2015/06/150619_video_honduras_militares_hospitales_corrupcion_aw',
        'info_dict': {
            'id': '150619_video_honduras_militares_hospitales_corrupcion_aw',
            'ext': 'mp4',
            'title': 'Honduras militariza sus hospitales por nuevo escándalo de corrupción',
            'duration': 87,
            'timestamp': 1434713142,
            'upload_date': '20150619',
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # single video from video playlist embedded with vxp-playlist-data JSON
        'url': 'http://www.bbc.com/news/video_and_audio/must_see/33376376',
        'info_dict': {
            'id': 'p02w6qjc',
            'ext': 'mp4',
            'title': '''Judge Mindy Glazer: "I'm sorry to see you here... I always wondered what happened to you"''',
            'duration': 56,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        # single video story with digitalData
        'url': 'http://www.bbc.com/travel/story/20150625-sri-lankas-spicy-secret',
        'info_dict': {
            'id': 'p02q6gc4',
            'ext': 'flv',
            'title': 'Sri Lanka’s spicy secret',
            'description': 'As a new train line to Jaffna opens up the country’s north, travellers can experience a truly distinct slice of Tamil culture.',
            'timestamp': 1437674293,
            'upload_date': '20150723',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        # single video story without digitalData
        'url': 'http://www.bbc.com/autos/story/20130513-hyundais-rock-star',
        'info_dict': {
            'id': 'p018zqqg',
            'ext': 'mp4',
            'title': 'Hyundai Santa Fe Sport: Rock star',
            'description': 'md5:b042a26142c4154a6e472933cf20793d',
            'timestamp': 1368473503,
            'upload_date': '20130513',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        # single video with playlist.sxml URL
        'url': 'http://www.bbc.com/sport/0/football/33653409',
        'info_dict': {
            'id': 'p02xycnp',
            'ext': 'mp4',
            'title': 'Transfers: Cristiano Ronaldo to Man Utd, Arsenal to spend?',
            'description': 'md5:398fca0e2e701c609d726e034fa1fc89',
            'duration': 140,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        # single video with playlist URL from weather section
        'url': 'http://www.bbc.com/weather/features/33601775',
        'only_matching': True,
    }, {
        # custom redirection to www.bbc.com
        'url': 'http://www.bbc.co.uk/news/science-environment-33661876',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if BBCCoUkIE.suitable(url) else super(BBCIE, cls).suitable(url)

    def _extract_from_media_meta(self, media_meta, video_id):
        # Direct links to media in media metadata (e.g.
        # http://www.bbc.com/turkce/haberler/2015/06/150615_telabyad_kentin_cogu)
        # TODO: there are also f4m and m3u8 streams incorporated in playlist.sxml
        source_files = media_meta.get('sourceFiles')
        if source_files:
            return [{
                'url': f['url'],
                'format_id': format_id,
                'ext': f.get('encoding'),
                'tbr': float_or_none(f.get('bitrate'), 1000),
                'filesize': int_or_none(f.get('filesize')),
            } for format_id, f in source_files.items() if f.get('url')], []

        programme_id = media_meta.get('externalId')
        if programme_id:
            return self._download_media_selector(programme_id)

        # Process playlist.sxml as legacy playlist
        href = media_meta.get('href')
        if href:
            playlist = self._download_legacy_playlist_url(href)
            _, _, _, _, formats, subtitles = self._extract_from_legacy_playlist(playlist, video_id)
            return formats, subtitles

        return [], []

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        timestamp = parse_iso8601(self._search_regex(
            [r'"datePublished":\s*"([^"]+)',
             r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"',
             r'itemprop="datePublished"[^>]+datetime="([^"]+)"'],
            webpage, 'date', default=None))

        # single video with playlist.sxml URL (e.g. http://www.bbc.com/sport/0/football/3365340ng)
        playlist = self._search_regex(
            r'<param[^>]+name="playlist"[^>]+value="([^"]+)"',
            webpage, 'playlist', default=None)
        if playlist:
            programme_id, title, description, duration, formats, subtitles = \
                self._process_legacy_playlist_url(playlist, playlist_id)
            self._sort_formats(formats)
            return {
                'id': programme_id,
                'title': title,
                'description': description,
                'duration': duration,
                'timestamp': timestamp,
                'formats': formats,
                'subtitles': subtitles,
            }

        # single video story (e.g. http://www.bbc.com/travel/story/20150625-sri-lankas-spicy-secret)
        programme_id = self._search_regex(
            [r'data-video-player-vpid="([\da-z]{8})"',
             r'<param[^>]+name="externalIdentifier"[^>]+value="([\da-z]{8})"'],
            webpage, 'vpid', default=None)
        if programme_id:
            formats, subtitles = self._download_media_selector(programme_id)
            self._sort_formats(formats)
            # digitalData may be missing (e.g. http://www.bbc.com/autos/story/20130513-hyundais-rock-star)
            digital_data = self._parse_json(
                self._search_regex(
                    r'var\s+digitalData\s*=\s*({.+?});?\n', webpage, 'digital data', default='{}'),
                programme_id, fatal=False)
            page_info = digital_data.get('page', {}).get('pageInfo', {})
            title = page_info.get('pageName') or self._og_search_title(webpage)
            description = page_info.get('description') or self._og_search_description(webpage)
            timestamp = parse_iso8601(page_info.get('publicationDate')) or timestamp
            return {
                'id': programme_id,
                'title': title,
                'description': description,
                'timestamp': timestamp,
                'formats': formats,
                'subtitles': subtitles,
            }

        playlist_title = self._html_search_regex(
            r'<title>(.*?)(?:\s*-\s*BBC [^ ]+)?</title>', webpage, 'playlist title')
        playlist_description = self._og_search_description(webpage, default=None)

        def extract_all(pattern):
            return list(filter(None, map(
                lambda s: self._parse_json(s, playlist_id, fatal=False),
                re.findall(pattern, webpage))))

        # Multiple video article (e.g.
        # http://www.bbc.co.uk/blogs/adamcurtis/entries/3662a707-0af9-3149-963f-47bea720b460)
        EMBED_URL = r'https?://(?:www\.)?bbc\.co\.uk/(?:[^/]+/)+[\da-z]{8}(?:\b[^"]+)?'
        entries = []
        for match in extract_all(r'new\s+SMP\(({.+?})\)'):
            embed_url = match.get('playerSettings', {}).get('externalEmbedUrl')
            if embed_url and re.match(EMBED_URL, embed_url):
                entries.append(embed_url)
        entries.extend(re.findall(
            r'setPlaylist\("(%s)"\)' % EMBED_URL, webpage))
        if entries:
            return self.playlist_result(
                [self.url_result(entry, 'BBCCoUk') for entry in entries],
                playlist_id, playlist_title, playlist_description)

        # Multiple video article (e.g. http://www.bbc.com/news/world-europe-32668511)
        medias = extract_all(r"data-media-meta='({[^']+})'")

        if not medias:
            # Single video article (e.g. http://www.bbc.com/news/video_and_audio/international)
            media_asset = self._search_regex(
                r'mediaAssetPage\.init\(\s*({.+?}), "/',
                webpage, 'media asset', default=None)
            if media_asset:
                media_asset_page = self._parse_json(media_asset, playlist_id, fatal=False)
                medias = []
                for video in media_asset_page.get('videos', {}).values():
                    medias.extend(video.values())

        if not medias:
            # Multiple video playlist with single `now playing` entry (e.g.
            # http://www.bbc.com/news/video_and_audio/must_see/33767813)
            vxp_playlist = self._parse_json(
                self._search_regex(
                    r'<script[^>]+class="vxp-playlist-data"[^>]+type="application/json"[^>]*>([^<]+)</script>',
                    webpage, 'playlist data'),
                playlist_id)
            playlist_medias = []
            for item in vxp_playlist:
                media = item.get('media')
                if not media:
                    continue
                playlist_medias.append(media)
                # Download single video if found media with asset id matching the video id from URL
                if item.get('advert', {}).get('assetId') == playlist_id:
                    medias = [media]
                    break
            # Fallback to the whole playlist
            if not medias:
                medias = playlist_medias

        entries = []
        for num, media_meta in enumerate(medias, start=1):
            formats, subtitles = self._extract_from_media_meta(media_meta, playlist_id)
            if not formats:
                continue
            self._sort_formats(formats)

            video_id = media_meta.get('externalId')
            if not video_id:
                video_id = playlist_id if len(medias) == 1 else '%s-%s' % (playlist_id, num)

            title = media_meta.get('caption')
            if not title:
                title = playlist_title if len(medias) == 1 else '%s - Video %s' % (playlist_title, num)

            duration = int_or_none(media_meta.get('durationInSeconds')) or parse_duration(media_meta.get('duration'))

            images = []
            for image in media_meta.get('images', {}).values():
                images.extend(image.values())
            if 'image' in media_meta:
                images.append(media_meta['image'])

            thumbnails = [{
                'url': image.get('href'),
                'width': int_or_none(image.get('width')),
                'height': int_or_none(image.get('height')),
            } for image in images]

            entries.append({
                'id': video_id,
                'title': title,
                'thumbnails': thumbnails,
                'duration': duration,
                'timestamp': timestamp,
                'formats': formats,
                'subtitles': subtitles,
            })

        return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)
