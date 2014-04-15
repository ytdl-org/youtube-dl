from __future__ import unicode_literals

import json
import os
import re

from .common import InfoExtractor
from ..utils import (
    compat_str,
    ExtractorError,
    formatSeconds,
)


class JustinTVIE(InfoExtractor):
    """Information extractor for justin.tv and twitch.tv"""
    # TODO: One broadcast may be split into multiple videos. The key
    # 'broadcast_id' is the same for all parts, and 'broadcast_part'
    # starts at 1 and increases. Can we treat all parts as one video?

    _VALID_URL = r"""(?x)^(?:http://)?(?:www\.)?(?:twitch|justin)\.tv/
        (?:
            (?P<channelid>[^/]+)|
            (?:(?:[^/]+)/b/(?P<videoid>[^/]+))|
            (?:(?:[^/]+)/c/(?P<chapterid>[^/]+))
        )
        /?(?:\#.*)?$
        """
    _JUSTIN_PAGE_LIMIT = 100
    IE_NAME = 'justin.tv'
    IE_DESC = 'justin.tv and twitch.tv'
    _TEST = {
        'url': 'http://www.twitch.tv/thegamedevhub/b/296128360',
        'md5': 'ecaa8a790c22a40770901460af191c9a',
        'info_dict': {
            'id': '296128360',
            'ext': 'flv',
            'upload_date': '20110927',
            'uploader_id': 25114803,
            'uploader': 'thegamedevhub',
            'title': 'Beginner Series - Scripting With Python Pt.1'
        }
    }

    # Return count of items, list of *valid* items
    def _parse_page(self, url, video_id):
        info_json = self._download_webpage(url, video_id,
                                           'Downloading video info JSON',
                                           'unable to download video info JSON')

        response = json.loads(info_json)
        if type(response) != list:
            error_text = response.get('error', 'unknown error')
            raise ExtractorError('Justin.tv API: %s' % error_text)
        info = []
        for clip in response:
            video_url = clip['video_file_url']
            if video_url:
                video_extension = os.path.splitext(video_url)[1][1:]
                video_date = re.sub('-', '', clip['start_time'][:10])
                video_uploader_id = clip.get('user_id', clip.get('channel_id'))
                video_id = clip['id']
                video_title = clip.get('title', video_id)
                info.append({
                    'id': compat_str(video_id),
                    'url': video_url,
                    'title': video_title,
                    'uploader': clip.get('channel_name', video_uploader_id),
                    'uploader_id': video_uploader_id,
                    'upload_date': video_date,
                    'ext': video_extension,
                })
        return (len(response), info)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        api_base = 'http://api.justin.tv'
        paged = False
        if mobj.group('channelid'):
            paged = True
            video_id = mobj.group('channelid')
            api = api_base + '/channel/archives/%s.json' % video_id
        elif mobj.group('chapterid'):
            chapter_id = mobj.group('chapterid')

            webpage = self._download_webpage(url, chapter_id)
            m = re.search(r'PP\.archive_id = "([0-9]+)";', webpage)
            if not m:
                raise ExtractorError('Cannot find archive of a chapter')
            archive_id = m.group(1)

            api = api_base + '/broadcast/by_chapter/%s.xml' % chapter_id
            doc = self._download_xml(
                api, chapter_id,
                note='Downloading chapter information',
                errnote='Chapter information download failed')
            for a in doc.findall('.//archive'):
                if archive_id == a.find('./id').text:
                    break
            else:
                raise ExtractorError('Could not find chapter in chapter information')

            video_url = a.find('./video_file_url').text
            video_ext = video_url.rpartition('.')[2] or 'flv'

            chapter_api_url = 'https://api.twitch.tv/kraken/videos/c' + chapter_id
            chapter_info = self._download_json(
                chapter_api_url, 'c' + chapter_id,
                note='Downloading chapter metadata',
                errnote='Download of chapter metadata failed')

            bracket_start = int(doc.find('.//bracket_start').text)
            bracket_end = int(doc.find('.//bracket_end').text)

            # TODO determine start (and probably fix up file)
            #  youtube-dl -v http://www.twitch.tv/firmbelief/c/1757457
            #video_url += '?start=' + TODO:start_timestamp
            # bracket_start is 13290, but we want 51670615
            self._downloader.report_warning('Chapter detected, but we can just download the whole file. '
                                            'Chapter starts at %s and ends at %s' % (formatSeconds(bracket_start), formatSeconds(bracket_end)))

            info = {
                'id': 'c' + chapter_id,
                'url': video_url,
                'ext': video_ext,
                'title': chapter_info['title'],
                'thumbnail': chapter_info['preview'],
                'description': chapter_info['description'],
                'uploader': chapter_info['channel']['display_name'],
                'uploader_id': chapter_info['channel']['name'],
            }
            return info
        else:
            video_id = mobj.group('videoid')
            api = api_base + '/broadcast/by_archive/%s.json' % video_id

        entries = []
        offset = 0
        limit = self._JUSTIN_PAGE_LIMIT
        while True:
            if paged:
                self.report_download_page(video_id, offset)
            page_url = api + ('?offset=%d&limit=%d' % (offset, limit))
            page_count, page_info = self._parse_page(page_url, video_id)
            entries.extend(page_info)
            if not paged or page_count != limit:
                break
            offset += limit
        return {
            '_type': 'playlist',
            'id': video_id,
            'entries': entries,
        }
