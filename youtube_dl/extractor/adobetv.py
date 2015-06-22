from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    unified_strdate,
    str_to_int,
    float_or_none,
    ISO639Utils,
)


class AdobeTVIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.adobe\.com/watch/[^/]+/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://tv.adobe.com/watch/the-complete-picture-with-julieanne-kost/quick-tip-how-to-draw-a-circle-around-an-object-in-photoshop/',
        'md5': '9bc5727bcdd55251f35ad311ca74fa1e',
        'info_dict': {
            'id': 'quick-tip-how-to-draw-a-circle-around-an-object-in-photoshop',
            'ext': 'mp4',
            'title': 'Quick Tip - How to Draw a Circle Around an Object in Photoshop',
            'description': 'md5:99ec318dc909d7ba2a1f2b038f7d2311',
            'thumbnail': 're:https?://.*\.jpg$',
            'upload_date': '20110914',
            'duration': 60,
            'view_count': int,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player = self._parse_json(
            self._search_regex(r'html5player:\s*({.+?})\s*\n', webpage, 'player'),
            video_id)

        title = player.get('title') or self._search_regex(
            r'data-title="([^"]+)"', webpage, 'title')
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(
            self._html_search_meta('datepublished', webpage, 'upload date'))

        duration = parse_duration(
            self._html_search_meta('duration', webpage, 'duration') or
            self._search_regex(
                r'Runtime:\s*(\d{2}:\d{2}:\d{2})',
                webpage, 'duration', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'<div class="views">\s*Views?:\s*([\d,.]+)\s*</div>',
            webpage, 'view count'))

        formats = [{
            'url': source['src'],
            'format_id': source.get('quality') or source['src'].split('-')[-1].split('.')[0] or None,
            'tbr': source.get('bitrate'),
        } for source in player['sources']]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }


class AdobeTVVideoIE(InfoExtractor):
    _VALID_URL = r'https?://video\.tv\.adobe\.com/v/(?P<id>\d+)'

    _TEST = {
        # From https://helpx.adobe.com/acrobat/how-to/new-experience-acrobat-dc.html?set=acrobat--get-started--essential-beginners
        'url': 'https://video.tv.adobe.com/v/2456/',
        'md5': '43662b577c018ad707a63766462b1e87',
        'info_dict': {
            'id': '2456',
            'ext': 'mp4',
            'title': 'New experience with Acrobat DC',
            'description': 'New experience with Acrobat DC',
            'duration': 248.667,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        player_params = self._parse_json(self._search_regex(
            r'var\s+bridge\s*=\s*([^;]+);', webpage, 'player parameters'),
            video_id)

        formats = [{
            'url': source['src'],
            'width': source.get('width'),
            'height': source.get('height'),
            'tbr': source.get('bitrate'),
        } for source in player_params['sources']]

        # For both metadata and downloaded files the duration varies among
        # formats. I just pick the max one
        duration = max(filter(None, [
            float_or_none(source.get('duration'), scale=1000)
            for source in player_params['sources']]))

        subtitles = {}
        for translation in player_params.get('translations', []):
            lang_id = translation.get('language_w3c') or ISO639Utils.long2short(translation['language_medium'])
            if lang_id not in subtitles:
                subtitles[lang_id] = []
            subtitles[lang_id].append({
                'url': translation['vttPath'],
                'ext': 'vtt',
            })

        return {
            'id': video_id,
            'formats': formats,
            'title': player_params['title'],
            'description': self._og_search_description(webpage),
            'duration': duration,
            'subtitles': subtitles,
        }
