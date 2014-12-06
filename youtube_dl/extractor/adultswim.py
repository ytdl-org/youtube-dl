# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
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
            'title': 'Rick and Morty - Pilot',
            'description': "Rick moves in with his daughter's family and establishes himself as a bad influence on his grandson, Morty. "
        }
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
            'title': 'American Dad - Putting Francine Out of Business',
            'description': 'Stan hatches a plan to get Francine out of the real estate business.Watch more American Dad on [adult swim].'
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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_path = mobj.group('show_path')
        episode_path = mobj.group('episode_path')
        is_playlist = True if mobj.group('is_playlist') else False

        webpage = self._download_webpage(url, episode_path)

        # Extract the value of `bootstrappedData` from the Javascript in the page.
        bootstrappedDataJS = self._search_regex(r'var bootstrappedData = ({.*});', webpage, episode_path)

        try:
            bootstrappedData = json.loads(bootstrappedDataJS)
        except ValueError as ve:
            errmsg = '%s: Failed to parse JSON ' % episode_path
            raise ExtractorError(errmsg, cause=ve)

        # Downloading videos from a /videos/playlist/ URL needs to be handled differently.
        # NOTE: We are only downloading one video (the current one) not the playlist
        if is_playlist:
            collections = bootstrappedData['playlists']['collections']
            collection = self.find_collection_by_linkURL(collections, show_path)
            video_info = self.find_video_info(collection, episode_path)

            show_title = video_info['showTitle']
            segment_ids = [video_info['videoPlaybackID']]
        else:
            collections = bootstrappedData['show']['collections']
            collection, video_info = self.find_collection_containing_video(collections, episode_path)

            show = bootstrappedData['show']
            show_title = show['title']
            segment_ids = [clip['videoPlaybackID'] for clip in video_info['clips']]

        episode_id = video_info['id']
        episode_title = video_info['title']
        episode_description = video_info['description']
        episode_duration = video_info.get('duration')

        entries = []
        for part_num, segment_id in enumerate(segment_ids):
            segment_url = 'http://www.adultswim.com/videos/api/v0/assets?id=%s&platform=mobile' % segment_id

            segment_title = '%s - %s' % (show_title, episode_title)
            if len(segment_ids) > 1:
                segment_title += ' Part %d' % (part_num + 1)

            idoc = self._download_xml(
                segment_url, segment_title,
                'Downloading segment information', 'Unable to download segment information')

            segment_duration = idoc.find('.//trt').text.strip()

            formats = []
            file_els = idoc.findall('.//files/file')

            for file_el in file_els:
                bitrate = file_el.attrib.get('bitrate')
                ftype = file_el.attrib.get('type')

                formats.append({
                    'format_id': '%s_%s' % (bitrate, ftype),
                    'url': file_el.text.strip(),
                    # The bitrate may not be a number (for example: 'iphone')
                    'tbr': int(bitrate) if bitrate.isdigit() else None,
                    'quality': 1 if ftype == 'hd' else -1
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
