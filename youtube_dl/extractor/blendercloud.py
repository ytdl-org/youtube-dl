# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
import re


class BlenderCloudBaseIE(InfoExtractor):
    # A video on the Blender Cloud site is referenced by a single alphanumeric node,
    # i.e. '56041550044a2a00d0d7e068'
    #
    # The data we want for any given node ID can be fetched at:
    url_node = "https://cloud.blender.org/nodes/%s/view"

    # TODO: Add authentication scheme for subscriber-only videos.
    #
    # This will require the use of a (paid) Blender ID token available from:
    # https://store.blender.org/product/membership/
    #
    # For now - ignore any subscriber-only videos and just grab the public ones.

    def notify_for(self, node_id, notify_type):
        notify_message = None
        if notify_type == 'subscribers_only':
            notify_message = 'Only available to Blender Cloud subscribers.'
        elif notify_type == 'no_video_sources_available':
            notify_message = 'No video sources available.'
        else:
            return None
        self.report_warning('%s - %s' % (node_id, notify_message))

    def get_node_title(self, source):
        return self._html_search_regex(
            r'<div\s*class=\"node-title\"\s*id=\"node-title\">(.*?)</div>', source, 'title').strip()

    def get_video_single(self, node_id, source):
        video_title = None
        video_formats = []
        if self.is_video(source, 'subscribers_only'):
            self.notify_for(node_id, 'subscribers_only')
        else:
            video_title = self.get_node_title(source)
            video_formats = self.get_video_formats(source)
            self._sort_formats(video_formats)
        return video_title, video_formats

    def get_video_playlist(self, display_id, source):
        entries = []
        for node_id in re.findall(r'data-node_id=\"([0-9a-z]+)\"\s*title=\"', source):
            webpage_node = self._download_webpage(self.url_node % node_id, node_id)
            if self.is_video(webpage_node, 'single'):
                title, formats = self.get_video_single(node_id, webpage_node)
                if title is not None:
                    entries.append({
                        'id': node_id,
                        'display_id': display_id,
                        'title': title,
                        'formats': formats,
                    })
            else:
                self.notify_for(node_id, 'no_video_sources_available')
        return entries

    @staticmethod
    def is_video(source, check_for):
        tag = None
        if check_for == 'subscribers_only':
            tag = 'Only available to Blender Cloud subscribers.'
        elif check_for == 'single':
            tag = '<section class="node-preview video">'
        elif check_for == 'playlist':
            tag = '<section class="node-preview group">'
        else:
            return False
        return True if tag in source else False

    @staticmethod
    def get_video_formats(source):
        video_formats = []
        for video in re.findall(r'<source\s*src=\"(.*?)\"\s*type="video/(.*?)"', source):
            video_url = video[0].replace('&amp;', '&')
            video_format_id = video[1].upper()
            fmt = {
                'url': video_url,
                'format_id': video_format_id,
                'quality': 2 if video_format_id == 'MP4' else 1,
            }
            video_formats.append(fmt)
        return video_formats


class BlenderCloudIE(BlenderCloudBaseIE):
    _VALID_URL = r'https?://cloud\.blender\.org/[^/]+/(?P<display_id>[0-9a-z-]+)/(?P<node_id>[0-9a-z]+)/?'
    _TESTS = [
        {
            # Single video
            'url': 'https://cloud.blender.org/p/game-asset-creation/56041550044a2a00d0d7e068',
            'info_dict': {
                'id': '56041550044a2a00d0d7e068',
                'display_id': 'game-asset-creation',
                'ext': 'mp4',
                'title': 'Introduction',
            },
        },
        {
            # Playlist (subsection)
            'url': 'https://cloud.blender.org/p/game-asset-creation/56041550044a2a00d0d7e069',
            'info_dict': {
                'id': '56041550044a2a00d0d7e069',
                'title': 'Section 1 - Understanding the Interface',
            },
            'playlist': [
                {
                    'info_dict': {
                        'id': '56041550044a2a00d0d7e06a',
                        'display_id': 'game-asset-creation',
                        'ext': 'mp4',
                        'title': 'Chapter 01 - First Encounters',
                    },
                },
                {
                    'info_dict': {
                        'id': '56041550044a2a00d0d7e06b',
                        'display_id': 'game-asset-creation',
                        'ext': 'mp4',
                        'title': 'Chapter 02 - Navigation',
                    },
                },
                {
                    'info_dict': {
                        'id': '56041550044a2a00d0d7e06c',
                        'display_id': 'game-asset-creation',
                        'ext': 'mp4',
                        'title': 'Chapter 03 - Layout Customizing',
                    },
                },
                {
                    'info_dict': {
                        'id': '56041550044a2a00d0d7e06d',
                        'display_id': 'game-asset-creation',
                        'ext': 'mp4',
                        'title': 'Chapter 04 - User Preference Changes',
                    },
                },
            ],
        },
        {
            # Playlist (subsection)
            'url': 'https://cloud.blender.org/p/creature-factory-2/5604151f044a2a00caa7b04b',
            'info_dict': {
                'id': '5604151f044a2a00caa7b04b',
                'title': '01 - First steps',
            },
            'playlist': [
                {
                    'info_dict': {
                        'id': '5604151f044a2a00caa7b04c',
                        'display_id': 'creature-factory-2',
                        'ext': 'mp4',
                        'title': 'Introduction',
                    },
                },
            ],
            'expected_warnings': [
                'Only available to Blender Cloud subscribers.'
            ],
        },
    ]

    def _real_extract(self, url):
        # extract a single video, or a playlist of subsection videos
        mobj = re.match(self._VALID_URL, url)
        node_id = mobj.group('node_id')
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(self.url_node % node_id, node_id)
        title = None
        formats = []
        if self.is_video(webpage, 'single'):
            title, formats = self.get_video_single(node_id, webpage)
        elif self.is_video(webpage, 'playlist'):
            entries = self.get_video_playlist(display_id, webpage)
            return self.playlist_result(
                entries, playlist_id=node_id, playlist_title=self.get_node_title(webpage))
        else:
            self.notify_for(node_id, 'no_video_sources_available')
        return {
            'id': node_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
        }


class BlenderCloudPlaylistIE(BlenderCloudBaseIE):
    _VALID_URL = r'https?://cloud\.blender\.org/[^/]+/(?P<display_id>[0-9a-z-]+)/?$'
    _TESTS = [
        {
            # Playlist (complete)
            'url': 'https://cloud.blender.org/p/blenderella',
            'info_dict': {
                'id': 'blenderella',
                'title': 'Learn Character Modeling — Blender Cloud',
            },
            'playlist': [
                {
                    'info_dict': {
                        'id': '56040ecf044a2a00a515adb0',
                        'display_id': 'blenderella',
                        'ext': 'mp4',
                        'title': '10 - Cheek, Jaw, Forehead, Scalp',
                    },
                },
            ],
            'expected_warnings': [
                'Only available to Blender Cloud subscribers.',
                'No video sources available.'
            ],
        },
        {
            # Playlist (complete)
            'url': 'https://cloud.blender.org/p/blender-inside-out/',
            'info_dict': {
                'id': 'blender-inside-out',
                'title': 'From Maya and Max to Blender — Blender Cloud',
            },
            'playlist': [
                {
                    'info_dict': {
                        'id': '560414b7044a2a00c4a6da99',
                        'display_id': 'blender-inside-out',
                        'ext': 'mp4',
                        'title': 'Interface Tour',
                    },
                },
                {
                    'info_dict': {
                        'id': '560414b7044a2a00c4a6da9d',
                        'display_id': 'blender-inside-out',
                        'ext': 'mp4',
                        'title': 'Search',
                    },
                },
                {
                    'info_dict': {
                        'id': '560414b7044a2a00c4a6da9b',
                        'display_id': 'blender-inside-out',
                        'ext': 'mp4',
                        'title': 'Selection Tools',
                    },
                },
                {
                    'info_dict': {
                        'id': '560414b7044a2a00c4a6da9c',
                        'display_id': 'blender-inside-out',
                        'ext': 'mp4',
                        'title': 'Transform Tools',
                    },
                },
                {
                    'info_dict': {
                        'id': '560414b7044a2a00c4a6da9a',
                        'display_id': 'blender-inside-out',
                        'ext': 'mp4',
                        'title': 'Viewport Navigation',
                    },
                },
            ],
            'expected_warnings': [
                'No video sources available.'
            ],
            'params': {
                'only_matching': True,
            },
        },
    ]

    def _real_extract(self, url):
        # extract the complete playlist for an entire video section
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)
        entries = []
        for node_id in re.findall(r'data-node_id=\"([0-9a-z]+)\"', webpage):
            webpage_node = self._download_webpage(self.url_node % node_id, node_id)
            if self.is_video(webpage_node, 'single'):
                title, formats = self.get_video_single(node_id, webpage_node)
                if title is not None:
                    entries.append({
                        'id': node_id,
                        'display_id': display_id,
                        'title': title,
                        'formats': formats,
                    })
            elif self.is_video(webpage_node, 'playlist'):
                entries = self.get_video_playlist(display_id, webpage_node)
            else:
                self.notify_for(node_id, 'no_video_sources_available')
        return self.playlist_result(
            entries, playlist_id=display_id,
            playlist_title=self._html_search_regex(
                r'<title>(.*?)</title>', webpage, 'title').strip())
