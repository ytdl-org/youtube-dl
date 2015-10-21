# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    xpath_text,
)


class AdultSwimIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?adultswim\.com/videos/(?P<is_playlist>playlists/)?(?P<show_path>[^/]+)/(?P<episode_path>[^/?#]+)/?'

    _TESTS = [{
        'url': 'http://adultswim.com/videos/rick-and-morty/pilot',
        'playlist': [
            {
                'md5': '247572debc75c7652f253c8daa51a14d',
                'info_dict': {
                    'id': 'rQxZvXQ4ROaSOqq-or2Mow-0',
                    'ext': 'flv',
                    'title': 'Rick and Morty - Pilot Part 1',
                    'description': "Rick moves in with his daughter's family and establishes himself as a bad influence on his grandson, Morty. "
                },
            },
            {
                'md5': '77b0e037a4b20ec6b98671c4c379f48d',
                'info_dict': {
                    'id': 'rQxZvXQ4ROaSOqq-or2Mow-3',
                    'ext': 'flv',
                    'title': 'Rick and Morty - Pilot Part 4',
                    'description': "Rick moves in with his daughter's family and establishes himself as a bad influence on his grandson, Morty. "
                },
            },
        ],
        'info_dict': {
            'id': 'rQxZvXQ4ROaSOqq-or2Mow',
            'title': 'Rick and Morty - Pilot',
            'description': "Rick moves in with his daughter's family and establishes himself as a bad influence on his grandson, Morty. "
        },
        'skip': 'This video is only available for registered users',
    }, {
        'url': 'http://www.adultswim.com/videos/playlists/american-parenting/putting-francine-out-of-business/',
        'playlist': [
            {
                'md5': '2eb5c06d0f9a1539da3718d897f13ec5',
                'info_dict': {
                    'id': '-t8CamQlQ2aYZ49ItZCFog-0',
                    'ext': 'flv',
                    'title': 'American Dad - Putting Francine Out of Business',
                    'description': 'Stan hatches a plan to get Francine out of the real estate business.Watch more American Dad on [adult swim].'
                },
            }
        ],
        'info_dict': {
            'id': '-t8CamQlQ2aYZ49ItZCFog',
            'title': 'American Dad - Putting Francine Out of Business',
            'description': 'Stan hatches a plan to get Francine out of the real estate business.Watch more American Dad on [adult swim].'
        },
    }, {
        'url': 'http://www.adultswim.com/videos/tim-and-eric-awesome-show-great-job/dr-steve-brule-for-your-wine/',
        'playlist': [
            {
                'md5': '3e346a2ab0087d687a05e1e7f3b3e529',
                'info_dict': {
                    'id': 'sY3cMUR_TbuE4YmdjzbIcQ-0',
                    'ext': 'flv',
                    'title': 'Tim and Eric Awesome Show Great Job! - Dr. Steve Brule, For Your Wine',
                    'description': 'Dr. Brule reports live from Wine Country with a special report on wines.  \r\nWatch Tim and Eric Awesome Show Great Job! episode #20, "Embarrassed" on Adult Swim.\r\n\r\n',
                },
            }
        ],
        'info_dict': {
            'id': 'sY3cMUR_TbuE4YmdjzbIcQ',
            'title': 'Tim and Eric Awesome Show Great Job! - Dr. Steve Brule, For Your Wine',
            'description': 'Dr. Brule reports live from Wine Country with a special report on wines.  \r\nWatch Tim and Eric Awesome Show Great Job! episode #20, "Embarrassed" on Adult Swim.\r\n\r\n',
        },
    }]

    @staticmethod
    def find_video_info(collection, slug):
        for video in collection.get('videos'):
            if video.get('slug') == slug:
                return video

    @staticmethod
    def find_collection_by_linkURL(collections, linkURL):
        for collection in collections:
            if collection.get('linkURL') == linkURL:
                return collection

    @staticmethod
    def find_collection_containing_video(collections, slug):
        for collection in collections:
            for video in collection.get('videos'):
                if video.get('slug') == slug:
                    return collection, video
        return None, None

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_path = mobj.group('show_path')
        episode_path = mobj.group('episode_path')
        is_playlist = True if mobj.group('is_playlist') else False

        webpage = self._download_webpage(url, episode_path)

        # Extract the value of `bootstrappedData` from the Javascript in the page.
        bootstrapped_data = self._parse_json(self._search_regex(
            r'var bootstrappedData = ({.*});', webpage, 'bootstraped data'), episode_path)

        # Downloading videos from a /videos/playlist/ URL needs to be handled differently.
        # NOTE: We are only downloading one video (the current one) not the playlist
        if is_playlist:
            collections = bootstrapped_data['playlists']['collections']
            collection = self.find_collection_by_linkURL(collections, show_path)
            video_info = self.find_video_info(collection, episode_path)

            show_title = video_info['showTitle']
            segment_ids = [video_info['videoPlaybackID']]
        else:
            collections = bootstrapped_data['show']['collections']
            collection, video_info = self.find_collection_containing_video(collections, episode_path)
            # Video wasn't found in the collections, let's try `slugged_video`.
            if video_info is None:
                if bootstrapped_data.get('slugged_video', {}).get('slug') == episode_path:
                    video_info = bootstrapped_data['slugged_video']
                else:
                    raise ExtractorError('Unable to find video info')

            show = bootstrapped_data['show']
            show_title = show['title']
            stream = video_info.get('stream')
            clips = [stream] if stream else video_info.get('clips')
            if not clips:
                raise ExtractorError(
                    'This video is only available via cable service provider subscription that'
                    ' is not currently supported. You may want to use --cookies.'
                    if video_info.get('auth') is True else 'Unable to find stream or clips',
                    expected=True)
            segment_ids = [clip['videoPlaybackID'] for clip in clips]

        episode_id = video_info['id']
        episode_title = video_info['title']
        episode_description = video_info['description']
        episode_duration = video_info.get('duration')

        entries = []
        for part_num, segment_id in enumerate(segment_ids):
            segment_url = 'http://www.adultswim.com/videos/api/v0/assets?id=%s&platform=desktop' % segment_id

            segment_title = '%s - %s' % (show_title, episode_title)
            if len(segment_ids) > 1:
                segment_title += ' Part %d' % (part_num + 1)

            idoc = self._download_xml(
                segment_url, segment_title,
                'Downloading segment information', 'Unable to download segment information')

            segment_duration = float_or_none(
                xpath_text(idoc, './/trt', 'segment duration').strip())

            formats = []
            file_els = idoc.findall('.//files/file') or idoc.findall('./files/file')

            unique_urls = []
            unique_file_els = []
            for file_el in file_els:
                media_url = file_el.text
                if not media_url or determine_ext(media_url) == 'f4m':
                    continue
                if file_el.text not in unique_urls:
                    unique_urls.append(file_el.text)
                    unique_file_els.append(file_el)

            for file_el in unique_file_els:
                bitrate = file_el.attrib.get('bitrate')
                ftype = file_el.attrib.get('type')
                media_url = file_el.text
                if determine_ext(media_url) == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        media_url, segment_title, 'mp4', preference=0, m3u8_id='hls'))
                else:
                    formats.append({
                        'format_id': '%s_%s' % (bitrate, ftype),
                        'url': file_el.text.strip(),
                        # The bitrate may not be a number (for example: 'iphone')
                        'tbr': int(bitrate) if bitrate.isdigit() else None,
                    })

            self._sort_formats(formats)

            entries.append({
                'id': segment_id,
                'title': segment_title,
                'formats': formats,
                'duration': segment_duration,
                'description': episode_description
            })

        return {
            '_type': 'playlist',
            'id': episode_id,
            'display_id': episode_path,
            'entries': entries,
            'title': '%s - %s' % (show_title, episode_title),
            'description': episode_description,
            'duration': episode_duration
        }
