# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    int_or_none,
    remove_end,
    unified_strdate,
    ExtractorError,
)


class LifeNewsIE(InfoExtractor):
    IE_NAME = 'lifenews'
    IE_DESC = 'LIFE | NEWS'
    _VALID_URL = r'http://lifenews\.ru/(?:mobile/)?(?P<section>news|video)/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://lifenews.ru/news/126342',
        'md5': 'e1b50a5c5fb98a6a544250f2e0db570a',
        'info_dict': {
            'id': '126342',
            'ext': 'mp4',
            'title': 'МВД разыскивает мужчин, оставивших в IKEA сумку с автоматом',
            'description': 'Камеры наблюдения гипермаркета зафиксировали троих мужчин, спрятавших оружейный арсенал в камере хранения.',
            'thumbnail': 're:http://.*\.jpg',
            'upload_date': '20140130',
        }
    }, {
        # video in <iframe>
        'url': 'http://lifenews.ru/news/152125',
        'md5': '77d19a6f0886cd76bdbf44b4d971a273',
        'info_dict': {
            'id': '152125',
            'ext': 'mp4',
            'title': 'В Сети появилось видео захвата «Правым сектором» колхозных полей ',
            'description': 'Жители двух поселков Днепропетровской области не простили радикалам угрозу лишения плодородных земель и пошли в лобовую. ',
            'upload_date': '20150402',
        }
    }, {
        'url': 'http://lifenews.ru/news/153461',
        'md5': '9b6ef8bc0ffa25aebc8bdb40d89ab795',
        'info_dict': {
            'id': '153461',
            'ext': 'mp4',
            'title': 'В Москве спасли потерявшегося медвежонка, который спрятался на дереве',
            'description': 'Маленький хищник не смог найти дорогу домой и обрел временное убежище на тополе недалеко от жилого массива, пока его не нашла соседская собака.',
            'upload_date': '20150505',
        }
    }, {
        'url': 'http://lifenews.ru/video/13035',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        section = mobj.group('section')

        webpage = self._download_webpage(
            'http://lifenews.ru/%s/%s' % (section, video_id),
            video_id, 'Downloading page')

        videos = re.findall(r'<video.*?poster="(?P<poster>[^"]+)".*?src="(?P<video>[^"]+)".*?></video>', webpage)
        iframe_link = self._html_search_regex(
            '<iframe[^>]+src=["\']([^"\']+)["\']', webpage, 'iframe link', default=None)
        if not videos and not iframe_link:
            raise ExtractorError('No media links available for %s' % video_id)

        title = remove_end(
            self._og_search_title(webpage),
            ' - Первый по срочным новостям — LIFE | NEWS')

        description = self._og_search_description(webpage)

        view_count = self._html_search_regex(
            r'<div class=\'views\'>\s*(\d+)\s*</div>', webpage, 'view count', fatal=False)
        comment_count = self._html_search_regex(
            r'=\'commentCount\'[^>]*>\s*(\d+)\s*<',
            webpage, 'comment count', fatal=False)

        upload_date = self._html_search_regex(
            r'<time[^>]*datetime=\'([^\']+)\'', webpage, 'upload date', fatal=False)
        if upload_date is not None:
            upload_date = unified_strdate(upload_date)

        common_info = {
            'description': description,
            'view_count': int_or_none(view_count),
            'comment_count': int_or_none(comment_count),
            'upload_date': upload_date,
        }

        def make_entry(video_id, media, video_number=None):
            cur_info = dict(common_info)
            cur_info.update({
                'id': video_id,
                'url': media[1],
                'thumbnail': media[0],
                'title': title if video_number is None else '%s-video%s' % (title, video_number),
            })
            return cur_info

        if iframe_link:
            iframe_link = self._proto_relative_url(iframe_link, 'http:')
            cur_info = dict(common_info)
            cur_info.update({
                '_type': 'url_transparent',
                'id': video_id,
                'title': title,
                'url': iframe_link,
            })
            return cur_info

        if len(videos) == 1:
            return make_entry(video_id, videos[0])
        else:
            return [make_entry(video_id, media, video_number + 1) for video_number, media in enumerate(videos)]


class LifeEmbedIE(InfoExtractor):
    IE_NAME = 'life:embed'
    _VALID_URL = r'http://embed\.life\.ru/embed/(?P<id>[\da-f]{32})'

    _TEST = {
        'url': 'http://embed.life.ru/embed/e50c2dec2867350528e2574c899b8291',
        'md5': 'b889715c9e49cb1981281d0e5458fbbe',
        'info_dict': {
            'id': 'e50c2dec2867350528e2574c899b8291',
            'ext': 'mp4',
            'title': 'e50c2dec2867350528e2574c899b8291',
            'thumbnail': 're:http://.*\.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = []
        for video_url in re.findall(r'"file"\s*:\s*"([^"]+)', webpage):
            video_url = compat_urlparse.urljoin(url, video_url)
            ext = determine_ext(video_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', m3u8_id='m3u8'))
            else:
                formats.append({
                    'url': video_url,
                    'format_id': ext,
                    'preference': 1,
                })
        self._sort_formats(formats)

        thumbnail = self._search_regex(
            r'"image"\s*:\s*"([^"]+)', webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': video_id,
            'thumbnail': thumbnail,
            'formats': formats,
        }
