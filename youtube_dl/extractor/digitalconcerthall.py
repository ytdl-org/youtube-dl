# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DigitalConcertHallIE(InfoExtractor):
    IE_DESC = 'DigitalConcertHall extractor'
    _VALID_URL = r'https?://(?:www\.)?digitalconcerthall\.com/(?P<language>[a-z]+)/concert/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.digitalconcerthall.com/en/concert/51841',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '51841',
            'language': 'en',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*/images/core/Phil.*\.jpg$',
        }
    }

    def debug_out(self, args):
        if not self._downloader.params.get('verbose', False):
            return

        self.to_screen('[debug] %s' % args)

    def _real_extract(self, url):
        MAX_TITLE_LENGTH = 128
        language, video_id = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'
        self.debug_out("url: " + url + " video_id: " + video_id + " language: " + language)
        webpage = self._download_webpage(url, video_id)
        playlist_title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title') or \
            self._og_search_title(webpage)
        self.debug_out("playlist_title: " + playlist_title)

        # this returns JSON containing the urls of the playlist
        # Note:  you must be authenticated to get the stream info
        playlist_dict = self._download_json(
            'https://www.digitalconcerthall.com/json_services/get_stream_urls?id='
            + video_id + "&language=" + language, video_id, note='Downloading Stream JSON').get('urls')
        # use the API to get other information about the concert
        vid_info_dict = self._download_json(
            'https://api.digitalconcerthall.com/v2/concert/'
            + video_id, video_id, headers={'Accept': 'application/json',
                                           'Accept-Language': language})
        embedded = vid_info_dict.get('_embedded')

        flat_list = []
        for embed_type in embedded:
            for item in embedded.get(embed_type):
                if embed_type == 'interview':
                    item['is_interview'] = 1
                else:
                    item['is_interview'] = 0
                flat_list.append(item)

        entries = []
        for key in playlist_dict:
            self.debug_out("key: " + key)
            m3u8_url = playlist_dict.get(key)[0].get('url')
            self.debug_out("key url: " + m3u8_url)
            formats = self._extract_m3u8_formats(
                m3u8_url, key, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
            self.debug_out(formats)
            vid_info = [x for x in flat_list if x.get('id') == key][0]
            if vid_info.get('is_interview') == 1:
                title = "Interview - " + vid_info.get('title', "unknown interview title")
            else:
                title = (vid_info.get('name_composer') if vid_info.get('name_composer')
                         else 'unknown composer') + ' - ' + vid_info.get('title', "unknown title")
            duration = vid_info.get('duration_total')
            # avoid filenames that exceed filesystem limits
            title = (title[:MAX_TITLE_LENGTH] + '..') if len(title) > MAX_TITLE_LENGTH else title
            # append the duration in minutes to the title
            title = title + " (" + str(round(duration / 60)) + " min.)"
            self.debug_out("title: " + title)
            timestamp = vid_info.get('date').get('published')
            entries.append({
                'id': key,
                'title': title,
                'url': m3u8_url,
                'formats': formats,
                'duration': duration,
                'timestamp': timestamp,
            })
            # use playlist description for video description by default
            # but if the video has a description, use it
            if vid_info_dict.get('short_description'):
                entries[-1]['description'] = vid_info_dict.get('short_description', "missing description")
            if vid_info.get('short_description'):
                entries[-1]['description'] = vid_info.get('short_description', "missing description")
            if vid_info.get('cuepoints'):
                chapters = []
                first_chapter = 1
                for chapter in vid_info.get('cuepoints'):
                    start_time = chapter.get('time')
                    # Often, the first chapter does not start at zero.  In this case,
                    # insert an intro chapter so that first chapter is the start of the music
                    if (first_chapter == 1) and (start_time != 0):
                        chapters.append({
                            'start_time': 0,
                            'end_time': start_time,
                            'title': '0. Intro'
                        })
                    first_chapter = 0
                    end_time = start_time + chapter.get('duration')
                    chapter_title = chapter.get('text')
                    chapters.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'title': chapter_title
                    })
                entries[-1]['chapters'] = chapters

        return {
            '_type': 'playlist',
            'id': video_id,
            'title': playlist_title,
            'entries': entries,
        }
