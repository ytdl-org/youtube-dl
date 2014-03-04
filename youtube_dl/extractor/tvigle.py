# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    clean_html,
    int_or_none,
)


class TvigleIE(InfoExtractor):
    IE_NAME = 'tvigle'
    IE_DESC = 'Интернет-телевидение Tvigle.ru'
    _VALID_URL = r'http://(?:www\.)?tvigle\.ru/category/.+?[\?&]v(?:ideo)?=(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'http://www.tvigle.ru/category/cinema/1608/?video=503081',
            'md5': '09afba4616666249f087efc6dcf83cb3',
            'info_dict': {
                'id': '503081',
                'ext': 'flv',
                'title': 'Брат 2 ',
                'description': 'md5:f5a42970f50648cee3d7ad740f3ae769',
                'upload_date': '20110919',
            },
        },
        {
            'url': 'http://www.tvigle.ru/category/men/vysotskiy_vospominaniya02/?flt=196&v=676433',
            'md5': 'e7efe5350dd5011d0de6550b53c3ba7b',
            'info_dict': {
                'id': '676433',
                'ext': 'flv',
                'title': 'Ведущий телепрограммы «60 минут» (США) о Владимире Высоцком',
                'description': 'md5:027f7dc872948f14c96d19b4178428a4',
                'upload_date': '20121218',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        video_data = self._download_xml(
            'http://www.tvigle.ru/xml/single.php?obj=%s' % video_id, video_id, 'Downloading video XML')

        video = video_data.find('./video')

        title = video.get('name')
        description = video.get('anons')
        if description:
            description = clean_html(description)
        thumbnail = video_data.get('img')
        upload_date = unified_strdate(video.get('date'))
        like_count = int_or_none(video.get('vtp'))

        formats = []
        for num, (format_id, format_note) in enumerate([['low_file', 'SQ'], ['file', 'HQ'], ['hd', 'HD 720']]):
            video_url = video.get(format_id)
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'format_id': format_id,
                'format_note': format_note,
                'quality': num,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'like_count': like_count,
            'age_limit': 18,
            'formats': formats,
        }