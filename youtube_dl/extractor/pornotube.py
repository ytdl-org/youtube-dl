from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    sanitized_Request,
)


class PornotubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?pornotube\.com/(?:[^?#]*?)/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.pornotube.com/orientation/straight/video/4964/title/weird-hot-and-wet-science',
        'md5': '60fc5a4f0d93a97968fc7999d98260c9',
        'info_dict': {
            'id': '4964',
            'ext': 'mp4',
            'upload_date': '20141203',
            'title': 'Weird Hot and Wet Science',
            'description': 'md5:a8304bef7ef06cb4ab476ca6029b01b0',
            'categories': ['Adult Humor', 'Blondes'],
            'uploader': 'Alpha Blue Archives',
            'thumbnail': 're:^https?://.*\\.jpg$',
            'timestamp': 1417582800,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Fetch origin token
        js_config = self._download_webpage(
            'http://www.pornotube.com/assets/src/app/config.js', video_id,
            note='Download JS config')
        originAuthenticationSpaceKey = self._search_regex(
            r"constant\('originAuthenticationSpaceKey',\s*'([^']+)'",
            js_config, 'originAuthenticationSpaceKey')

        # Fetch actual token
        token_req_data = {
            'authenticationSpaceKey': originAuthenticationSpaceKey,
            'credentials': 'Clip Application',
        }
        token_req = sanitized_Request(
            'https://api.aebn.net/auth/v1/token/primal',
            data=json.dumps(token_req_data).encode('utf-8'))
        token_req.add_header('Content-Type', 'application/json')
        token_req.add_header('Origin', 'http://www.pornotube.com')
        token_answer = self._download_json(
            token_req, video_id, note='Requesting primal token')
        token = token_answer['tokenKey']

        # Get video URL
        delivery_req = sanitized_Request(
            'https://api.aebn.net/delivery/v1/clips/%s/MP4' % video_id)
        delivery_req.add_header('Authorization', token)
        delivery_info = self._download_json(
            delivery_req, video_id, note='Downloading delivery information')
        video_url = delivery_info['mediaUrl']

        # Get additional info (title etc.)
        info_req = sanitized_Request(
            'https://api.aebn.net/content/v1/clips/%s?expand='
            'title,description,primaryImageNumber,startSecond,endSecond,'
            'movie.title,movie.MovieId,movie.boxCoverFront,movie.stars,'
            'movie.studios,stars.name,studios.name,categories.name,'
            'clipActive,movieActive,publishDate,orientations' % video_id)
        info_req.add_header('Authorization', token)
        info = self._download_json(
            info_req, video_id, note='Downloading metadata')

        timestamp = int_or_none(info.get('publishDate'), scale=1000)
        uploader = info.get('studios', [{}])[0].get('name')
        movie_id = info['movie']['movieId']
        thumbnail = 'http://pic.aebn.net/dis/t/%s/%s_%08d.jpg' % (
            movie_id, movie_id, info['primaryImageNumber'])
        categories = [c['name'] for c in info.get('categories')]

        return {
            'id': video_id,
            'url': video_url,
            'title': info['title'],
            'description': info.get('description'),
            'timestamp': timestamp,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'categories': categories,
            'age_limit': 18,
        }
