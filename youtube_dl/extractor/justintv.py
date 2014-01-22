import json
import os
import re

from .common import InfoExtractor
from ..utils import (
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
    IE_NAME = u'justin.tv'
    _TEST = {
        u'url': u'http://www.twitch.tv/thegamedevhub/b/296128360',
        u'file': u'296128360.flv',
        u'md5': u'ecaa8a790c22a40770901460af191c9a',
        u'info_dict': {
            u"upload_date": u"20110927", 
            u"uploader_id": 25114803, 
            u"uploader": u"thegamedevhub", 
            u"title": u"Beginner Series - Scripting With Python Pt.1"
        }
    }

    def report_download_page(self, channel, offset):
        """Report attempt to download a single page of videos."""
        self.to_screen(u'%s: Downloading video information from %d to %d' %
                (channel, offset, offset + self._JUSTIN_PAGE_LIMIT))

    # Return count of items, list of *valid* items
    def _parse_page(self, url, video_id):
        info_json = self._download_webpage(url, video_id,
                                           u'Downloading video info JSON',
                                           u'unable to download video info JSON')

        response = json.loads(info_json)
        if type(response) != list:
            error_text = response.get('error', 'unknown error')
            raise ExtractorError(u'Justin.tv API: %s' % error_text)
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
                    'id': video_id,
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
        if mobj is None:
            raise ExtractorError(u'invalid URL: %s' % url)

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
                raise ExtractorError(u'Cannot find archive of a chapter')
            archive_id = m.group(1)

            api = api_base + '/broadcast/by_chapter/%s.xml' % chapter_id
            doc = self._download_xml(api, chapter_id,
                                             note=u'Downloading chapter information',
                                             errnote=u'Chapter information download failed')
            for a in doc.findall('.//archive'):
                if archive_id == a.find('./id').text:
                    break
            else:
                raise ExtractorError(u'Could not find chapter in chapter information')

            video_url = a.find('./video_file_url').text
            video_ext = video_url.rpartition('.')[2] or u'flv'

            chapter_api_url = u'https://api.twitch.tv/kraken/videos/c' + chapter_id
            chapter_info_json = self._download_webpage(chapter_api_url, u'c' + chapter_id,
                                   note='Downloading chapter metadata',
                                   errnote='Download of chapter metadata failed')
            chapter_info = json.loads(chapter_info_json)

            bracket_start = int(doc.find('.//bracket_start').text)
            bracket_end = int(doc.find('.//bracket_end').text)

            # TODO determine start (and probably fix up file)
            #  youtube-dl -v http://www.twitch.tv/firmbelief/c/1757457
            #video_url += u'?start=' + TODO:start_timestamp
            # bracket_start is 13290, but we want 51670615
            self._downloader.report_warning(u'Chapter detected, but we can just download the whole file. '
                                            u'Chapter starts at %s and ends at %s' % (formatSeconds(bracket_start), formatSeconds(bracket_end)))

            info = {
                'id': u'c' + chapter_id,
                'url': video_url,
                'ext': video_ext,
                'title': chapter_info['title'],
                'thumbnail': chapter_info['preview'],
                'description': chapter_info['description'],
                'uploader': chapter_info['channel']['display_name'],
                'uploader_id': chapter_info['channel']['name'],
            }
            return [info]
        else:
            video_id = mobj.group('videoid')
            api = api_base + '/broadcast/by_archive/%s.json' % video_id

        self.report_extraction(video_id)

        info = []
        offset = 0
        limit = self._JUSTIN_PAGE_LIMIT
        while True:
            if paged:
                self.report_download_page(video_id, offset)
            page_url = api + ('?offset=%d&limit=%d' % (offset, limit))
            page_count, page_info = self._parse_page(page_url, video_id)
            info.extend(page_info)
            if not paged or page_count != limit:
                break
            offset += limit
        return info
