from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
)


class VevoBaseIE(InfoExtractor):
    def _extract_json(self, webpage, video_id):
        return self._parse_json(
            self._search_regex(
                r'window\.__INITIAL_STORE__\s*=\s*({.+?});\s*</script>',
                webpage, 'initial store'),
            video_id)


class VevoIE(VevoBaseIE):
    '''
    Accepts urls from vevo.com or in the format 'vevo:{id}'
    (currently used by MTVIE and MySpaceIE)
    '''
    _VALID_URL = r'''(?x)
        (?:https?://(?:www\.)?vevo\.com/watch/(?!playlist|genre)(?:[^/]+/(?:[^/]+/)?)?|
           https?://cache\.vevo\.com/m/html/embed\.html\?video=|
           https?://videoplayer\.vevo\.com/embed/embedded\?videoId=|
           vevo:)
        (?P<id>[^&?#]+)'''

    _TESTS = [{
        'url': 'http://www.vevo.com/watch/hurts/somebody-to-die-for/GB1101300280',
        'md5': '95ee28ee45e70130e3ab02b0f579ae23',
        'info_dict': {
            'id': 'GB1101300280',
            'ext': 'mp4',
            'title': 'Hurts - Somebody to Die For',
            'timestamp': 1372032000,
            'upload_date': '20130624',
            'uploader': 'Hurts',
            'track': 'Somebody to Die For',
            'artist': 'Hurts',
        },
    }, {
        'note': 'v3 SMIL format',
        'url': 'http://www.vevo.com/watch/cassadee-pope/i-wish-i-could-break-your-heart/USUV71302923',
        'md5': 'f6ab09b034f8c22969020b042e5ac7fc',
        'info_dict': {
            'id': 'USUV71302923',
            'ext': 'mp4',
            'title': 'Cassadee Pope - I Wish I Could Break Your Heart',
            'timestamp': 1392681600,
            'upload_date': '20140218',
            'uploader': 'Cassadee Pope',
            'track': 'I Wish I Could Break Your Heart',
            'artist': 'Cassadee Pope',
        },
    }, {
        'note': 'Age-limited video',
        'url': 'https://www.vevo.com/watch/justin-timberlake/tunnel-vision-explicit/USRV81300282',
        'info_dict': {
            'id': 'USRV81300282',
            'ext': 'mp4',
            'title': 'Justin Timberlake - Tunnel Vision',
            'age_limit': 18,
            'timestamp': 1372809600,
            'upload_date': '20130703',
            'uploader': 'Justin Timberlake',
            'track': 'Tunnel Vision',
            'artist': 'Justin Timberlake',
        },
    }, {
        'note': 'No video_info',
        'url': 'http://www.vevo.com/watch/k-camp-1/Till-I-Die/USUV71503000',
        'md5': '8b83cc492d72fc9cf74a02acee7dc1b0',
        'info_dict': {
            'id': 'USUV71503000',
            'ext': 'mp4',
            'title': 'K Camp ft. T.I. - Till I Die',
            'age_limit': 18,
            'timestamp': 1449446400,
            'upload_date': '20151207',
            'uploader': 'K Camp',
            'track': 'Till I Die',
            'artist': 'K Camp',
        },
    }, {
        'note': 'Featured test',
        'url': 'https://www.vevo.com/watch/lemaitre/Wait/USUV71402190',
        'md5': 'd28675e5e8805035d949dc5cf161071d',
        'info_dict': {
            'id': 'USUV71402190',
            'ext': 'mp4',
            'title': 'Lemaitre ft. LoLo - Wait',
            'age_limit': 0,
            'uploader': 'Lemaitre',
            'track': 'Wait',
            'artist': 'Lemaitre',
        },
    }, {
        'note': 'Only available via webpage',
        'url': 'http://www.vevo.com/watch/GBUV71600656',
        'md5': '67e79210613865b66a47c33baa5e37fe',
        'info_dict': {
            'id': 'GBUV71600656',
            'ext': 'mp4',
            'title': 'ABC - Viva Love',
            'age_limit': 0,
            'uploader': 'ABC',
            'track': 'Viva Love',
            'artist': 'ABC',
        },
    }, {
        # no genres available
        'url': 'http://www.vevo.com/watch/INS171400764',
        'only_matching': True,
    }, {
        # Another case available only via the webpage; using streams/streamsV3 formats
        # Geo-restricted to Netherlands/Germany
        'url': 'http://www.vevo.com/watch/boostee/pop-corn-clip-officiel/FR1A91600909',
        'only_matching': True,
    }]
    _VERSIONS = {
        0: 'youtube',  # only in AuthenticateVideo videoVersions
        1: 'level3',
        2: 'akamai',
        3: 'level3',
        4: 'amazon',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'http://www.vevo.com/watch/%s' % video_id

        webpage = self._download_webpage(url, video_id)
        json_data = self._extract_json(webpage, video_id)

        data = json_data['apollo']['data']

        meta = data.get('$%s.basicMetaV3' % video_id, {})
        artists = []
        video_versions = []
        for key, value in data.items():
            if (key.startswith('$%s.basicMetaV3.artists.' % video_id) and
                key.endswith('.basicMeta')):
                artists.append(value)
            elif key.startswith('%s.streamsV3.' % video_id):
                video_versions.append(value)

        if 'streams' in json_data.get('default', {}):
            video_versions = json_data['default']['streams'][video_id][0]

        uploader = None
        artist = None
        featured_artists = []
        for curr_artist in artists:
            if curr_artist.get('role') == 'Featured':
                featured_artists.append(curr_artist['name'])
            else:
                artist = uploader = curr_artist['name']
        featured_artists.sort()

        formats = []
        for video_version in video_versions:
            version = self._VERSIONS.get(video_version.get('version'), 'generic')
            version_url = video_version.get('url')
            if not version_url:
                if video_version.get('errorCode') == 'video-not-viewable-in-country':
                    raise self.raise_geo_restricted()
                continue

            if '.ism' in version_url:
                continue
            elif '.mpd' in version_url:
                formats.extend(self._extract_mpd_formats(
                    version_url, video_id, mpd_id='dash-%s' % version,
                    note='Downloading %s MPD information' % version,
                    errnote='Failed to download %s MPD information' % version,
                    fatal=False))
            elif '.m3u8' in version_url:
                formats.extend(self._extract_m3u8_formats(
                    version_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls-%s' % version,
                    note='Downloading %s m3u8 information' % version,
                    errnote='Failed to download %s m3u8 information' % version,
                    fatal=False))
            else:
                m = re.search(r'''(?xi)
                    _(?P<width>[0-9]+)x(?P<height>[0-9]+)
                    _(?P<vcodec>[a-z0-9]+)
                    _(?P<vbr>[0-9]+)
                    _(?P<acodec>[a-z0-9]+)
                    _(?P<abr>[0-9]+)
                    \.(?P<ext>[a-z0-9]+)''', version_url)
                if not m:
                    continue

                formats.append({
                    'url': version_url,
                    'format_id': 'http-%s-%s' % (version, video_version['quality']),
                    'vcodec': m.group('vcodec'),
                    'acodec': m.group('acodec'),
                    'vbr': int(m.group('vbr')),
                    'abr': int(m.group('abr')),
                    'ext': m.group('ext'),
                    'width': int(m.group('width')),
                    'height': int(m.group('height')),
                })
        self._sort_formats(formats)

        track = meta['title']
        if featured_artists:
            artist = '%s ft. %s' % (artist, ' & '.join(featured_artists))
        title = '%s - %s' % (artist, track) if artist else track

        is_explicit = meta.get('explicit')
        if is_explicit is True:
            age_limit = 18
        elif is_explicit is False:
            age_limit = 0
        else:
            age_limit = None

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': meta.get('thumbnailUrl'),
            'timestamp': parse_iso8601(data.get('$%s.basicMetaV3.premieres.0' % video_id, {}).get('startDate')),
            'uploader': uploader,
            'duration': int_or_none(meta.get('duration')),
            'view_count': int_or_none(data.get('$%s.views' % video_id, {}).get('viewsTotal')),
            'age_limit': age_limit,
            'track': track,
            'artist': uploader,
        }


class VevoPlaylistIE(VevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?vevo\.com/watch/(?P<kind>playlist|genre)/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.vevo.com/watch/playlist/dadbf4e7-b99f-4184-9670-6f0e547b6a29',
        'info_dict': {
            'id': 'dadbf4e7-b99f-4184-9670-6f0e547b6a29',
            'title': 'Best Of: Birdman',
            'description': 'Ca$h Money Records\' ballin\' boss turns 48 today.',
        },
        'playlist_count': 24,
    }, {
        'url': 'http://www.vevo.com/watch/genre/rock',
        'info_dict': {
            'id': 'rock',
            'title': 'Rock',
        },
        'playlist_count': 20,
    }, {
        'url': 'http://www.vevo.com/watch/playlist/dadbf4e7-b99f-4184-9670-6f0e547b6a29?index=1',
        'md5': '32dcdfddddf9ec6917fc88ca26d36282',
        'info_dict': {
            'id': 'USCMV1100073',
            'ext': 'mp4',
            'title': 'Birdman ft. Lil Wayne & Nicki Minaj - Y.U. MAD',
            'uploader': 'Birdman',
            'track': 'Y.U. MAD',
            'artist': 'Birdman',
        },
        'params': {
            'noplaylist': True,
        },
    }, {
        'url': 'http://www.vevo.com/watch/genre/rock?index=0',
        'only_matching': True,
    }]

    _MORE_VIDEOS_URL = 'https://veil.vevoprd.com/graphql'

    _JSON_TEMPLATE = ('''{"query":"query MorePlaylistVideos($id:String){'''
                      '''playlists(ids:[$id]){videos(limit:%d,offset:0){'''
                      '''items{isrc}}}}","variables":{"id":"%s"}}''')

    def _download_single(self, video_id):
        
        return self._single_result(video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        playlist_kind = mobj.group('kind')

        webpage = self._download_webpage(url, playlist_id)

        json_data = self._extract_json(webpage, playlist_id)
        data = json_data['apollo']['data']
        meta = data['$%s.basicMeta' % playlist_id]

        if playlist_kind == 'genre':
            playlist_count = 20
            playlist = [
                item['id']
                for item in data['$%s.videos' % playlist_id]['data']
            ]
        else:
            playlist_count = meta['videoCount']
            token = json_data.get('default', {}).get('user',
                {}).get('accessTokens', {}).get('access_token')
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer %s' % token,
            }
            json_data = self._download_json(self._MORE_VIDEOS_URL,
                playlist_id, headers=headers, data=(self._JSON_TEMPLATE
                % (playlist_count, playlist_id)).encode('utf-8'))
            playlist = [
                item['isrc']
                for item in json_data['data']['playlists'][0]['videos']['items']
            ]

        entries = [
            self.url_result('vevo:%s' % video_id, VevoIE.ie_key())
            for video_id in playlist
        ]

        qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        index = int_or_none(qs.get('index', [None])[0])

        if self._downloader.params.get('noplaylist') and not index is None:
            if 0 <= index < playlist_count:
                self.to_screen('Downloading just video %s because'
                               'of --no-playlist' % playlist[index])
                return entries[index]
            else:
                raise ExtractorError('Video of index %s not found'
                                     ' on this playlist' % index)

        self.to_screen('Downloading playlist %s - add --no-playlist'
                       ' to just download video' % playlist_id)

        return self.playlist_result(
            entries, playlist_id, meta.get('title')
            or meta.get('name'), meta.get('description'))
