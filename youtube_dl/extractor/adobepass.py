# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import time
import xml.etree.ElementTree as etree

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    unescapeHTML,
    urlencode_postdata,
    unified_timestamp,
    ExtractorError,
)


MSO_INFO = {
    'DTV': {
        'name': 'DirecTV',
        'username_field': 'username',
        'password_field': 'password',
    },
    'Rogers': {
        'name': 'Rogers Cable',
        'username_field': 'UserName',
        'password_field': 'UserPassword',
    },
}


class AdobePassIE(InfoExtractor):
    _SERVICE_PROVIDER_TEMPLATE = 'https://sp.auth.adobe.com/adobe-services/%s'
    _USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:47.0) Gecko/20100101 Firefox/47.0'
    _MVPD_CACHE = 'ap-mvpd'

    @staticmethod
    def _get_mvpd_resource(provider_id, title, guid, rating):
        channel = etree.Element('channel')
        channel_title = etree.SubElement(channel, 'title')
        channel_title.text = provider_id
        item = etree.SubElement(channel, 'item')
        resource_title = etree.SubElement(item, 'title')
        resource_title.text = title
        resource_guid = etree.SubElement(item, 'guid')
        resource_guid.text = guid
        resource_rating = etree.SubElement(item, 'media:rating')
        resource_rating.attrib = {'scheme': 'urn:v-chip'}
        resource_rating.text = rating
        return '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">' + etree.tostring(channel).decode() + '</rss>'

    def _extract_mvpd_auth(self, url, video_id, requestor_id, resource):
        def xml_text(xml_str, tag):
            return self._search_regex(
                '<%s>(.+?)</%s>' % (tag, tag), xml_str, tag)

        def is_expired(token, date_ele):
            token_expires = unified_timestamp(re.sub(r'[_ ]GMT', '', xml_text(token, date_ele)))
            return token_expires and token_expires <= int(time.time())

        def post_form(form_page_res, note, data={}):
            form_page, urlh = form_page_res
            post_url = self._html_search_regex(r'<form[^>]+action=(["\'])(?P<url>.+?)\1', form_page, 'post url', group='url')
            if not re.match(r'https?://', post_url):
                post_url = compat_urlparse.urljoin(urlh.geturl(), post_url)
            form_data = self._hidden_inputs(form_page)
            form_data.update(data)
            return self._download_webpage_handle(
                post_url, video_id, note, data=urlencode_postdata(form_data), headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                })

        def raise_mvpd_required():
            raise ExtractorError(
                'This video is only available for users of participating TV providers. '
                'Use --ap-mso to specify Adobe Pass Multiple-system operator Identifier '
                'and --ap-username and --ap-password or --netrc to provide account credentials.', expected=True)

        mvpd_headers = {
            'ap_42': 'anonymous',
            'ap_11': 'Linux i686',
            'ap_z': self._USER_AGENT,
            'User-Agent': self._USER_AGENT,
        }

        guid = xml_text(resource, 'guid')
        count = 0
        while count < 2:
            requestor_info = self._downloader.cache.load(self._MVPD_CACHE, requestor_id) or {}
            authn_token = requestor_info.get('authn_token')
            if authn_token and is_expired(authn_token, 'simpleTokenExpires'):
                authn_token = None
            if not authn_token:
                # TODO add support for other TV Providers
                mso_id = self._downloader.params.get('ap_mso')
                if not mso_id:
                    raise_mvpd_required()
                username, password = self._get_login_info('ap_username', 'ap_password', mso_id)
                if not username or not password:
                    raise_mvpd_required()
                mso_info = MSO_INFO[mso_id]

                provider_redirect_page_res = self._download_webpage_handle(
                    self._SERVICE_PROVIDER_TEMPLATE % 'authenticate/saml', video_id,
                    'Downloading Provider Redirect Page', query={
                        'noflash': 'true',
                        'mso_id': mso_id,
                        'requestor_id': requestor_id,
                        'no_iframe': 'false',
                        'domain_name': 'adobe.com',
                        'redirect_url': url,
                    })
                provider_login_page_res = post_form(
                    provider_redirect_page_res, 'Downloading Provider Login Page')
                mvpd_confirm_page_res = post_form(provider_login_page_res, 'Logging in', {
                    mso_info['username_field']: username,
                    mso_info['password_field']: password,
                })
                if mso_id == 'DTV':
                    post_form(mvpd_confirm_page_res, 'Confirming Login')

                session = self._download_webpage(
                    self._SERVICE_PROVIDER_TEMPLATE % 'session', video_id,
                    'Retrieving Session', data=urlencode_postdata({
                        '_method': 'GET',
                        'requestor_id': requestor_id,
                    }), headers=mvpd_headers)
                if '<pendingLogout' in session:
                    self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                    count += 1
                    continue
                authn_token = unescapeHTML(xml_text(session, 'authnToken'))
                requestor_info['authn_token'] = authn_token
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)

            authz_token = requestor_info.get(guid)
            if authz_token and is_expired(authz_token, 'simpleTokenTTL'):
                authz_token = None
            if not authz_token:
                authorize = self._download_webpage(
                    self._SERVICE_PROVIDER_TEMPLATE % 'authorize', video_id,
                    'Retrieving Authorization Token', data=urlencode_postdata({
                        'resource_id': resource,
                        'requestor_id': requestor_id,
                        'authentication_token': authn_token,
                        'mso_id': xml_text(authn_token, 'simpleTokenMsoID'),
                        'userMeta': '1',
                    }), headers=mvpd_headers)
                if '<pendingLogout' in authorize:
                    self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                    count += 1
                    continue
                authz_token = unescapeHTML(xml_text(authorize, 'authzToken'))
                requestor_info[guid] = authz_token
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, requestor_info)

            mvpd_headers.update({
                'ap_19': xml_text(authn_token, 'simpleSamlNameID'),
                'ap_23': xml_text(authn_token, 'simpleSamlSessionIndex'),
            })

            short_authorize = self._download_webpage(
                self._SERVICE_PROVIDER_TEMPLATE % 'shortAuthorize',
                video_id, 'Retrieving Media Token', data=urlencode_postdata({
                    'authz_token': authz_token,
                    'requestor_id': requestor_id,
                    'session_guid': xml_text(authn_token, 'simpleTokenAuthenticationGuid'),
                    'hashed_guid': 'false',
                }), headers=mvpd_headers)
            if '<pendingLogout' in short_authorize:
                self._downloader.cache.store(self._MVPD_CACHE, requestor_id, {})
                count += 1
                continue
            return short_authorize
