# coding: utf-8
from __future__ import unicode_literals

import datetime
import json
import hashlib
import hmac
import re

from .common import InfoExtractor
from .anvato import AnvatoIE
from ..utils import (
    smuggle_url,
    urlencode_postdata,
    xpath_text,
)


class ScrippsNetworksWatchIE(InfoExtractor):
    IE_NAME = 'scrippsnetworks:watch'
    _VALID_URL = r'''(?x)
                    https?://
                        watch\.
                        (?P<site>hgtv|foodnetwork|travelchannel|diynetwork|cookingchanneltv|geniuskitchen)\.com/
                        (?:
                            player\.[A-Z0-9]+\.html\#|
                            show/(?:[^/]+/){2}|
                            player/
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [{
        'url': 'http://watch.hgtv.com/show/HGTVE/Best-Ever-Treehouses/2241515/Best-Ever-Treehouses/',
        'md5': '26545fd676d939954c6808274bdb905a',
        'info_dict': {
            'id': '4173834',
            'ext': 'mp4',
            'title': 'Best Ever Treehouses',
            'description': "We're searching for the most over the top treehouses.",
            'uploader': 'ANV',
            'upload_date': '20170922',
            'timestamp': 1506056400,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': [AnvatoIE.ie_key()],
    }, {
        'url': 'http://watch.diynetwork.com/show/DSAL/Salvage-Dawgs/2656646/Covington-Church/',
        'only_matching': True,
    }, {
        'url': 'http://watch.diynetwork.com/player.HNT.html#2656646',
        'only_matching': True,
    }, {
        'url': 'http://watch.geniuskitchen.com/player/3787617/Ample-Hills-Ice-Cream-Bike/',
        'only_matching': True,
    }]

    _SNI_TABLE = {
        'hgtv': 'hgtv',
        'diynetwork': 'diy',
        'foodnetwork': 'food',
        'cookingchanneltv': 'cook',
        'travelchannel': 'trav',
        'geniuskitchen': 'genius',
    }
    _SNI_HOST = 'web.api.video.snidigital.com'

    _AWS_REGION = 'us-east-1'
    _AWS_IDENTITY_ID_JSON = json.dumps({
        'IdentityId': '%s:7655847c-0ae7-4d9b-80d6-56c062927eb3' % _AWS_REGION
    })
    _AWS_USER_AGENT = 'aws-sdk-js/2.80.0 callback'
    _AWS_API_KEY = 'E7wSQmq0qK6xPrF13WmzKiHo4BQ7tip4pQcSXVl1'
    _AWS_SERVICE = 'execute-api'
    _AWS_REQUEST = 'aws4_request'
    _AWS_SIGNED_HEADERS = ';'.join([
        'host', 'x-amz-date', 'x-amz-security-token', 'x-api-key'])
    _AWS_CANONICAL_REQUEST_TEMPLATE = '''GET
%(uri)s

host:%(host)s
x-amz-date:%(date)s
x-amz-security-token:%(token)s
x-api-key:%(key)s

%(signed_headers)s
%(payload_hash)s'''

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, video_id = mobj.group('site', 'id')

        def aws_hash(s):
            return hashlib.sha256(s.encode('utf-8')).hexdigest()

        token = self._download_json(
            'https://cognito-identity.us-east-1.amazonaws.com/', video_id,
            data=self._AWS_IDENTITY_ID_JSON.encode('utf-8'),
            headers={
                'Accept': '*/*',
                'Content-Type': 'application/x-amz-json-1.1',
                'Referer': url,
                'X-Amz-Content-Sha256': aws_hash(self._AWS_IDENTITY_ID_JSON),
                'X-Amz-Target': 'AWSCognitoIdentityService.GetOpenIdToken',
                'X-Amz-User-Agent': self._AWS_USER_AGENT,
            })['Token']

        sts = self._download_xml(
            'https://sts.amazonaws.com/', video_id, data=urlencode_postdata({
                'Action': 'AssumeRoleWithWebIdentity',
                'RoleArn': 'arn:aws:iam::710330595350:role/Cognito_WebAPIUnauth_Role',
                'RoleSessionName': 'web-identity',
                'Version': '2011-06-15',
                'WebIdentityToken': token,
            }), headers={
                'Referer': url,
                'X-Amz-User-Agent': self._AWS_USER_AGENT,
                'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            })

        def get(key):
            return xpath_text(
                sts, './/{https://sts.amazonaws.com/doc/2011-06-15/}%s' % key,
                fatal=True)

        access_key_id = get('AccessKeyId')
        secret_access_key = get('SecretAccessKey')
        session_token = get('SessionToken')

        # Task 1: http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
        uri = '/1/web/brands/%s/episodes/scrid/%s' % (self._SNI_TABLE[site_id], video_id)
        datetime_now = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        date = datetime_now[:8]
        canonical_string = self._AWS_CANONICAL_REQUEST_TEMPLATE % {
            'uri': uri,
            'host': self._SNI_HOST,
            'date': datetime_now,
            'token': session_token,
            'key': self._AWS_API_KEY,
            'signed_headers': self._AWS_SIGNED_HEADERS,
            'payload_hash': aws_hash(''),
        }

        # Task 2: http://docs.aws.amazon.com/general/latest/gr/sigv4-create-string-to-sign.html
        credential_string = '/'.join([date, self._AWS_REGION, self._AWS_SERVICE, self._AWS_REQUEST])
        string_to_sign = '\n'.join([
            'AWS4-HMAC-SHA256', datetime_now, credential_string,
            aws_hash(canonical_string)])

        # Task 3: http://docs.aws.amazon.com/general/latest/gr/sigv4-calculate-signature.html
        def aws_hmac(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256)

        def aws_hmac_digest(key, msg):
            return aws_hmac(key, msg).digest()

        def aws_hmac_hexdigest(key, msg):
            return aws_hmac(key, msg).hexdigest()

        k_secret = 'AWS4' + secret_access_key
        k_date = aws_hmac_digest(k_secret.encode('utf-8'), date)
        k_region = aws_hmac_digest(k_date, self._AWS_REGION)
        k_service = aws_hmac_digest(k_region, self._AWS_SERVICE)
        k_signing = aws_hmac_digest(k_service, self._AWS_REQUEST)

        signature = aws_hmac_hexdigest(k_signing, string_to_sign)

        auth_header = ', '.join([
            'AWS4-HMAC-SHA256 Credential=%s' % '/'.join(
                [access_key_id, date, self._AWS_REGION, self._AWS_SERVICE, self._AWS_REQUEST]),
            'SignedHeaders=%s' % self._AWS_SIGNED_HEADERS,
            'Signature=%s' % signature,
        ])

        mcp_id = self._download_json(
            'https://%s%s' % (self._SNI_HOST, uri), video_id, headers={
                'Accept': '*/*',
                'Referer': url,
                'Authorization': auth_header,
                'X-Amz-Date': datetime_now,
                'X-Amz-Security-Token': session_token,
                'X-Api-Key': self._AWS_API_KEY,
            })['results'][0]['mcpId']

        return self.url_result(
            smuggle_url(
                'anvato:anvato_scripps_app_web_prod_0837996dbe373629133857ae9eb72e740424d80a:%s' % mcp_id,
                {'geo_countries': ['US']}),
            AnvatoIE.ie_key(), video_id=mcp_id)
