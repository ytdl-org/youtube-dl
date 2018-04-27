# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str
)
from ..utils import (
    int_or_none,
    ExtractorError,
    float_or_none,
    determine_ext
)


class PuhuTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?puhutv\.com/(?P<id>[a-z0-9-]+)-izle'
    _TESTS = [
        { # A Film
            'url': 'https://puhutv.com/sut-kardesler-izle',
            'md5': '51f11ccdeef908753b4e3a99d19be939',
            'info_dict': {
                'id': '5085',
                'display_id': 'sut-kardesler',
                'ext': 'mp4',
                'title': 'Süt Kardeşler',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'Arzu Film',
                'description': 'md5:405fd024df916ca16731114eb18e511a',
                'uploader_id': '43',
                'upload_date': '20160729',
            },
        },
        { # An Episode
            'url': 'https://puhutv.com/jet-sosyete-1-bolum-izle',
            'md5': 'e47096511f5ee1fee3586a5714955a25',
            'info_dict': {
                'id': '18501',
                'display_id': 'jet-sosyete-1-bolum',
                'ext': 'mp4',
                'title': 'Jet Sosyete 1. Sezon 1. Bölüm',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'BKM',
                'description': 'md5:0312864b87d6b9b917694a5742fffabd',
                'uploader_id': '269',
                'upload_date': '20180220',
            },
        },
        { # Has subtitle
            'url': 'https://puhutv.com/dip-1-bolum-izle',
            'md5': 'ef912104860ad0496b73c57d7f03bf8e',
            'info_dict': {
                'id': '18944',
                'display_id': 'dip-1-bolum',
                'ext': 'mp4',
                'title': 'Dip 1. Sezon 1. Bölüm',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'TMC',
                'description': 'md5:8459001a7decfdc4104ca38a979a41fd',
                'uploader_id': '25',
                'upload_date': '20180330',
            },
            'params': {
                'skip_download': True,
            }
        }
    ]
    IE_NAME = 'puhutv'
    _SUBTITLE_LANGS = { # currently supported for some series
        'English':'en',
        'Deutsch':'de',
        'عربى':'ar'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(
            'https://puhutv.com/api/slug/%s-izle' % video_id,
            video_id).get('data')

        id = compat_str(info.get('id'))
        title = info.get('title').get('name')
        if(info.get('display_name')):
            title += ' ' + info.get('display_name')
        description = info.get('title').get('description')
        upload_date = info.get('created_at').split('T')[0].replace('-', '')
        uploader = info.get('title').get('producer').get('name')
        uploader_id = compat_str(info.get('title').get('producer').get('id'))
        view_count = int_or_none(info.get('content').get('watch_count'))
        duration = float_or_none(info.get('content').get('duration_in_ms'), scale=1000)
        thumbnail = 'https://%s' % info.get('content').get('images').get('wide').get('main')
        release_year = int_or_none(info.get('title').get('released_at'))
        webpage_url = info.get('web_url')

        # for series
        season_number = int_or_none(info.get('season_number'))
        season_id = int_or_none(info.get('season_id'))
        episode_number = int_or_none(info.get('episode_number'))


        tags = []
        for tag in info.get('title').get('genres'):
            tags.append(tag.get('name'))

        thumbnails = []
        for key,image in info.get('content').get('images').get('wide').items():
            thumbnails.append({
                'url': image,
                'id': key
            })

        subtitles = {}
        for subtitle in info.get('content').get('subtitles'):
            lang = subtitle.get('language')
            sub_url = subtitle.get('url')
            subtitles[self._SUBTITLE_LANGS.get(lang, lang)] = [{
                'url': sub_url,
                'ext': determine_ext(sub_url)
            }]

        format_dict = self._download_json(
            'https://puhutv.com/api/assets/%s/videos' % id,
            video_id, 'Downloading sources').get('data').get('videos')
        if not format_dict:
            raise ExtractorError('This video not available in your country')

        formats = []
        for format in format_dict:
            media_url = format.get('url')
            ext = format.get('video_format')
            quality = format.get('quality')
            if ext == 'hls':
                format_id = 'hls-%s' % quality
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'm3u8', preference=-1,
                    m3u8_id=format_id, fatal=False))
            else:
                if format.get('is_playlist') == False:
                    formats.append({
                        'url': media_url,
                        'format_id': 'http-%s' % quality,
                        'ext': ext
                    })
        self._sort_formats(formats)

        return {
            'id': id,
            'display_id': video_id,
            'title': title,
            'description': description,
            'season_id': season_id,
            'season_number': season_number,
            'episode_number': episode_number,
            'release_year': release_year,
            'upload_date': upload_date,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            'duration': duration,
            'tags': tags,
            'subtitles': subtitles,
            'webpage_url': webpage_url,
            'thumbnail': thumbnail,
            'thumbnails': thumbnails,
            'formats': formats
        }
