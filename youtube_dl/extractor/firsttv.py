# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_xpath
from ..utils import (
    int_or_none,
    qualities,
    unified_strdate,
    xpath_attr,
    xpath_element,
    xpath_text,
    xpath_with_ns,
)


class FirstTVIE(InfoExtractor):
    IE_NAME = '1tv'
    IE_DESC = 'Первый канал'
    _VALID_URL = r'https?://(?:www\.)?1tv\.ru/(?:[^/]+/)+p?(?P<id>\d+)'

    _TESTS = [{
        # single format via video_materials.json API
        'url': 'http://www.1tv.ru/prj/inprivate/vypusk/35930',
        'md5': '82a2777648acae812d58b3f5bd42882b',
        'info_dict': {
            'id': '35930',
            'ext': 'mp4',
            'title': 'Гость Людмила Сенчина. Наедине со всеми. Выпуск от 12.02.2015',
            'description': 'md5:357933adeede13b202c7c21f91b871b2',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'upload_date': '20150212',
            'duration': 2694,
        },
    }, {
        # multiple formats via video_materials.json API
        'url': 'http://www.1tv.ru/video_archive/projects/dobroeutro/p113641',
        'info_dict': {
            'id': '113641',
            'ext': 'mp4',
            'title': 'Весенняя аллергия. Доброе утро. Фрагмент выпуска от 07.04.2016',
            'description': 'md5:8dcebb3dded0ff20fade39087fd1fee2',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'upload_date': '20160407',
            'duration': 179,
            'formats': 'mincount:3',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # single format only available via ONE_ONLINE_VIDEOS.archive_single_xml API
        'url': 'http://www.1tv.ru/video_archive/series/f7552/p47038',
        'md5': '519d306c5b5669761fd8906c39dbee23',
        'info_dict': {
            'id': '47038',
            'ext': 'mp4',
            'title': '"Побег". Второй сезон. 3 серия',
            'description': 'md5:3abf8f6b9bce88201c33e9a3d794a00b',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'upload_date': '20120516',
            'duration': 3080,
        },
    }, {
        'url': 'http://www.1tv.ru/videoarchive/9967',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Videos with multiple formats only available via this API
        video = self._download_json(
            'http://www.1tv.ru/video_materials.json?legacy_id=%s' % video_id,
            video_id, fatal=False)

        description, thumbnail, upload_date, duration = [None] * 4

        if video:
            item = video[0]
            title = item['title']
            quality = qualities(('ld', 'sd', 'hd', ))
            formats = [{
                'url': f['src'],
                'format_id': f.get('name'),
                'quality': quality(f.get('name')),
            } for f in item['mbr'] if f.get('src')]
            thumbnail = item.get('poster')
        else:
            # Some videos are not available via video_materials.json
            video = self._download_xml(
                'http://www.1tv.ru/owa/win/ONE_ONLINE_VIDEOS.archive_single_xml?pid=%s' % video_id,
                video_id)

            NS_MAP = {
                'media': 'http://search.yahoo.com/mrss/',
            }

            item = xpath_element(video, './channel/item', fatal=True)
            title = xpath_text(item, './title', fatal=True)
            formats = [{
                'url': content.attrib['url'],
            } for content in item.findall(
                compat_xpath(xpath_with_ns('./media:content', NS_MAP))) if content.attrib.get('url')]
            thumbnail = xpath_attr(
                item, xpath_with_ns('./media:thumbnail', NS_MAP), 'url')

        self._sort_formats(formats)

        webpage = self._download_webpage(url, video_id, 'Downloading page', fatal=False)
        if webpage:
            title = self._html_search_regex(
                (r'<div class="tv_translation">\s*<h1><a href="[^"]+">([^<]*)</a>',
                 r"'title'\s*:\s*'([^']+)'"),
                webpage, 'title', default=None) or title
            description = self._html_search_regex(
                r'<div class="descr">\s*<div>&nbsp;</div>\s*<p>([^<]*)</p></div>',
                webpage, 'description', default=None) or self._html_search_meta(
                'description', webpage, 'description')
            thumbnail = thumbnail or self._og_search_thumbnail(webpage)
            duration = int_or_none(self._html_search_meta(
                'video:duration', webpage, 'video duration', fatal=False))
            upload_date = unified_strdate(self._html_search_meta(
                'ya:ovs:upload_date', webpage, 'upload date', fatal=False))

        return {
            'id': video_id,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'duration': int_or_none(duration),
            'formats': formats
        }
