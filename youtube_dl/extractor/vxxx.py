# coding: utf-8
from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    parse_duration,
    strip_or_none,
    unified_timestamp,
    url_or_none,
)


class VXXXIE(InfoExtractor):
    _VALID_URL = r'https?://vxxx\.com/video-(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://vxxx.com/video-80747/',
        'md5': '2f4bfd829b682ff9e3da1bda71b81b81',
        'info_dict': {
            'id': '80747',
            'ext': 'mp4',
            'title': 'Monica Aka Selina',
            'display_id': 'monica-aka-selina',
            'thumbnail': 'https://tn.vxxx.com/contents/videos_screenshots/80000/80747/420x236/1.jpg',
            'description': None,
            'timestamp': 1607167706,
            'upload_date': '20201205',
            'duration': 2373.0,
            'categories': ['Anal', 'Asian', 'BDSM', 'Brunette', 'Toys',
                           'Fetish', 'HD', 'Interracial', 'MILF'],
            'age_limit': 18,
        }
    }]

    _BASE_URL = 'https://vxxx.com'
    _INFO_OBJECT_URL_TMPL = '{0}/api/json/video/86400/0/{1}/{2}.json'
    _FORMAT_OBJECT_URL_TMPL = '{0}/api/videofile.php?video_id={1}'

    def _download_info_object(self, video_id):
        return self._download_json(
            self._INFO_OBJECT_URL_TMPL.format(
                self._BASE_URL,
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': self._BASE_URL})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            self._FORMAT_OBJECT_URL_TMPL.format(self._BASE_URL, video_id),
            video_id,
            headers={'Referer': self._BASE_URL}
        )

    def _decode_base164(self, e):
        """
        Some non-standard encoding called "base164" in the JavaScript code. It's
        similar to the regular base64 with a slightly different alphabet:
            - "АВСЕМ" are Cyrillic letters instead of uppercase Latin letters
            - "." is used instead of "+"; "," is used instead of "/"
            - "~" is used for padding instead of "="
        """

        # using the kwarg to memoise the result
        def get_trans_tbl(from_, to, tbl={}):
            k = (from_, to)
            if not tbl.get(k):
                tbl[k] = str.maketrans(from_, to)
            return tbl[k]

        trans_tbl = get_trans_tbl(
            '\u0410\u0412\u0421\u0415\u041c.,~',
            'ABCEM+/=')
        return base64.b64decode(e.translate(trans_tbl)).decode()

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info_object = self._download_info_object(video_id)

        title = info_object['title']
        stats = info_object.get('statistics') or {}
        info = {
            'id': video_id,
            'title': title,
            'display_id': info_object.get('dir'),
            'thumbnail': url_or_none(info_object.get('thumb')),
            'description': strip_or_none(info_object.get('description')) or None,
            'timestamp': unified_timestamp(info_object.get('post_date')),
            'duration': parse_duration(info_object.get('duration')),
            'view_count': int_or_none(stats.get('viewed')),
            'like_count': int_or_none(stats.get('likes')),
            'dislike_count': int_or_none(stats.get('dislikes')),
            'average_rating': float_or_none(stats.get('rating')),
            'categories': [category['title'] for category in (info_object.get('categories') or {}).values()
                           if category.get('title')],
            'age_limit': 18,
        }

        format_object = self._download_format_object(video_id)
        m3u8_formats = self._extract_m3u8_formats(
            '{0}/{1}&f=video.m3u8'.format(
                self._BASE_URL,
                self._decode_base164(format_object[0]['video_url'])
            ),
            video_id, 'mp4')
        self._sort_formats(m3u8_formats)
        info['formats'] = m3u8_formats

        return info


class InPornIE(VXXXIE):
    _VALID_URL = r'https?://(?:www\.)?inporn\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://inporn.com/video/533613/2k-t-2nd-season-parm-151/',
        'md5': 'c358d1da6b451ebe7cfb00dd89741607',
        'info_dict': {
            'id': '533613',
            'ext': 'mp4',
            'title': '2k 美月まい - ガーリー系アパレルモt゙ルの挑発パンチラ 2nd Season [parm-151]',
            'display_id': '2k-t-2nd-season-parm-151',
            'thumbnail': 'https://tn.inporn.com/media/tn/533613_1.jpg',
            'description': None,
            'timestamp': 1664571262,
            'upload_date': '20220930',
            'duration': 480.0,
            'categories': ['Asian', 'Brunette', 'Casting', 'HD', 'Japanese',
                           'JAV Uncensored'],
            'age_limit': 18,
        },
    }]

    _BASE_URL = 'https://inporn.com'


class MrGayIE(VXXXIE):
    _VALID_URL = r'https?://mrgay\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://mrgay.com/video/10169199/jpn-crossdresser-6/',
        'md5': 'b5780a9437c205b4bc87eb939b23e8ef',
        'info_dict': {
            'id': '10169199',
            'ext': 'mp4',
            'title': 'Jpn Crossdresser 6',
            'display_id': 'jpn-crossdresser-6',
            'thumbnail': 'https://tn.mrgay.com/media/tn/10169199_1.jpg',
            'description': None,
            'timestamp': 1651066888,
            'upload_date': '20220427',
            'duration': 834.0,
            'categories': ['Amateur', 'Asian', 'Brunette', 'Crossdressing',
                           'Japanese', 'Webcam'],
            'age_limit': 18,
        }
    }]

    _BASE_URL = 'https://mrgay.com'


# The following three extractors are for "friend" sites whose videos could be
# extracted in the same way, but unsupported by youtube-dl due to missing proper
# DMCA notices. Consider re-enable them if their DMCA pages become available.
class BdsmxTubeIE(VXXXIE):
    _VALID_URL = r'https?://bdsmx\.tube/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://bdsmx.tube/video/127583/latex-puppy-leashed/',
        'md5': '79751d4ed75668afe07a660c4bcb2f1b',
        'info_dict': {
            'id': '127583',
            'ext': 'mp4',
            'title': 'Latex Puppy Leashed',
            'display_id': 'latex-puppy-leashed',
            'thumbnail': 'https://tn.bdsmx-porn.com/contents/videos_screenshots/127000/127583/480x270/1.jpg',
            'description': None,
            'timestamp': 1651003323,
            'upload_date': '20220426',
            'duration': 68.0,
            'categories': ['Asian', 'Brunette', 'Cosplay', 'Fetish',
                           'Fuck Machine', 'Gagging', 'Japanese',
                           'JAV Uncensored', 'Latex', 'Leather', 'POV'],
            'age_limit': 18,
        }
    }]
    _WORKING = False

    _BASE_URL = 'https://bdsmx.tube'


class BlackPornTubeIE(VXXXIE):
    _VALID_URL = r'https?://blackporn\.tube/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://blackporn.tube/video/10043813/young-ebony-babe-gets-super-wet/',
        'md5': '4a4c126970f2f1453b8b2050947fc870',
        'info_dict': {
            'id': '10043813',
            'ext': 'mp4',
            'title': 'Young Ebony Babe Gets Super Wet',
            'display_id': 'young-ebony-babe-gets-super-wet',
            'thumbnail': 'https://tn.blackporn.tube/contents/videos_screenshots/10043000/10043813/480x270/1.jpg',
            'description': None,
            'timestamp': 1654806141,
            'upload_date': '20220609',
            'duration': 193.0,
            'categories': ['BDSM', 'Bondage', 'Celebrity', 'Ebony', 'Fetish',
                           'Shibari Bondage', 'Solo Female',
                           'Tattoo'],
            'age_limit': 18,
        }
    }]
    _WORKING = False

    _BASE_URL = 'https://blackporn.tube'


class XMilfIE(VXXXIE):
    _VALID_URL = r'https?://xmilf\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://xmilf.com/video/143777/big-boob-brunette-masturbates3/',
        'md5': 'a196fe8daebe194a758754c81e9232ad',
        'info_dict': {
            'id': '143777',
            'ext': 'mp4',
            'title': 'Big Boob Brunette Masturbates',
            'display_id': 'big-boob-brunette-masturbates3',
            'thumbnail': 'https://tn.xmilf.com/contents/videos_screenshots/143000/143777/480x270/1.jpg',
            'description': None,
            'timestamp': 1662465481,
            'upload_date': '20220906',
            'duration': 480.0,
            'categories': ['Amateur', 'Big Tits', 'Brunette', 'Fetish', 'HD',
                           'Lingerie', 'MILF', 'Webcam'],
            'age_limit': 18,
        }
    }]
    _WORKING = False

    _BASE_URL = 'https://xmilf.com'
