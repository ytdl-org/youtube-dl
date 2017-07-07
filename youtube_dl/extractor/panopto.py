# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import compat_str

from ..utils import (
    ExtractorError,
    smuggle_url,
    unsmuggle_url,
)

import re
from random import random
import json


class PanoptoBaseIE(InfoExtractor):
    """The base class with common methods for Panopto extractors."""

    @classmethod
    def _match_organization(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        m = cls._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group('org'))


class PanoptoIE(PanoptoBaseIE):
    """Extracts a single Panopto video including all available streams."""

    _VALID_URL = r'^https?:\/\/(?P<org>[a-z0-9]+)\.hosted\.panopto.com\/Panopto\/Pages\/Viewer\.aspx\?id=(?P<id>[a-f0-9-]+)'

    @staticmethod
    def _get_contribs_str(contribs):
        s = ''
        for c in contribs:
            s += '%s, ' % c['DisplayName']
        return s[:-2] if len(contribs) else ''

    def _real_extract(self, url):
        video_id = self._match_id(url)
        org = self._match_organization(url)

        delivery_info = self._download_json(
            'https://%s.hosted.panopto.com/Panopto/Pages/Viewer/DeliveryInfo.aspx' % org,
            video_id,
            query={
                'deliveryId': video_id,
                'invocationId': '',
                'isLiveNotes': 'false',
                'refreshAuthCookie': 'true',
                'isActiveBroadcast': 'false',
                'isEditing': 'false',
                'isKollectiveAgentInstalled': 'false',
                'isEmbed': 'false',
                'responseType': 'json',
            }
        )

        if 'ErrorCode' in delivery_info:
            self._downloader.report_warning("If the video you are trying to download requires you to sign-in, you will "
                                            "need to provide a cookies file that allows the downloader to authenticate "
                                            "with Panopto. If the error below is about unauthorized access, this is "
                                            "most likely the issue.")
            raise ExtractorError(
                'API error: (%s) %s' %
                (delivery_info['ErrorCode'], delivery_info['ErrorMessage'] if 'ErrorMessage' in delivery_info else '')
            )

        streams = []
        for this_stream in delivery_info['Delivery']['Streams']:
            new_stream = {
                'id': this_stream['PublicID'],
                'title': this_stream['Tag'],
                'formats': [],
            }
            if 'StreamUrl' in this_stream:
                new_stream['formats'].append({
                    'url': this_stream['StreamUrl'],
                })
            if 'StreamHttpUrl' in this_stream:
                new_stream['formats'].append({
                    'url': this_stream['StreamHttpUrl'],
                })
            if len(new_stream['formats']):
                streams.append(new_stream)

        if not streams:
            raise ExtractorError('No streams found.')

        result = {
            'id': video_id,
            'title': delivery_info['Delivery']['SessionName'],
            'thumbnail': 'https://%s.hosted.panopto.com/Panopto/Services/FrameGrabber.svc/FrameRedirect?objectId=%s&mode=Delivery&random=%s' %
                         (org, video_id, random()),
        }

        if len(streams) == 1:
            result['formats'] = streams[0]['formats']
        else:
            result['_type'] = 'multi_video'
            result['entries'] = streams

        if 'Contributors' in delivery_info['Delivery']:
            result['uploader'] = self._get_contribs_str(delivery_info['Delivery']['Contributors'])

        if 'SessionStartTime' in delivery_info['Delivery']:
            result['timestamp'] = delivery_info['Delivery']['SessionStartTime'] - 11640000000

        if 'Duration' in delivery_info['Delivery']:
            result['duration'] = delivery_info['Delivery']['Duration']

        thumbnails = []
        if 'Timestamps' in delivery_info['Delivery']:
            for timestamp in delivery_info['Delivery']['Timestamps']:
                thumbnails.append({
                    # 'url': 'https://%s.hosted.panopto.com/Panopto/Pages/Viewer/Thumb.aspx?eventTargetPID=%s&sessionPID=%s&number=%s&isPrimary=false&absoluteTime=%s' %
                    #    (org, timestamp['ObjectPublicIdentifier'], timestamp['SessionID'], timestamp['ObjectSequenceNumber'], timestamp['AbsoluteTime']),
                    'url': 'https://%s.hosted.panopto.com/Panopto/Pages/Viewer/Image.aspx?id=%s&number=%s&x=undefined' %
                           (org, timestamp['ObjectIdentifier'], timestamp['ObjectSequenceNumber'])
                })

        if len(thumbnails):
            if result.get('entries') is not None:
                result['entries'][1]['thumbnails'] = thumbnails
            else:
                result['thumbnails'] = thumbnails

        return result


class PanoptoFolderIE(PanoptoBaseIE):
    """Recursively extracts a folder of Panopto videos, digging as far as possible into subfolders."""

    _VALID_URL = r'^https?:\/\/(?P<org>[a-z0-9]+)\.hosted\.panopto.com\/Panopto\/Pages\/Sessions\/List\.aspx#folderID=(?:"|%22)(?P<id>[a-f0-9-]+)'

    def _real_extract(self, url):
        url, smuggled = unsmuggle_url(url)
        if smuggled is None:
            smuggled = {}
        folder_id = self._match_id(url)
        org = self._match_organization(url)

        folder_data = self._download_json(
            'https://%s.hosted.panopto.com/Panopto/Services/Data.svc/GetSessions' % org,
            folder_id,
            'Downloading folder listing',
            'Failed to download folder listing',
            data=json.dumps({
                'queryParameters': {
                    'query': None,
                    'sortColumn': 1,
                    'sortAscending': False,
                    'maxResults': 10000,
                    'page': 0,
                    'startDate': None,
                    'endDate': None,
                    'folderID': folder_id,
                    'bookmarked': False,
                    'getFolderData': True,
                    'isSharedWithMe': False,
                },
            }, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json'})['d']

        entries = []
        if 'Results' in folder_data and folder_data['Results'] is not None:
            for video in folder_data['Results']:
                new_video = {
                    'id': video['DeliveryID'],
                    'title': video['SessionName'],
                    'url': video['ViewerUrl'],
                    '_type': 'url_transparent',
                    'ie_key': 'Panopto',
                }
                if 'prev_folders' in smuggled:
                    new_video['title'] = smuggled['prev_folders'] + ' -- ' + new_video['title']
                entries.append(new_video)

        if 'Subfolders' in folder_data and folder_data['Subfolders'] is not None:
            for subfolder in folder_data['Subfolders']:
                new_folder = {
                    'id': subfolder['ID'],
                    'title': subfolder['Name'],
                    '_type': 'url_transparent',
                    'ie_key': 'PanoptoFolder',
                }
                if 'prev_folders' in smuggled:
                    new_folder['title'] = smuggled['prev_folders'] + ' -- ' + new_folder['title']
                new_folder['url'] = smuggle_url('https://%s.hosted.panopto.com/Panopto/Pages/Sessions/List.aspx#folderID="%s"' %
                                                (org, subfolder['ID']), {'prev_folders': new_folder['title']})
                entries.append(new_folder)

        if not entries:
            raise ExtractorError('Folder is empty or authentication failed')

        return {
            'id': folder_id,
            'title': folder_data['Results'][0]['FolderName'] if len(folder_data['Results']) else folder_data['Subfolders'][0]['ParentFolderName'],
            '_type': 'playlist',
            'entries': entries,
        }
