# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    int_or_none,
)


class KalturaIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                (?:
                    kaltura:(?P<partner_id_s>\d+):(?P<id_s>[0-9a-z_]+)|
                    https?://
                        (:?(?:www|cdnapisec)\.)?kaltura\.com/
                        (?:
                            (?:
                                # flash player
                                index\.php/kwidget/
                                (?:[^/]+/)*?wid/_(?P<partner_id>\d+)/
                                (?:[^/]+/)*?entry_id/(?P<id>[0-9a-z_]+)|
                                # html5 player
                                html5/html5lib/
                                (?:[^/]+/)*?entry_id/(?P<id_html5>[0-9a-z_]+)
                                .*\?.*\bwid=_(?P<partner_id_html5>\d+)
                            )
                        )
                )
                '''
    _API_BASE = 'http://cdnapi.kaltura.com/api_v3/index.php?'
    _TESTS = [
        {
            'url': 'kaltura:269692:1_1jc2y3e4',
            'md5': '3adcbdb3dcc02d647539e53f284ba171',
            'info_dict': {
                'id': '1_1jc2y3e4',
                'ext': 'mp4',
                'title': 'Track 4',
                'upload_date': '20131219',
                'uploader_id': 'mlundberg@wolfgangsvault.com',
                'description': 'The Allman Brothers Band, 12/16/1981',
                'thumbnail': 're:^https?://.*/thumbnail/.*',
                'timestamp': int,
            },
        },
        {
            'url': 'http://www.kaltura.com/index.php/kwidget/cache_st/1300318621/wid/_269692/uiconf_id/3873291/entry_id/1_1jc2y3e4',
            'only_matching': True,
        },
        {
            'url': 'https://cdnapisec.kaltura.com/index.php/kwidget/wid/_557781/uiconf_id/22845202/entry_id/1_plr1syf3',
            'only_matching': True,
        },
        {
            'url': 'https://cdnapisec.kaltura.com/html5/html5lib/v2.30.2/mwEmbedFrame.php/p/1337/uiconf_id/20540612/entry_id/1_sf5ovm7u?wid=_243342',
            'only_matching': True,
        }
    ]

    def _kaltura_api_call(self, video_id, actions, *args, **kwargs):
        params = actions[0]
        if len(actions) > 1:
            for i, a in enumerate(actions[1:], start=1):
                for k, v in a.items():
                    params['%d:%s' % (i, k)] = v

        query = compat_urllib_parse.urlencode(params)
        url = self._API_BASE + query
        data = self._download_json(url, video_id, *args, **kwargs)

        status = data if len(actions) == 1 else data[0]
        if status.get('objectType') == 'KalturaAPIException':
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, status['message']))

        return data

    def _get_kaltura_signature(self, video_id, partner_id):
        actions = [{
            'apiVersion': '3.1',
            'expiry': 86400,
            'format': 1,
            'service': 'session',
            'action': 'startWidgetSession',
            'widgetId': '_%s' % partner_id,
        }]
        return self._kaltura_api_call(
            video_id, actions, note='Downloading Kaltura signature')['ks']

    def _get_video_info(self, video_id, partner_id):
        signature = self._get_kaltura_signature(video_id, partner_id)
        actions = [
            {
                'action': 'null',
                'apiVersion': '3.1.5',
                'clientTag': 'kdp:v3.8.5',
                'format': 1,  # JSON, 2 = XML, 3 = PHP
                'service': 'multirequest',
                'ks': signature,
            },
            {
                'action': 'get',
                'entryId': video_id,
                'service': 'baseentry',
                'version': '-1',
            },
            {
                'action': 'getContextData',
                'contextDataParams:objectType': 'KalturaEntryContextDataParams',
                'contextDataParams:referrer': 'http://www.kaltura.com/',
                'contextDataParams:streamerType': 'http',
                'entryId': video_id,
                'service': 'baseentry',
            },
        ]
        return self._kaltura_api_call(
            video_id, actions, note='Downloading video info JSON')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        partner_id = mobj.group('partner_id_s') or mobj.group('partner_id') or mobj.group('partner_id_html5')
        entry_id = mobj.group('id_s') or mobj.group('id') or mobj.group('id_html5')

        info, source_data = self._get_video_info(entry_id, partner_id)

        formats = [{
            'format_id': '%(fileExt)s-%(bitrate)s' % f,
            'ext': f['fileExt'],
            'tbr': f['bitrate'],
            'fps': f.get('frameRate'),
            'filesize_approx': int_or_none(f.get('size'), invscale=1024),
            'container': f.get('containerFormat'),
            'vcodec': f.get('videoCodecId'),
            'height': f.get('height'),
            'width': f.get('width'),
            'url': '%s/flavorId/%s' % (info['dataUrl'], f['id']),
        } for f in source_data['flavorAssets']]
        self._sort_formats(formats)

        return {
            'id': entry_id,
            'title': info['name'],
            'formats': formats,
            'description': info.get('description'),
            'thumbnail': info.get('thumbnailUrl'),
            'duration': info.get('duration'),
            'timestamp': info.get('createdAt'),
            'uploader_id': info.get('userId'),
            'view_count': info.get('plays'),
        }
