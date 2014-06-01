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
                'id': '46301138',
                'ext': 'mp4',
                'title': 'Новый Человек-Паук. Высокое напряжение. Восстание Электро',
                'timestamp': 1393232740,
                'upload_date': '20140224',
                'uploader': 'sonypicturesrus',
                'uploader_id': 'sonypicturesrus@mail.ru',
                'duration': 184,
            },
        },
        {
            'url': 'http://my.mail.ru/corp/hitech/video/news_hi-tech_mail_ru/1263.html',
            'md5': '00a91a58c3402204dcced523777b475f',
            'info_dict': {
                'id': '46843144',
                'ext': 'mp4',
                'title': 'Samsung Galaxy S5 Hammer Smash Fail Battery Explosion',
                'timestamp': 1397217632,
                'upload_date': '20140411',
                'uploader': 'hitech',
                'uploader_id': 'hitech@corp.mail.ru',
                'duration': 245,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('idv1')

        if not video_id:
            video_id = mobj.group('idv2prefix') + mobj.group('idv2suffix')

        video_data = self._download_json(
            'http://api.video.mail.ru/videos/%s.json?new=1' % video_id, video_id, 'Downloading video JSON')

        author = video_data['author']
        uploader = author['name']
        uploader_id = author['id']

        movie = video_data['movie']
        content_id = str(movie['contentId'])
        title = movie['title']
        if title.endswith('.mp4'):
            title = title[:-4]
        thumbnail = movie['poster']
        duration = movie['duration']

        view_count = video_data['views_count']

        formats = [
            {
                'url': video['url'],
                'format_id': video['name'],
            } for video in video_data['videos']
        ]

        return {
            'id': content_id,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': video_data['timestamp'],
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }