# encoding: utf-8
from __future__ import unicode_literals

import re
import datetime

from .common import InfoExtractor


class MailRuIE(InfoExtractor):
    IE_NAME = 'mailru'
    IE_DESC = 'Видео@Mail.Ru'
    _VALID_URL = r'http://(?:www\.)?my\.mail\.ru/video/.*#video=/?(?P<id>[^/]+/[^/]+/[^/]+/\d+)'

    _TEST = {
        'url': 'http://my.mail.ru/video/top#video=/mail/sonypicturesrus/75/76',
        'md5': 'dea205f03120046894db4ebb6159879a',
        'info_dict': {
            'id': '46301138',
            'ext': 'mp4',
            'title': 'Новый Человек-Паук. Высокое напряжение. Восстание Электро',
            'upload_date': '20140224',
            'uploader': 'sonypicturesrus',
            'uploader_id': 'sonypicturesrus@mail.ru',
            'duration': 184,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video_data = self._download_json(
            'http://videoapi.my.mail.ru/videos/%s.json?new=1' % video_id, video_id, 'Downloading video JSON')

        author = video_data['author']
        uploader = author['name']
        uploader_id = author['id']

        movie = video_data['movie']
        content_id = str(movie['contentId'])
        title = movie['title']
        thumbnail = movie['poster']
        duration = movie['duration']

        upload_date = datetime.datetime.fromtimestamp(video_data['timestamp']).strftime('%Y%m%d')
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
            'upload_date': upload_date,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }