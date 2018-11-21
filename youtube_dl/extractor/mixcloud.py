from __future__ import unicode_literals

import functools
import itertools
import re

from .common import InfoExtractor
from ..compat import (
    compat_b64decode,
    compat_chr,
    compat_ord,
    compat_str,
    compat_urllib_parse_unquote,
    compat_urlparse,
    compat_zip
)
from ..utils import (
    clean_html,
    ExtractorError,
    int_or_none,
    OnDemandPagedList,
    str_to_int,
    try_get,
    urljoin,
)


class MixcloudIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|beta|m)\.)?mixcloud\.com/([^/]+)/(?!stream|uploads|favorites|listens|playlists)([^/]+)'
    IE_NAME = 'mixcloud'

    _TESTS = [{
        'url': 'http://www.mixcloud.com/dholbach/cryptkeeper/',
        'info_dict': {
            'id': 'dholbach-cryptkeeper',
            'ext': 'm4a',
            'title': 'Cryptkeeper',
            'description': 'After quite a long silence from myself, finally another Drum\'n\'Bass mix with my favourite current dance floor bangers.',
            'uploader': 'Daniel Holbach',
            'uploader_id': 'dholbach',
            'thumbnail': r're:https?://.*\.jpg',
            'view_count': int,
        },
    }, {
        'url': 'http://www.mixcloud.com/gillespeterson/caribou-7-inch-vinyl-mix-chat/',
        'info_dict': {
            'id': 'gillespeterson-caribou-7-inch-vinyl-mix-chat',
            'ext': 'mp3',
            'title': 'Caribou 7 inch Vinyl Mix & Chat',
            'description': 'md5:2b8aec6adce69f9d41724647c65875e8',
            'uploader': 'Gilles Peterson Worldwide',
            'uploader_id': 'gillespeterson',
            'thumbnail': 're:https?://.*',
            'view_count': int,
        },
    }, {
        'url': 'https://beta.mixcloud.com/RedLightRadio/nosedrip-15-red-light-radio-01-18-2016/',
        'only_matching': True,
    }]

    @staticmethod
    def _decrypt_xor_cipher(key, ciphertext):
        """Encrypt/Decrypt XOR cipher. Both ways are possible because it's XOR."""
        return ''.join([
            compat_chr(compat_ord(ch) ^ compat_ord(k))
            for ch, k in compat_zip(ciphertext, itertools.cycle(key))])

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group(1)
        cloudcast_name = mobj.group(2)
        track_id = compat_urllib_parse_unquote('-'.join((uploader, cloudcast_name)))

        webpage = self._download_webpage(url, track_id)

        # Legacy path
        encrypted_play_info = self._search_regex(
            r'm-play-info="([^"]+)"', webpage, 'play info', default=None)

        if encrypted_play_info is not None:
            # Decode
            encrypted_play_info = compat_b64decode(encrypted_play_info)
        else:
            # New path
            full_info_json = self._parse_json(self._html_search_regex(
                r'<script id="relay-data" type="text/x-mixcloud">([^<]+)</script>',
                webpage, 'play info'), 'play info')
            for item in full_info_json:
                item_data = try_get(
                    item, lambda x: x['cloudcast']['data']['cloudcastLookup'],
                    dict)
                if try_get(item_data, lambda x: x['streamInfo']['url']):
                    info_json = item_data
                    break
            else:
                raise ExtractorError('Failed to extract matching stream info')

        message = self._html_search_regex(
            r'(?s)<div[^>]+class="global-message cloudcast-disabled-notice-light"[^>]*>(.+?)<(?:a|/div)',
            webpage, 'error message', default=None)

        js_url = self._search_regex(
            r'<script[^>]+\bsrc=["\"](https://(?:www\.)?mixcloud\.com/media/(?:js2/www_js_4|js/www)\.[^>]+\.js)',
            webpage, 'js url')
        js = self._download_webpage(js_url, track_id, 'Downloading JS')
        # Known plaintext attack
        if encrypted_play_info:
            kps = ['{"stream_url":']
            kpa_target = encrypted_play_info
        else:
            kps = ['https://', 'http://']
            kpa_target = compat_b64decode(info_json['streamInfo']['url'])
        for kp in kps:
            partial_key = self._decrypt_xor_cipher(kpa_target, kp)
            for quote in ["'", '"']:
                key = self._search_regex(
                    r'{0}({1}[^{0}]*){0}'.format(quote, re.escape(partial_key)),
                    js, 'encryption key', default=None)
                if key is not None:
                    break
            else:
                continue
            break
        else:
            raise ExtractorError('Failed to extract encryption key')

        if encrypted_play_info is not None:
            play_info = self._parse_json(self._decrypt_xor_cipher(key, encrypted_play_info), 'play info')
            if message and 'stream_url' not in play_info:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, message), expected=True)
            song_url = play_info['stream_url']
            formats = [{
                'format_id': 'normal',
                'url': song_url
            }]

            title = self._html_search_regex(r'm-title="([^"]+)"', webpage, 'title')
            thumbnail = self._proto_relative_url(self._html_search_regex(
                r'm-thumbnail-url="([^"]+)"', webpage, 'thumbnail', fatal=False))
            uploader = self._html_search_regex(
                r'm-owner-name="([^"]+)"', webpage, 'uploader', fatal=False)
            uploader_id = self._search_regex(
                r'\s+"profile": "([^"]+)",', webpage, 'uploader id', fatal=False)
            description = self._og_search_description(webpage)
            view_count = str_to_int(self._search_regex(
                [r'<meta itemprop="interactionCount" content="UserPlays:([0-9]+)"',
                 r'/listeners/?">([0-9,.]+)</a>',
                 r'(?:m|data)-tooltip=["\']([\d,.]+) plays'],
                webpage, 'play count', default=None))

        else:
            title = info_json['name']
            thumbnail = urljoin(
                'https://thumbnailer.mixcloud.com/unsafe/600x600/',
                try_get(info_json, lambda x: x['picture']['urlRoot'], compat_str))
            uploader = try_get(info_json, lambda x: x['owner']['displayName'])
            uploader_id = try_get(info_json, lambda x: x['owner']['username'])
            description = try_get(info_json, lambda x: x['description'])
            view_count = int_or_none(try_get(info_json, lambda x: x['plays']))

            stream_info = info_json['streamInfo']
            formats = []

            def decrypt_url(f_url):
                for k in (key, 'IFYOUWANTTHEARTISTSTOGETPAIDDONOTDOWNLOADFROMMIXCLOUD'):
                    decrypted_url = self._decrypt_xor_cipher(k, f_url)
                    if re.search(r'^https?://[0-9a-z.]+/[0-9A-Za-z/.?=&_-]+$', decrypted_url):
                        return decrypted_url

            for url_key in ('url', 'hlsUrl', 'dashUrl'):
                format_url = stream_info.get(url_key)
                if not format_url:
                    continue
                decrypted = decrypt_url(compat_b64decode(format_url))
                if not decrypted:
                    continue
                if url_key == 'hlsUrl':
                    formats.extend(self._extract_m3u8_formats(
                        decrypted, track_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False))
                elif url_key == 'dashUrl':
                    formats.extend(self._extract_mpd_formats(
                        decrypted, track_id, mpd_id='dash', fatal=False))
                else:
                    formats.append({
                        'format_id': 'http',
                        'url': decrypted,
                        'downloader_options': {
                            # Mixcloud starts throttling at >~5M
                            'http_chunk_size': 5242880,
                        },
                    })
            self._sort_formats(formats)

        return {
            'id': track_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
        }


class MixcloudPlaylistBaseIE(InfoExtractor):
    _PAGE_SIZE = 24

    def _find_urls_in_page(self, page):
        for url in re.findall(r'm-play-button m-url="(?P<url>[^"]+)"', page):
            yield self.url_result(
                compat_urlparse.urljoin('https://www.mixcloud.com', clean_html(url)),
                MixcloudIE.ie_key())

    def _fetch_tracks_page(self, path, video_id, page_name, current_page, real_page_number=None):
        real_page_number = real_page_number or current_page + 1
        return self._download_webpage(
            'https://www.mixcloud.com/%s/' % path, video_id,
            note='Download %s (page %d)' % (page_name, current_page + 1),
            errnote='Unable to download %s' % page_name,
            query={'page': real_page_number, 'list': 'main', '_ajax': '1'},
            headers={'X-Requested-With': 'XMLHttpRequest'})

    def _tracks_page_func(self, page, video_id, page_name, current_page):
        resp = self._fetch_tracks_page(page, video_id, page_name, current_page)

        for item in self._find_urls_in_page(resp):
            yield item

    def _get_user_description(self, page_content):
        return self._html_search_regex(
            r'<div[^>]+class="profile-bio"[^>]*>(.+?)</div>',
            page_content, 'user description', fatal=False)


class MixcloudUserIE(MixcloudPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mixcloud\.com/(?P<user>[^/]+)/(?P<type>uploads|favorites|listens)?/?$'
    IE_NAME = 'mixcloud:user'

    _TESTS = [{
        'url': 'http://www.mixcloud.com/dholbach/',
        'info_dict': {
            'id': 'dholbach_uploads',
            'title': 'Daniel Holbach (uploads)',
            'description': 'md5:def36060ac8747b3aabca54924897e47',
        },
        'playlist_mincount': 11,
    }, {
        'url': 'http://www.mixcloud.com/dholbach/uploads/',
        'info_dict': {
            'id': 'dholbach_uploads',
            'title': 'Daniel Holbach (uploads)',
            'description': 'md5:def36060ac8747b3aabca54924897e47',
        },
        'playlist_mincount': 11,
    }, {
        'url': 'http://www.mixcloud.com/dholbach/favorites/',
        'info_dict': {
            'id': 'dholbach_favorites',
            'title': 'Daniel Holbach (favorites)',
            'description': 'md5:def36060ac8747b3aabca54924897e47',
        },
        'params': {
            'playlist_items': '1-100',
        },
        'playlist_mincount': 100,
    }, {
        'url': 'http://www.mixcloud.com/dholbach/listens/',
        'info_dict': {
            'id': 'dholbach_listens',
            'title': 'Daniel Holbach (listens)',
            'description': 'md5:def36060ac8747b3aabca54924897e47',
        },
        'params': {
            'playlist_items': '1-100',
        },
        'playlist_mincount': 100,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user')
        list_type = mobj.group('type')

        # if only a profile URL was supplied, default to download all uploads
        if list_type is None:
            list_type = 'uploads'

        video_id = '%s_%s' % (user_id, list_type)

        profile = self._download_webpage(
            'https://www.mixcloud.com/%s/' % user_id, video_id,
            note='Downloading user profile',
            errnote='Unable to download user profile')

        username = self._og_search_title(profile)
        description = self._get_user_description(profile)

        entries = OnDemandPagedList(
            functools.partial(
                self._tracks_page_func,
                '%s/%s' % (user_id, list_type), video_id, 'list of %s' % list_type),
            self._PAGE_SIZE)

        return self.playlist_result(
            entries, video_id, '%s (%s)' % (username, list_type), description)


class MixcloudPlaylistIE(MixcloudPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mixcloud\.com/(?P<user>[^/]+)/playlists/(?P<playlist>[^/]+)/?$'
    IE_NAME = 'mixcloud:playlist'

    _TESTS = [{
        'url': 'https://www.mixcloud.com/RedBullThre3style/playlists/tokyo-finalists-2015/',
        'info_dict': {
            'id': 'RedBullThre3style_tokyo-finalists-2015',
            'title': 'National Champions 2015',
            'description': 'md5:6ff5fb01ac76a31abc9b3939c16243a3',
        },
        'playlist_mincount': 16,
    }, {
        'url': 'https://www.mixcloud.com/maxvibes/playlists/jazzcat-on-ness-radio/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user')
        playlist_id = mobj.group('playlist')
        video_id = '%s_%s' % (user_id, playlist_id)

        webpage = self._download_webpage(
            url, user_id,
            note='Downloading playlist page',
            errnote='Unable to download playlist page')

        title = self._html_search_regex(
            r'<a[^>]+class="parent active"[^>]*><b>\d+</b><span[^>]*>([^<]+)',
            webpage, 'playlist title',
            default=None) or self._og_search_title(webpage, fatal=False)
        description = self._get_user_description(webpage)

        entries = OnDemandPagedList(
            functools.partial(
                self._tracks_page_func,
                '%s/playlists/%s' % (user_id, playlist_id), video_id, 'tracklist'),
            self._PAGE_SIZE)

        return self.playlist_result(entries, video_id, title, description)


class MixcloudStreamIE(MixcloudPlaylistBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mixcloud\.com/(?P<id>[^/]+)/stream/?$'
    IE_NAME = 'mixcloud:stream'

    _TEST = {
        'url': 'https://www.mixcloud.com/FirstEar/stream/',
        'info_dict': {
            'id': 'FirstEar',
            'title': 'First Ear',
            'description': 'Curators of good music\nfirstearmusic.com',
        },
        'playlist_mincount': 192,
    }

    def _real_extract(self, url):
        user_id = self._match_id(url)

        webpage = self._download_webpage(url, user_id)

        entries = []
        prev_page_url = None

        def _handle_page(page):
            entries.extend(self._find_urls_in_page(page))
            return self._search_regex(
                r'm-next-page-url="([^"]+)"', page,
                'next page URL', default=None)

        next_page_url = _handle_page(webpage)

        for idx in itertools.count(0):
            if not next_page_url or prev_page_url == next_page_url:
                break

            prev_page_url = next_page_url
            current_page = int(self._search_regex(
                r'\?page=(\d+)', next_page_url, 'next page number'))

            next_page_url = _handle_page(self._fetch_tracks_page(
                '%s/stream' % user_id, user_id, 'stream', idx,
                real_page_number=current_page))

        username = self._og_search_title(webpage)
        description = self._get_user_description(webpage)

        return self.playlist_result(entries, user_id, username, description)
