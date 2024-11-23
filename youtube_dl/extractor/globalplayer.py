# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    join_nonempty,
    merge_dicts,
    parse_duration,
    str_or_none,
    T,
    traverse_obj,
    unified_strdate,
    unified_timestamp,
    urlhandle_detect_ext,
)


class GlobalPlayerBaseIE(InfoExtractor):

    def _get_page_props(self, url, video_id):
        webpage = self._download_webpage(url, video_id)
        return self._search_nextjs_data(webpage, video_id)['props']['pageProps']

    def _request_ext(self, url, video_id):
        return urlhandle_detect_ext(self._request_webpage(  # Server rejects HEAD requests
            url, video_id, note='Determining source extension'))

    @staticmethod
    def _clean_desc(x):
        x = clean_html(x)
        if x:
            x = x.replace('\xa0', ' ')
        return x

    def _extract_audio(self, episode, series):

        return merge_dicts({
            'vcodec': 'none',
        }, traverse_obj(series, {
            'series': 'title',
            'series_id': 'id',
            'thumbnail': 'imageUrl',
            'uploader': 'itunesAuthor',  # podcasts only
        }), traverse_obj(episode, {
            'id': 'id',
            'description': ('description', T(self._clean_desc)),
            'duration': ('duration', T(parse_duration)),
            'thumbnail': 'imageUrl',
            'url': 'streamUrl',
            'timestamp': (('pubDate', 'startDate'), T(unified_timestamp)),
            'title': 'title',
        }, get_all=False), rev=True)


class GlobalPlayerLiveIE(GlobalPlayerBaseIE):
    _VALID_URL = r'https?://www\.globalplayer\.com/live/(?P<id>\w+)/\w+'
    _TESTS = [{
        'url': 'https://www.globalplayer.com/live/smoothchill/uk/',
        'info_dict': {
            'id': '2mx1E',
            'ext': 'aac',
            'display_id': 'smoothchill-uk',
            'title': 're:^Smooth Chill.+$',
            'thumbnail': 'https://herald.musicradio.com/media/f296ade8-50c9-4f60-911f-924e96873620.png',
            'description': 'Music To Chill To',
            # 'live_status': 'is_live',
            'is_live': True,
        },
    }, {
        # national station
        'url': 'https://www.globalplayer.com/live/heart/uk/',
        'info_dict': {
            'id': '2mwx4',
            'ext': 'aac',
            'description': 'turn up the feel good!',
            'thumbnail': 'https://herald.musicradio.com/media/49b9e8cb-15bf-4bf2-8c28-a4850cc6b0f3.png',
            # 'live_status': 'is_live',
            'is_live': True,
            'title': 're:^Heart UK.+$',
            'display_id': 'heart-uk',
        },
    }, {
        # regional variation
        'url': 'https://www.globalplayer.com/live/heart/london/',
        'info_dict': {
            'id': 'AMqg',
            'ext': 'aac',
            'thumbnail': 'https://herald.musicradio.com/media/49b9e8cb-15bf-4bf2-8c28-a4850cc6b0f3.png',
            'title': 're:^Heart London.+$',
            # 'live_status': 'is_live',
            'is_live': True,
            'display_id': 'heart-london',
            'description': 'turn up the feel good!',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        station = self._get_page_props(url, video_id)['station']
        stream_url = station['streamUrl']

        return merge_dicts({
            'id': station['id'],
            'display_id': (
                join_nonempty('brandSlug', 'slug', from_dict=station)
                or station.get('legacyStationPrefix')),
            'url': stream_url,
            'ext': self._request_ext(stream_url, video_id),
            'vcodec': 'none',
            'is_live': True,
        }, {
            'title': self._live_title(traverse_obj(
                station, (('name', 'brandName'), T(str_or_none)),
                get_all=False)),
        }, traverse_obj(station, {
            'description': 'tagline',
            'thumbnail': 'brandLogo',
        }), rev=True)


class GlobalPlayerLivePlaylistIE(GlobalPlayerBaseIE):
    _VALID_URL = r'https?://www\.globalplayer\.com/playlists/(?P<id>\w+)'
    _TESTS = [{
        # "live playlist"
        'url': 'https://www.globalplayer.com/playlists/8bLk/',
        'info_dict': {
            'id': '8bLk',
            'ext': 'aac',
            # 'live_status': 'is_live',
            'is_live': True,
            'description': r're:(?s).+\bclassical\b.+\bClassic FM Hall [oO]f Fame\b',
            'thumbnail': 'https://images.globalplayer.com/images/551379?width=450&signature=oMLPZIoi5_dBSHnTMREW0Xg76mA=',
            'title': 're:Classic FM Hall of Fame.+$'
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        station = self._get_page_props(url, video_id)['playlistData']
        stream_url = station['streamUrl']

        return merge_dicts({
            'id': video_id,
            'url': stream_url,
            'ext': self._request_ext(stream_url, video_id),
            'vcodec': 'none',
            'is_live': True,
        }, traverse_obj(station, {
            'title': 'title',
            'description': ('description', T(self._clean_desc)),
            'thumbnail': 'image',
        }), rev=True)


class GlobalPlayerAudioIE(GlobalPlayerBaseIE):
    _VALID_URL = r'https?://www\.globalplayer\.com/(?:(?P<podcast>podcasts)/|catchup/\w+/\w+/)(?P<id>\w+)/?(?:$|[?#])'
    _TESTS = [{
        # podcast
        'url': 'https://www.globalplayer.com/podcasts/42KuaM/',
        'playlist_mincount': 5,
        'info_dict': {
            'id': '42KuaM',
            'title': 'Filthy Ritual',
            'thumbnail': 'md5:60286e7d12d795bd1bbc9efc6cee643e',
            'categories': ['Society & Culture', 'True Crime'],
            'uploader': 'Global',
            'description': r're:(?s).+\bscam\b.+?\bseries available now\b',
        },
    }, {
        # radio catchup
        'url': 'https://www.globalplayer.com/catchup/lbc/uk/46vyD7z/',
        'playlist_mincount': 2,
        'info_dict': {
            'id': '46vyD7z',
            'description': 'Nick Ferrari At Breakfast is Leading Britain\'s Conversation.',
            'title': 'Nick Ferrari',
            'thumbnail': 'md5:4df24d8a226f5b2508efbcc6ae874ebf',
        },
    }]

    def _real_extract(self, url):
        video_id, podcast = self._match_valid_url(url).group('id', 'podcast')
        props = self._get_page_props(url, video_id)
        series = props['podcastInfo'] if podcast else props['catchupInfo']

        return merge_dicts({
            '_type': 'playlist',
            'id': video_id,
            'entries': [self._extract_audio(ep, series) for ep in traverse_obj(
                        series, ('episodes', lambda _, v: v['id'] and v['streamUrl']))],
            'categories': traverse_obj(series, ('categories', Ellipsis, 'name')) or None,
        }, traverse_obj(series, {
            'description': ('description', T(self._clean_desc)),
            'thumbnail': 'imageUrl',
            'title': 'title',
            'uploader': 'itunesAuthor',  # podcasts only
        }), rev=True)


class GlobalPlayerAudioEpisodeIE(GlobalPlayerBaseIE):
    _VALID_URL = r'https?://www\.globalplayer\.com/(?:(?P<podcast>podcasts)|catchup/\w+/\w+)/episodes/(?P<id>\w+)/?(?:$|[?#])'
    _TESTS = [{
        # podcast
        'url': 'https://www.globalplayer.com/podcasts/episodes/7DrfNnE/',
        'info_dict': {
            'id': '7DrfNnE',
            'ext': 'mp3',
            'title': 'Filthy Ritual - Trailer',
            'description': 'md5:1f1562fd0f01b4773b590984f94223e0',
            'thumbnail': 'md5:60286e7d12d795bd1bbc9efc6cee643e',
            'duration': 225.0,
            'timestamp': 1681254900,
            'series': 'Filthy Ritual',
            'series_id': '42KuaM',
            'upload_date': '20230411',
            'uploader': 'Global',
        },
    }, {
        # radio catchup
        'url': 'https://www.globalplayer.com/catchup/lbc/uk/episodes/2zGq26Vcv1fCWhddC4JAwETXWe/',
        'only_matching': True,
        # expired: refresh the details with a current show for a full test
        'info_dict': {
            'id': '2zGq26Vcv1fCWhddC4JAwETXWe',
            'ext': 'm4a',
            'timestamp': 1682056800,
            'series': 'Nick Ferrari',
            'thumbnail': 'md5:4df24d8a226f5b2508efbcc6ae874ebf',
            'upload_date': '20230421',
            'series_id': '46vyD7z',
            'description': 'Nick Ferrari At Breakfast is Leading Britain\'s Conversation.',
            'title': 'Nick Ferrari',
            'duration': 10800.0,
        },
    }]

    def _real_extract(self, url):
        video_id, podcast = self._match_valid_url(url).group('id', 'podcast')
        props = self._get_page_props(url, video_id)
        episode = props['podcastEpisode'] if podcast else props['catchupEpisode']

        return self._extract_audio(
            episode, traverse_obj(episode, 'podcast', 'show', expected_type=dict) or {})


class GlobalPlayerVideoIE(GlobalPlayerBaseIE):
    _VALID_URL = r'https?://www\.globalplayer\.com/videos/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://www.globalplayer.com/videos/2JsSZ7Gm2uP/',
        'info_dict': {
            'id': '2JsSZ7Gm2uP',
            'ext': 'mp4',
            'description': 'md5:6a9f063c67c42f218e42eee7d0298bfd',
            'thumbnail': 'md5:d4498af48e15aae4839ce77b97d39550',
            'upload_date': '20230420',
            'title': 'Treble Malakai Bayoh sings a sublime Handel aria at Classic FM Live',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._get_page_props(url, video_id)['videoData']

        return merge_dicts({
            'id': video_id,
        }, traverse_obj(meta, {
            'url': 'url',
            'thumbnail': ('image', 'url'),
            'title': 'title',
            'upload_date': ('publish_date', T(unified_strdate)),
            'description': 'description',
        }), rev=True)
