# coding: utf-8
from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlencode,
    compat_urlparse,
    compat_parse_qs,
)
from ..utils import (
    clean_html,
    ExtractorError,
    int_or_none,
    unsmuggle_url,
)


class KalturaIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                (?:
                    kaltura:(?P<partner_id>\d+):(?P<id>[0-9a-z_]+)|
                    https?://
                        (:?(?:www|cdnapi(?:sec)?)\.)?kaltura\.com/
                        (?:
                            (?:
                                # flash player
                                index\.php/kwidget|
                                # html5 player
                                html5/html5lib/[^/]+/mwEmbedFrame\.php
                            )
                        )(?:/(?P<path>[^?]+))?(?:\?(?P<query>.*))?
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
                'title': 'Straight from the Heart',
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

        query = compat_urllib_parse_urlencode(params)
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
                'action': 'getbyentryid',
                'entryId': video_id,
                'service': 'flavorAsset',
            },
        ]
        return self._kaltura_api_call(
            video_id, actions, note='Downloading video info JSON')

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        mobj = re.match(self._VALID_URL, url)
        partner_id, entry_id = mobj.group('partner_id', 'id')
        ks = None
        if partner_id and entry_id:
            info, flavor_assets = self._get_video_info(entry_id, partner_id)
        else:
            path, query = mobj.group('path', 'query')
            if not path and not query:
                raise ExtractorError('Invalid URL', expected=True)
            params = {}
            if query:
                params = compat_parse_qs(query)
            if path:
                splitted_path = path.split('/')
                params.update(dict((zip(splitted_path[::2], [[v] for v in splitted_path[1::2]]))))
            if 'wid' in params:
                partner_id = params['wid'][0][1:]
            elif 'p' in params:
                partner_id = params['p'][0]
            else:
                raise ExtractorError('Invalid URL', expected=True)
            if 'entry_id' in params:
                entry_id = params['entry_id'][0]
                info, flavor_assets = self._get_video_info(entry_id, partner_id)
            elif 'uiconf_id' in params and 'flashvars[referenceId]' in params:
                reference_id = params['flashvars[referenceId]'][0]
                webpage = self._download_webpage(url, reference_id)
                entry_data = self._parse_json(self._search_regex(
                    r'window\.kalturaIframePackageData\s*=\s*({.*});',
                    webpage, 'kalturaIframePackageData'),
                    reference_id)['entryResult']
                info, flavor_assets = entry_data['meta'], entry_data['contextData']['flavorAssets']
                entry_id = info['id']
            else:
                raise ExtractorError('Invalid URL', expected=True)
            ks = params.get('flashvars[ks]', [None])[0]

        source_url = smuggled_data.get('source_url')
        if source_url:
            referrer = base64.b64encode(
                '://'.join(compat_urlparse.urlparse(source_url)[:2])
                .encode('utf-8')).decode('utf-8')
        else:
            referrer = None

        def sign_url(unsigned_url):
            if ks:
                unsigned_url += '/ks/%s' % ks
            if referrer:
                unsigned_url += '?referrer=%s' % referrer
            return unsigned_url

        formats = []
        for f in flavor_assets:
            # Continue if asset is not ready
            if f['status'] != 2:
                continue
            video_url = sign_url('%s/flavorId/%s' % (info['dataUrl'], f['id']))
            formats.append({
                'format_id': '%(fileExt)s-%(bitrate)s' % f,
                'ext': f.get('fileExt'),
                'tbr': int_or_none(f['bitrate']),
                'fps': int_or_none(f.get('frameRate')),
                'filesize_approx': int_or_none(f.get('size'), invscale=1024),
                'container': f.get('containerFormat'),
                'vcodec': f.get('videoCodecId'),
                'height': int_or_none(f.get('height')),
                'width': int_or_none(f.get('width')),
                'url': video_url,
            })
        m3u8_url = sign_url(info['dataUrl'].replace('format/url', 'format/applehttp'))
        formats.extend(self._extract_m3u8_formats(
            m3u8_url, entry_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))

        self._check_formats(formats, entry_id)
        self._sort_formats(formats)

        return {
            'id': entry_id,
            'title': info['name'],
            'formats': formats,
            'description': clean_html(info.get('description')),
            'thumbnail': info.get('thumbnailUrl'),
            'duration': info.get('duration'),
            'timestamp': info.get('createdAt'),
            'uploader_id': info.get('userId'),
            'view_count': info.get('plays'),
        }
