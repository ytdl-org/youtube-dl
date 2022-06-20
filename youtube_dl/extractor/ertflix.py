# coding: utf-8
from __future__ import unicode_literals
from ..utils import( parse_age_limit,
    determine_ext,
    parse_age_limit,
    str_or_none,
    try_get,
    url_or_none,
)
from .common import InfoExtractor


class ErtflixIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ertflix\.gr/(?:series|vod)/(?P<id>[a-z]{3}\.\d+)'
    _TESTS = [{
        'url': 'https://www.ertflix.gr/en/vod/vod.130833-the-incredible-story-of-the-giant-pear-i-apisteyti-istoria-toy-gigantioy-achladioy',
        'info_dict': {
            'id': '130833',
            'displayid' : 'Η απίστευτη ιστορία του γιγάντιου αχλαδιού',
            'ext': 'mp4',
            'title': 'Η απίστευτη ιστορία του γιγάντιου αχλαδιού',
            'description' : 'The incredible story of the giant pear.',
            'thumbnail': r're:^https?://.*\.jpg$',
       },
        'params': {
            'format': 'bestvideo',
        }
    },{'url': 'https://www.ertflix.gr/en/series/ser.161418-dunata',
        'info_dict': {
            'id': '161418',
            'displayid' : 'Out Loud',
            'ext': 'mp4',
            'title': 'Out Loud',
            'description' : 'It is a celebration, a performance, a gathering of friends, a concert, a game show ',
            'thumbnail': r're:^https?://.*\.jpg$',
       },
    }]

    def _extract_formats_and_subs(self, video_id, allow_none=True):
        media_info = self._call_api(video_id, codename=video_id)
        formats, subs = [], {}
        for media_file in try_get(media_info, lambda x: x['MediaFiles'], list) or []:
            for media in try_get(media_file, lambda x: x['Formats'], list) or []:
                fmt_url = url_or_none(try_get(media, lambda x: x['Url']))
                if not fmt_url:
                    continue
                ext = determine_ext(fmt_url)
                if ext == 'm3u8':
                    formats_, subs_ = self._extract_m3u8_formats_and_subtitles(
                        fmt_url, video_id, m3u8_id='hls', ext='mp4', fatal=False)
                elif ext == 'mpd':
                    formats_, subs_ = self._extract_mpd_formats_and_subtitles(
                        fmt_url, video_id, mpd_id='dash', fatal=False)
                else:
                    formats.append({
                        'url': fmt_url,
                        'format_id': str_or_none(media.get('Id')),
                    })
                    continue
                formats.extend(formats_)
                self._merge_subtitles(subs_, target=subs)

        if formats or not allow_none:
            self._sort_formats(formats)
        return formats, subs

    @staticmethod
    def _parse_age_rating(info_dict):
        return parse_age_limit(
            info_dict.get('AgeRating')
            or (info_dict.get('IsAdultContent') and 18)
            or (info_dict.get('IsKidsContent') and 0))

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_url = self._search_regex(
            r"url\s*:\s*'(rtmp://[^']+)'",
            webpage, 'video URL')

        video_id = self._search_regex(
            r'mediaid\s*=\s*(\d+)',
            webpage, 'video id', fatal=False)
        
        description = self._og_search_description(webpage)

        title = self._og_search_title(webpage)

        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'url' : video_url,
            'title': title,
            'description': description ,
            'thumbnail' : thumbnail 
        } 
