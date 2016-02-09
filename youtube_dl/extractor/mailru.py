# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MailRuIE(InfoExtractor):
    IE_NAME = 'mailru'
    IE_DESC = 'Видео@Mail.Ru'
    _VALID_URL = r'http://(?:www\.)?my\.mail\.ru/(?:video/.*#video=/?(?P<idv1>(?:[^/]+/){3}\d+)|(?:(?P<idv2prefix>(?:[^/]+/){2})video/(?P<idv2suffix>[^/]+/\d+))\.html)'

    _TESTS = [
        {
            'url': 'http://my.mail.ru/video/top#video=/mail/sonypicturesrus/75/76',
            'md5': 'dea205f03120046894db4ebb6159879a',
            'info_dict': {
                'id': '46301138_76',
                'ext': 'mp4',
                'title': 'Новый Человек-Паук. Высокое напряжение. Восстание Электро',
                'timestamp': 1393232740,
                'upload_date': '20140224',
                'uploader': 'sonypicturesrus',
                'uploader_id': 'sonypicturesrus@mail.ru',
                'duration': 184,
            },
            'skip': 'Not accessible from Travis CI server',
        },
        {
            'url': 'http://my.mail.ru/corp/hitech/video/news_hi-tech_mail_ru/1263.html',
            'md5': '00a91a58c3402204dcced523777b475f',
            'info_dict': {
                'id': '46843144_1263',
                'ext': 'mp4',
                'title': 'Samsung Galaxy S5 Hammer Smash Fail Battery Explosion',
                'timestamp': 1397217632,
                'upload_date': '20140411',
                'uploader': 'hitech',
                'uploader_id': 'hitech@corp.mail.ru',
                'duration': 245,
            },
            'skip': 'Not accessible from Travis CI server',
        },
        {
            # only available via metaUrl API
            'url': 'http://my.mail.ru/mail/720pizle/video/_myvideo/502.html',
            'md5': '3b26d2491c6949d031a32b96bd97c096',
            'info_dict': {
                'id': '56664382_502',
                'ext': 'mp4',
                'title': ':8336',
                'timestamp': 1449094163,
                'upload_date': '20151202',
                'uploader': '720pizle@mail.ru',
                'uploader_id': '720pizle@mail.ru',
                'duration': 6001,
            },
            'skip': 'Not accessible from Travis CI server',
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('idv1')

        if not video_id:
            video_id = mobj.group('idv2prefix') + mobj.group('idv2suffix')

        webpage = self._download_webpage(url, video_id)

        video_data = None

        page_config = self._parse_json(self._search_regex(
            r'(?s)<script[^>]+class="sp-video__page-config"[^>]*>(.+?)</script>',
            webpage, 'page config', default='{}'), video_id, fatal=False)
        if page_config:
            meta_url = page_config.get('metaUrl') or page_config.get('video', {}).get('metaUrl')
            if meta_url:
                video_data = self._download_json(
                    meta_url, video_id, 'Downloading video meta JSON', fatal=False)

        # Fallback old approach
        if not video_data:
            video_data = self._download_json(
                'http://api.video.mail.ru/videos/%s.json?new=1' % video_id,
                video_id, 'Downloading video JSON')

        author = video_data['author']
        uploader = author['name']
        uploader_id = author.get('id') or author.get('email')
        view_count = video_data.get('views_count')

        meta_data = video_data['meta']
        content_id = '%s_%s' % (
            meta_data.get('accId', ''), meta_data['itemId'])
        title = meta_data['title']
        if title.endswith('.mp4'):
            title = title[:-4]
        thumbnail = meta_data['poster']
        duration = meta_data['duration']
        timestamp = meta_data['timestamp']

        formats = [
            {
                'url': video['url'],
                'format_id': video['key'],
                'height': int(video['key'].rstrip('p'))
            } for video in video_data['videos']
        ]
        self._sort_formats(formats)

        return {
            'id': content_id,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
