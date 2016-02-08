# coding: utf-8
from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor


class TVLandIE(MTVServicesInfoExtractor):
    IE_NAME = 'tvland.com'
    _VALID_URL = r'https?://(?:www\.)?tvland\.com/(?:video-clips|episodes)/(?P<id>[^/?#.]+)'
    _FEED_URL = 'http://www.tvland.com/feeds/mrss/'
    _TESTS = [{
        'url': 'http://www.tvland.com/episodes/hqhps2/everybody-loves-raymond-the-invasion-ep-048',
        'playlist': [
            {
                'md5': '227e9723b9669c05bf51098b10287aa7',
                'info_dict': {
                    'id': 'bcbd3a83-3aca-4dca-809b-f78a87dcccdd',
                    'ext': 'mp4',
                    'title': 'Everybody Loves Raymond|Everybody Loves Raymond 048 HD, Part 1 of 5',
                }
            },
            {
                'md5': '9fa2b764ec0e8194fb3ebb01a83df88b',
                'info_dict': {
                    'id': 'f4279548-6e13-40dd-92e8-860d27289197',
                    'ext': 'mp4',
                    'title': 'Everybody Loves Raymond|Everybody Loves Raymond 048 HD, Part 2 of 5',
                }
            },
            {
                'md5': 'fde4c3bccd7cc7e3576b338734153cec',
                'info_dict': {
                    'id': '664e4a38-53ef-4115-9bc9-d0f789ec6334',
                    'ext': 'mp4',
                    'title': 'Everybody Loves Raymond|Everybody Loves Raymond 048 HD, Part 3 of 5',
                }
            },
            {
                'md5': '247f6780cda6891f2e49b8ae2b10e017',
                'info_dict': {
                    'id': '9146ecf5-b15a-4d78-879c-6679b77f4960',
                    'ext': 'mp4',
                    'title': 'Everybody Loves Raymond|Everybody Loves Raymond 048 HD, Part 4 of 5',
                }
            },
            {
                'md5': 'fd269f33256e47bad5eb6c40de089ff6',
                'info_dict': {
                    'id': '04334a2e-9a47-4214-a8c2-ae5792e2fab7',
                    'ext': 'mp4',
                    'title': 'Everybody Loves Raymond|Everybody Loves Raymond 048 HD, Part 5 of 5',
                }
            }
        ],
    }, {
        'url': 'http://www.tvland.com/video-clips/zea2ev/younger-younger--hilary-duff---little-lies',
        'md5': 'e2c6389401cf485df26c79c247b08713',
        'info_dict': {
            'id': 'b8697515-4bbe-4e01-83d5-fa705ce5fa88',
            'ext': 'mp4',
            'title': 'Younger|Younger: Hilary Duff - Little Lies',
            'description': 'md5:7d192f56ca8d958645c83f0de8ef0269'
        },
    }]
