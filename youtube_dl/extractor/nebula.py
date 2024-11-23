# coding: utf-8
from __future__ import unicode_literals

import itertools

from .art19 import Art19IE
from .common import InfoExtractor
from ..compat import (
    compat_HTTPError as HTTPError,
    compat_kwargs,
    compat_str as str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    json_stringify,
    # make_archive_id,
    merge_dicts,
    parse_iso8601,
    smuggle_url,
    str_or_none,
    T,
    traverse_obj,
    try_call,
    unsmuggle_url,
    update_url,
    url_basename,
    url_or_none,
    urljoin,
)

_BASE_URL_RE = r'https?://(?:www\.|beta\.)?(?:watchnebula\.com|nebula\.app|nebula\.tv)'


class NebulaBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'watchnebula'
    _token = _api_token = None

    def _real_initialize(self):
        self._login()

    def _login(self):
        if not self._api_token:
            self._api_token = try_call(
                lambda: self._get_cookies('https://nebula.tv')['nebula_auth.apiToken'].value)
        self._token = self._download_json(
            'https://users.api.nebula.app/api/v1/authorization/', None,
            headers={'Authorization': 'Token {0}'.format(self._api_token)} if self._api_token else {},
            note='Authorizing to Nebula', data=b'')['token']
        if self._token:
            return

        username, password = self._get_login_info()
        if username is None:
            return
        self._perform_login(username, password)

    def _perform_login(self, username, password):
        try:
            response = self._download_json(
                'https://nebula.tv/auth/login/', None,
                'Logging in to Nebula', 'Login failed',
                data=json_stringify({'email': username, 'password': password}),
                headers={'content-type': 'application/json'})
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                raise ExtractorError('Login failed: Invalid username or password', expected=True)
            raise
        self._api_token = traverse_obj(response, ('key', T(str)))
        if not self._api_token:
            raise ExtractorError('Login failed: No token')

    def _call_api(self, *args, **kwargs):

        def kwargs_set_token(kw):
            kw.setdefault('headers', {})['Authorization'] = 'Bearer {0}'.format(self._token)
            return compat_kwargs(kw)

        if self._token:
            kwargs = kwargs_set_token(kwargs)
        try:
            return self._download_json(*args, **kwargs)
        except ExtractorError as e:
            if not isinstance(e.cause, HTTPError) or e.cause.status not in (401, 403):
                raise
            self.to_screen(
                'Reauthorizing with Nebula and retrying, because last API '
                'call resulted in error {0}'.format(e.cause.status))
            self._real_initialize()
            if self._token:
                kwargs = kwargs_set_token(kwargs)
            return self._download_json(*args, **kwargs)

    def _extract_formats(self, content_id, slug):
        for retry in (False, True):
            try:
                # fmts, subs = self._extract_m3u8_formats_and_subtitles(
                fmts, subs = self._extract_m3u8_formats(
                    'https://content.api.nebula.app/{0}s/{1}/manifest.m3u8'.format(
                        content_id.split(':', 1)[0], content_id),
                    slug, 'mp4', query={
                        'token': self._token,
                        'app_version': '23.10.0',
                        'platform': 'ios',
                    }), {}
                self._sort_formats(fmts)
                return {'formats': fmts, 'subtitles': subs}
            except ExtractorError as e:
                if not isinstance(e.cause, HTTPError):
                    raise
                if e.cause.status == 401:
                    self.raise_login_required()
                if not retry and e.cause.status == 403:
                    self.to_screen('Reauthorizing with Nebula and retrying, because fetching video resulted in error')
                    self._real_initialize()
                    continue
                raise

    def _extract_video_metadata(self, episode):
        channel_url = traverse_obj(
            episode, (('channel_slug', 'class_slug'), T(lambda u: urljoin('https://nebula.tv/', u))), get_all=False)
        return merge_dicts({
            'id': episode['id'].partition(':')[2],
            'title': episode['title'],
            'channel_url': channel_url,
            'uploader_url': channel_url,
        }, traverse_obj(episode, {
            'display_id': 'slug',
            'description': 'description',
            'timestamp': ('published_at', T(parse_iso8601)),
            'duration': ('duration', T(int_or_none)),
            'channel_id': 'channel_slug',
            'uploader_id': 'channel_slug',
            'channel': 'channel_title',
            'uploader': 'channel_title',
            'series': 'channel_title',
            'creator': 'channel_title',
            'thumbnail': ('images', 'thumbnail', 'src', T(url_or_none)),
            'episode_number': ('order', T(int_or_none)),

            # Old code was wrongly setting extractor_key from NebulaSubscriptionsIE
            # '_old_archive_ids': ('zype_id', {lambda x: [
            #    make_archive_id(NebulaIE, x), make_archive_id(NebulaSubscriptionsIE, x)] if x else None}),
        }))


class NebulaIE(NebulaBaseIE):
    IE_NAME = 'nebula:video'
    _VALID_URL = r'{0}/videos/(?P<id>[\w-]+)'.format(_BASE_URL_RE)
    _TESTS = [{
        'url': 'https://nebula.tv/videos/that-time-disney-remade-beauty-and-the-beast',
        'info_dict': {
            'id': '84ed544d-4afd-4723-8cd5-2b95261f0abf',
            'ext': 'mp4',
            'title': 'That Time Disney Remade Beauty and the Beast',
            'description': 'Note: this video was originally posted on YouTube with the sponsor read included. We weren’t able to remove it without reducing video quality, so it’s presented here in its original context.',
            'upload_date': '20180731',
            'timestamp': 1533009600,
            'channel': 'Lindsay Ellis',
            'channel_id': 'lindsayellis',
            'uploader': 'Lindsay Ellis',
            'uploader_id': 'lindsayellis',
            'uploader_url': r're:https://nebula\.(tv|app)/lindsayellis',
            'series': 'Lindsay Ellis',
            'display_id': 'that-time-disney-remade-beauty-and-the-beast',
            'channel_url': r're:https://nebula\.(tv|app)/lindsayellis',
            'creator': 'Lindsay Ellis',
            'duration': 2212,
            'thumbnail': r're:https?://images\.nebula\.tv/[a-f\d-]+$',
            # '_old_archive_ids': ['nebula 5c271b40b13fd613090034fd', 'nebulasubscriptions 5c271b40b13fd613090034fd'],
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
    }, {
        'url': 'https://nebula.tv/videos/the-logistics-of-d-day-landing-craft-how-the-allies-got-ashore',
        'md5': 'd05739cf6c38c09322422f696b569c23',
        'info_dict': {
            'id': '7e623145-1b44-4ca3-aa0b-ed25a247ea34',
            'ext': 'mp4',
            'title': 'Landing Craft - How The Allies Got Ashore',
            'description': r're:^In this episode we explore the unsung heroes of D-Day, the landing craft.',
            'upload_date': '20200327',
            'timestamp': 1585348140,
            'channel': 'Real Engineering — The Logistics of D-Day',
            'channel_id': 'd-day',
            'uploader': 'Real Engineering — The Logistics of D-Day',
            'uploader_id': 'd-day',
            'series': 'Real Engineering — The Logistics of D-Day',
            'display_id': 'the-logistics-of-d-day-landing-craft-how-the-allies-got-ashore',
            'creator': 'Real Engineering — The Logistics of D-Day',
            'duration': 841,
            'channel_url': 'https://nebula.tv/d-day',
            'uploader_url': 'https://nebula.tv/d-day',
            'thumbnail': r're:https?://images\.nebula\.tv/[a-f\d-]+$',
            # '_old_archive_ids': ['nebula 5e7e78171aaf320001fbd6be', 'nebulasubscriptions 5e7e78171aaf320001fbd6be'],
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
        'skip': 'Only available for registered users',
    }, {
        'url': 'https://nebula.tv/videos/money-episode-1-the-draw',
        'md5': 'ebe28a7ad822b9ee172387d860487868',
        'info_dict': {
            'id': 'b96c5714-9e2b-4ec3-b3f1-20f6e89cc553',
            'ext': 'mp4',
            'title': 'Episode 1: The Draw',
            'description': r'contains:There’s free money on offer… if the players can all work together.',
            'upload_date': '20200323',
            'timestamp': 1584980400,
            'channel': 'Tom Scott Presents: Money',
            'channel_id': 'tom-scott-presents-money',
            'uploader': 'Tom Scott Presents: Money',
            'uploader_id': 'tom-scott-presents-money',
            'uploader_url': 'https://nebula.tv/tom-scott-presents-money',
            'duration': 825,
            'channel_url': 'https://nebula.tv/tom-scott-presents-money',
            'series': 'Tom Scott Presents: Money',
            'display_id': 'money-episode-1-the-draw',
            'thumbnail': r're:https?://images\.nebula\.tv/[a-f\d-]+$',
            # '_old_archive_ids': ['nebula 5e779ebdd157bc0001d1c75a', 'nebulasubscriptions 5e779ebdd157bc0001d1c75a'],
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
        'skip': 'Only available for registered users',
    }, {
        'url': 'https://watchnebula.com/videos/money-episode-1-the-draw',
        'only_matching': True,
    }, {
        'url': 'https://nebula.tv/videos/tldrnewseu-did-the-us-really-blow-up-the-nordstream-pipelines',
        'info_dict': {
            'id': 'e389af9d-1dab-44f2-8788-ee24deb7ff0d',
            'ext': 'mp4',
            'display_id': 'tldrnewseu-did-the-us-really-blow-up-the-nordstream-pipelines',
            'title': 'Did the US Really Blow Up the NordStream Pipelines?',
            'description': 'md5:b4e2a14e3ff08f546a3209c75261e789',
            'upload_date': '20230223',
            'timestamp': 1677144070,
            'channel': 'TLDR News EU',
            'channel_id': 'tldrnewseu',
            'uploader': 'TLDR News EU',
            'uploader_id': 'tldrnewseu',
            'uploader_url': r're:https://nebula\.(tv|app)/tldrnewseu',
            'duration': 524,
            'channel_url': r're:https://nebula\.(tv|app)/tldrnewseu',
            'series': 'TLDR News EU',
            'thumbnail': r're:https?://images\.nebula\.tv/[a-f\d-]+$',
            'creator': 'TLDR News EU',
            # '_old_archive_ids': ['nebula 63f64c74366fcd00017c1513', 'nebulasubscriptions 63f64c74366fcd00017c1513'],
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
    }, {
        'url': 'https://beta.nebula.tv/videos/money-episode-1-the-draw',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        slug = self._match_id(url)
        url, smuggled_data = unsmuggle_url(url, {})
        if smuggled_data.get('id'):
            return merge_dicts({
                'id': smuggled_data['id'],
                'display_id': slug,
                'title': '',
            }, self._extract_formats(smuggled_data['id'], slug))

        metadata = self._call_api(
            'https://content.api.nebula.app/content/videos/{0}'.format(slug),
            slug, note='Fetching video metadata')
        return merge_dicts(
            self._extract_video_metadata(metadata),
            self._extract_formats(metadata['id'], slug),
            rev=True
        )


class NebulaClassIE(NebulaBaseIE):
    IE_NAME = 'nebula:media'
    _VALID_URL = r'{0}/(?!(?:myshows|library|videos)/)(?P<id>[\w-]+)/(?P<ep>[\w-]+)/?(?:$|[?#])'.format(_BASE_URL_RE)
    _TESTS = [{
        'url': 'https://nebula.tv/copyright-for-fun-and-profit/14',
        'info_dict': {
            'id': 'd7432cdc-c608-474d-942c-f74345daed7b',
            'ext': 'mp4',
            'display_id': '14',
            'channel_url': 'https://nebula.tv/copyright-for-fun-and-profit',
            'episode_number': 14,
            'thumbnail': r're:https?://images\.nebula\.tv/[a-f\d-]+$',
            'uploader_url': 'https://nebula.tv/copyright-for-fun-and-profit',
            'duration': 646,
            'episode': 'Episode 14',
            'title': 'Photos, Sculpture, and Video',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
        'skip': 'Only available for registered users',
    }, {
        'add_ies': [Art19IE],
        'url': 'https://nebula.tv/extremitiespodcast/pyramiden-the-high-arctic-soviet-ghost-town',
        'info_dict': {
            'ext': 'mp3',
            'id': '83ef3b53-049e-4211-b34e-7bb518e67d64',
            'description': r"re:(?s)20 years ago, what was previously the Soviet Union's .{467}#do-not-sell-my-info\.$",
            'series_id': 'e0223cfc-f39c-4ad4-8724-bd8731bd31b5',
            'modified_timestamp': 1629410982,
            'episode_id': '83ef3b53-049e-4211-b34e-7bb518e67d64',
            'series': 'Extremities',
            # 'modified_date': '20200903',
            'upload_date': '20200902',
            'title': 'Pyramiden: The High-Arctic Soviet Ghost Town',
            'release_timestamp': 1571237958,
            'thumbnail': r're:^https?://content\.production\.cdn\.art19\.com.*\.jpeg$',
            'duration': 1546.05714,
            'timestamp': 1599085555,
            'release_date': '20191016',
        },
    }, {
        'url': 'https://nebula.tv/thelayover/the-layover-episode-1',
        'info_dict': {
            'ext': 'mp3',
            'id': '9d74a762-00bb-45a8-9e8d-9ed47c04a1d0',
            'episode_number': 1,
            'thumbnail': r're:https?://images\.nebula\.tv/[a-f\d-]+$',
            'release_date': '20230304',
            'modified_date': '20230403',
            'series': 'The Layover',
            'episode_id': '9d74a762-00bb-45a8-9e8d-9ed47c04a1d0',
            'modified_timestamp': 1680554566,
            'duration': 3130.46401,
            'release_timestamp': 1677943800,
            'title': 'The Layover — Episode 1',
            'series_id': '874303a5-4900-4626-a4b6-2aacac34466a',
            'upload_date': '20230303',
            'episode': 'Episode 1',
            'timestamp': 1677883672,
            'description': 'md5:002cca89258e3bc7c268d5b8c24ba482',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': 'm3u8',
        },
        'skip': 'Only available for registered users',
    }]

    def _real_extract(self, url):
        slug, episode = self._match_valid_url(url).group('id', 'ep')
        url, smuggled_data = unsmuggle_url(url, {})
        if smuggled_data.get('id'):
            return merge_dicts({
                'id': smuggled_data['id'],
                'display_id': slug,
                'title': '',
            }, self._extract_formats(smuggled_data['id'], slug))

        metadata = self._call_api(
            'https://content.api.nebula.app/content/{0}/{1}/?include=lessons'.format(
                slug, episode),
            slug, note='Fetching class/podcast metadata')
        content_type = traverse_obj(metadata, 'type')
        if content_type == 'lesson':
            return merge_dicts(
                self._extract_video_metadata(metadata),
                self._extract_formats(metadata['id'], slug))
        elif content_type == 'podcast_episode':
            episode_url = metadata.get('episode_url')
            if not episode_url and metadata.get('premium'):
                self.raise_login_required()

            if Art19IE.suitable(episode_url):
                return self.url_result(episode_url, Art19IE.ie_key())
            return merge_dicts({
                'id': metadata['id'],
                'title': metadata['title'],
            }, traverse_obj(metadata, {
                'url': ('episode_url', T(url_or_none)),
                'description': ('description', T(str_or_none)),
                'timestamp': ('published_at', T(parse_iso8601)),
                'duration': ('duration', T(int_or_none)),
                'channel_id': ('channel_id', T(str_or_none)),
                'channel': ('channel_title', T(str_or_none)),
                'thumbnail': ('assets', 'regular', T(url_or_none)),
            }))

        raise ExtractorError('Unexpected content type {0!r}'.format(content_type))


class NebulaPlaylistBaseIE(NebulaBaseIE):
    _BASE_API_URL = 'https://content.api.nebula.app/'
    _API_QUERY = {'ordering': '-published_at'}

    @classmethod
    def _get_api_url(cls, item_id, path='/video_episodes/'):
        return update_url(cls._BASE_API_URL, path=path, query_update=cls._API_QUERY)

    @staticmethod
    def _get_episode_url(episode, episode_id):
        return 'https://nebula.tv/videos/{0}'.format(episode_id)

    @classmethod
    def url_result(cls, url, *args, **kwargs):
        url_transparent = kwargs.pop('url_transparent', False)
        smuggled_data = kwargs.pop('smuggled_data', None)
        if smuggled_data:
            url = smuggle_url(url, smuggled_data)
        ie_key = args[0] if len(args) > 0 else kwargs.get('ie_key')
        if not ie_key:
            args = (NebulaIE.ie_key(),) + args
        return merge_dicts(
            {'_type': 'url_transparent'} if url_transparent else {},
            super(NebulaPlaylistBaseIE, cls).url_result(url, *args),
            **kwargs)

    def _generate_playlist_entries(self, pl_id=None, slug=None, dl_note=None):
        next_url = self._get_api_url(pl_id)
        if dl_note is None:
            dl_note = self.IE_NAME.rpartition(':')[::2]
            if dl_note[0] and dl_note[1]:
                dl_note = '{0} '.format(dl_note[1])
            else:
                dl_note = ''
        slug = slug or pl_id
        for page_num in itertools.count(1):
            episodes = self._call_api(
                next_url, slug, note='Retrieving {0}page {1}'.format(
                    dl_note, page_num))
            for episode in traverse_obj(episodes, ('results', Ellipsis)):
                metadata = self._extract_video_metadata(episode)
                yield self.url_result(
                    self._get_episode_url(episode, metadata['display_id']),
                    smuggled_data={'id': episode['id']}, url_transparent=True,
                    **metadata)
            next_url = episodes.get('next')
            if not next_url:
                break


class NebulaSubscriptionsIE(NebulaPlaylistBaseIE):
    IE_NAME = 'nebula:subscriptions'
    _VALID_URL = r'{0}/myshows'.format(_BASE_URL_RE)
    _API_QUERY = {
        'following': 'true',
        'include': 'engagement',
        'ordering': '-published_at',
    }
    _TESTS = [{
        'url': 'https://nebula.tv/myshows',
        'playlist_mincount': 1,
        'info_dict': {
            'id': 'myshows',
        },
        'skip': 'You must be logged in to find your subscriptions',
    }]

    def _call_api(self, *args, **kwargs):

        try:
            return super(NebulaSubscriptionsIE, self)._call_api(*args, **kwargs)
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                self.raise_login_required('You must be logged in to find your subscriptions')
            raise

    def _real_extract(self, url):
        slug = url_basename(url)
        return self.playlist_result(self._generate_playlist_entries(slug), slug)


class NebulaChannelIE(NebulaPlaylistBaseIE):
    IE_NAME = 'nebula:channel'
    _VALID_URL = r'{0}/(?!myshows|library|videos)(?P<id>[\w-]+)/?(?:$|[?#])'.format(_BASE_URL_RE)
    _TESTS = [{
        'url': 'https://nebula.tv/tom-scott-presents-money',
        'info_dict': {
            'id': 'tom-scott-presents-money',
            'title': 'Tom Scott Presents: Money',
            'description': 'Tom Scott hosts a series all about trust, negotiation and money.',
        },
        'playlist_count': 5,
    }, {
        'url': 'https://nebula.tv/lindsayellis',
        'info_dict': {
            'id': 'lindsayellis',
            'title': 'Lindsay Ellis',
            'description': 'Enjoy these hottest of takes on Disney, Transformers, and Musicals.',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://nebula.tv/johnnyharris',
        'info_dict': {
            'id': 'johnnyharris',
            'title': 'Johnny Harris',
            'description': 'I make videos about maps and many other things.',
        },
        'playlist_mincount': 90,
    }, {
        'url': 'https://nebula.tv/copyright-for-fun-and-profit',
        'info_dict': {
            'id': 'copyright-for-fun-and-profit',
            'title': 'Copyright for Fun and Profit',
            'description': 'md5:6690248223eed044a9f11cd5a24f9742',
        },
        'playlist_count': 23,
    }, {
        'url': 'https://nebula.tv/trussissuespodcast',
        'info_dict': {
            'id': 'trussissuespodcast',
            'title': 'Bite the Ballot',
            'description': 'md5:a08c4483bc0b705881d3e0199e721385',
        },
        'playlist_mincount': 80,
    }]

    @classmethod
    def _get_api_url(cls, item_id, path='/video_channels/{0}/video_episodes/'):
        return super(NebulaChannelIE, cls)._get_api_url(
            item_id, path=path.format(item_id))

    @classmethod
    def _get_episode_url(cls, episode, episode_id):
        return (
            episode.get('share_url')
            or super(NebulaChannelIE, cls)._get_episode_url(episode, episode_id))

    def _generate_class_entries(self, channel):
        for lesson in traverse_obj(channel, ('lessons', Ellipsis)):
            metadata = self._extract_video_metadata(lesson)
            yield self.url_result(
                lesson.get('share_url') or 'https://nebula.tv/{0}/{1}'.format(
                    metadata['class_slug'], metadata['slug']),
                smuggled_data={'id': lesson['id']}, url_transparent=True,
                **metadata)

    def _generate_podcast_entries(self, collection_id, collection_slug):
        next_url = 'https://content.api.nebula.app/podcast_channels/{0}/podcast_episodes/?ordering=-published_at&premium=true'.format(
            collection_id)
        for page_num in itertools.count(1):
            episodes = self._call_api(next_url, collection_slug, note='Retrieving podcast page {0}'.format(page_num))

            for episode in traverse_obj(episodes, ('results', lambda _, v: url_or_none(v['share_url']))):
                yield self.url_result(episode['share_url'], NebulaClassIE)
            next_url = episodes.get('next')
            if not next_url:
                break

    def _real_extract(self, url):
        collection_slug = self._match_id(url)
        channel = self._call_api(
            'https://content.api.nebula.app/content/{0}/?include=lessons'.format(
                collection_slug),
            collection_slug, note='Retrieving channel')

        channel_type = traverse_obj(channel, 'type')
        if channel_type == 'class':
            entries = self._generate_class_entries(channel)
        elif channel_type == 'podcast_channel':
            entries = self._generate_podcast_entries(channel['id'], collection_slug)
        else:
            entries = self._generate_playlist_entries(channel['id'], collection_slug)

        return self.playlist_result(
            entries,
            playlist_id=collection_slug,
            playlist_title=channel.get('title'),
            playlist_description=channel.get('description'))
