# encoding: utf-8
from __future__ import unicode_literals

from .brightcove import BrightcoveIE
from .common import InfoExtractor
from ..utils import ExtractorError
from ..compat import compat_urllib_request


class NownessBaseIE(InfoExtractor):
    def extract_url_result(self, post):
        if post['type'] == 'video':
            for media in post['media']:
                if media['type'] == 'video':
                    video_id = media['content']
                    source = media['source']
                    if source == 'brightcove':
                        player_code = self._download_webpage(
                            'http://www.nowness.com/iframe?id=%s' % video_id, video_id,
                            note='Downloading player JavaScript',
                            errnote='Player download failed')
                        bc_url = BrightcoveIE._extract_brightcove_url(player_code)
                        if bc_url is None:
                            raise ExtractorError('Could not find player definition')
                        return self.url_result(bc_url, 'Brightcove')
                    elif source == 'vimeo':
                        return self.url_result('http://vimeo.com/%s' % video_id, 'Vimeo')
                    elif source == 'youtube':
                        return self.url_result(video_id, 'Youtube')
                    elif source == 'cinematique':
                        # youtube-dl currently doesn't support cinematique
                        # return self.url_result('http://cinematique.com/embed/%s' % video_id, 'Cinematique')
                        pass

    def api_request(self, url, request_path):
        display_id = self._match_id(url)

        lang = 'zh-cn' if 'cn.nowness.com' in url else 'en-us'
        request = compat_urllib_request.Request('http://api.nowness.com/api/' + request_path % display_id, headers={
            'X-Nowness-Language': lang,
        })
        json_data = self._download_json(request, display_id)
        return display_id, json_data


class NownessIE(NownessBaseIE):
    IE_NAME = 'nowness'
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/(?:story|(?:series|category)/[^/]+)/(?P<id>[^/]+?)(?:$|[?#])'
    _TESTS = [
        {
            'url': 'https://www.nowness.com/story/candor-the-art-of-gesticulation',
            'md5': '068bc0202558c2e391924cb8cc470676',
            'info_dict': {
                'id': '2520295746001',
                'ext': 'mp4',
                'title': 'Candor: The Art of Gesticulation',
                'description': 'Candor: The Art of Gesticulation',
                'thumbnail': 're:^https?://.*\.jpg',
                'uploader': 'Nowness',
            }
        },
        {
            'url': 'https://cn.nowness.com/story/kasper-bjorke-ft-jaakko-eino-kalevi-tnr',
            'md5': 'e79cf125e387216f86b2e0a5b5c63aa3',
            'info_dict': {
                'id': '3716354522001',
                'ext': 'mp4',
                'title': 'Kasper Bjørke ft. Jaakko Eino Kalevi: TNR',
                'description': 'Kasper Bjørke ft. Jaakko Eino Kalevi: TNR',
                'thumbnail': 're:^https?://.*\.jpg',
                'uploader': 'Nowness',
            }
        },
    ]

    def _real_extract(self, url):
        display_id, post = self.api_request(url, 'post/getBySlug/%s')
        return self.extract_url_result(post)


class NownessPlaylistIE(NownessBaseIE):
    IE_NAME = 'nowness:playlist'
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/playlist/(?P<id>\d+)'
    _TEST = {
        'url': 'https://www.nowness.com/playlist/3286/i-guess-thats-why-they-call-it-the-blues',
        'info_dict':
        {
            'id': '3286',
        },
        'playlist_mincount': 8,
    }

    def _real_extract(self, url):
        playlist_id, playlist = self.api_request(url, 'post?PlaylistId=%s')
        entries = [self.extract_url_result(item) for item in playlist['items']]
        return self.playlist_result(entries, playlist_id)


class NownessSerieIE(NownessBaseIE):
    IE_NAME = 'nowness:serie'
    _VALID_URL = r'https?://(?:(?:www|cn)\.)?nowness\.com/series/(?P<id>[^/]+?)(?:$|[?#])'
    _TEST = {
        'url': 'https://www.nowness.com/series/60-seconds',
        'info_dict':
        {
            'id': '60',
        },
        'playlist_mincount': 4,
    }

    def _real_extract(self, url):
        display_id, serie = self.api_request(url, 'series/getBySlug/%s')
        serie_id = str(serie['id'])
        entries = [self.extract_url_result(post) for post in serie['posts']]
        return self.playlist_result(entries, serie_id)
