# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor


class AmaraIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?amara\.org/(?:\w+/)?videos/(?P<id>\w+)'
    _TESTS = [
        {
            'url': 'https://amara.org/en/videos/jVx79ZKGK1ky/info/why-jury-trials-are-becoming-less-common/?tab=video',
            'md5': 'ea10daf2b6154b8c1ecf9922aca5e8ae',
            'info_dict': {
                'id': 'h6ZuVdvYnfE',
                'ext': 'mp4',
                'title': 'Why jury trials are becoming less common',
                'description': 'md5:a61811c319943960b6ab1c23e0cbc2c1',
                'thumbnail': r're:^https?://.*\.jpg$',
                'subtitles': dict,
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
                'id': 'ChimamandaAdichie_2009G-transcript',
                'ext': 'mp4',
                'title': 'The danger of a single story',
                'description': 'md5:d769b31139c3b8bb5be9177f62ea3f23',
                'thumbnail': r're:^https?://.*\.jpg$',
                'subtitles': dict,
                'upload_date': '20131206'
            }
        }
    ]

    def get_subtitles_for_language(self, language):
        return [{
            'ext': type,
            'url': language['subtitles_uri'].replace('format=json', 'format=' + type)
        } for type in ['vtt', 'srt', 'json']]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._download_json('https://amara.org/api/videos/%s/' % video_id, video_id, query={'format': 'json'})

        video_url = meta.get('all_urls')[0]
        subtitles = dict([(language['code'], self.get_subtitles_for_language(language)) for language in meta.get('languages', []) if language['published']])

        return {
            '_type': 'url_transparent',
            'url': video_url,
            'id': video_id,
            'subtitles': subtitles,
            'title': meta['title'],
            'description': meta.get('description'),
            'thumbnail': meta.get('thumbnail')
        }
