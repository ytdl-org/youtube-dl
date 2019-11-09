# coding: utf-8
from __future__ import unicode_literals

import itertools
import re
import random
import json

from .common import InfoExtractor
from ..compat import (
    compat_kwargs,
    compat_parse_qs,
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    clean_html,
    ExtractorError,
    float_or_none,
    int_or_none,
    orderedSet,
    parse_duration,
    parse_iso8601,
    qualities,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
    urljoin,
)


class TwitchBaseIE(InfoExtractor):
    _VALID_URL_BASE = r'https?://(?:(?:www|go|m)\.)?twitch\.tv'

    _API_BASE = 'https://api.twitch.tv'
    _USHER_BASE = 'https://usher.ttvnw.net'
    _LOGIN_FORM_URL = 'https://www.twitch.tv/login'
    _LOGIN_POST_URL = 'https://passport.twitch.tv/login'
    _CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
    _NETRC_MACHINE = 'twitch'

    def _handle_error(self, response):
        if not isinstance(response, dict):
            return
        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s - %s' % (self.IE_NAME, error, response.get('message')),
                expected=True)

    def _call_api(self, path, item_id, *args, **kwargs):
        headers = kwargs.get('headers', {}).copy()
        headers['Client-ID'] = self._CLIENT_ID
        kwargs['headers'] = headers
        response = self._download_json(
            '%s/%s' % (self._API_BASE, path), item_id,
            *args, **compat_kwargs(kwargs))
        self._handle_error(response)
        return response

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        def fail(message):
            raise ExtractorError(
                'Unable to login. Twitch said: %s' % message, expected=True)

        def login_step(page, urlh, note, data):
            form = self._hidden_inputs(page)
            form.update(data)

            page_url = urlh.geturl()
            post_url = self._search_regex(
                r'<form[^>]+action=(["\'])(?P<url>.+?)\1', page,
                'post url', default=self._LOGIN_POST_URL, group='url')
            post_url = urljoin(page_url, post_url)

            headers = {
                'Referer': page_url,
                'Origin': page_url,
                'Content-Type': 'text/plain;charset=UTF-8',
            }

            response = self._download_json(
                post_url, None, note, data=json.dumps(form).encode(),
                headers=headers, expected_status=400)
            error = response.get('error_description') or response.get('error_code')
            if error:
                fail(error)

            if 'Authenticated successfully' in response.get('message', ''):
                return None, None

            redirect_url = urljoin(
                post_url,
                response.get('redirect') or response['redirect_path'])
            return self._download_webpage_handle(
                redirect_url, None, 'Downloading login redirect page',
                headers=headers)

        login_page, handle = self._download_webpage_handle(
            self._LOGIN_FORM_URL, None, 'Downloading login page')

        # Some TOR nodes and public proxies are blocked completely
        if 'blacklist_message' in login_page:
            fail(clean_html(login_page))

        redirect_page, handle = login_step(
            login_page, handle, 'Logging in', {
                'username': username,
                'password': password,
                'client_id': self._CLIENT_ID,
            })

        # Successful login
        if not redirect_page:
            return

        if re.search(r'(?i)<form[^>]+id="two-factor-submit"', redirect_page) is not None:
            # TODO: Add mechanism to request an SMS or phone call
            tfa_token = self._get_tfa_info('two-factor authentication token')
            login_step(redirect_page, handle, 'Submitting TFA token', {
                'authy_token': tfa_token,
                'remember_2fa': 'true',
            })

    def _prefer_source(self, formats):
        try:
            source = next(f for f in formats if f['format_id'] == 'Source')
            source['quality'] = 10
        except StopIteration:
            for f in formats:
                if '/chunked/' in f['url']:
                    f.update({
                        'quality': 10,
                        'format_note': 'Source',
                    })
        self._sort_formats(formats)


class TwitchItemBaseIE(TwitchBaseIE):
    def _download_info(self, item, item_id):
        return self._extract_info(self._call_api(
            'kraken/videos/%s%s' % (item, item_id), item_id,
            'Downloading %s info JSON' % self._ITEM_TYPE))

    def _extract_media(self, item_id):
        info = self._download_info(self._ITEM_SHORTCUT, item_id)
        response = self._call_api(
            'api/videos/%s%s' % (self._ITEM_SHORTCUT, item_id), item_id,
            'Downloading %s playlist JSON' % self._ITEM_TYPE)
        entries = []
        chunks = response['chunks']
        qualities = list(chunks.keys())
        for num, fragment in enumerate(zip(*chunks.values()), start=1):
            formats = []
            for fmt_num, fragment_fmt in enumerate(fragment):
                format_id = qualities[fmt_num]
                fmt = {
                    'url': fragment_fmt['url'],
                    'format_id': format_id,
                    'quality': 1 if format_id == 'live' else 0,
                }
                m = re.search(r'^(?P<height>\d+)[Pp]', format_id)
                if m:
                    fmt['height'] = int(m.group('height'))
                formats.append(fmt)
            self._sort_formats(formats)
            entry = dict(info)
            entry['id'] = '%s_%d' % (entry['id'], num)
            entry['title'] = '%s part %d' % (entry['title'], num)
            entry['formats'] = formats
            entries.append(entry)
        return self.playlist_result(entries, info['id'], info['title'])

    def _extract_info(self, info):
        status = info.get('status')
        if status == 'recording':
            is_live = True
        elif status == 'recorded':
            is_live = False
        else:
            is_live = None
        return {
            'id': info['_id'],
            'title': info.get('title') or 'Untitled Broadcast',
            'description': info.get('description'),
            'duration': int_or_none(info.get('length')),
            'thumbnail': info.get('preview'),
            'uploader': info.get('channel', {}).get('display_name'),
            'uploader_id': info.get('channel', {}).get('name'),
            'timestamp': parse_iso8601(info.get('recorded_at')),
            'view_count': int_or_none(info.get('views')),
            'is_live': is_live,
        }

    def _real_extract(self, url):
        return self._extract_media(self._match_id(url))


class TwitchVideoIE(TwitchItemBaseIE):
    IE_NAME = 'twitch:video'
    _VALID_URL = r'%s/[^/]+/b/(?P<id>\d+)' % TwitchBaseIE._VALID_URL_BASE
    _ITEM_TYPE = 'video'
    _ITEM_SHORTCUT = 'a'

    _TEST = {
        'url': 'http://www.twitch.tv/riotgames/b/577357806',
        'info_dict': {
            'id': 'a577357806',
            'title': 'Worlds Semifinals - Star Horn Royal Club vs. OMG',
        },
        'playlist_mincount': 12,
        'skip': 'HTTP Error 404: Not Found',
    }


class TwitchChapterIE(TwitchItemBaseIE):
    IE_NAME = 'twitch:chapter'
    _VALID_URL = r'%s/[^/]+/c/(?P<id>\d+)' % TwitchBaseIE._VALID_URL_BASE
    _ITEM_TYPE = 'chapter'
    _ITEM_SHORTCUT = 'c'

    _TESTS = [{
        'url': 'http://www.twitch.tv/acracingleague/c/5285812',
        'info_dict': {
            'id': 'c5285812',
            'title': 'ACRL Off Season - Sports Cars @ Nordschleife',
        },
        'playlist_mincount': 3,
        'skip': 'HTTP Error 404: Not Found',
    }, {
        'url': 'http://www.twitch.tv/tsm_theoddone/c/2349361',
        'only_matching': True,
    }]


class TwitchVodIE(TwitchItemBaseIE):
    IE_NAME = 'twitch:vod'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:(?:www|go|m)\.)?twitch\.tv/(?:[^/]+/v(?:ideo)?|videos)/|
                            player\.twitch\.tv/\?.*?\bvideo=v?
                        )
                        (?P<id>\d+)
                    '''
    _ITEM_TYPE = 'vod'
    _ITEM_SHORTCUT = 'v'

    _TESTS = [{
        'url': 'http://www.twitch.tv/riotgames/v/6528877?t=5m10s',
        'info_dict': {
            'id': 'v6528877',
            'ext': 'mp4',
            'title': 'LCK Summer Split - Week 6 Day 1',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 17208,
            'timestamp': 1435131709,
            'upload_date': '20150624',
            'uploader': 'Riot Games',
            'uploader_id': 'riotgames',
            'view_count': int,
            'start_time': 310,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        # Untitled broadcast (title is None)
        'url': 'http://www.twitch.tv/belkao_o/v/11230755',
        'info_dict': {
            'id': 'v11230755',
            'ext': 'mp4',
            'title': 'Untitled Broadcast',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1638,
            'timestamp': 1439746708,
            'upload_date': '20150816',
            'uploader': 'BelkAO_o',
            'uploader_id': 'belkao_o',
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'skip': 'HTTP Error 404: Not Found',
    }, {
        'url': 'http://player.twitch.tv/?t=5m10s&video=v6528877',
        'only_matching': True,
    }, {
        'url': 'https://www.twitch.tv/videos/6528877',
        'only_matching': True,
    }, {
        'url': 'https://m.twitch.tv/beagsandjam/v/247478721',
        'only_matching': True,
    }, {
        'url': 'https://www.twitch.tv/northernlion/video/291940395',
        'only_matching': True,
    }, {
        'url': 'https://player.twitch.tv/?video=480452374',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        item_id = self._match_id(url)

        info = self._download_info(self._ITEM_SHORTCUT, item_id)
        access_token = self._call_api(
            'api/vods/%s/access_token' % item_id, item_id,
            'Downloading %s access token' % self._ITEM_TYPE)

        formats = self._extract_m3u8_formats(
            '%s/vod/%s.m3u8?%s' % (
                self._USHER_BASE, item_id,
                compat_urllib_parse_urlencode({
                    'allow_source': 'true',
                    'allow_audio_only': 'true',
                    'allow_spectre': 'true',
                    'player': 'twitchweb',
                    'nauth': access_token['token'],
                    'nauthsig': access_token['sig'],
                })),
            item_id, 'mp4', entry_protocol='m3u8_native')

        self._prefer_source(formats)
        info['formats'] = formats

        parsed_url = compat_urllib_parse_urlparse(url)
        query = compat_parse_qs(parsed_url.query)
        if 't' in query:
            info['start_time'] = parse_duration(query['t'][0])

        if info.get('timestamp') is not None:
            info['subtitles'] = {
                'rechat': [{
                    'url': update_url_query(
                        'https://rechat.twitch.tv/rechat-messages', {
                            'video_id': 'v%s' % item_id,
                            'start': info['timestamp'],
                        }),
                    'ext': 'json',
                }],
            }

        return info


class TwitchPlaylistBaseIE(TwitchBaseIE):
    _PLAYLIST_PATH = 'kraken/channels/%s/videos/?offset=%d&limit=%d'
    _PAGE_LIMIT = 100

    def _extract_playlist(self, channel_id):
        info = self._call_api(
            'kraken/channels/%s' % channel_id,
            channel_id, 'Downloading channel info JSON')
        channel_name = info.get('display_name') or info.get('name')
        entries = []
        offset = 0
        limit = self._PAGE_LIMIT
        broken_paging_detected = False
        counter_override = None
        for counter in itertools.count(1):
            response = self._call_api(
                self._PLAYLIST_PATH % (channel_id, offset, limit),
                channel_id,
                'Downloading %s JSON page %s'
                % (self._PLAYLIST_TYPE, counter_override or counter))
            page_entries = self._extract_playlist_page(response)
            if not page_entries:
                break
            total = int_or_none(response.get('_total'))
            # Since the beginning of March 2016 twitch's paging mechanism
            # is completely broken on the twitch side. It simply ignores
            # a limit and returns the whole offset number of videos.
            # Working around by just requesting all videos at once.
            # Upd: pagination bug was fixed by twitch on 15.03.2016.
            if not broken_paging_detected and total and len(page_entries) > limit:
                self.report_warning(
                    'Twitch pagination is broken on twitch side, requesting all videos at once',
                    channel_id)
                broken_paging_detected = True
                offset = total
                counter_override = '(all at once)'
                continue
            entries.extend(page_entries)
            if broken_paging_detected or total and len(page_entries) >= total:
                break
            offset += limit
        return self.playlist_result(
            [self._make_url_result(entry) for entry in orderedSet(entries)],
            channel_id, channel_name)

    def _make_url_result(self, url):
        try:
            video_id = 'v%s' % TwitchVodIE._match_id(url)
            return self.url_result(url, TwitchVodIE.ie_key(), video_id=video_id)
        except AssertionError:
            return self.url_result(url)

    def _extract_playlist_page(self, response):
        videos = response.get('videos')
        return [video['url'] for video in videos] if videos else []

    def _real_extract(self, url):
        return self._extract_playlist(self._match_id(url))


class TwitchProfileIE(TwitchPlaylistBaseIE):
    IE_NAME = 'twitch:profile'
    _VALID_URL = r'%s/(?P<id>[^/]+)/profile/?(?:\#.*)?$' % TwitchBaseIE._VALID_URL_BASE
    _PLAYLIST_TYPE = 'profile'

    _TESTS = [{
        'url': 'http://www.twitch.tv/vanillatv/profile',
        'info_dict': {
            'id': 'vanillatv',
            'title': 'VanillaTV',
        },
        'playlist_mincount': 412,
    }, {
        'url': 'http://m.twitch.tv/vanillatv/profile',
        'only_matching': True,
    }]


class TwitchVideosBaseIE(TwitchPlaylistBaseIE):
    _VALID_URL_VIDEOS_BASE = r'%s/(?P<id>[^/]+)/videos' % TwitchBaseIE._VALID_URL_BASE
    _PLAYLIST_PATH = TwitchPlaylistBaseIE._PLAYLIST_PATH + '&broadcast_type='


class TwitchAllVideosIE(TwitchVideosBaseIE):
    IE_NAME = 'twitch:videos:all'
    _VALID_URL = r'%s/all' % TwitchVideosBaseIE._VALID_URL_VIDEOS_BASE
    _PLAYLIST_PATH = TwitchVideosBaseIE._PLAYLIST_PATH + 'archive,upload,highlight'
    _PLAYLIST_TYPE = 'all videos'

    _TESTS = [{
        'url': 'https://www.twitch.tv/spamfish/videos/all',
        'info_dict': {
            'id': 'spamfish',
            'title': 'Spamfish',
        },
        'playlist_mincount': 869,
    }, {
        'url': 'https://m.twitch.tv/spamfish/videos/all',
        'only_matching': True,
    }]


class TwitchUploadsIE(TwitchVideosBaseIE):
    IE_NAME = 'twitch:videos:uploads'
    _VALID_URL = r'%s/uploads' % TwitchVideosBaseIE._VALID_URL_VIDEOS_BASE
    _PLAYLIST_PATH = TwitchVideosBaseIE._PLAYLIST_PATH + 'upload'
    _PLAYLIST_TYPE = 'uploads'

    _TESTS = [{
        'url': 'https://www.twitch.tv/spamfish/videos/uploads',
        'info_dict': {
            'id': 'spamfish',
            'title': 'Spamfish',
        },
        'playlist_mincount': 0,
    }, {
        'url': 'https://m.twitch.tv/spamfish/videos/uploads',
        'only_matching': True,
    }]


class TwitchPastBroadcastsIE(TwitchVideosBaseIE):
    IE_NAME = 'twitch:videos:past-broadcasts'
    _VALID_URL = r'%s/past-broadcasts' % TwitchVideosBaseIE._VALID_URL_VIDEOS_BASE
    _PLAYLIST_PATH = TwitchVideosBaseIE._PLAYLIST_PATH + 'archive'
    _PLAYLIST_TYPE = 'past broadcasts'

    _TESTS = [{
        'url': 'https://www.twitch.tv/spamfish/videos/past-broadcasts',
        'info_dict': {
            'id': 'spamfish',
            'title': 'Spamfish',
        },
        'playlist_mincount': 0,
    }, {
        'url': 'https://m.twitch.tv/spamfish/videos/past-broadcasts',
        'only_matching': True,
    }]


class TwitchHighlightsIE(TwitchVideosBaseIE):
    IE_NAME = 'twitch:videos:highlights'
    _VALID_URL = r'%s/highlights' % TwitchVideosBaseIE._VALID_URL_VIDEOS_BASE
    _PLAYLIST_PATH = TwitchVideosBaseIE._PLAYLIST_PATH + 'highlight'
    _PLAYLIST_TYPE = 'highlights'

    _TESTS = [{
        'url': 'https://www.twitch.tv/spamfish/videos/highlights',
        'info_dict': {
            'id': 'spamfish',
            'title': 'Spamfish',
        },
        'playlist_mincount': 805,
    }, {
        'url': 'https://m.twitch.tv/spamfish/videos/highlights',
        'only_matching': True,
    }]


class TwitchStreamIE(TwitchBaseIE):
    IE_NAME = 'twitch:stream'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:(?:www|go|m)\.)?twitch\.tv/|
                            player\.twitch\.tv/\?.*?\bchannel=
                        )
                        (?P<id>[^/#?]+)
                    '''

    _TESTS = [{
        'url': 'http://www.twitch.tv/shroomztv',
        'info_dict': {
            'id': '12772022048',
            'display_id': 'shroomztv',
            'ext': 'mp4',
            'title': 're:^ShroomzTV [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'description': 'H1Z1 - lonewolfing with ShroomzTV | A3 Battle Royale later - @ShroomzTV',
            'is_live': True,
            'timestamp': 1421928037,
            'upload_date': '20150122',
            'uploader': 'ShroomzTV',
            'uploader_id': 'shroomztv',
            'view_count': int,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.twitch.tv/miracle_doto#profile-0',
        'only_matching': True,
    }, {
        'url': 'https://player.twitch.tv/?channel=lotsofs',
        'only_matching': True,
    }, {
        'url': 'https://go.twitch.tv/food',
        'only_matching': True,
    }, {
        'url': 'https://m.twitch.tv/food',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return (False
                if any(ie.suitable(url) for ie in (
                    TwitchVideoIE,
                    TwitchChapterIE,
                    TwitchVodIE,
                    TwitchProfileIE,
                    TwitchAllVideosIE,
                    TwitchUploadsIE,
                    TwitchPastBroadcastsIE,
                    TwitchHighlightsIE,
                    TwitchClipsIE))
                else super(TwitchStreamIE, cls).suitable(url))

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        stream = self._call_api(
            'kraken/streams/%s?stream_type=all' % channel_id, channel_id,
            'Downloading stream JSON').get('stream')

        if not stream:
            raise ExtractorError('%s is offline' % channel_id, expected=True)

        # Channel name may be typed if different case than the original channel name
        # (e.g. http://www.twitch.tv/TWITCHPLAYSPOKEMON) that will lead to constructing
        # an invalid m3u8 URL. Working around by use of original channel name from stream
        # JSON and fallback to lowercase if it's not available.
        channel_id = stream.get('channel', {}).get('name') or channel_id.lower()

        access_token = self._call_api(
            'api/channels/%s/access_token' % channel_id, channel_id,
            'Downloading channel access token')

        query = {
            'allow_source': 'true',
            'allow_audio_only': 'true',
            'allow_spectre': 'true',
            'p': random.randint(1000000, 10000000),
            'player': 'twitchweb',
            'segment_preference': '4',
            'sig': access_token['sig'].encode('utf-8'),
            'token': access_token['token'].encode('utf-8'),
        }
        formats = self._extract_m3u8_formats(
            '%s/api/channel/hls/%s.m3u8?%s'
            % (self._USHER_BASE, channel_id, compat_urllib_parse_urlencode(query)),
            channel_id, 'mp4')
        self._prefer_source(formats)

        view_count = stream.get('viewers')
        timestamp = parse_iso8601(stream.get('created_at'))

        channel = stream['channel']
        title = self._live_title(channel.get('display_name') or channel.get('name'))
        description = channel.get('status')

        thumbnails = []
        for thumbnail_key, thumbnail_url in stream['preview'].items():
            m = re.search(r'(?P<width>\d+)x(?P<height>\d+)\.jpg$', thumbnail_key)
            if not m:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int(m.group('width')),
                'height': int(m.group('height')),
            })

        return {
            'id': compat_str(stream['_id']),
            'display_id': channel_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'uploader': channel.get('display_name'),
            'uploader_id': channel.get('name'),
            'timestamp': timestamp,
            'view_count': view_count,
            'formats': formats,
            'is_live': True,
        }


class TwitchClipsIE(TwitchBaseIE):
    IE_NAME = 'twitch:clips'
    _VALID_URL = r'https?://(?:clips\.twitch\.tv/(?:embed\?.*?\bclip=|(?:[^/]+/)*)|(?:www\.)?twitch\.tv/[^/]+/clip/)(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'https://clips.twitch.tv/FaintLightGullWholeWheat',
        'md5': '761769e1eafce0ffebfb4089cb3847cd',
        'info_dict': {
            'id': '42850523',
            'ext': 'mp4',
            'title': 'EA Play 2016 Live from the Novo Theatre',
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1465767393,
            'upload_date': '20160612',
            'creator': 'EA',
            'uploader': 'stereotype_',
            'uploader_id': '43566419',
        },
    }, {
        # multiple formats
        'url': 'https://clips.twitch.tv/rflegendary/UninterestedBeeDAESuppy',
        'only_matching': True,
    }, {
        'url': 'https://www.twitch.tv/sergeynixon/clip/StormyThankfulSproutFutureMan',
        'only_matching': True,
    }, {
        'url': 'https://clips.twitch.tv/embed?clip=InquisitiveBreakableYogurtJebaited',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        status = self._download_json(
            'https://clips.twitch.tv/api/v2/clips/%s/status' % video_id,
            video_id)

        formats = []

        for option in status['quality_options']:
            if not isinstance(option, dict):
                continue
            source = url_or_none(option.get('source'))
            if not source:
                continue
            formats.append({
                'url': source,
                'format_id': option.get('quality'),
                'height': int_or_none(option.get('quality')),
                'fps': int_or_none(option.get('frame_rate')),
            })

        self._sort_formats(formats)

        info = {
            'formats': formats,
        }

        clip = self._call_api(
            'kraken/clips/%s' % video_id, video_id, fatal=False, headers={
                'Accept': 'application/vnd.twitchtv.v5+json',
            })

        if clip:
            quality_key = qualities(('tiny', 'small', 'medium'))
            thumbnails = []
            thumbnails_dict = clip.get('thumbnails')
            if isinstance(thumbnails_dict, dict):
                for thumbnail_id, thumbnail_url in thumbnails_dict.items():
                    thumbnails.append({
                        'id': thumbnail_id,
                        'url': thumbnail_url,
                        'preference': quality_key(thumbnail_id),
                    })

            info.update({
                'id': clip.get('tracking_id') or video_id,
                'title': clip.get('title') or video_id,
                'duration': float_or_none(clip.get('duration')),
                'views': int_or_none(clip.get('views')),
                'timestamp': unified_timestamp(clip.get('created_at')),
                'thumbnails': thumbnails,
                'creator': try_get(clip, lambda x: x['broadcaster']['display_name'], compat_str),
                'uploader': try_get(clip, lambda x: x['curator']['display_name'], compat_str),
                'uploader_id': try_get(clip, lambda x: x['curator']['id'], compat_str),
            })
        else:
            info.update({
                'title': video_id,
                'id': video_id,
            })

        return info
