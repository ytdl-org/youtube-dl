from __future__ import unicode_literals
import re
import json
import base64

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    ExtractorError,
    determine_ext,
    int_or_none,
)


class OoyalaBaseIE(InfoExtractor):

    def _extract_result(self, info, more_info):
        embedCode = info['embedCode']
        video_url = info.get('ipad_url') or info['url']

        if determine_ext(video_url) == 'm3u8':
            formats = self._extract_m3u8_formats(video_url, embedCode, ext='mp4')
        else:
            formats = [{
                'url': video_url,
                'ext': 'mp4',
            }]

        return {
            'id': embedCode,
            'title': unescapeHTML(info['title']),
            'formats': formats,
            'description': unescapeHTML(more_info['description']),
            'thumbnail': more_info['promo'],
        }

    def _extract(self, player_url, video_id):
        player = self._download_webpage(player_url, video_id)
        mobile_url = self._search_regex(r'mobile_player_url="(.+?)&device="',
                                        player, 'mobile player url')
        # Looks like some videos are only available for particular devices
        # (e.g. http://player.ooyala.com/player.js?embedCode=x1b3lqZDq9y_7kMyC2Op5qo-p077tXD0
        # is only available for ipad)
        # Working around with fetching URLs for all the devices found starting with 'unknown'
        # until we succeed or eventually fail for each device.
        devices = re.findall(r'device\s*=\s*"([^"]+)";', player)
        devices.remove('unknown')
        devices.insert(0, 'unknown')
        for device in devices:
            mobile_player = self._download_webpage(
                '%s&device=%s' % (mobile_url, device), video_id,
                'Downloading mobile player JS for %s device' % device)
            videos_info = self._search_regex(
                r'var streams=window.oo_testEnv\?\[\]:eval\("\((\[{.*?}\])\)"\);',
                mobile_player, 'info', fatal=False, default=None)
            if videos_info:
                break

        if not videos_info:
            formats = []
            auth_data = self._download_json(
                'http://player.ooyala.com/sas/player_api/v1/authorization/embed_code/%s/%s?domain=www.example.org&supportedFormats=mp4,webm' % (video_id, video_id),
                video_id)

            cur_auth_data = auth_data['authorization_data'][video_id]

            for stream in cur_auth_data['streams']:
                formats.append({
                    'url': base64.b64decode(stream['url']['data'].encode('ascii')).decode('utf-8'),
                    'ext': stream.get('delivery_type'),
                    'format': stream.get('video_codec'),
                    'format_id': stream.get('profile'),
                    'width': int_or_none(stream.get('width')),
                    'height': int_or_none(stream.get('height')),
                    'abr': int_or_none(stream.get('audio_bitrate')),
                    'vbr': int_or_none(stream.get('video_bitrate')),
                })
            if formats:
                return {
                    'id': video_id,
                    'formats': formats,
                    'title': 'Ooyala video',
                }

            if not cur_auth_data['authorized']:
                raise ExtractorError(cur_auth_data['message'], expected=True)

        if not videos_info:
            raise ExtractorError('Unable to extract info')
        videos_info = videos_info.replace('\\"', '"')
        videos_more_info = self._search_regex(
            r'eval\("\(({.*?\\"promo\\".*?})\)"', mobile_player, 'more info').replace('\\"', '"')
        videos_info = json.loads(videos_info)
        videos_more_info = json.loads(videos_more_info)

        if videos_more_info.get('lineup'):
            videos = [self._extract_result(info, more_info) for (info, more_info) in zip(videos_info, videos_more_info['lineup'])]
            return {
                '_type': 'playlist',
                'id': video_id,
                'title': unescapeHTML(videos_more_info['title']),
                'entries': videos,
            }
        else:
            return self._extract_result(videos_info[0], videos_more_info)


class OoyalaIE(OoyalaBaseIE):
    _VALID_URL = r'(?:ooyala:|https?://.+?\.ooyala\.com/.*?(?:embedCode|ec)=)(?P<id>.+?)(&|$)'

    _TESTS = [
        {
            # From http://it.slashdot.org/story/13/04/25/178216/recovering-data-from-broken-hard-drives-and-ssds-video
            'url': 'http://player.ooyala.com/player.js?embedCode=pxczE2YjpfHfn1f3M-ykG_AmJRRn0PD8',
            'info_dict': {
                'id': 'pxczE2YjpfHfn1f3M-ykG_AmJRRn0PD8',
                'ext': 'mp4',
                'title': 'Explaining Data Recovery from Hard Drives and SSDs',
                'description': 'How badly damaged does a drive have to be to defeat Russell and his crew? Apparently, smashed to bits.',
            },
        }, {
            # Only available for ipad
            'url': 'http://player.ooyala.com/player.js?embedCode=x1b3lqZDq9y_7kMyC2Op5qo-p077tXD0',
            'info_dict': {
                'id': 'x1b3lqZDq9y_7kMyC2Op5qo-p077tXD0',
                'ext': 'mp4',
                'title': 'Simulation Overview - Levels of Simulation',
                'description': '',
            },
        },
        {
            # Information available only through SAS api
            # From http://community.plm.automation.siemens.com/t5/News-NX-Manufacturing/Tool-Path-Divide/ba-p/4187
            'url': 'http://player.ooyala.com/player.js?embedCode=FiOG81ZTrvckcchQxmalf4aQj590qTEx',
            'md5': 'a84001441b35ea492bc03736e59e7935',
            'info_dict': {
                'id': 'FiOG81ZTrvckcchQxmalf4aQj590qTEx',
                'ext': 'mp4',
                'title': 'Ooyala video',
            }
        }
    ]

    @staticmethod
    def _url_for_embed_code(embed_code):
        return 'http://player.ooyala.com/player.js?embedCode=%s' % embed_code

    @classmethod
    def _build_url_result(cls, embed_code):
        return cls.url_result(cls._url_for_embed_code(embed_code),
                              ie=cls.ie_key())

    def _real_extract(self, url):
        embed_code = self._match_id(url)
        player_url = 'http://player.ooyala.com/player.js?embedCode=%s' % embed_code
        return self._extract(player_url, embed_code)


class OoyalaExternalIE(OoyalaBaseIE):
    _VALID_URL = r'''(?x)
                    (?:
                        ooyalaexternal:|
                        https?://.+?\.ooyala\.com/.*?\bexternalId=
                    )
                    (?P<partner_id>[^:]+)
                    :
                    (?P<id>.+)
                    (?:
                        :|
                        .*?&pcode=
                    )
                    (?P<pcode>.+?)
                    (&|$)
                    '''

    _TEST = {
        'url': 'https://player.ooyala.com/player.js?externalId=espn:10365079&pcode=1kNG061cgaoolOncv54OAO1ceO-I&adSetCode=91cDU6NuXTGKz3OdjOxFdAgJVtQcKJnI&callback=handleEvents&hasModuleParams=1&height=968&playerBrandingId=7af3bd04449c444c964f347f11873075&targetReplaceId=videoPlayer&width=1656&wmode=opaque&allowScriptAccess=always',
        'info_dict': {
            'id': 'FkYWtmazr6Ed8xmvILvKLWjd4QvYZpzG',
            'ext': 'mp4',
            'title': 'dm_140128_30for30Shorts___JudgingJewellv2',
            'description': '',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        partner_id = mobj.group('partner_id')
        video_id = mobj.group('id')
        pcode = mobj.group('pcode')
        player_url = 'http://player.ooyala.com/player.js?externalId=%s:%s&pcode=%s' % (partner_id, video_id, pcode)
        return self._extract(player_url, video_id)
