# coding: utf-8
from __future__ import unicode_literals

import re

from .radiocanada import RadioCanadaIE
from ..utils import (
    extract_attributes,
    int_or_none,
    merge_dicts,
    urlencode_postdata,
)


class TouTvIE(RadioCanadaIE):
    _NETRC_MACHINE = 'toutv'
    IE_NAME = 'tou.tv'
    _VALID_URL = r'https?://ici\.tou\.tv/(?P<id>[a-zA-Z0-9_-]+(?:/S[0-9]+[EC][0-9]+)?)'

    _TESTS = [{
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
    }, {
        'url': 'http://ici.tou.tv/hackers',
        'only_matching': True,
    }, {
        'url': 'https://ici.tou.tv/l-age-adulte/S01C501',
        'only_matching': True,
    }]

    def _real_initialize(self):
        email, password = self._get_login_info()
        if email is None:
            return
        login_webpage = self._download_webpage(
            'https://services.radio-canada.ca/auth/oauth/v2/authorize',
            None, 'Downloading login page', query={
                'client_id': '4dd36440-09d5-4468-8923-b6d91174ad36',
                'redirect_uri': 'https://ici.tou.tv/logincallback',
                'response_type': 'token',
                'scope': 'id.write media-validation.read',
                'state': '/',
            })

        def extract_form_url_and_data(wp, default_form_url, form_spec_re=''):
            form, form_elem = re.search(
                r'(?s)((<form[^>]+?%s[^>]*?>).+?</form>)' % form_spec_re, wp).groups()
            form_data = self._hidden_inputs(form)
            form_url = extract_attributes(form_elem).get('action') or default_form_url
            return form_url, form_data

        post_url, form_data = extract_form_url_and_data(
            login_webpage,
            'https://services.radio-canada.ca/auth/oauth/v2/authorize/login',
            r'(?:id|name)="Form-login"')
        form_data.update({
            'login-email': email,
            'login-password': password,
        })
        consent_webpage = self._download_webpage(
            post_url, None, 'Logging in', data=urlencode_postdata(form_data))
        post_url, form_data = extract_form_url_and_data(
            consent_webpage,
            'https://services.radio-canada.ca/auth/oauth/v2/authorize/consent')
        _, urlh = self._download_webpage_handle(
            post_url, None, 'Following Redirection',
            data=urlencode_postdata(form_data))
        self._access_token = self._search_regex(
            r'access_token=([\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})',
            urlh.geturl(), 'access token')
        self._claims = self._call_api('validation/v2/getClaims')['claims']

    def _real_extract(self, url):
        path = self._match_id(url)
        metadata = self._download_json('http://ici.tou.tv/presentation/%s' % path, path)
        # IsDrm does not necessarily mean the video is DRM protected (see
        # https://github.com/rg3/youtube-dl/issues/13994).
        if metadata.get('IsDrm'):
            self.report_warning('This video is probably DRM protected.', path)
        video_id = metadata['IdMedia']
        details = metadata['Details']

        return merge_dicts({
            'id': video_id,
            'title': details.get('OriginalTitle'),
            'thumbnail': details.get('ImageUrl'),
            'duration': int_or_none(details.get('LengthInSeconds')),
        }, self._extract_info(metadata.get('AppCode', 'toutv'), video_id))
