# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import time
import xml.etree.ElementTree as etree

from .common import InfoExtractor
from ..utils import (
    unescapeHTML,
    urlencode_postdata,
    unified_timestamp,
)


class AdobePass(InfoExtractor):
    _SERVICE_PROVIDER_TEMPLATE = 'https://sp.auth.adobe.com/adobe-services/%s'
    _USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:47.0) Gecko/20100101 Firefox/47.0'

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

        mvpd_headers = {
            'ap_42': 'anonymous',
            'ap_11': 'Linux i686',
            'ap_z': self._USER_AGENT,
            'User-Agent': self._USER_AGENT,
        }

        guid = xml_text(resource, 'guid')
        requestor_info = self._downloader.cache.load('mvpd', requestor_id) or {}
        authn_token = requestor_info.get('authn_token')
        if authn_token:
            token_expires = unified_timestamp(re.sub(r'[_ ]GMT', '', xml_text(authn_token, 'simpleTokenExpires')))
            if token_expires and token_expires <= int(time.time()):
                authn_token = None
                requestor_info = {}
        if not authn_token:
            # TODO add support for other TV Providers
            mso_id = 'DTV'
            username, password = self._get_netrc_login_info(mso_id)
            if not username or not password:
                return ''

            def post_form(form_page, note, data={}):
                post_url = self._html_search_regex(r'<form[^>]+action=(["\'])(?P<url>.+?)\1', form_page, 'post url', group='url')
                return self._download_webpage(
                    post_url, video_id, note, data=urlencode_postdata(data or self._hidden_inputs(form_page)), headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                    })

            provider_redirect_page = self._download_webpage(
                self._SERVICE_PROVIDER_TEMPLATE % 'authenticate/saml', video_id,
                'Downloading Provider Redirect Page', query={
                    'noflash': 'true',
                    'mso_id': mso_id,
                    'requestor_id': requestor_id,
                    'no_iframe': 'false',
                    'domain_name': 'adobe.com',
                    'redirect_url': url,
                })
            provider_login_page = post_form(
                provider_redirect_page, 'Downloading Provider Login Page')
            mvpd_confirm_page = post_form(provider_login_page, 'Logging in', {
                'username': username,
                'password': password,
            })
            post_form(mvpd_confirm_page, 'Confirming Login')

            session = self._download_webpage(
                self._SERVICE_PROVIDER_TEMPLATE % 'session', video_id,
                'Retrieving Session', data=urlencode_postdata({
                    '_method': 'GET',
                    'requestor_id': requestor_id,
                }), headers=mvpd_headers)
            if '<pendingLogout' in session:
                self._downloader.cache.store('mvpd', requestor_id, {})
                return self._extract_mvpd_auth(url, video_id, requestor_id, resource)
            authn_token = unescapeHTML(xml_text(session, 'authnToken'))
            requestor_info['authn_token'] = authn_token
            self._downloader.cache.store('mvpd', requestor_id, requestor_info)

        authz_token = requestor_info.get(guid)
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
                self._downloader.cache.store('mvpd', requestor_id, {})
                return self._extract_mvpd_auth(url, video_id, requestor_id, resource)
            authz_token = unescapeHTML(xml_text(authorize, 'authzToken'))
            requestor_info[guid] = authz_token
            self._downloader.cache.store('mvpd', requestor_id, requestor_info)

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
            self._downloader.cache.store('mvpd', requestor_id, {})
            return self._extract_mvpd_auth(url, video_id, requestor_id, resource)
        return short_authorize