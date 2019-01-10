# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    clean_html,
    ExtractorError,
    int_or_none,
    merge_dicts,
    str_or_none,
    str_to_int,
    try_get,
    unified_strdate,
    urlencode_postdata,
    urljoin,
)


class HKETVIE(InfoExtractor):
    IE_NAME = 'hketv'
    IE_DESC = '香港教育局教育電視 (HKETV) Educational Television, Hong Kong Educational Bureau'
    _GEO_BYPASS = False
    _GEO_COUNTRIES = ['HK']
    _VALID_URL = r'https?://(?:www\.)?hkedcity\.net/etv/resource/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.hkedcity.net/etv/resource/2932360618',
        'md5': 'f193712f5f7abb208ddef3c5ea6ed0b7',
        'info_dict': {
            'id': '2932360618',
            'ext': 'mp4',
            'title': '喜閱一生(共享閱讀樂) (中、英文字幕可供選擇)',
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
    }, {
        'url': 'https://www.hkedcity.net/etv/resource/972641418',
        'md5': '1ed494c1c6cf7866a8290edad9b07dc9',
        'info_dict': {
            'id': '972641418',
            'ext': 'mp4',
            'title': '衣冠楚楚 (天使系列之一)',
            'description': '天國仙境，有兩位可愛的天使小姐妹。她們對幾千年來天使衣著一成不變頗有不滿。她們下望人世間：只見人們穿著七彩繽紛、款式各異的服裝，漂亮極了。天使姐妹決定下凡考察衣著，以設計天使新裝。  下到人間，姐妹試穿各式各樣的衣著，引發連串奇特有趣的情節：她們穿著校服在街上閒逛時，被女警誤認為逃學而送回學校，到校後又被體育老師誤認為是新同學，匆匆忙忙換上運動服後在操場上大顯神通。她們穿著護士服在醫院散步時，又被誤認為當班護士，而投入追尋失蹤病童、治病救人的工作中去。姐妹倆還到過玩具店，與布娃娃們談論衣著。她們也去過服裝設計學校，被當成小模特兒而試穿各式服裝。最令姐妹倆興奮的是一場盛大的民族服裝表演會。身穿盛裝的十二個民族的少女在台上翩翩起舞，各種服飾七彩繽紛、美不勝收。姐妹們情不自禁地穿上民族服裝，小天使變成了少數民族姑娘……最後天使姐妹回到天上，對於天使究竟穿甚麼樣的衣服好，她們還是拿不定主意。  節目通過天使姐妹的奇特經歷，反復示範各式衣服鞋襪的正確讀音及談論衣著時的常用句式，並以盛大的民族服裝表演活動，帶出有關服裝的文化知識。內容豐富而饒有趣味。',
            'upload_date': '20070109',
            'duration': 907,
            'subtitles': {},
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
        title = self._html_search_meta('ed_title', webpage, fatal=True)

        file_id = self._html_search_regex(r'post_var\["file_id"\]\s*=\s*(.+?);', webpage, 'file ID')
        curr_url = self._html_search_regex(r'post_var\["curr_url"\]\s*=\s*"(.+?)";', webpage, 'curr URL')
        data = {
            'action': 'get_info',
            'curr_url': curr_url,
            'file_id': file_id,
            'video_url': file_id,
        }
        _APPS_BASE_URL = 'https://apps.hkedcity.net'
        handler_url = _APPS_BASE_URL + '/media/play/handler.php'

        response = self._download_json(
            handler_url, video_id,
            data=urlencode_postdata(data),
            headers=merge_dicts({'Content-Type': 'application/x-www-form-urlencoded'},
                                self.geo_verification_headers()))

        result = response['result']

        formats = []
        subtitles = {}

        if response.get('success') and response.get('access'):
            width = int_or_none(result.get('width'))
            height = int_or_none(result.get('height'))

            playlist0 = try_get(result, lambda x: x['playlist'][0], dict)
            fmts = playlist0.get('sources')
            for fmt in fmts:
                file_path = fmt.get('file')
                if file_path:
                    file_url = urljoin(_APPS_BASE_URL, file_path)
                    # If we ever wanted to provide the final resolved URL that
                    # does not require cookies, albeit with a shorter lifespan:
                    #     urlh = self._downloader.urlopen(file_url)
                    #     resolved_url = urlh.geturl()

                    label = fmt.get('label')
                    w = None
                    h = None
                    if label == 'HD':
                        h = 720
                    elif label == 'SD':
                        h = 360
                    if h:
                        if width and height:
                            w = h * width // height
                        else:
                            w = h * 4 // 3

                    formats.append({
                        'format_id': label,
                        'ext': fmt.get('type'),
                        'url': file_url,
                        'width': w,
                        'height': h,
                    })

            tracks = playlist0.get('tracks', [])
            for track in tracks:
                if not isinstance(track, dict):
                    continue
                track_kind = str_or_none(track.get('kind'))
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
            if 'Video streaming is not available in your country' in error:
                self.raise_geo_restricted(msg=error, countries=self._GEO_COUNTRIES)
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
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            fatal=False)
        like_count = int_or_none(try_get(emotion, lambda x: x['data']['emotion_data'][0]['count']))

        return {
            'id': video_id,
            'title': title,
            'description': self._html_search_meta('description', webpage, fatal=False),
            'upload_date': unified_strdate(self._html_search_meta('ed_date', webpage, fatal=False), day_first=False),
            'duration': int_or_none(result.get('length')),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': urljoin(_APPS_BASE_URL, result.get('image')),
            'view_count': str_to_int(result.get('view_count')),
            'like_count': like_count,
        }
