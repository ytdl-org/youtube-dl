# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    GeoRestrictedError,
    clean_html,
    int_or_none,
    merge_dicts,
    str_to_int,
    try_get,
    unified_strdate,
    urlencode_postdata,
    urljoin,
)


class HKETVIE(InfoExtractor):
    IE_NAME = 'hketv'
    IE_DESC = '香港教育局教育電視 (HKETV) Educational Television, Hong Kong Educational Bureau'
    _VALID_URL = r'https?://(?:www\.)?hkedcity\.net/etv/resource/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.hkedcity.net/etv/resource/2932360618',
        'md5': 'f193712f5f7abb208ddef3c5ea6ed0b7',
        'info_dict': {
            'id': '2932360618',
            'ext': 'mp4',
            'title': '喜閱一生(共享閱讀樂)',
            'description': '本節目輯錄了「閱讀滿Fun嘉年華」和「二○一八響應世界閱讀日――悅愛閱讀・愈讀愈愛」的活動花絮，並由學者、作家、演藝界人士等，分享培養子女閱讀興趣和習慣的方法，以及呼籲大家一同分享閱讀的樂趣。',
            'upload_date': '20181024',
            'duration': 900,
            'subtitles': {
                'en': [{
                    'url': 'https://apps.hkedcity.net/media/mediaplayer/caption.php?f=74395&lang=en',
                    'ext': 'srt',
                }],
                'zh-Hant': [{
                    'url': 'https://apps.hkedcity.net/media/mediaplayer/caption.php?f=74395&lang=qmt',
                    'ext': 'srt',
                }],
            }
        },
    }]

    _CC_LANGS = {
        '中文（繁體中文）': 'zh-Hant',
        '中文（简体中文）': 'zh-Hans',
        'English': 'en',
        'Bahasa Indonesia': 'id',
        '\u0939\u093f\u0928\u094d\u0926\u0940': 'hi',
        '\u0928\u0947\u092a\u093e\u0932\u0940': 'ne',
        'Tagalog': 'tl',
        '\u0e44\u0e17\u0e22': 'th',
        '\u0627\u0631\u062f\u0648': 'ur',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        file_id = self._html_search_regex(r'post_var\["file_id"\] = ([0-9]+);', webpage, 'file ID')
        curr_url = self._html_search_regex(r'post_var\["curr_url"\] = "(.+?)";', webpage, 'curr URL')
        data = {
            'action': 'get_info',
            'curr_url': curr_url,
            'file_id': file_id,
            'video_url': file_id,
        }
        _APPS_BASE_URL = 'https://apps.hkedcity.net'
        handler_url = urljoin(_APPS_BASE_URL, '/media/play/handler.php')

        response = self._download_json(
            handler_url, video_id,
            data=urlencode_postdata(data),
            headers=merge_dicts({'Content-Type': 'application/x-www-form-urlencoded'},
                                self.geo_verification_headers()))

        result = try_get(response, lambda x: x['result'], dict)

        formats = []
        subtitles = {}

        thumbnail_php = urljoin(_APPS_BASE_URL, result.get('image'))
        thumbnail_urlh = self._downloader.urlopen(thumbnail_php)
        thumbnail = thumbnail_urlh.geturl()

        if response.get('success') and response.get('access'):
            width = str_to_int(result.get('width'))
            height = str_to_int(result.get('height'))

            playlist0 = try_get(result, lambda x: x['playlist'][0], dict)
            fmts = try_get(playlist0, lambda x: x['sources'], list)
            for fmt in fmts:
                label = fmt.get('label')
                if label == 'HD':
                    h = 720
                elif label == 'SD':
                    h = 360
                w = h * width // height
                urlh = self._downloader.urlopen(urljoin(_APPS_BASE_URL, fmt.get('file')))
                formats.append({
                    'format_id': label,
                    'ext': fmt.get('type'),
                    'url': urlh.geturl(),
                    'width': w,
                    'height': h,
                })

            tracks = try_get(playlist0, lambda x: x['tracks'], list)
            for track in tracks:
                if not isinstance(track, dict):
                    continue
                track_kind = track.get('kind')
                if not track_kind or not isinstance(track_kind, compat_str):
                    continue
                if track_kind.lower() not in ('captions', 'subtitles'):
                    continue
                track_url = urljoin(_APPS_BASE_URL, track.get('file'))
                if not track_url:
                    continue
                track_label = track.get('label')
                subtitles.setdefault(self._CC_LANGS.get(track_label, track_label), []).append({
                    'url': self._proto_relative_url(track_url),
                    'ext': 'srt',
                })

        else:
            error = clean_html(response.get('access_err_msg'))
            if error.find('Video streaming is not available in your country'):
                raise GeoRestrictedError(error)
            else:
                raise ExtractorError(error)

        # Likes
        emotion = self._download_json(
            'https://emocounter.hkedcity.net/handler.php',
            video_id,
            data=urlencode_postdata({
                'action': 'get_emotion',
                'data[bucket_id]': 'etv',
                'data[identifier]': video_id,
            }),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
        if emotion.get('result'):
            like_count = str_to_int(try_get(emotion, lambda x: x['data']['emotion_data'][0]['count'], str))

        return {
            'id': video_id,
            'title': self._html_search_meta('ed_title', webpage),
            'description': self._html_search_meta('description', webpage, fatal=False),
            'upload_date': unified_strdate(self._html_search_meta('ed_date', webpage, fatal=False), day_first=False),
            'duration': int_or_none(result.get('length')),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
            'view_count': str_to_int(result.get('view_count')),
            'like_count': like_count,
        }
