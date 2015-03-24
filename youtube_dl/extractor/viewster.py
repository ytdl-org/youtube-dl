from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_request


class ViewsterIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?viewster\.com/movie/(?P<id>\d+-\d+-\d+)'
    _TESTS = [{
        # movielink, paymethod=fre
        'url': 'http://www.viewster.com/movie/1293-19341-000/hout-wood/',
        'playlist': [{
            'md5': '8f9d94b282d80c42b378dffdbb11caf3',
            'info_dict': {
                'id': '1293-19341-000-movie',
                'ext': 'flv',
                'title': "'Hout' (Wood) - Movie",
            },
        }],
        'info_dict': {
            'id': '1293-19341-000',
            'title': "'Hout' (Wood)",
            'description': 'md5:925733185a9242ef96f436937683f33b',
        }
    }, {
        # movielink, paymethod=adv
        'url': 'http://www.viewster.com/movie/1140-11855-000/the-listening-project/',
        'playlist': [{
            'md5': '77a005453ca7396cbe3d35c9bea30aef',
            'info_dict': {
                'id': '1140-11855-000-movie',
                'ext': 'flv',
                'title': "THE LISTENING PROJECT - Movie",
            },
        }],
        'info_dict': {
            'id': '1140-11855-000',
            'title': "THE LISTENING PROJECT",
            'description': 'md5:714421ae9957e112e672551094bf3b08',
        }
    }, {
        # direct links, no movielink
        'url': 'http://www.viewster.com/movie/1198-56411-000/sinister/',
        'playlist': [{
            'md5': '0307b7eac6bfb21ab0577a71f6eebd8f',
            'info_dict': {
                'id': '1198-56411-000-trailer',
                'ext': 'mp4',
                'title': "Sinister - Trailer",
            },
        }, {
            'md5': '80b9ee3ad69fb368f104cb5d9732ae95',
            'info_dict': {
                'id': '1198-56411-000-behind-scenes',
                'ext': 'mp4',
                'title': "Sinister - Behind Scenes",
            },
        }, {
            'md5': '3b3ea897ecaa91fca57a8a94ac1b15c5',
            'info_dict': {
                'id': '1198-56411-000-scene-from-movie',
                'ext': 'mp4',
                'title': "Sinister - Scene from movie",
            },
        }],
        'info_dict': {
            'id': '1198-56411-000',
            'title': "Sinister",
            'description': 'md5:014c40b0488848de9683566a42e33372',
        }
    }]

    _ACCEPT_HEADER = 'application/json, text/javascript, */*; q=0.01'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        request = compat_urllib_request.Request(
            'http://api.live.viewster.com/api/v1/movie/%s' % video_id)
        request.add_header('Accept', self._ACCEPT_HEADER)

        movie = self._download_json(
            request, video_id, 'Downloading movie metadata JSON')

        title = movie.get('title') or movie['original_title']
        description = movie.get('synopsis')
        thumbnail = movie.get('large_artwork') or movie.get('artwork')

        entries = []
        for clip in movie['play_list']:
            entry = None

            # movielink api
            link_request = clip.get('link_request')
            if link_request:
                request = compat_urllib_request.Request(
                    'http://api.live.viewster.com/api/v1/movielink?movieid=%(movieid)s&action=%(action)s&paymethod=%(paymethod)s&price=%(price)s&currency=%(currency)s&language=%(language)s&subtitlelanguage=%(subtitlelanguage)s&ischromecast=%(ischromecast)s'
                    % link_request)
                request.add_header('Accept', self._ACCEPT_HEADER)

                movie_link = self._download_json(
                    request, video_id, 'Downloading movie link JSON', fatal=False)

                if movie_link:
                    formats = self._extract_f4m_formats(
                        movie_link['url'] + '&hdcore=3.2.0&plugin=flowplayer-3.2.0.1', video_id)
                    self._sort_formats(formats)
                    entry = {
                        'formats': formats,
                    }

            # direct link
            clip_url = clip.get('clip_data', {}).get('url')
            if clip_url:
                entry = {
                    'url': clip_url,
                    'ext': 'mp4',
                }

            if entry:
                entry.update({
                    'id': '%s-%s' % (video_id, clip['canonical_title']),
                    'title': '%s - %s' % (title, clip['title']),
                })
                entries.append(entry)

        playlist = self.playlist_result(entries, video_id, title, description)
        playlist['thumbnail'] = thumbnail
        return playlist
