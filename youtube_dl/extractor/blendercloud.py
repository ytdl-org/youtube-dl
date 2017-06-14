# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
import re


class BlenderCloudIE(InfoExtractor):
    _VALID_URL = r'https?://cloud\.blender\.org/[^/]+/(?P<display_id>[0-9a-z-]+)/(?P<base_node_id>[0-9a-z]+)?'

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
            # Playlist
            'url': 'https://cloud.blender.org/p/blenderella/',
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
    ]

    def get_node_title(self, source):
        node_title = None
        node_title = self._html_search_regex(
            r'<div\s*id=\"node-title\"\s*class=\"node-title\">(.*?)</div>', source, 'title').strip()
        #print "BlenderCloudIE : get_node_title : node_title : %s" % node_title
        return node_title

    def get_webpage_title(self, source):
        webpage_title = None
        webpage_title = self._html_search_regex(
            r'<title>(.*?)</title>', source, 'title').strip()
        #print "BlenderCloudIE : get_webpage_title : webpage_title : %s" % webpage_title
        return webpage_title

    def is_video_subscriber_only(self, source):
        errmsg_subscribers_only = 'Only available to Blender Cloud subscribers.'
        return True if errmsg_subscribers_only in source else False

    def get_video_formats(self, source):
        video_formats = []
        for video in re.findall(r'<source\s*src=\"(.*?)\"\s*type="video/(.*?)"', source):
            #print "BlenderCloudIE : get_video_formats : video : %s" % video[0]
            #print "BlenderCloudIE : get_video_formats : video_type : %s" % video[1]
            video_url = video[0].replace('&amp;', '&')
            video_format_id = video[1].upper()
            fmt = {
                'url': video_url,
                'format_id': video_format_id,
                'quality': 2 if video_format_id == 'MP4' else 1,
            }
            video_formats.append(fmt)
        return video_formats

    def _real_extract(self, url):
        #print "BlenderCloudIE : _real_extract : %s" % url

        mobj = re.match(self._VALID_URL, url)
        base_node_id = mobj.group('base_node_id')
        display_id = mobj.group('display_id')
        #print "BlenderCloudIE : _real_extract : base_node_id : %s" % base_node_id
        #print "BlenderCloudIE : _real_extract : display_id : %s" % display_id

        url_node = "https://cloud.blender.org/nodes/%s/view"

        warning_subscribers_only = 'Only available to Blender Cloud subscribers.'
        warning_no_video_sources = 'No video sources available.'

        if base_node_id:
            # extract a single video -or- a playlist of subsection videos

            webpage = self._download_webpage(url_node % base_node_id, base_node_id)

            if "<section class=\"node-preview video\">" in webpage:
                # this node references a single video (i.e. a single node)

                title = None
                formats = []

                if self.is_video_subscriber_only(webpage):
                    self.report_warning('%s - %s' % (base_node_id, warning_subscribers_only))
                else:
                    title = self.get_node_title(webpage)
                    formats = self.get_video_formats(webpage)
                    self._check_formats(formats, base_node_id)
                    self._sort_formats(formats)

                return {
                    'id': base_node_id,
                    'display_id': display_id,
                    'title': title,
                    'formats': formats,
                }
            elif "<section class=\"node-preview group\">" in webpage:
                # this node references a playlist of subsection videos (i.e. multiple nodes)

                entries = []
                for node_id in re.findall(r'data-node_id=\"([0-9a-z]+)\"\s*title=\"', webpage):
                    #print "BlenderCloudIE : _real_extract : node_id : %s" % node_id

                    webpage_node = self._download_webpage(url_node % node_id, node_id)

                    if "<section class=\"node-preview video\">" in webpage_node:
                        if self.is_video_subscriber_only(webpage_node):
                            self.report_warning('%s - %s' % (node_id, warning_subscribers_only))
                        else:
                            title = self.get_node_title(webpage_node)
                            formats = self.get_video_formats(webpage_node)
                            self._check_formats(formats, node_id)
                            self._sort_formats(formats)

                            entries.append({
                                'id': node_id,
                                'display_id': display_id,
                                'title': title,
                                'formats': formats,
                            })
                    else:
                        self.report_warning('%s - %s' % (node_id, warning_no_video_sources))

                #print "BlenderCloudIE : _real_extract : entries : %s" % entries
                return self.playlist_result(entries, playlist_id=base_node_id, playlist_title=self.get_node_title(webpage))
            else:
                self.report_warning('%s - %s' % (base_node_id, warning_no_video_sources))
                return {
                    'id': base_node_id,
                    'display_id': display_id,
                    'title': None,
                    'formats': [],
                }
        else:
            # extract the entire playlist for an entire video section

            webpage = self._download_webpage(url, display_id)

            entries = []
            for node_id in re.findall(r'data-node_id=\"([0-9a-z]+)\"\s*class=\"', webpage):
                #print "BlenderCloudIE : _real_extract : node_id : %s" % node_id

                webpage_node = self._download_webpage(url_node % node_id, node_id)

                if "<section class=\"node-preview video\">" in webpage_node:
                    # this node references a single video (i.e. a single node)

                    title = None
                    formats = []

                    if self.is_video_subscriber_only(webpage_node):
                        self.report_warning('%s - %s' % (node_id, warning_subscribers_only))
                    else:
                        title = self.get_node_title(webpage_node)
                        formats = self.get_video_formats(webpage_node)
                        self._check_formats(formats, node_id)
                        self._sort_formats(formats)

                        entries.append({
                            'id': node_id,
                            'display_id': display_id,
                            'title': title,
                            'formats': formats,
                        })
                elif "<section class=\"node-preview group\">" in webpage_node:
                    # this node references a playlist of subsection videos (i.e. multiple nodes)

                    for sub_node_id in re.findall(r'data-node_id=\"([0-9a-z]+)\"\s*title=\"', webpage_node):
                        #print "BlenderCloudIE : _real_extract : sub_node_id : %s" % sub_node_id

                        webpage_sub_node = self._download_webpage(url_node % sub_node_id, sub_node_id)

                        if "<section class=\"node-preview video\">" in webpage_sub_node:
                            if self.is_video_subscriber_only(webpage_sub_node):
                                self.report_warning('%s - %s' % (sub_node_id, warning_subscribers_only))
                            else:
                                title = self.get_node_title(webpage_sub_node)
                                formats = self.get_video_formats(webpage_sub_node)
                                self._check_formats(formats, sub_node_id)
                                self._sort_formats(formats)

                                entries.append({
                                    'id': sub_node_id,
                                    'display_id': display_id,
                                    'title': title,
                                    'formats': formats,
                                })
                        else:
                            self.report_warning('%s - %s' % (sub_node_id, warning_no_video_sources))
                else:
                    self.report_warning('%s - %s' % (node_id, warning_no_video_sources))

            return self.playlist_result(entries, playlist_id=display_id, playlist_title=self.get_webpage_title(webpage))
