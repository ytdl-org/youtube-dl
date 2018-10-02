# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from .kaltura import KalturaIE


class AZMedienBaseIE(InfoExtractor):
    _PARTNER_ID = '1719221'

    def _kaltura_video(self, partner_id, entry_id):
        return self.url_result(
            'kaltura:%s:%s' % (partner_id, entry_id), ie=KalturaIE.ie_key(),
            video_id=entry_id)


class AZMedienIE(AZMedienBaseIE):
    IE_DESC = 'AZ Medien videos'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?P<host>
                            telezueri\.ch|
                            telebaern\.tv|
                            telem1\.ch
                        )/
                        [^/]+/
                        (?P<id>
                            [^/]+-(?P<article_id>\d+)
                        )
                        (?:
                            \#video=
                            (?P<kaltura_id>
                                [_0-9a-z]+
                            )
                        )?
                    '''

    _TESTS = [{
        'url': 'https://www.telezueri.ch/sonntalk/bundesrats-vakanzen-eu-rahmenabkommen-133214569',
        'info_dict': {
            'id': '1_anruz3wy',
            'ext': 'mp4',
            'title': 'Bundesrats-Vakanzen / EU-Rahmenabkommen',
            'description': 'md5:dd9f96751ec9c35e409a698a328402f3',
            'uploader_id': 'TVOnline',
            'upload_date': '20180930',
            'timestamp': 1538328802,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.telebaern.tv/telebaern-news/montag-1-oktober-2018-ganze-sendung-133531189#video=0_7xjo9lf1',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        mobj = re.match(self._VALID_URL, url)
        entry_id = mobj.group('kaltura_id')

        if not entry_id:
            webpage = self._download_webpage(url, video_id)
            api_path = self._search_regex(
                r'["\']apiPath["\']\s*:\s*["\']([^"^\']+)["\']',
                webpage, 'api path')
            api_url = 'https://www.%s%s' % (mobj.group('host'), api_path)
            payload = {
                'query': '''query VideoContext($articleId: ID!) {
                    article: node(id: $articleId) {
                      ... on Article {
                        mainAssetRelation {
                          asset {
                            ... on VideoAsset {
                              kalturaId
                            }
                          }
                        }
                      }
                    }
                  }''',
                'variables': {'articleId': 'Article:%s' % mobj.group('article_id')},
            }
            json_data = self._download_json(
                api_url, video_id, headers={
                    'Content-Type': 'application/json',
                },
                data=json.dumps(payload).encode())
            entry_id = json_data['data']['article']['mainAssetRelation']['asset']['kalturaId']

        return self._kaltura_video(self._PARTNER_ID, entry_id)
