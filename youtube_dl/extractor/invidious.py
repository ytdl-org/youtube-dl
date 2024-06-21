from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse

INSTANCES = [
    'y.com.sb',
    'yt.artemislena.eu'
]

INSTANCES_HOST_REGEX = '(?:' + '|'.join([instance.replace('.', r'\.') for instance in INSTANCES]) + ')'


class InvidiousIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?' + INSTANCES_HOST_REGEX + r'/watch\?v=(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://y.com.sb/watch?v=xKTygGa6hg0',
            'info_dict': {
                'id': 'xKTygGa6hg0',
                'ext': 'mp4',
                'title': 'Coding in C++ - Creating a Player Controller - CRYENGINE Summer Academy S1E5 - [Tutorial]',
                'uploader': 'CRYENGINE',
                'uploader_id': 'UCtaXcIVFp8HEpthm7qwtKCQ',
                'description': 'md5:7aa75816d40ffccdbf3e15a90b05fca3',
            }
        },
        {
            'url': 'https://yt.artemislena.eu/watch?v=BaW_jenozKc',
            'md5': '5515885fed58607bfae88f7d2090bc93',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
                'channel_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'tags': ['youtube-dl'],
                'duration': 10,
                'view_count': int,
                'like_count': int,
                'dislike_count': int,
            }
        },
    ]

    def __init__(self, downloader=None):
        super().__init__(downloader)

    # type is either 'video' or 'audio'
    # ext is the file extension
    @staticmethod
    def _get_additional_format_data(format_type, bitrate, resolution, fps):
        out = {}

        try:
            type_and_ext, codecs = format_type.split(';')
        except Exception:
            pass

        try:
            type_, ext = type_and_ext.split('/')
            # codec = codecs.split('"')[1]
            out['ext'] = ext
            # if type_ == 'audio':
            #     out['acodec'] = codec
            # elif type_ == 'video':
            #     out['vcodec'] = codec
        except Exception:
            pass

        try:
            bitrate = float(bitrate) / 1000
            # if type_ == 'audio':
            #     out['abr'] = bitrate
            # elif type_ == 'video':
            #     out['vbr'] = bitrate
            # out['tbr'] = bitrate
        except Exception:
            pass

        try:
            if type_ == 'audio':
                out['resolution'] = type_and_ext + ' @ ' + str(bitrate) + 'k - audio only'
            elif type_ == 'video':
                out['resolution'] = resolution + ' - ' + type_and_ext + ' @ ' + str(fps) + 'fps - video only'
        except Exception:
            pass

        return out

    def _patch_url(self, url):
        return compat_urllib_parse.urlparse(url)._replace(netloc=self.url_netloc).geturl()

    def _get_formats(self, api_response):
        all_formats = []

        # Video/audio only
        for format_ in api_response.get('adaptiveFormats') or []:
            all_formats.append({
                'url': self._patch_url(format_['url']),
                'format_id': format_.get('itag'),
                # 'fps': format_.get('fps'),
                # 'container': format_.get('container')
            } | InvidiousIE._get_additional_format_data(format_.get('type'), format_.get('bitrate'), format_.get('resolution'), format_.get('fps')))

        # Both video and audio
        for format_ in api_response.get('formatStreams') or []:
            all_formats.append({
                'url': self._patch_url(format_['url']),
                'format_id': format_.get('itag'),
                # 'fps': format_.get('fps'),
                # 'container': format_.get('container')
            } | InvidiousIE._get_additional_format_data(format_.get('type'), format_.get('bitrate'), format_.get('resolution'), format_.get('fps')))

        return all_formats

    def _get_thumbnails(self, api_response):
        thumbnails = []
        video_thumbnails = api_response.get('videoThumbnails') or []

        for inversed_quality, thumbnail in enumerate(video_thumbnails):
            thumbnails.append({
                'id': thumbnail.get('quality'),
                'url': thumbnail.get('url'),
                'quality': len(video_thumbnails) - inversed_quality,
                'width': thumbnail.get('width'),
                'height': thumbnail.get('height')
            })

        return thumbnails

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = None

        # host_url will contain `http[s]://example.com` where `example.com` is the used invidious instance.
        url_parsed = compat_urllib_parse.urlparse(url)
        self.url_netloc = url_parsed.netloc
        host_url = url_parsed.scheme + '://' + url_parsed.netloc

        api_response = self._download_json(host_url + '/api/v1/videos/' + video_id, video_id)

        def download_webpage_and(fn, fatal=True):
            global webpage
            if webpage is None:
                webpage = self._download_webpage(url, video_id, fatal=fatal)
            return fn()

        out = {
            'id': video_id,
            'title': api_response.get('title') or download_webpage_and(lambda: self._og_search_title(webpage)),
            'description': api_response.get('description') or download_webpage_and(lambda: self._og_search_description(webpage)),

            'release_timestamp': api_response.get('published'),

            'uploader': api_response.get('author'),
            'uploader_id': api_response.get('authorId'),
            'channel': api_response.get('author'),
            'channel_id': api_response.get('authorId'),
            'channel_url': host_url + api_response.get('authorUrl'),

            'duration': api_response.get('lengthSeconds'),

            'view_count': api_response.get('viewCount'),
            'like_count': api_response.get('likeCount'),
            'dislike_count': api_response.get('dislikeCount'),

            # 'isFamilyFriendly': 18 if api_response.get('isFamilyFriendly') == False else None

            'tags': api_response.get('keywords'),
            'is_live': api_response.get('liveNow'),

            'formats': self._get_formats(api_response),
            'thumbnails': self._get_thumbnails(api_response)
        }

        if api_response.get('isFamilyFriendly') is False:
            out['age_limit'] = 18

        return out


class InvidiousPlaylistIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?' + INSTANCES_HOST_REGEX + r'/playlist\?list=(?P<id>.+)'
    _TEST = {
        'url': 'https://yt.artemislena.eu/playlist?list=PLowKtXNTBypGqImE405J2565dvjafglHU',
        'md5': 'de4a9175071169961fe7cf2b6740da12',
        'info_dict': {
            'id': 'HyznrdDSSGM',
            'ext': 'mp4',
            'title': '8-bit computer update',
            'uploader': 'Ben Eater',
            'uploader_id': 'UCS0N5baNlQWJCUrhCEo8WlA',
            'description': 'An update on my plans to build another 8-bit computer from scratch and make videos of the whole process! Buy a kit and build your own! https://eater.net/8bit/kits\n\nSupport me on Patreon: https://www.patreon.com/beneater',
        }
    }

    def _get_entries(self, api_response):
        return [InvidiousIE(self._downloader)._real_extract(self.host_url + '/watch?v=' + video['videoId'])
                for video in api_response['videos']]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        # host_url will contain `http[s]://example.com` where `example.com` is the used invidious instance.
        url_parsed = compat_urllib_parse.urlparse(url)
        self.host_url = url_parsed.scheme + '://' + url_parsed.netloc

        api_response = self._download_json(self.host_url + '/api/v1/playlists/' + playlist_id, playlist_id)
        return InfoExtractor.playlist_result(self._get_entries(api_response), playlist_id, api_response.get('title'), api_response.get('description')) | {
            'release_timestamp': api_response.get('updated'),

            'uploader': api_response.get('author'),
            'uploader_id': api_response.get('authorId'),
        }
