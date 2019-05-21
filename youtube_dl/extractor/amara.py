# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .youtube import YoutubeIE
from .vimeo import VimeoIE
from .generic import GenericIE


class AmaraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?amara\.org/(?:\w+/)?videos/(?P<id>\w+).*'
    _TESTS = [
        {
            'url': 'https://amara.org/en/videos/jVx79ZKGK1ky/info/why-jury-trials-are-becoming-less-common/?tab=video',
            'md5': 'ea10daf2b6154b8c1ecf9922aca5e8ae',
            'info_dict': {
                'id': 'jVx79ZKGK1ky',
                'ext': 'mp4',
                'title': 'Why jury trials are becoming less common',
                'description': 'A new analysis of federal court cases published last week by The New York Times shows that jury trials are becoming increasingly less common. In 1997, 3,200 out of 63,000 federal defendants were convicted in jury trials. But by 2015, even as the number of defendants grew to 81,000, jury convictions dropped to 1,650. Benjamin Weiser of The New York Times joins William Brangham from Maine.',
                'thumbnail': r're:^https?://.*\.jpg$',
                'subtitles': {
                    'en': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/jVx79ZKGK1ky/languages/en/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/jVx79ZKGK1ky/languages/en/subtitles/?format=srt'}
                    ]
                },
                'upload_date': '20160813',
                'uploader': 'PBS NewsHour',
                'uploader_id': 'PBSNewsHour'
            }
        },
        {
            'url': 'https://amara.org/en/videos/kYkK1VUTWW5I/info/vimeo-at-ces-2011',
            'md5': '99392c75fa05d432a8f11df03612195e',
            'info_dict': {
                'id': '18622084',
                'ext': 'mov',
                'title': 'Vimeo at CES 2011!',
                'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
                'thumbnail': r're:^https?://.*\.jpg$',
                'subtitles': dict,
                'timestamp': 1294649110,
                'upload_date': '20110110',
                'uploader': 'Sam Morrill',
                'uploader_id': 'sammorrill'
            }
        },
        {
            'url': 'https://amara.org/en/videos/s8KL7I3jLmh6/info/the-danger-of-a-single-story/',
            'md5': 'd3970f08512738ee60c5807311ff5d3f',
            'info_dict': {
                'id': 's8KL7I3jLmh6',
                'ext': 'mp4',
                'title': 'The danger of a single story',
                'description': 'Our lives, our cultures, are composed of many overlapping stories. Novelist Chimamanda Adichie tells the story of how she found her authentic cultural voice -- and warns that if we hear only a single story about another person or country, we risk a critical misunderstanding.',
                'thumbnail': r're:^https?://.*\.jpg$',
                'subtitles': {
                    'el': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/el/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/el/subtitles/?format=srt'}
                    ],
                    'eo': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/eo/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/eo/subtitles/?format=srt'}
                    ],
                    'en': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/en/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/en/subtitles/?format=srt'}
                    ],
                    'af': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/af/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/af/subtitles/?format=srt'}
                    ],
                    'vi': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/vi/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/vi/subtitles/?format=srt'}
                    ],
                    'ca': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ca/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ca/subtitles/?format=srt'}
                    ],
                    'it': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/it/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/it/subtitles/?format=srt'}
                    ],
                    'ar': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ar/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ar/subtitles/?format=srt'}
                    ],
                    'pt-br': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/pt-br/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/pt-br/subtitles/?format=srt'}
                    ],
                    'cs': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/cs/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/cs/subtitles/?format=srt'}
                    ],
                    'gl': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/gl/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/gl/subtitles/?format=srt'}
                    ],
                    'id': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/id/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/id/subtitles/?format=srt'}
                    ],
                    'es': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/es/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/es/subtitles/?format=srt'}
                    ],
                    'ru': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ru/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ru/subtitles/?format=srt'}
                    ],
                    'az': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/az/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/az/subtitles/?format=srt'}
                    ],
                    'nl': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/nl/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/nl/subtitles/?format=srt'}
                    ],
                    'pt': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/pt/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/pt/subtitles/?format=srt'}
                    ],
                    'swa': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/swa/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/swa/subtitles/?format=srt'}
                    ],
                    'zh-tw': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/zh-tw/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/zh-tw/subtitles/?format=srt'}
                    ],
                    'nb': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/nb/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/nb/subtitles/?format=srt'}
                    ],
                    'tr': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/tr/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/tr/subtitles/?format=srt'}
                    ],
                    'lv': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/lv/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/lv/subtitles/?format=srt'}
                    ],
                    'zh-cn': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/zh-cn/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/zh-cn/subtitles/?format=srt'}
                    ],
                    'lt': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/lt/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/lt/subtitles/?format=srt'}
                    ],
                    'th': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/th/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/th/subtitles/?format=srt'}
                    ],
                    'ro': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ro/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ro/subtitles/?format=srt'}
                    ],
                    'fr': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/fr/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/fr/subtitles/?format=srt'}
                    ],
                    'bg': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/bg/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/bg/subtitles/?format=srt'}
                    ],
                    'uk': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/uk/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/uk/subtitles/?format=srt'}
                    ],
                    'hr': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/hr/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/hr/subtitles/?format=srt'}
                    ],
                    'bo': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/bo/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/bo/subtitles/?format=srt'}
                    ],
                    'hu': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/hu/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/hu/subtitles/?format=srt'}
                    ],
                    'fa': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/fa/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/fa/subtitles/?format=srt'}
                    ],
                    'hi': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/hi/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/hi/subtitles/?format=srt'}
                    ],
                    'fi': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/fi/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/fi/subtitles/?format=srt'}
                    ],
                    'ja': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ja/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ja/subtitles/?format=srt'}
                    ],
                    'he': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/he/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/he/subtitles/?format=srt'}
                    ],
                    'ka': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ka/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ka/subtitles/?format=srt'}
                    ],
                    'sr': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sr/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sr/subtitles/?format=srt'}
                    ],
                    'mn': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/mn/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/mn/subtitles/?format=srt'}
                    ],
                    'ko': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ko/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ko/subtitles/?format=srt'}
                    ],
                    'sv': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sv/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sv/subtitles/?format=srt'}
                    ],
                    'mk': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/mk/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/mk/subtitles/?format=srt'}
                    ],
                    'sk': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sk/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sk/subtitles/?format=srt'}
                    ],
                    'de': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/de/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/de/subtitles/?format=srt'}
                    ],
                    'pl': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/pl/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/pl/subtitles/?format=srt'}
                    ],
                    'ku': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ku/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/ku/subtitles/?format=srt'}
                    ],
                    'sl': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sl/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/sl/subtitles/?format=srt'}
                    ],
                    'my': [
                        {'ext': 'vtt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/my/subtitles/?format=vtt'},
                        {'ext': 'srt', 'url': 'https://amara.org/api/videos/s8KL7I3jLmh6/languages/my/subtitles/?format=srt'}
                    ]
                },
                'upload_date': '20131206'
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._download_json('https://amara.org/api/videos/%s/?extra=player_urls&format=json' % video_id, video_id)

        video_urls = meta.get('all_urls')
        youtube_urls = filter(YoutubeIE.suitable, video_urls)
        vimeo_urls = filter(VimeoIE.suitable, video_urls)

        if len(youtube_urls) > 0:
            ie_info = YoutubeIE(downloader=self._downloader).extract(youtube_urls[0])
        elif len(vimeo_urls) > 0:
            ie_info = VimeoIE(downloader=self._downloader).extract(vimeo_urls[0])
        else:
            ie_info = GenericIE(downloader=self._downloader).extract(video_urls[0])

        subtitles = ie_info.get('subtitles', {}).copy()
        subtitles.update(dict(map(lambda language: [
            language['code'],
            [
                {
                    'ext': 'vtt',
                    'url': language['subtitles_uri'].replace('format=json', 'format=vtt')
                }, {
                    'ext': 'srt',
                    'url': language['subtitles_uri'].replace('format=json', 'format=srt')
                },
            ] + ie_info.get('subtitles', {}).get(language['code'], [])
        ], filter(lambda language: language['published'], meta.get('languages', [])))))

        info = ie_info.copy()
        info.update({ 'id': video_id, 'subtitles': subtitles })

        if meta['title']: info.update({ 'title': meta['title' ]})
        if meta['description']: info.update({ 'description': meta['description' ]})
        if meta['thumbnail']: info.update({ 'thumbnail': meta['thumbnail' ]})

        return info
