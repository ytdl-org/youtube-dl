from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none
from ..compat import compat_urllib_parse_urlencode


class TwentyThreeVideoIE(InfoExtractor):
    IE_NAME = '23video'
    _VALID_URL = r'https?://(?P<domain>[^.]+\.(?:twentythree\.net|kglteater\.dk|23video\.com|filmweb\.no))/v\.ihtml/player\.html\?(?P<query>.*?\bphoto(?:_|%5f)id=(?P<id>\d+).*)'
    _TESTS = [{
        'url': 'https://video.twentythree.net/v.ihtml/player.html?showDescriptions=0&source=site&photo%5fid=20448876&autoPlay=1',
        'md5': '75fcf216303eb1dae9920d651f85ced4',
        'info_dict': {
            'id': '20448876',
            'ext': 'mp4',
            'title': 'Video Marketing Minute: Personalized Video',
            'timestamp': 1513855354,
            'upload_date': '20171221',
            'uploader_id': '12258964',
            'uploader': 'Rasmus Bysted',
        }
    }, {
        'url': 'https://bonnier-publications-danmark.23video.com/v.ihtml/player.html?token=f0dc46476e06e13afd5a1f84a29e31e8&source=embed&photo%5fid=36137620',
        'md5': '772a91f83d129ee5f015b12bea61a78b',
        'info_dict': {
            'id': '36137620',
            'ext': 'mp4',
            'title': 'Photoshop Elements 2019 - Photo Text',
            'timestamp': 1538664032,
            'upload_date': '20181004',
            'uploader_id': '10801356',
            'uploader': 'Kristoffer Engbo',
        }
    }, {
        'url': 'https://video.kglteater.dk/v.ihtml/player.html?source=share&photo%5fid=65098499',
        'md5': '4e20a33ce86b13ca114ee44a0a8d8efb',
        'info_dict': {
            'id': '65098499',
            'ext': 'mp4',
            'title': 'Askepot',
            'timestamp': 1605173942,
            'upload_date': '20201112',
            'uploader_id': '62151179',
            'uploader': 'jbny',
        }
    }, {
        'url': 'https://video.kglteater.dk/v.ihtml/player.html?showDescriptions=0&source=site&photo%5fid=52486482&autoPlay=1',
        'md5': 'c39ffb965079fb4395788e6814ec3cdc',
        'info_dict': {
            'id': '52486482',
            'ext': 'mp4',
            'title': 'N\xf8ddekn\xe6kkeren 2019',
            'timestamp': 1558953133,
            'upload_date': '20190527',
            'uploader_id': '7450690',
            'uploader': 'Tejs Holm',
        }
    }]

    def _real_extract(self, url):
        domain, query, photo_id = re.match(self._VALID_URL, url).groups()
        base_url = 'https://%s' % domain

        def is_geo_blocked():
            # /api/player/settings
            playersettings_0 = {'player_id': 0, 'parameters': 'showDescriptions=0&source=site&photo%5fid=' + photo_id + '&autoPlay=1', '_li': 0, '_bot': 0}
            playersettings_0_param = '/api/player/settings?' + compat_urllib_parse_urlencode(playersettings_0)

            # /api/live/list
            livelist_1 = {'include_actions_p': 1, 'showDescriptions': 0, 'source': 'site', 'photo_id': photo_id, 'autoPlay': 1, 'upcoming_p': 1, 'ordering': 'streaming', 'player_id': 0}
            livelist_1_param = '/api/live/list?' + compat_urllib_parse_urlencode(livelist_1)

            # /api/photo/list
            photolist_2 = {'size': 10, 'include_actions_p': 1, 'showDescriptions': 0, 'source': 'site', 'photo_id': photo_id, 'autoPlay': 1, 'player_id': 0}
            photolist_2_param = '/api/photo/list?' + compat_urllib_parse_urlencode(photolist_2)

            new_query = {'format': 'json', 'callback': 'test', 'playersettings_0': playersettings_0_param, 'livelist_1': livelist_1_param, 'photolist_2': photolist_2_param}
            photolist_result = self._download_json(
                base_url + '/api/concatenate',
                photo_id,
                query=new_query,
                transform_source=lambda s: self._search_regex(r'(?s)({.+})', s, 'photolist_2')
            )["photolist_2"]

            if "photos" in photolist_result:
                for photo in photolist_result['photos']:
                    if photo['photo_id'] == photo_id:
                        return photo['protection_method'] == 'geoblocking'

            return False

        def get_video_query():
            if is_geo_blocked():
                token = self._download_json(
                    base_url + '/api/protection/verify',
                    photo_id,
                    query={'protection_method': 'geoblocking', 'object_id': photo_id, 'object_type': 'photo', 'format': 'json', 'callback': 'visualplatform_1'},
                    transform_source=lambda s: self._search_regex(r'(?s)({.+})', s, 'protectedtoken'))['protectedtoken']['protected_token']

                return {'format': 'json', 'token': token}
            else:
                return {'format': 'json'}

        video_query = get_video_query()
        photo_data = self._download_json(
            base_url + '/api/photo/list?' + query, photo_id,
            query=video_query,
            transform_source=lambda s: self._search_regex(r'(?s)({.+})', s, 'photo data'))['photo']

        title = photo_data['title']
        formats = []

        audio_path = photo_data.get('audio_download')
        if audio_path:
            formats.append({
                'format_id': 'audio',
                'url': base_url + audio_path,
                'filesize': int_or_none(photo_data.get('audio_size')),
                'vcodec': 'none',
            })

        def add_common_info_to_list(l, template, id_field, id_value):
            f_base = template % id_value
            f_path = photo_data.get(f_base + 'download')
            if not f_path:
                return
            l.append({
                id_field: id_value,
                'url': base_url + f_path,
                'width': int_or_none(photo_data.get(f_base + 'width')),
                'height': int_or_none(photo_data.get(f_base + 'height')),
                'filesize': int_or_none(photo_data.get(f_base + 'size')),
            })

        for f in ('mobile_high', 'medium', 'hd', '1080p', '4k'):
            add_common_info_to_list(formats, 'video_%s_', 'format_id', f)

        thumbnails = []
        for t in ('quad16', 'quad50', 'quad75', 'quad100', 'small', 'portrait', 'standard', 'medium', 'large', 'original'):
            add_common_info_to_list(thumbnails, '%s_', 'id', t)

        return {
            'id': photo_id,
            'title': title,
            'timestamp': int_or_none(photo_data.get('creation_date_epoch')),
            'duration': int_or_none(photo_data.get('video_length')),
            'view_count': int_or_none(photo_data.get('view_count')),
            'comment_count': int_or_none(photo_data.get('number_of_comments')),
            'uploader_id': photo_data.get('user_id'),
            'uploader': photo_data.get('display_name'),
            'thumbnails': thumbnails,
            'formats': formats,
        }
