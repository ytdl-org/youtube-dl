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
    _VALID_URL = r'https?://lifenews\.ru/(?:mobile/)?(?P<section>news|video)/(?P<id>\d+)'

    _TESTS = [{
        # single video embedded via video/source
        'url': 'http://lifenews.ru/news/98736',
        'md5': '77c95eaefaca216e32a76a343ad89d23',
        'info_dict': {
            'id': '98736',
            'ext': 'mp4',
            'title': 'Мужчина нашел дома архив оборонного завода',
            'description': 'md5:3b06b1b39b5e2bea548e403d99b8bf26',
            'upload_date': '20120805',
        }
    }, {
        # single video embedded via iframe
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
        # two videos embedded via iframe
        'url': 'http://lifenews.ru/news/153461',
        'info_dict': {
            'id': '153461',
            'title': 'В Москве спасли потерявшегося медвежонка, который спрятался на дереве',
            'description': 'Маленький хищник не смог найти дорогу домой и обрел временное убежище на тополе недалеко от жилого массива, пока его не нашла соседская собака.',
            'upload_date': '20150505',
        },
        'playlist': [{
            'md5': '9b6ef8bc0ffa25aebc8bdb40d89ab795',
            'info_dict': {
                'id': '153461-video1',
                'ext': 'mp4',
                'title': 'В Москве спасли потерявшегося медвежонка, который спрятался на дереве (Видео 1)',
                'description': 'Маленький хищник не смог найти дорогу домой и обрел временное убежище на тополе недалеко от жилого массива, пока его не нашла соседская собака.',
                'upload_date': '20150505',
            },
        }, {
            'md5': 'ebb3bf3b1ce40e878d0d628e93eb0322',
            'info_dict': {
                'id': '153461-video2',
                'ext': 'mp4',
                'title': 'В Москве спасли потерявшегося медвежонка, который спрятался на дереве (Видео 2)',
                'description': 'Маленький хищник не смог найти дорогу домой и обрел временное убежище на тополе недалеко от жилого массива, пока его не нашла соседская собака.',
                'upload_date': '20150505',
            },
        }],
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

        video_urls = re.findall(
            r'<video[^>]+><source[^>]+src=["\'](.+?)["\']', webpage)

        iframe_links = re.findall(
            r'<iframe[^>]+src=["\']((?:https?:)?//embed\.life\.ru/embed/.+?)["\']',
            webpage)

        if not video_urls and not iframe_links:
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

        def make_entry(video_id, video_url, index=None):
            cur_info = dict(common_info)
            cur_info.update({
                'id': video_id if not index else '%s-video%s' % (video_id, index),
                'url': video_url,
                'title': title if not index else '%s (Видео %s)' % (title, index),
            })
            return cur_info

        def make_video_entry(video_id, video_url, index=None):
            video_url = compat_urlparse.urljoin(url, video_url)
            return make_entry(video_id, video_url, index)

        def make_iframe_entry(video_id, video_url, index=None):
            video_url = self._proto_relative_url(video_url, 'http:')
            cur_info = make_entry(video_id, video_url, index)
            cur_info['_type'] = 'url_transparent'
            return cur_info

        if len(video_urls) == 1 and not iframe_links:
            return make_video_entry(video_id, video_urls[0])

        if len(iframe_links) == 1 and not video_urls:
            return make_iframe_entry(video_id, iframe_links[0])

        entries = []

        if video_urls:
            for num, video_url in enumerate(video_urls, 1):
                entries.append(make_video_entry(video_id, video_url, num))

        if iframe_links:
            for num, iframe_link in enumerate(iframe_links, len(video_urls) + 1):
                entries.append(make_iframe_entry(video_id, iframe_link, num))

        playlist = common_info.copy()
        playlist.update(self.playlist_result(entries, video_id, title, description))
        return playlist


class LifeEmbedIE(InfoExtractor):
    IE_NAME = 'life:embed'
    _VALID_URL = r'https?://embed\.life\.ru/embed/(?P<id>[\da-f]{32})'

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
