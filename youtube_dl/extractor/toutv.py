# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    ExtractorError,
    urlencode_postdata,
    extract_attributes,
    smuggle_url,
)


class TouTvIE(InfoExtractor):
    _NETRC_MACHINE = 'toutv'
    IE_NAME = 'tou.tv'
    _VALID_URL = r'https?://ici\.tou\.tv/(?P<id>[a-zA-Z0-9_-]+/S[0-9]+E[0-9]+)'
    _access_token = None
    _claims = None

    _TEST = {
        'url': 'http://ici.tou.tv/garfield-tout-court/S2015E17',
        'info_dict': {
            'id': '122017',
            'ext': 'mp4',
            'title': 'Saison 2015 Épisode 17',
            'description': 'La photo de famille 2',
            'upload_date': '20100717',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'skip': '404 Not Found',
    }

    def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            return
        state = 'http://ici.tou.tv//'
        webpage = self._download_webpage(state, None, 'Downloading homepage')
        toutvlogin = self._parse_json(self._search_regex(
            r'(?s)toutvlogin\s*=\s*({.+?});', webpage, 'toutvlogin'), None, js_to_json)
        authorize_url = toutvlogin['host'] + '/auth/oauth/v2/authorize'
        login_webpage = self._download_webpage(
            authorize_url, None, 'Downloading login page', query={
                'client_id': toutvlogin['clientId'],
                'redirect_uri': 'https://ici.tou.tv/login/loginCallback',
                'response_type': 'token',
                'scope': 'media-drmt openid profile email id.write media-validation.read.privileged',
                'state': state,
            })
        login_form = self._search_regex(
            r'(?s)(<form[^>]+id="Form-login".+?</form>)', login_webpage, 'login form')
        form_data = self._hidden_inputs(login_form)
        form_data.update({
            'login-email': email,
            'login-password': password,
        })
        post_url = extract_attributes(login_form).get('action') or authorize_url
        _, urlh = self._download_webpage_handle(
            post_url, None, 'Logging in', data=urlencode_postdata(form_data))
        self._access_token = self._search_regex(
            r'access_token=([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})',
            urlh.geturl(), 'access token')
        self._claims = self._download_json(
            'https://services.radio-canada.ca/media/validation/v2/getClaims',
            None, 'Extracting Claims', query={
                'token': self._access_token,
                'access_token': self._access_token,
            })['claims']

    def _real_extract(self, url):
        path = self._match_id(url)
        metadata = self._download_json('http://ici.tou.tv/presentation/%s' % path, path)
        if metadata.get('IsDrm'):
            raise ExtractorError('This video is DRM protected.', expected=True)
        video_id = metadata['IdMedia']
        details = metadata['Details']
        title = details['OriginalTitle']
        video_url = 'radiocanada:%s:%s' % (metadata.get('AppCode', 'toutv'), video_id)
        if self._access_token and self._claims:
            video_url = smuggle_url(video_url, {
                'access_token': self._access_token,
                'claims': self._claims,
            })

        return {
            '_type': 'url_transparent',
            'url': video_url,
            'id': video_id,
            'title': title,
            'thumbnail': details.get('ImageUrl'),
            'duration': int_or_none(details.get('LengthInSeconds')),
        }
