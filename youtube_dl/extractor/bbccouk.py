from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class BBCCoUkIE(InfoExtractor):
    IE_NAME = 'bbc.co.uk'
    IE_DESC = 'BBC - iPlayer Radio'
    _VALID_URL = r'https?://(?:www\.)?bbc\.co\.uk/programmes/(?P<id>[\da-z]{8})'

    _TEST = {
        'url': 'http://www.bbc.co.uk/programmes/p01q7wz1',
        'info_dict': {
            'id': 'p01q7wz4',
            'ext': 'flv',
            'title': 'Friction: Blu Mar Ten guest mix: Blu Mar Ten - Guest Mix',
            'description': 'Blu Mar Ten deliver a Guest Mix for Friction.',
            'duration': 1936,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        group_id = mobj.group('id')

        playlist = self._download_xml('http://www.bbc.co.uk/iplayer/playlist/%s' % group_id, group_id,
            'Downloading playlist XML')

        item = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}item')
        if item is None:
            no_items = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}noItems')
            if no_items is not None:
                reason = no_items.get('reason')
                if reason == 'preAvailability':
                    msg = 'Episode %s is not yet available' % group_id
                elif reason == 'postAvailability':
                    msg = 'Episode %s is no longer available' % group_id
                else:
                    msg = 'Episode %s is not available: %s' % (group_id, reason)
                raise ExtractorError(msg, expected=True)
            raise ExtractorError('Failed to extract media for episode %s' % group_id, expected=True)

        title = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}title').text
        description = playlist.find('./{http://bbc.co.uk/2008/emp/playlist}summary').text

        radio_programme_id = item.get('identifier')
        duration = int(item.get('duration'))

        media_selection = self._download_xml(
            'http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/pc/vpid/%s'  % radio_programme_id,
            radio_programme_id, 'Downloading media selection XML')

        formats = []
        for media in media_selection.findall('./{http://bbc.co.uk/2008/mp/mediaselection}media'):
            bitrate = int(media.get('bitrate'))
            encoding = media.get('encoding')
            service = media.get('service')
            connection = media.find('./{http://bbc.co.uk/2008/mp/mediaselection}connection')
            protocol = connection.get('protocol')
            priority = connection.get('priority')
            supplier = connection.get('supplier')
            if protocol == 'http':
                href = connection.get('href')
                # ASX playlist
                if supplier == 'asx':
                    asx = self._download_xml(href, radio_programme_id, 'Downloading %s ASX playlist' % service)
                    for i, ref in enumerate(asx.findall('./Entry/ref')):
                        formats.append({
                            'url': ref.get('href'),
                            'format_id': '%s_ref%s' % (service, i),
                            'abr': bitrate,
                            'acodec': encoding,
                            'preference': priority,
                        })
                    continue
                # Direct link
                formats.append({
                    'url': href,
                    'format_id': service,
                    'abr': bitrate,
                    'acodec': encoding,
                    'preference': priority,
                })
            elif protocol == 'rtmp':
                application = connection.get('application', 'ondemand')
                auth_string = connection.get('authString')
                identifier = connection.get('identifier')
                server = connection.get('server')
                formats.append({
                    'url': '%s://%s/%s?%s' % (protocol, server, application, auth_string),
                    'play_path': identifier,
                    'app': '%s?%s' % (application, auth_string),
                    'rtmp_live': False,
                    'ext': 'flv',
                    'format_id': service,
                    'abr': bitrate,
                    'acodec': encoding,
                    'preference': priority,
                })

        self._sort_formats(formats)

        return {
            'id': radio_programme_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats,
        }