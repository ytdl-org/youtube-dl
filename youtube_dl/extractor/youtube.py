# coding: utf-8

from __future__ import unicode_literals

import itertools
import json
import os.path
import random
import re
import traceback

from .common import InfoExtractor, SearchInfoExtractor
from ..compat import (
    compat_chr,
    compat_HTTPError,
    compat_map as map,
    compat_str,
    compat_urllib_parse,
    compat_urllib_parse_parse_qs as compat_parse_qs,
    compat_urllib_parse_unquote_plus,
    compat_urllib_parse_urlparse,
    compat_zip as zip,
)
from ..jsinterp import JSInterpreter
from ..utils import (
    ExtractorError,
    clean_html,
    dict_get,
    error_to_compat_str,
    float_or_none,
    extract_attributes,
    get_element_by_attribute,
    int_or_none,
    js_to_json,
    LazyList,
    merge_dicts,
    mimetype2ext,
    parse_codecs,
    parse_duration,
    parse_qs,
    qualities,
    remove_start,
    smuggle_url,
    str_or_none,
    str_to_int,
    traverse_obj,
    try_get,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    update_url,
    update_url_query,
    url_or_none,
    urlencode_postdata,
    urljoin,
)


class YoutubeBaseInfoExtractor(InfoExtractor):
    """Provide base functions for Youtube extractors"""
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _TWOFACTOR_URL = 'https://accounts.google.com/signin/challenge'

    _LOOKUP_URL = 'https://accounts.google.com/_/signin/sl/lookup'
    _CHALLENGE_URL = 'https://accounts.google.com/_/signin/sl/challenge'
    _TFA_URL = 'https://accounts.google.com/_/signin/challenge?hl=en&TL={0}'

    _NETRC_MACHINE = 'youtube'
    # If True it will raise an error if no login info is provided
    _LOGIN_REQUIRED = False

    _PLAYLIST_ID_RE = r'(?:(?:PL|LL|EC|UU|FL|RD|UL|TL|PU|OLAK5uy_)[0-9A-Za-z-_]{10,}|RDMM)'

    def _login(self):
        """
        Attempt to log in to YouTube.
        True is returned if successful or skipped.
        False is returned if login failed.

        If _LOGIN_REQUIRED is set and no authentication was provided, an error is raised.
        """
        username, password = self._get_login_info()
        # No authentication to be performed
        if username is None:
            if self._LOGIN_REQUIRED and self._downloader.params.get('cookiefile') is None:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return True

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note='Downloading login page',
            errnote='unable to fetch login page', fatal=False)
        if login_page is False:
            return

        login_form = self._hidden_inputs(login_page)

        def req(url, f_req, note, errnote):
            data = login_form.copy()
            data.update({
                'pstMsg': 1,
                'checkConnection': 'youtube',
                'checkedDomains': 'youtube',
                'hl': 'en',
                'deviceinfo': '[null,null,null,[],null,"US",null,null,[],"GlifWebSignIn",null,[null,null,[]]]',
                'f.req': json.dumps(f_req),
                'flowName': 'GlifWebSignIn',
                'flowEntry': 'ServiceLogin',
                # TODO: reverse actual botguard identifier generation algo
                'bgRequest': '["identifier",""]',
            })
            return self._download_json(
                url, None, note=note, errnote=errnote,
                transform_source=lambda s: re.sub(r'^[^[]*', '', s),
                fatal=False,
                data=urlencode_postdata(data), headers={
                    'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
                    'Google-Accounts-XSRF': 1,
                })

        def warn(message):
            self._downloader.report_warning(message)

        lookup_req = [
            username,
            None, [], None, 'US', None, None, 2, False, True,
            [
                None, None,
                [2, 1, None, 1,
                 'https://accounts.google.com/ServiceLogin?passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Fnext%3D%252F%26action_handle_signin%3Dtrue%26hl%3Den%26app%3Ddesktop%26feature%3Dsign_in_button&hl=en&service=youtube&uilel=3&requestPath=%2FServiceLogin&Page=PasswordSeparationSignIn',
                 None, [], 4],
                1, [None, None, []], None, None, None, True
            ],
            username,
        ]

        lookup_results = req(
            self._LOOKUP_URL, lookup_req,
            'Looking up account info', 'Unable to look up account info')

        if lookup_results is False:
            return False

        user_hash = try_get(lookup_results, lambda x: x[0][2], compat_str)
        if not user_hash:
            warn('Unable to extract user hash')
            return False

        challenge_req = [
            user_hash,
            None, 1, None, [1, None, None, None, [password, None, True]],
            [
                None, None, [2, 1, None, 1, 'https://accounts.google.com/ServiceLogin?passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Fnext%3D%252F%26action_handle_signin%3Dtrue%26hl%3Den%26app%3Ddesktop%26feature%3Dsign_in_button&hl=en&service=youtube&uilel=3&requestPath=%2FServiceLogin&Page=PasswordSeparationSignIn', None, [], 4],
                1, [None, None, []], None, None, None, True
            ]]

        challenge_results = req(
            self._CHALLENGE_URL, challenge_req,
            'Logging in', 'Unable to log in')

        if challenge_results is False:
            return

        login_res = try_get(challenge_results, lambda x: x[0][5], list)
        if login_res:
            login_msg = try_get(login_res, lambda x: x[5], compat_str)
            warn(
                'Unable to login: %s' % 'Invalid password'
                if login_msg == 'INCORRECT_ANSWER_ENTERED' else login_msg)
            return False

        res = try_get(challenge_results, lambda x: x[0][-1], list)
        if not res:
            warn('Unable to extract result entry')
            return False

        login_challenge = try_get(res, lambda x: x[0][0], list)
        if login_challenge:
            challenge_str = try_get(login_challenge, lambda x: x[2], compat_str)
            if challenge_str == 'TWO_STEP_VERIFICATION':
                # SEND_SUCCESS - TFA code has been successfully sent to phone
                # QUOTA_EXCEEDED - reached the limit of TFA codes
                status = try_get(login_challenge, lambda x: x[5], compat_str)
                if status == 'QUOTA_EXCEEDED':
                    warn('Exceeded the limit of TFA codes, try later')
                    return False

                tl = try_get(challenge_results, lambda x: x[1][2], compat_str)
                if not tl:
                    warn('Unable to extract TL')
                    return False

                tfa_code = self._get_tfa_info('2-step verification code')

                if not tfa_code:
                    warn(
                        'Two-factor authentication required. Provide it either interactively or with --twofactor <code>'
                        '(Note that only TOTP (Google Authenticator App) codes work at this time.)')
                    return False

                tfa_code = remove_start(tfa_code, 'G-')

                tfa_req = [
                    user_hash, None, 2, None,
                    [
                        9, None, None, None, None, None, None, None,
                        [None, tfa_code, True, 2]
                    ]]

                tfa_results = req(
                    self._TFA_URL.format(tl), tfa_req,
                    'Submitting TFA code', 'Unable to submit TFA code')

                if tfa_results is False:
                    return False

                tfa_res = try_get(tfa_results, lambda x: x[0][5], list)
                if tfa_res:
                    tfa_msg = try_get(tfa_res, lambda x: x[5], compat_str)
                    warn(
                        'Unable to finish TFA: %s' % 'Invalid TFA code'
                        if tfa_msg == 'INCORRECT_ANSWER_ENTERED' else tfa_msg)
                    return False

                check_cookie_url = try_get(
                    tfa_results, lambda x: x[0][-1][2], compat_str)
            else:
                CHALLENGES = {
                    'LOGIN_CHALLENGE': "This device isn't recognized. For your security, Google wants to make sure it's really you.",
                    'USERNAME_RECOVERY': 'Please provide additional information to aid in the recovery process.',
                    'REAUTH': "There is something unusual about your activity. For your security, Google wants to make sure it's really you.",
                }
                challenge = CHALLENGES.get(
                    challenge_str,
                    '%s returned error %s.' % (self.IE_NAME, challenge_str))
                warn('%s\nGo to https://accounts.google.com/, login and solve a challenge.' % challenge)
                return False
        else:
            check_cookie_url = try_get(res, lambda x: x[2], compat_str)

        if not check_cookie_url:
            warn('Unable to extract CheckCookie URL')
            return False

        check_cookie_results = self._download_webpage(
            check_cookie_url, None, 'Checking cookie', fatal=False)

        if check_cookie_results is False:
            return False

        if 'https://myaccount.google.com/' not in check_cookie_results:
            warn('Unable to log in')
            return False

        return True

    def _initialize_consent(self):
        cookies = self._get_cookies('https://www.youtube.com/')
        if cookies.get('__Secure-3PSID'):
            return
        consent_id = None
        consent = cookies.get('CONSENT')
        if consent:
            if 'YES' in consent.value:
                return
            consent_id = self._search_regex(
                r'PENDING\+(\d+)', consent.value, 'consent', default=None)
        if not consent_id:
            consent_id = random.randint(100, 999)
        self._set_cookie('.youtube.com', 'CONSENT', 'YES+cb.20210328-17-p0.en+FX+%s' % consent_id)

    def _real_initialize(self):
        self._initialize_consent()
        if self._downloader is None:
            return
        if not self._login():
            return

    _DEFAULT_API_DATA = {
        'context': {
            'client': {
                'clientName': 'WEB',
                'clientVersion': '2.20201021.03.00',
            }
        },
    }

    _YT_INITIAL_DATA_RE = r'(?:window\s*\[\s*["\']ytInitialData["\']\s*\]|ytInitialData)\s*=\s*({.+?})\s*;'
    _YT_INITIAL_PLAYER_RESPONSE_RE = r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;'
    _YT_INITIAL_BOUNDARY_RE = r'(?:var\s+meta|</script|\n)'

    def _call_api(self, ep, query, video_id, fatal=True, headers=None):
        data = self._DEFAULT_API_DATA.copy()
        data.update(query)
        real_headers = {'content-type': 'application/json'}
        if headers:
            real_headers.update(headers)

        return self._download_json(
            'https://www.youtube.com/youtubei/v1/%s' % ep, video_id=video_id,
            note='Downloading API JSON', errnote='Unable to download API page',
            data=json.dumps(data).encode('utf8'), fatal=fatal,
            headers=real_headers,
            query={'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'})

    def _extract_yt_initial_data(self, video_id, webpage):
        return self._parse_json(
            self._search_regex(
                (r'%s\s*%s' % (self._YT_INITIAL_DATA_RE, self._YT_INITIAL_BOUNDARY_RE),
                 self._YT_INITIAL_DATA_RE), webpage, 'yt initial data'),
            video_id)

    def _extract_ytcfg(self, video_id, webpage):
        return self._parse_json(
            self._search_regex(
                r'ytcfg\.set\s*\(\s*({.+?})\s*\)\s*;', webpage, 'ytcfg',
                default='{}'), video_id, fatal=False) or {}

    def _extract_video(self, renderer):
        video_id = renderer['videoId']
        title = try_get(
            renderer,
            (lambda x: x['title']['runs'][0]['text'],
             lambda x: x['title']['simpleText'],
             lambda x: x['headline']['simpleText']), compat_str)
        description = try_get(
            renderer, lambda x: x['descriptionSnippet']['runs'][0]['text'],
            compat_str)
        duration = parse_duration(try_get(
            renderer, lambda x: x['lengthText']['simpleText'], compat_str))
        view_count_text = try_get(
            renderer, lambda x: x['viewCountText']['simpleText'], compat_str) or ''
        view_count = str_to_int(self._search_regex(
            r'^([\d,]+)', re.sub(r'\s', '', view_count_text),
            'view count', default=None))
        uploader = try_get(
            renderer,
            (lambda x: x['ownerText']['runs'][0]['text'],
             lambda x: x['shortBylineText']['runs'][0]['text']), compat_str)
        return {
            '_type': 'url',
            'ie_key': YoutubeIE.ie_key(),
            'id': video_id,
            'url': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'view_count': view_count,
            'uploader': uploader,
        }

    def _search_results(self, query, params):
        data = {
            'context': {
                'client': {
                    'clientName': 'WEB',
                    'clientVersion': '2.20201021.03.00',
                }
            },
            'query': query,
        }
        if params:
            data['params'] = params
        for page_num in itertools.count(1):
            search = self._download_json(
                'https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
                video_id='query "%s"' % query,
                note='Downloading page %s' % page_num,
                errnote='Unable to download API page', fatal=False,
                data=json.dumps(data).encode('utf8'),
                headers={'content-type': 'application/json'})
            if not search:
                break
            slr_contents = try_get(
                search,
                (lambda x: x['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'],
                 lambda x: x['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']),
                list)
            if not slr_contents:
                break
            for slr_content in slr_contents:
                isr_contents = try_get(
                    slr_content,
                    lambda x: x['itemSectionRenderer']['contents'],
                    list)
                if not isr_contents:
                    continue
                for content in isr_contents:
                    if not isinstance(content, dict):
                        continue
                    video = content.get('videoRenderer')
                    if not isinstance(video, dict):
                        continue
                    video_id = video.get('videoId')
                    if not video_id:
                        continue
                    yield self._extract_video(video)
            token = try_get(
                slr_contents,
                lambda x: x[-1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'],
                compat_str)
            if not token:
                break
            data['continuation'] = token

    @staticmethod
    def _owner_endpoints_path():
        return [
            Ellipsis,
            lambda k, _: k.endswith('SecondaryInfoRenderer'),
            ('owner', 'videoOwner'), 'videoOwnerRenderer', 'title',
            'runs', Ellipsis]

    def _extract_channel_id(self, webpage, videodetails={}, metadata={}, renderers=[]):
        channel_id = None
        if any((videodetails, metadata, renderers)):
            channel_id = (
                traverse_obj(videodetails, 'channelId')
                or traverse_obj(metadata, 'externalChannelId', 'externalId')
                or traverse_obj(renderers,
                                self._owner_endpoints_path() + [
                                    'navigationEndpoint', 'browseEndpoint', 'browseId'],
                                get_all=False)
            )
        return channel_id or self._html_search_meta(
            'channelId', webpage, 'channel id', default=None)

    def _extract_author_var(self, webpage, var_name,
                            videodetails={}, metadata={}, renderers=[]):
        result = None
        paths = {
            #       (HTML, videodetails, metadata, renderers)
            'name': ('content', 'author', (('ownerChannelName', None), 'title'), ['text']),
            'url': ('href', 'ownerProfileUrl', 'vanityChannelUrl',
                    ['navigationEndpoint', 'browseEndpoint', 'canonicalBaseUrl'])
        }
        if any((videodetails, metadata, renderers)):
            result = (
                traverse_obj(videodetails, paths[var_name][1], get_all=False)
                or traverse_obj(metadata, paths[var_name][2], get_all=False)
                or traverse_obj(renderers,
                                self._owner_endpoints_path() + paths[var_name][3],
                                get_all=False)
            )
        return result or traverse_obj(
            extract_attributes(self._search_regex(
                r'''(?s)(<link\b[^>]+\bitemprop\s*=\s*("|')%s\2[^>]*>)'''
                % re.escape(var_name),
                get_element_by_attribute('itemprop', 'author', webpage) or '',
                'author link', default='')),
            paths[var_name][0])

    @staticmethod
    def _yt_urljoin(url_or_path):
        return urljoin('https://www.youtube.com', url_or_path)

    def _extract_uploader_id(self, uploader_url):
        return self._search_regex(
            r'/(?:(?:channel|user)/|(?=@))([^/?&#]+)', uploader_url or '',
            'uploader id', default=None)


class YoutubeIE(YoutubeBaseInfoExtractor):
    IE_DESC = 'YouTube.com'
    _INVIDIOUS_SITES = (
        # invidious-redirect websites
        r'(?:www\.)?redirect\.invidious\.io',
        r'(?:(?:www|dev)\.)?invidio\.us',
        # Invidious instances taken from https://github.com/iv-org/documentation/blob/master/Invidious-Instances.md
        r'(?:(?:www|no)\.)?invidiou\.sh',
        r'(?:(?:www|fi)\.)?invidious\.snopyta\.org',
        r'(?:www\.)?invidious\.kabi\.tk',
        r'(?:www\.)?invidious\.13ad\.de',
        r'(?:www\.)?invidious\.mastodon\.host',
        r'(?:www\.)?invidious\.zapashcanon\.fr',
        r'(?:www\.)?(?:invidious(?:-us)?|piped)\.kavin\.rocks',
        r'(?:www\.)?invidious\.tinfoil-hat\.net',
        r'(?:www\.)?invidious\.himiko\.cloud',
        r'(?:www\.)?invidious\.reallyancient\.tech',
        r'(?:www\.)?invidious\.tube',
        r'(?:www\.)?invidiou\.site',
        r'(?:www\.)?invidious\.site',
        r'(?:www\.)?invidious\.xyz',
        r'(?:www\.)?invidious\.nixnet\.xyz',
        r'(?:www\.)?invidious\.048596\.xyz',
        r'(?:www\.)?invidious\.drycat\.fr',
        r'(?:www\.)?inv\.skyn3t\.in',
        r'(?:www\.)?tube\.poal\.co',
        r'(?:www\.)?tube\.connect\.cafe',
        r'(?:www\.)?vid\.wxzm\.sx',
        r'(?:www\.)?vid\.mint\.lgbt',
        r'(?:www\.)?vid\.puffyan\.us',
        r'(?:www\.)?yewtu\.be',
        r'(?:www\.)?yt\.elukerio\.org',
        r'(?:www\.)?yt\.lelux\.fi',
        r'(?:www\.)?invidious\.ggc-project\.de',
        r'(?:www\.)?yt\.maisputain\.ovh',
        r'(?:www\.)?ytprivate\.com',
        r'(?:www\.)?invidious\.13ad\.de',
        r'(?:www\.)?invidious\.toot\.koeln',
        r'(?:www\.)?invidious\.fdn\.fr',
        r'(?:www\.)?watch\.nettohikari\.com',
        r'(?:www\.)?invidious\.namazso\.eu',
        r'(?:www\.)?invidious\.silkky\.cloud',
        r'(?:www\.)?invidious\.exonip\.de',
        r'(?:www\.)?invidious\.riverside\.rocks',
        r'(?:www\.)?invidious\.blamefran\.net',
        r'(?:www\.)?invidious\.moomoo\.de',
        r'(?:www\.)?ytb\.trom\.tf',
        r'(?:www\.)?yt\.cyberhost\.uk',
        r'(?:www\.)?kgg2m7yk5aybusll\.onion',
        r'(?:www\.)?qklhadlycap4cnod\.onion',
        r'(?:www\.)?axqzx4s6s54s32yentfqojs3x5i7faxza6xo3ehd4bzzsg2ii4fv2iid\.onion',
        r'(?:www\.)?c7hqkpkpemu6e7emz5b4vyz7idjgdvgaaa3dyimmeojqbgpea3xqjoid\.onion',
        r'(?:www\.)?fz253lmuao3strwbfbmx46yu7acac2jz27iwtorgmbqlkurlclmancad\.onion',
        r'(?:www\.)?invidious\.l4qlywnpwqsluw65ts7md3khrivpirse744un3x7mlskqauz5pyuzgqd\.onion',
        r'(?:www\.)?owxfohz4kjyv25fvlqilyxast7inivgiktls3th44jhk3ej3i7ya\.b32\.i2p',
        r'(?:www\.)?4l2dgddgsrkf2ous66i6seeyi6etzfgrue332grh2n7madpwopotugyd\.onion',
        r'(?:www\.)?w6ijuptxiku4xpnnaetxvnkc5vqcdu7mgns2u77qefoixi63vbvnpnqd\.onion',
        r'(?:www\.)?kbjggqkzv65ivcqj6bumvp337z6264huv5kpkwuv6gu5yjiskvan7fad\.onion',
        r'(?:www\.)?grwp24hodrefzvjjuccrkw3mjq4tzhaaq32amf33dzpmuxe7ilepcmad\.onion',
        r'(?:www\.)?hpniueoejy4opn7bc4ftgazyqjoeqwlvh2uiku2xqku6zpoa4bf5ruid\.onion',
    )
    _VALID_URL = r"""(?x)^
                     (
                         (?:https?://|//)                                    # http(s):// or protocol-independent URL
                         (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie|kids)?\.com|
                            (?:www\.)?deturl\.com/www\.youtube\.com|
                            (?:www\.)?pwnyoutube\.com|
                            (?:www\.)?hooktube\.com|
                            (?:www\.)?yourepeat\.com|
                            tube\.majestyc\.net|
                            %(invidious)s|
                            youtube\.googleapis\.com)/                        # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/(?!videoseries))                # v/ or embed/ or e/
                             |shorts/
                             |(?:                                             # or the v= param in all its forms
                                 (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?[&;])??                                # any other preceding param (like /?s=tuff&v=xxxx or ?s=tuff&amp;v=V36LpHqtcDY)
                                 v=
                             )
                         ))
                         |(?:
                            youtu\.be|                                        # just youtu.be/xxxx
                            vid\.plus|                                        # or vid.plus/xxxx
                            zwearz\.com/watch|                                # or zwearz.com/watch/xxxx
                            %(invidious)s
                         )/
                         |(?:www\.)?cleanvideosearch\.com/media/action/yt/watch\?videoId=
                         )
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     (?P<id>[0-9A-Za-z_-]{11})                                # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $""" % {
        'invidious': '|'.join(_INVIDIOUS_SITES),
    }
    _PLAYER_INFO_RE = (
        r'/s/player/(?P<id>[a-zA-Z0-9_-]{8,})/player',
        r'/(?P<id>[a-zA-Z0-9_-]{8,})/player(?:_ias\.vflset(?:/[a-zA-Z]{2,3}_[a-zA-Z]{2,3})?|-plasma-ias-(?:phone|tablet)-[a-z]{2}_[A-Z]{2}\.vflset)/base\.js$',
        r'\b(?P<id>vfl[a-zA-Z0-9_-]+)\b.*?\.js$',
    )
    _SUBTITLE_FORMATS = ('json3', 'srv1', 'srv2', 'srv3', 'ttml', 'vtt')

    _GEO_BYPASS = False

    IE_NAME = 'youtube'
    _TESTS = [
        {
            'url': 'https://www.youtube.com/watch?v=BaW_jenozKc&t=1s&end=9',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': '@PhilippHagemeister',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@PhilippHagemeister',
                'channel': 'Philipp Hagemeister',
                'channel_id': 'UCLqxVugv74EIW3VWh2NOa3Q',
                'channel_url': r're:https?://(?:www\.)?youtube\.com/channel/UCLqxVugv74EIW3VWh2NOa3Q',
                'upload_date': '20121002',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'tags': ['youtube-dl'],
                'duration': 10,
                'view_count': int,
                'like_count': int,
                'thumbnail': 'https://i.ytimg.com/vi/BaW_jenozKc/maxresdefault.jpg',
                'start_time': 1,
                'end_time': 9,
            },
        },
        {
            'url': '//www.YouTube.com/watch?v=yZIXLfi8CZQ',
            'note': 'Embed-only video (#1746)',
            'info_dict': {
                'id': 'yZIXLfi8CZQ',
                'ext': 'mp4',
                'upload_date': '20120608',
                'title': 'Principal Sexually Assaults A Teacher - Episode 117 - 8th June 2012',
                'description': 'md5:09b78bd971f1e3e289601dfba15ca4f7',
                'uploader': 'SET India',
                'uploader_id': 'setindia',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/setindia',
                'age_limit': 18,
            },
            'skip': 'Private video',
        },
        {
            'url': 'https://www.youtube.com/watch?v=BaW_jenozKc&v=yZIXLfi8CZQ',
            'note': 'Use the first video ID in the URL',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': '@PhilippHagemeister',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@PhilippHagemeister',
                'upload_date': '20121002',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'tags': ['youtube-dl'],
                'duration': 10,
                'view_count': int,
                'like_count': int,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://www.youtube.com/watch?v=a9LDPn-MO4I',
            'note': '256k DASH audio (format 141) via DASH manifest',
            'info_dict': {
                'id': 'a9LDPn-MO4I',
                'ext': 'm4a',
                'upload_date': '20121002',
                'uploader_id': '8KVIDEO',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/8KVIDEO',
                'description': '',
                'uploader': '8KVIDEO',
                'title': 'UHDTV TEST 8K VIDEO.mp4'
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141',
            },
            'skip': 'format 141 not served any more',
        },
        # DASH manifest with encrypted signature
        {
            'url': 'https://www.youtube.com/watch?v=IB3lcPjvWLA',
            'info_dict': {
                'id': 'IB3lcPjvWLA',
                'ext': 'm4a',
                'title': 'Afrojack, Spree Wilson - The Spark (Official Music Video) ft. Spree Wilson',
                'description': 'md5:8f5e2b82460520b619ccac1f509d43bf',
                'duration': 244,
                'uploader': 'AfrojackVEVO',
                'uploader_id': '@AfrojackVEVO',
                'upload_date': '20131011',
                'abr': 129.495,
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141/bestaudio[ext=m4a]',
            },
        },
        # Controversy video
        {
            'url': 'https://www.youtube.com/watch?v=T4XJQO3qol8',
            'info_dict': {
                'id': 'T4XJQO3qol8',
                'ext': 'mp4',
                'duration': 219,
                'upload_date': '20100909',
                'uploader': 'Amazing Atheist',
                'uploader_id': '@theamazingatheist',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@theamazingatheist',
                'title': 'Burning Everyone\'s Koran',
                'description': 'SUBSCRIBE: http://www.youtube.com/saturninefilms \r\n\r\nEven Obama has taken a stand against freedom on this issue: http://www.huffingtonpost.com/2010/09/09/obama-gma-interview-quran_n_710282.html',
            }
        },
        # Age-gated videos
        {
            'note': 'Age-gated video (No vevo, embed allowed)',
            'url': 'https://youtube.com/watch?v=HtVdAasjOgU',
            'info_dict': {
                'id': 'HtVdAasjOgU',
                'ext': 'mp4',
                'title': 'The Witcher 3: Wild Hunt - The Sword Of Destiny Trailer',
                'description': r're:(?s).{100,}About the Game\n.*?The Witcher 3: Wild Hunt.{100,}',
                'duration': 142,
                'uploader': 'The Witcher',
                'uploader_id': '@thewitcher',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@thewitcher',
                'upload_date': '20140605',
                'thumbnail': 'https://i.ytimg.com/vi/HtVdAasjOgU/maxresdefault.jpg',
                'age_limit': 18,
                'categories': ['Gaming'],
                'tags': 'count:17',
                'channel': 'The Witcher',
                'channel_url': 'https://www.youtube.com/channel/UCzybXLxv08IApdjdN0mJhEg',
                'channel_id': 'UCzybXLxv08IApdjdN0mJhEg',
                'view_count': int,
                'like_count': int,
            },
        },
        {
            'note': 'Age-gated video with embed allowed in public site',
            'url': 'https://youtube.com/watch?v=HsUATh_Nc2U',
            'info_dict': {
                'id': 'HsUATh_Nc2U',
                'ext': 'mp4',
                'title': 'Godzilla 2 (Official Video)',
                'description': 'md5:bf77e03fcae5529475e500129b05668a',
                'duration': 177,
                'uploader': 'FlyingKitty',
                'uploader_id': '@FlyingKitty900',
                'upload_date': '20200408',
                'thumbnail': 'https://i.ytimg.com/vi/HsUATh_Nc2U/maxresdefault.jpg',
                'age_limit': 18,
                'categories': ['Entertainment'],
                'tags': ['Flyingkitty', 'godzilla 2'],
                'channel': 'FlyingKitty',
                'channel_url': 'https://www.youtube.com/channel/UCYQT13AtrJC0gsM1far_zJg',
                'channel_id': 'UCYQT13AtrJC0gsM1far_zJg',
                'view_count': int,
                'like_count': int,
            },
        },
        {
            'note': 'Age-gated video embeddable only with clientScreen=EMBED',
            'url': 'https://youtube.com/watch?v=Tq92D6wQ1mg',
            'info_dict': {
                'id': 'Tq92D6wQ1mg',
                'ext': 'mp4',
                'title': '[MMD] Adios - EVERGLOW [+Motion DL]',
                'description': 'md5:17eccca93a786d51bc67646756894066',
                'duration': 106,
                'uploader': 'Projekt Melody',
                'uploader_id': '@ProjektMelody',
                'upload_date': '20191227',
                'age_limit': 18,
                'thumbnail': 'https://i.ytimg.com/vi/Tq92D6wQ1mg/sddefault.jpg',
                'tags': ['mmd', 'dance', 'mikumikudance', 'kpop', 'vtuber'],
                'categories': ['Entertainment'],
                'channel': 'Projekt Melody',
                'channel_url': 'https://www.youtube.com/channel/UC1yoRdFoFJaCY-AGfD9W0wQ',
                'channel_id': 'UC1yoRdFoFJaCY-AGfD9W0wQ',
                'view_count': int,
                'like_count': int,
            },
        },
        {
            'note': 'Non-Age-gated non-embeddable video',
            'url': 'https://youtube.com/watch?v=MeJVWBSsPAY',
            'info_dict': {
                'id': 'MeJVWBSsPAY',
                'ext': 'mp4',
                'title': 'OOMPH! - Such Mich Find Mich (Lyrics)',
                'description': 'Fan Video. Music & Lyrics by OOMPH!.',
                'duration': 210,
                'upload_date': '20130730',
                'uploader': 'Herr Lurik',
                'uploader_id': '@HerrLurik',
                'uploader_url': 'http://www.youtube.com/@HerrLurik',
                'age_limit': 0,
                'thumbnail': 'https://i.ytimg.com/vi/MeJVWBSsPAY/hqdefault.jpg',
                'tags': ['oomph', 'such mich find mich', 'lyrics', 'german industrial', 'musica industrial'],
                'categories': ['Music'],
                'channel': 'Herr Lurik',
                'channel_url': 'https://www.youtube.com/channel/UCdR3RSDPqub28LjZx0v9-aA',
                'channel_id': 'UCdR3RSDPqub28LjZx0v9-aA',
                'artist': 'OOMPH!',
                'view_count': int,
                'like_count': int,
            },
        },
        {
            'note': 'Non-bypassable age-gated video',
            'url': 'https://youtube.com/watch?v=Cr381pDsSsA',
            'only_matching': True,
        },
        {
            'note': 'Age-gated video only available with authentication (not via embed workaround)',
            'url': 'XgnwCQzjau8',
            'only_matching': True,
            'skip': '''This video has been removed for violating YouTube's Community Guidelines''',
        },
        # video_info is None (https://github.com/ytdl-org/youtube-dl/issues/4421)
        # YouTube Red ad is not captured for creator
        {
            'url': '__2ABJjxzNo',
            'info_dict': {
                'id': '__2ABJjxzNo',
                'ext': 'mp4',
                'duration': 266,
                'upload_date': '20100430',
                'uploader_id': '@deadmau5',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@deadmau5',
                'creator': 'deadmau5',
                'description': 'md5:6cbcd3a92ce1bc676fc4d6ab4ace2336',
                'uploader': 'deadmau5',
                'title': 'Deadmau5 - Some Chords (HD)',
                'alt_title': 'Some Chords',
            },
            'expected_warnings': [
                'DASH manifest missing',
            ]
        },
        # Olympics (https://github.com/ytdl-org/youtube-dl/issues/4431)
        {
            'url': 'lqQg6PlCWgI',
            'info_dict': {
                'id': 'lqQg6PlCWgI',
                'ext': 'mp4',
                'title': 'Hockey - Women -  GER-AUS - London 2012 Olympic Games',
                'description': r're:(?s)(?:.+\s)?HO09  - Women -  GER-AUS - Hockey - 31 July 2012 - London 2012 Olympic Games\s*',
                'duration': 6085,
                'upload_date': '20150827',
                'uploader_id': '@Olympics',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@Olympics',
                'uploader': r're:Olympics?',
                'age_limit': 0,
                'thumbnail': 'https://i.ytimg.com/vi/lqQg6PlCWgI/maxresdefault.jpg',
                'categories': ['Sports'],
                'tags': ['Hockey', '2012-07-31', '31 July 2012', 'Riverbank Arena', 'Session', 'Olympics', 'Olympic Games', 'London 2012', '2012 Summer Olympics', 'Summer Games'],
                'channel': 'Olympics',
                'channel_url': 'https://www.youtube.com/channel/UCTl3QQTvqHFjurroKxexy2Q',
                'channel_id': 'UCTl3QQTvqHFjurroKxexy2Q',
                'view_count': int,
                'like_count': int,
            },
        },
        # Non-square pixels
        {
            'url': 'https://www.youtube.com/watch?v=_b-2C3KPAM0',
            'info_dict': {
                'id': '_b-2C3KPAM0',
                'ext': 'mp4',
                'stretched_ratio': 16 / 9.,
                'duration': 85,
                'upload_date': '20110310',
                'uploader_id': '@AllenMeow',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@AllenMeow',
                'description': 'made by Wacom from Korea | 字幕&加油添醋 by TY\'s Allen | 感謝heylisa00cavey1001同學熱情提供梗及翻譯',
                'uploader': '孫ᄋᄅ',
                'title': '[A-made] 變態妍字幕版 太妍 我就是這樣的人',
            },
        },
        # url_encoded_fmt_stream_map is empty string
        {
            'url': 'qEJwOuvDf7I',
            'info_dict': {
                'id': 'qEJwOuvDf7I',
                'ext': 'webm',
                'title': 'Обсуждение судебной практики по выборам 14 сентября 2014 года в Санкт-Петербурге',
                'description': '',
                'upload_date': '20150404',
                'uploader_id': 'spbelect',
                'uploader': 'Наблюдатели Петербурга',
            },
            'params': {
                'skip_download': 'requires avconv',
            },
            'skip': 'This live event has ended.',
        },
        # Extraction from multiple DASH manifests (https://github.com/ytdl-org/youtube-dl/pull/6097)
        {
            'url': 'https://www.youtube.com/watch?v=FIl7x6_3R5Y',
            'info_dict': {
                'id': 'FIl7x6_3R5Y',
                'ext': 'webm',
                'title': 'md5:7b81415841e02ecd4313668cde88737a',
                'description': 'md5:116377fd2963b81ec4ce64b542173306',
                'duration': 220,
                'upload_date': '20150625',
                'uploader_id': 'dorappi2000',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/dorappi2000',
                'uploader': 'dorappi2000',
                'formats': 'mincount:31',
            },
            'skip': 'not actual any more',
        },
        # DASH manifest with segment_list
        {
            'url': 'https://www.youtube.com/embed/CsmdDsKjzN8',
            'md5': '8ce563a1d667b599d21064e982ab9e31',
            'info_dict': {
                'id': 'CsmdDsKjzN8',
                'ext': 'mp4',
                'upload_date': '20150501',  # According to '<meta itemprop="datePublished"', but in other places it's 20150510
                'uploader': 'Airtek',
                'description': 'Retransmisión en directo de la XVIII media maratón de Zaragoza.',
                'uploader_id': 'UCzTzUmjXxxacNnL8I3m4LnQ',
                'title': 'Retransmisión XVIII Media maratón Zaragoza 2015',
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '135',  # bestvideo
            },
            'skip': 'This live event has ended.',
        },
        {
            # Multifeed videos (multiple cameras), URL is for Main Camera
            'url': 'https://www.youtube.com/watch?v=jvGDaLqkpTg',
            'info_dict': {
                'id': 'jvGDaLqkpTg',
                'title': 'Tom Clancy Free Weekend Rainbow Whatever',
                'description': 'md5:e03b909557865076822aa169218d6a5d',
            },
            'playlist': [{
                'info_dict': {
                    'id': 'jvGDaLqkpTg',
                    'ext': 'mp4',
                    'title': 'Tom Clancy Free Weekend Rainbow Whatever (Main Camera)',
                    'description': 'md5:e03b909557865076822aa169218d6a5d',
                    'duration': 10643,
                    'upload_date': '20161111',
                    'uploader': 'Team PGP',
                    'uploader_id': 'UChORY56LMMETTuGjXaJXvLg',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UChORY56LMMETTuGjXaJXvLg',
                },
            }, {
                'info_dict': {
                    'id': '3AKt1R1aDnw',
                    'ext': 'mp4',
                    'title': 'Tom Clancy Free Weekend Rainbow Whatever (Camera 2)',
                    'description': 'md5:e03b909557865076822aa169218d6a5d',
                    'duration': 10991,
                    'upload_date': '20161111',
                    'uploader': 'Team PGP',
                    'uploader_id': 'UChORY56LMMETTuGjXaJXvLg',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UChORY56LMMETTuGjXaJXvLg',
                },
            }, {
                'info_dict': {
                    'id': 'RtAMM00gpVc',
                    'ext': 'mp4',
                    'title': 'Tom Clancy Free Weekend Rainbow Whatever (Camera 3)',
                    'description': 'md5:e03b909557865076822aa169218d6a5d',
                    'duration': 10995,
                    'upload_date': '20161111',
                    'uploader': 'Team PGP',
                    'uploader_id': 'UChORY56LMMETTuGjXaJXvLg',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UChORY56LMMETTuGjXaJXvLg',
                },
            }, {
                'info_dict': {
                    'id': '6N2fdlP3C5U',
                    'ext': 'mp4',
                    'title': 'Tom Clancy Free Weekend Rainbow Whatever (Camera 4)',
                    'description': 'md5:e03b909557865076822aa169218d6a5d',
                    'duration': 10990,
                    'upload_date': '20161111',
                    'uploader': 'Team PGP',
                    'uploader_id': 'UChORY56LMMETTuGjXaJXvLg',
                    'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UChORY56LMMETTuGjXaJXvLg',
                },
            }],
            'params': {
                'skip_download': True,
            },
            'skip': 'Not multifeed any more',
        },
        {
            # Multifeed video with comma in title (see https://github.com/ytdl-org/youtube-dl/issues/8536)
            'url': 'https://www.youtube.com/watch?v=gVfLd0zydlo',
            'info_dict': {
                'id': 'gVfLd0zydlo',
                'title': 'DevConf.cz 2016 Day 2 Workshops 1 14:00 - 15:30',
            },
            'playlist_count': 2,
            'skip': 'Not multifeed any more',
        },
        {
            'url': 'https://vid.plus/FlRa-iH7PGw',
            'only_matching': True,
        },
        {
            'url': 'https://zwearz.com/watch/9lWxNJF-ufM/electra-woman-dyna-girl-official-trailer-grace-helbig.html',
            'only_matching': True,
        },
        {
            # Title with JS-like syntax "};" (see https://github.com/ytdl-org/youtube-dl/issues/7468)
            # Also tests cut-off URL expansion in video description (see
            # https://github.com/ytdl-org/youtube-dl/issues/1892,
            # https://github.com/ytdl-org/youtube-dl/issues/8164)
            'url': 'https://www.youtube.com/watch?v=lsguqyKfVQg',
            'info_dict': {
                'id': 'lsguqyKfVQg',
                'ext': 'mp4',
                'title': '{dark walk}; Loki/AC/Dishonored; collab w/Elflover21',
                'alt_title': 'Dark Walk',
                'description': 'md5:8085699c11dc3f597ce0410b0dcbb34a',
                'duration': 133,
                'upload_date': '20151119',
                'uploader_id': '@IronSoulElf',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@IronSoulElf',
                'uploader': 'IronSoulElf',
                'creator': r're:Todd Haberman[;,]\s+Daniel Law Heath and Aaron Kaplan',
                'track': 'Dark Walk',
                'artist': r're:Todd Haberman[;,]\s+Daniel Law Heath and Aaron Kaplan',
                'album': 'Position Music - Production Music Vol. 143 - Dark Walk',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # Tags with '};' (see https://github.com/ytdl-org/youtube-dl/issues/7468)
            'url': 'https://www.youtube.com/watch?v=Ms7iBXnlUO8',
            'only_matching': True,
        },
        {
            # Video with yt:stretch=17:0
            'url': 'https://www.youtube.com/watch?v=Q39EVAstoRM',
            'info_dict': {
                'id': 'Q39EVAstoRM',
                'ext': 'mp4',
                'title': 'Clash Of Clans#14 Dicas De Ataque Para CV 4',
                'description': 'md5:ee18a25c350637c8faff806845bddee9',
                'upload_date': '20151107',
                'uploader_id': 'UCCr7TALkRbo3EtFzETQF1LA',
                'uploader': 'CH GAMER DROID',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'This video does not exist.',
        },
        {
            # Video with incomplete 'yt:stretch=16:'
            'url': 'https://www.youtube.com/watch?v=FRhJzUSJbGI',
            'only_matching': True,
        },
        {
            # Video licensed under Creative Commons
            'url': 'https://www.youtube.com/watch?v=M4gD1WSo5mA',
            'info_dict': {
                'id': 'M4gD1WSo5mA',
                'ext': 'mp4',
                'title': 'md5:e41008789470fc2533a3252216f1c1d1',
                'description': 'md5:a677553cf0840649b731a3024aeff4cc',
                'duration': 721,
                'upload_date': '20150127',
                'uploader_id': '@BKCHarvard',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@BKCHarvard',
                'uploader': 'The Berkman Klein Center for Internet & Society',
                'license': 'Creative Commons Attribution license (reuse allowed)',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # Channel-like uploader_url
            'url': 'https://www.youtube.com/watch?v=eQcmzGIKrzg',
            'info_dict': {
                'id': 'eQcmzGIKrzg',
                'ext': 'mp4',
                'title': 'Democratic Socialism and Foreign Policy | Bernie Sanders',
                'description': 'md5:13a2503d7b5904ef4b223aa101628f39',
                'duration': 4060,
                'upload_date': '20151119',
                'uploader': 'Bernie Sanders',
                'uploader_id': '@BernieSanders',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@BernieSanders',
                'license': 'Creative Commons Attribution license (reuse allowed)',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://www.youtube.com/watch?feature=player_embedded&amp;amp;v=V36LpHqtcDY',
            'only_matching': True,
        },
        {
            # YouTube Red paid video (https://github.com/ytdl-org/youtube-dl/issues/10059)
            'url': 'https://www.youtube.com/watch?v=i1Ko8UG-Tdo',
            'only_matching': True,
        },
        {
            # Rental video preview
            'url': 'https://www.youtube.com/watch?v=yYr8q0y5Jfg',
            'info_dict': {
                'id': 'uGpuVWrhIzE',
                'ext': 'mp4',
                'title': 'Piku - Trailer',
                'description': 'md5:c36bd60c3fd6f1954086c083c72092eb',
                'upload_date': '20150811',
                'uploader': 'FlixMatrix',
                'uploader_id': 'FlixMatrixKaravan',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/FlixMatrixKaravan',
                'license': 'Standard YouTube License',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'This video is not available.',
        },
        {
            # YouTube Red video with episode data
            'url': 'https://www.youtube.com/watch?v=iqKdEhx-dD4',
            'info_dict': {
                'id': 'iqKdEhx-dD4',
                'ext': 'mp4',
                'title': 'Isolation - Mind Field (Ep 1)',
                'description': 'md5:f540112edec5d09fc8cc752d3d4ba3cd',
                'duration': 2085,
                'upload_date': '20170118',
                'uploader': 'Vsauce',
                'uploader_id': '@Vsauce',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@Vsauce',
                'series': 'Mind Field',
                'season_number': 1,
                'episode_number': 1,
            },
            'params': {
                'skip_download': True,
            },
            'expected_warnings': [
                'Skipping DASH manifest',
            ],
        },
        {
            # The following content has been identified by the YouTube community
            # as inappropriate or offensive to some audiences.
            'url': 'https://www.youtube.com/watch?v=6SJNVb0GnPI',
            'info_dict': {
                'id': '6SJNVb0GnPI',
                'ext': 'mp4',
                'title': 'Race Differences in Intelligence',
                'description': 'md5:5d161533167390427a1f8ee89a1fc6f1',
                'duration': 965,
                'upload_date': '20140124',
                'uploader': 'New Century Foundation',
                'uploader_id': 'UCEJYpZGqgUob0zVVEaLhvVg',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UCEJYpZGqgUob0zVVEaLhvVg',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'This video has been removed for violating YouTube\'s policy on hate speech.',
        },
        {
            # itag 212
            'url': '1t24XAntNCY',
            'only_matching': True,
        },
        {
            # geo restricted to JP
            'url': 'sJL6WA-aGkQ',
            'only_matching': True,
        },
        {
            'url': 'https://invidio.us/watch?v=BaW_jenozKc',
            'only_matching': True,
        },
        {
            'url': 'https://redirect.invidious.io/watch?v=BaW_jenozKc',
            'only_matching': True,
        },
        {
            # from https://nitter.pussthecat.org/YouTube/status/1360363141947944964#m
            'url': 'https://redirect.invidious.io/Yh0AhrY9GjA',
            'only_matching': True,
        },
        {
            # DRM protected
            'url': 'https://www.youtube.com/watch?v=s7_qI6_mIXc',
            'only_matching': True,
        },
        {
            # Video with unsupported adaptive stream type formats
            'url': 'https://www.youtube.com/watch?v=Z4Vy8R84T1U',
            'info_dict': {
                'id': 'Z4Vy8R84T1U',
                'ext': 'mp4',
                'title': 'saman SMAN 53 Jakarta(Sancety) opening COFFEE4th at SMAN 53 Jakarta',
                'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
                'duration': 433,
                'upload_date': '20130923',
                'uploader': 'Amelia Putri Harwita',
                'uploader_id': 'UCpOxM49HJxmC1qCalXyB3_Q',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UCpOxM49HJxmC1qCalXyB3_Q',
                'formats': 'maxcount:10',
            },
            'params': {
                'skip_download': True,
                'youtube_include_dash_manifest': False,
            },
            'skip': 'not actual any more',
        },
        {
            # Youtube Music Auto-generated description
            'url': 'https://music.youtube.com/watch?v=MgNrAu2pzNs',
            'info_dict': {
                'id': 'MgNrAu2pzNs',
                'ext': 'mp4',
                'title': 'Voyeur Girl',
                'description': 'md5:7ae382a65843d6df2685993e90a8628f',
                'upload_date': '20190312',
                'uploader': 'Stephen - Topic',
                'uploader_id': 'UC-pWHpBjdGG69N9mM2auIAA',
                'artist': 'Stephen',
                'track': 'Voyeur Girl',
                'album': 'it\'s too much love to know my dear',
                'release_date': '20190313',
                'release_year': 2019,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://www.youtubekids.com/watch?v=3b8nCWDgZ6Q',
            'only_matching': True,
        },
        {
            # invalid -> valid video id redirection
            'url': 'DJztXj2GPfl',
            'info_dict': {
                'id': 'DJztXj2GPfk',
                'ext': 'mp4',
                'title': 'Panjabi MC - Mundian To Bach Ke (The Dictator Soundtrack)',
                'description': 'md5:bf577a41da97918e94fa9798d9228825',
                'upload_date': '20090125',
                'uploader': 'Prochorowka',
                'uploader_id': 'Prochorowka',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/Prochorowka',
                'artist': 'Panjabi MC',
                'track': 'Beware of the Boys (Mundian to Bach Ke) - Motivo Hi-Lectro Remix',
                'album': 'Beware of the Boys (Mundian To Bach Ke)',
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Video unavailable',
        },
        {
            # empty description results in an empty string
            'url': 'https://www.youtube.com/watch?v=x41yOUIvK2k',
            'info_dict': {
                'id': 'x41yOUIvK2k',
                'ext': 'mp4',
                'title': 'IMG 3456',
                'description': '',
                'upload_date': '20170613',
                'uploader': 'ElevageOrVert',
                'uploader_id': '@ElevageOrVert',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # with '};' inside yt initial data (see [1])
            # see [2] for an example with '};' inside ytInitialPlayerResponse
            # 1. https://github.com/ytdl-org/youtube-dl/issues/27093
            # 2. https://github.com/ytdl-org/youtube-dl/issues/27216
            'url': 'https://www.youtube.com/watch?v=CHqg6qOn4no',
            'info_dict': {
                'id': 'CHqg6qOn4no',
                'ext': 'mp4',
                'title': 'Part 77   Sort a list of simple types in c#',
                'description': 'md5:b8746fa52e10cdbf47997903f13b20dc',
                'upload_date': '20130831',
                'uploader': 'kudvenkat',
                'uploader_id': '@Csharp-video-tutorialsBlogspot',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # another example of '};' in ytInitialData
            'url': 'https://www.youtube.com/watch?v=gVfgbahppCY',
            'only_matching': True,
        },
        {
            'url': 'https://www.youtube.com/watch_popup?v=63RmMXCd_bQ',
            'only_matching': True,
        },
        {
            # https://github.com/ytdl-org/youtube-dl/pull/28094
            'url': 'OtqTfy26tG0',
            'info_dict': {
                'id': 'OtqTfy26tG0',
                'ext': 'mp4',
                'title': 'Burn Out',
                'description': 'md5:8d07b84dcbcbfb34bc12a56d968b6131',
                'upload_date': '20141120',
                'uploader': 'The Cinematic Orchestra - Topic',
                'uploader_id': 'UCIzsJBIyo8hhpFm1NK0uLgw',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UCIzsJBIyo8hhpFm1NK0uLgw',
                'artist': 'The Cinematic Orchestra',
                'track': 'Burn Out',
                'album': 'Every Day',
                'release_data': None,
                'release_year': None,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # controversial video, only works with bpctr when authenticated with cookies
            'url': 'https://www.youtube.com/watch?v=nGC3D_FkCmg',
            'only_matching': True,
        },
        {
            # restricted location, https://github.com/ytdl-org/youtube-dl/issues/28685
            'url': 'cBvYw8_A0vQ',
            'info_dict': {
                'id': 'cBvYw8_A0vQ',
                'ext': 'mp4',
                'title': '4K Ueno Okachimachi  Street  Scenes  上野御徒町歩き',
                'description': 'md5:ea770e474b7cd6722b4c95b833c03630',
                'upload_date': '20201120',
                'uploader': 'Walk around Japan',
                'uploader_id': '@walkaroundjapan7124',
                'uploader_url': r're:https?://(?:www\.)?youtube\.com/@walkaroundjapan7124',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # YT 'Shorts'
            'url': 'https://youtube.com/shorts/4L2J27mJ3Dc',
            'info_dict': {
                'id': '4L2J27mJ3Dc',
                'ext': 'mp4',
                'title': 'Midwest Squid Game #Shorts',
                'description': 'md5:976512b8a29269b93bbd8a61edc45a6d',
                'upload_date': '20211025',
                'uploader': 'Charlie Berens',
                'uploader_id': '@CharlieBerens',
            },
            'params': {
                'skip_download': True,
            },
        },
    ]
    _formats = {
        '5': {'ext': 'flv', 'width': 400, 'height': 240, 'acodec': 'mp3', 'abr': 64, 'vcodec': 'h263'},
        '6': {'ext': 'flv', 'width': 450, 'height': 270, 'acodec': 'mp3', 'abr': 64, 'vcodec': 'h263'},
        '13': {'ext': '3gp', 'acodec': 'aac', 'vcodec': 'mp4v'},
        '17': {'ext': '3gp', 'width': 176, 'height': 144, 'acodec': 'aac', 'abr': 24, 'vcodec': 'mp4v'},
        '18': {'ext': 'mp4', 'width': 640, 'height': 360, 'acodec': 'aac', 'abr': 96, 'vcodec': 'h264'},
        '22': {'ext': 'mp4', 'width': 1280, 'height': 720, 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264'},
        '34': {'ext': 'flv', 'width': 640, 'height': 360, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},
        '35': {'ext': 'flv', 'width': 854, 'height': 480, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},
        # itag 36 videos are either 320x180 (BaW_jenozKc) or 320x240 (__2ABJjxzNo), abr varies as well
        '36': {'ext': '3gp', 'width': 320, 'acodec': 'aac', 'vcodec': 'mp4v'},
        '37': {'ext': 'mp4', 'width': 1920, 'height': 1080, 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264'},
        '38': {'ext': 'mp4', 'width': 4096, 'height': 3072, 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264'},
        '43': {'ext': 'webm', 'width': 640, 'height': 360, 'acodec': 'vorbis', 'abr': 128, 'vcodec': 'vp8'},
        '44': {'ext': 'webm', 'width': 854, 'height': 480, 'acodec': 'vorbis', 'abr': 128, 'vcodec': 'vp8'},
        '45': {'ext': 'webm', 'width': 1280, 'height': 720, 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8'},
        '46': {'ext': 'webm', 'width': 1920, 'height': 1080, 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8'},
        '59': {'ext': 'mp4', 'width': 854, 'height': 480, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},
        '78': {'ext': 'mp4', 'width': 854, 'height': 480, 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264'},


        # 3D videos
        '82': {'ext': 'mp4', 'height': 360, 'format_note': '3D', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264', 'preference': -20},
        '83': {'ext': 'mp4', 'height': 480, 'format_note': '3D', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264', 'preference': -20},
        '84': {'ext': 'mp4', 'height': 720, 'format_note': '3D', 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264', 'preference': -20},
        '85': {'ext': 'mp4', 'height': 1080, 'format_note': '3D', 'acodec': 'aac', 'abr': 192, 'vcodec': 'h264', 'preference': -20},
        '100': {'ext': 'webm', 'height': 360, 'format_note': '3D', 'acodec': 'vorbis', 'abr': 128, 'vcodec': 'vp8', 'preference': -20},
        '101': {'ext': 'webm', 'height': 480, 'format_note': '3D', 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8', 'preference': -20},
        '102': {'ext': 'webm', 'height': 720, 'format_note': '3D', 'acodec': 'vorbis', 'abr': 192, 'vcodec': 'vp8', 'preference': -20},

        # Apple HTTP Live Streaming
        '91': {'ext': 'mp4', 'height': 144, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 48, 'vcodec': 'h264', 'preference': -10},
        '92': {'ext': 'mp4', 'height': 240, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 48, 'vcodec': 'h264', 'preference': -10},
        '93': {'ext': 'mp4', 'height': 360, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264', 'preference': -10},
        '94': {'ext': 'mp4', 'height': 480, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 128, 'vcodec': 'h264', 'preference': -10},
        '95': {'ext': 'mp4', 'height': 720, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 256, 'vcodec': 'h264', 'preference': -10},
        '96': {'ext': 'mp4', 'height': 1080, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 256, 'vcodec': 'h264', 'preference': -10},
        '132': {'ext': 'mp4', 'height': 240, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 48, 'vcodec': 'h264', 'preference': -10},
        '151': {'ext': 'mp4', 'height': 72, 'format_note': 'HLS', 'acodec': 'aac', 'abr': 24, 'vcodec': 'h264', 'preference': -10},

        # DASH mp4 video
        '133': {'ext': 'mp4', 'height': 240, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '134': {'ext': 'mp4', 'height': 360, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '135': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '136': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '137': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '138': {'ext': 'mp4', 'format_note': 'DASH video', 'vcodec': 'h264'},  # Height can vary (https://github.com/ytdl-org/youtube-dl/issues/4559)
        '160': {'ext': 'mp4', 'height': 144, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '212': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '264': {'ext': 'mp4', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '298': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'h264', 'fps': 60},
        '299': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'h264', 'fps': 60},
        '266': {'ext': 'mp4', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'h264'},

        # Dash mp4 audio
        '139': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 48, 'container': 'm4a_dash'},
        '140': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 128, 'container': 'm4a_dash'},
        '141': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 256, 'container': 'm4a_dash'},
        '256': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'container': 'm4a_dash'},
        '258': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'container': 'm4a_dash'},
        '325': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'dtse', 'container': 'm4a_dash'},
        '328': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'ec-3', 'container': 'm4a_dash'},

        # Dash webm
        '167': {'ext': 'webm', 'height': 360, 'width': 640, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp8'},
        '168': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp8'},
        '169': {'ext': 'webm', 'height': 720, 'width': 1280, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp8'},
        '170': {'ext': 'webm', 'height': 1080, 'width': 1920, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp8'},
        '218': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp8'},
        '219': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp8'},
        '278': {'ext': 'webm', 'height': 144, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp9'},
        '242': {'ext': 'webm', 'height': 240, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '243': {'ext': 'webm', 'height': 360, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '244': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '245': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '246': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '247': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '248': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '271': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        # itag 272 videos are either 3840x2160 (e.g. RtoitU2A-3E) or 7680x4320 (sLprVF6d7Ug)
        '272': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '302': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},
        '303': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},
        '308': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},
        '313': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '315': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'vp9', 'fps': 60},

        # Dash webm audio
        '171': {'ext': 'webm', 'acodec': 'vorbis', 'format_note': 'DASH audio', 'abr': 128},
        '172': {'ext': 'webm', 'acodec': 'vorbis', 'format_note': 'DASH audio', 'abr': 256},

        # Dash webm audio with opus inside
        '249': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 50},
        '250': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 70},
        '251': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 160},

        # RTMP (unnamed)
        '_rtmp': {'protocol': 'rtmp'},

        # av01 video only formats sometimes served with "unknown" codecs
        '394': {'acodec': 'none', 'vcodec': 'av01.0.05M.08'},
        '395': {'acodec': 'none', 'vcodec': 'av01.0.05M.08'},
        '396': {'acodec': 'none', 'vcodec': 'av01.0.05M.08'},
        '397': {'acodec': 'none', 'vcodec': 'av01.0.05M.08'},
    }

    @classmethod
    def suitable(cls, url):
        if parse_qs(url).get('list', [None])[0]:
            return False
        return super(YoutubeIE, cls).suitable(url)

    def __init__(self, *args, **kwargs):
        super(YoutubeIE, self).__init__(*args, **kwargs)
        self._code_cache = {}
        self._player_cache = {}

    def _signature_cache_id(self, example_sig):
        """ Return a string representation of a signature """
        return '.'.join(compat_str(len(part)) for part in example_sig.split('.'))

    @classmethod
    def _extract_player_info(cls, player_url):
        for player_re in cls._PLAYER_INFO_RE:
            id_m = re.search(player_re, player_url)
            if id_m:
                break
        else:
            raise ExtractorError('Cannot identify player %r' % player_url)
        return id_m.group('id')

    def _get_player_code(self, video_id, player_url, player_id=None):
        if not player_id:
            player_id = self._extract_player_info(player_url)

        if player_id not in self._code_cache:
            self._code_cache[player_id] = self._download_webpage(
                player_url, video_id,
                note='Downloading player ' + player_id,
                errnote='Download of %s failed' % player_url)
        return self._code_cache[player_id]

    def _extract_signature_function(self, video_id, player_url, example_sig):
        player_id = self._extract_player_info(player_url)

        # Read from filesystem cache
        func_id = 'js_%s_%s' % (
            player_id, self._signature_cache_id(example_sig))
        assert os.path.basename(func_id) == func_id

        cache_spec = self._downloader.cache.load('youtube-sigfuncs', func_id)
        if cache_spec is not None:
            return lambda s: ''.join(s[i] for i in cache_spec)

        code = self._get_player_code(video_id, player_url, player_id)
        res = self._parse_sig_js(code)

        test_string = ''.join(map(compat_chr, range(len(example_sig))))
        cache_res = res(test_string)
        cache_spec = [ord(c) for c in cache_res]

        self._downloader.cache.store('youtube-sigfuncs', func_id, cache_spec)
        return res

    def _print_sig_code(self, func, example_sig):
        def gen_sig_code(idxs):
            def _genslice(start, end, step):
                starts = '' if start == 0 else str(start)
                ends = (':%d' % (end + step)) if end + step >= 0 else ':'
                steps = '' if step == 1 else (':%d' % step)
                return 's[%s%s%s]' % (starts, ends, steps)

            step = None
            # Quelch pyflakes warnings - start will be set when step is set
            start = '(Never used)'
            for i, prev in zip(idxs[1:], idxs[:-1]):
                if step is not None:
                    if i - prev == step:
                        continue
                    yield _genslice(start, prev, step)
                    step = None
                    continue
                if i - prev in [-1, 1]:
                    step = i - prev
                    start = prev
                    continue
                else:
                    yield 's[%d]' % prev
            if step is None:
                yield 's[%d]' % i
            else:
                yield _genslice(start, i, step)

        test_string = ''.join(map(compat_chr, range(len(example_sig))))
        cache_res = func(test_string)
        cache_spec = [ord(c) for c in cache_res]
        expr_code = ' + '.join(gen_sig_code(cache_spec))
        signature_id_tuple = '(%s)' % (
            ', '.join(compat_str(len(p)) for p in example_sig.split('.')))
        code = ('if tuple(len(p) for p in s.split(\'.\')) == %s:\n'
                '    return %s\n') % (signature_id_tuple, expr_code)
        self.to_screen('Extracted signature function:\n' + code)

    def _parse_sig_js(self, jscode):
        funcname = self._search_regex(
            (r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
             r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(',
             r'\bm=(?P<sig>[a-zA-Z0-9$]{2,})\(decodeURIComponent\(h\.s\)\)',
             r'\bc&&\(c=(?P<sig>[a-zA-Z0-9$]{2,})\(decodeURIComponent\(c\)\)',
             r'(?:\b|[^a-zA-Z0-9$])(?P<sig>[a-zA-Z0-9$]{2,})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)(?:;[a-zA-Z0-9$]{2}\.[a-zA-Z0-9$]{2}\(a,\d+\))?',
             r'(?P<sig>[a-zA-Z0-9$]+)\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
             # Obsolete patterns
             r'("|\')signature\1\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
             r'\.sig\|\|(?P<sig>[a-zA-Z0-9$]+)\(',
             r'yt\.akamaized\.net/\)\s*\|\|\s*.*?\s*[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?:encodeURIComponent\s*\()?\s*(?P<sig>[a-zA-Z0-9$]+)\(',
             r'\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
             r'\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*(?P<sig>[a-zA-Z0-9$]+)\(',
             r'\bc\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*\([^)]*\)\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\('),
            jscode, 'Initial JS player signature function name', group='sig')

        jsi = JSInterpreter(jscode)
        initial_function = jsi.extract_function(funcname)
        return lambda s: initial_function([s])

    def _decrypt_signature(self, s, video_id, player_url):
        """Turn the encrypted s field into a working signature"""

        if player_url is None:
            raise ExtractorError('Cannot decrypt signature without player_url')

        try:
            player_id = (player_url, self._signature_cache_id(s))
            if player_id not in self._player_cache:
                func = self._extract_signature_function(
                    video_id, player_url, s
                )
                self._player_cache[player_id] = func
            func = self._player_cache[player_id]
            if self._downloader.params.get('youtube_print_sig_code'):
                self._print_sig_code(func, s)
            return func(s)
        except Exception as e:
            tb = traceback.format_exc()
            raise ExtractorError(
                'Signature extraction failed: ' + tb, cause=e)

    def _extract_player_url(self, webpage):
        player_url = self._search_regex(
            r'"(?:PLAYER_JS_URL|jsUrl)"\s*:\s*"([^"]+)"',
            webpage or '', 'player URL', fatal=False)
        if not player_url:
            return
        if player_url.startswith('//'):
            player_url = 'https:' + player_url
        elif not re.match(r'https?://', player_url):
            player_url = compat_urllib_parse.urljoin(
                'https://www.youtube.com', player_url)
        return player_url

    # from yt-dlp
    # See also:
    # 1. https://github.com/ytdl-org/youtube-dl/issues/29326#issuecomment-894619419
    # 2. https://code.videolan.org/videolan/vlc/-/blob/4fb284e5af69aa9ac2100ccbdd3b88debec9987f/share/lua/playlist/youtube.lua#L116
    # 3. https://github.com/ytdl-org/youtube-dl/issues/30097#issuecomment-950157377
    def _extract_n_function_name(self, jscode):
        target = r'(?P<nfunc>[a-zA-Z_$][\w$]*)(?:\[(?P<idx>\d+)\])?'
        nfunc_and_idx = self._search_regex(
            r'\.get\("n"\)\)&&\(b=(%s)\([\w$]+\)' % (target, ),
            jscode, 'Initial JS player n function name')
        nfunc, idx = re.match(target, nfunc_and_idx).group('nfunc', 'idx')
        if not idx:
            return nfunc
        if int_or_none(idx) == 0:
            real_nfunc = self._search_regex(
                r'var %s\s*=\s*\[([a-zA-Z_$][\w$]*)\];' % (re.escape(nfunc), ), jscode,
                'Initial JS player n function alias ({nfunc}[{idx}])'.format(**locals()))
            if real_nfunc:
                return real_nfunc
        return self._parse_json(self._search_regex(
            r'var %s\s*=\s*(\[.+?\]);' % (re.escape(nfunc), ), jscode,
            'Initial JS player n function name ({nfunc}[{idx}])'.format(**locals())), nfunc, transform_source=js_to_json)[int(idx)]

    def _extract_n_function(self, video_id, player_url):
        player_id = self._extract_player_info(player_url)
        func_code = self._downloader.cache.load('youtube-nsig', player_id)

        if func_code:
            jsi = JSInterpreter(func_code)
        else:
            jscode = self._get_player_code(video_id, player_url, player_id)
            funcname = self._extract_n_function_name(jscode)
            jsi = JSInterpreter(jscode)
            func_code = jsi.extract_function_code(funcname)
            self._downloader.cache.store('youtube-nsig', player_id, func_code)

        if self._downloader.params.get('youtube_print_sig_code'):
            self.to_screen('Extracted nsig function from {0}:\n{1}\n'.format(player_id, func_code[1]))

        return lambda s: jsi.extract_function_from_code(*func_code)([s])

    def _n_descramble(self, n_param, player_url, video_id):
        """Compute the response to YT's "n" parameter challenge,
           or None

        Args:
        n_param     -- challenge string that is the value of the
                       URL's "n" query parameter
        player_url  -- URL of YT player JS
        video_id
        """

        sig_id = ('nsig_value', n_param)
        if sig_id in self._player_cache:
            return self._player_cache[sig_id]

        try:
            player_id = ('nsig', player_url)
            if player_id not in self._player_cache:
                self._player_cache[player_id] = self._extract_n_function(video_id, player_url)
            func = self._player_cache[player_id]
            ret = func(n_param)
            if ret.startswith('enhanced_except_'):
                raise ExtractorError('Unhandled exception in decode')
            self._player_cache[sig_id] = ret
            if self._downloader.params.get('verbose', False):
                self._downloader.to_screen('[debug] [%s] %s' % (self.IE_NAME, 'Decrypted nsig {0} => {1}'.format(n_param, self._player_cache[sig_id])))
            return self._player_cache[sig_id]
        except Exception as e:
            self._downloader.report_warning(
                '[%s] %s (%s %s)' % (
                    self.IE_NAME,
                    'Unable to decode n-parameter: download likely to be throttled',
                    error_to_compat_str(e),
                    traceback.format_exc()))

    def _unthrottle_format_urls(self, video_id, player_url, formats):
        for fmt in formats:
            parsed_fmt_url = compat_urllib_parse.urlparse(fmt['url'])
            n_param = compat_parse_qs(parsed_fmt_url.query).get('n')
            if not n_param:
                continue
            n_param = n_param[-1]
            n_response = self._n_descramble(n_param, player_url, video_id)
            if n_response is None:
                # give up if descrambling failed
                break
            for fmt_dct in traverse_obj(fmt, (None, (None, ('fragments', Ellipsis))), expected_type=dict):
                fmt_dct['url'] = update_url(
                    fmt_dct['url'], query_update={'n': [n_response]})

    # from yt-dlp, with tweaks
    def _extract_signature_timestamp(self, video_id, player_url, ytcfg=None, fatal=False):
        """
        Extract signatureTimestamp (sts)
        Required to tell API what sig/player version is in use.
        """
        sts = int_or_none(ytcfg.get('STS')) if isinstance(ytcfg, dict) else None
        if not sts:
            # Attempt to extract from player
            if player_url is None:
                error_msg = 'Cannot extract signature timestamp without player_url.'
                if fatal:
                    raise ExtractorError(error_msg)
                self._downloader.report_warning(error_msg)
                return
            code = self._get_player_code(video_id, player_url)
            sts = int_or_none(self._search_regex(
                r'(?:signatureTimestamp|sts)\s*:\s*(?P<sts>[0-9]{5})', code or '',
                'JS player signature timestamp', group='sts', fatal=fatal))
        return sts

    def _mark_watched(self, video_id, player_response):
        playback_url = url_or_none(try_get(
            player_response,
            lambda x: x['playbackTracking']['videostatsPlaybackUrl']['baseUrl']))
        if not playback_url:
            return

        # cpn generation algorithm is reverse engineered from base.js.
        # In fact it works even with dummy cpn.
        CPN_ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
        cpn = ''.join((CPN_ALPHABET[random.randint(0, 256) & 63] for _ in range(0, 16)))

        playback_url = update_url(
            playback_url, query_update={
                'ver': ['2'],
                'cpn': [cpn],
            })

        self._download_webpage(
            playback_url, video_id, 'Marking watched',
            'Unable to mark watched', fatal=False)

    @staticmethod
    def _extract_urls(webpage):
        # Embedded YouTube player
        entries = [
            unescapeHTML(mobj.group('url'))
            for mobj in re.finditer(r'''(?x)
            (?:
                <iframe[^>]+?src=|
                data-video-url=|
                <embed[^>]+?src=|
                embedSWF\(?:\s*|
                <object[^>]+data=|
                new\s+SWFObject\(
            )
            (["\'])
                (?P<url>(?:https?:)?//(?:www\.)?youtube(?:-nocookie)?\.com/
                (?:embed|v|p)/[0-9A-Za-z_-]{11}.*?)
            \1''', webpage)]

        # lazyYT YouTube embed
        entries.extend(list(map(
            unescapeHTML,
            re.findall(r'class="lazyYT" data-youtube-id="([^"]+)"', webpage))))

        # Wordpress "YouTube Video Importer" plugin
        matches = re.findall(r'''(?x)<div[^>]+
            class=(?P<q1>[\'"])[^\'"]*\byvii_single_video_player\b[^\'"]*(?P=q1)[^>]+
            data-video_id=(?P<q2>[\'"])([^\'"]+)(?P=q2)''', webpage)
        entries.extend(m[-1] for m in matches)

        return entries

    @staticmethod
    def _extract_url(webpage):
        urls = YoutubeIE._extract_urls(webpage)
        return urls[0] if urls else None

    @classmethod
    def extract_id(cls, url):
        mobj = re.match(cls._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _extract_chapters_from_json(self, data, video_id, duration):
        chapters_list = try_get(
            data,
            lambda x: x['playerOverlays']
                       ['playerOverlayRenderer']
                       ['decoratedPlayerBarRenderer']
                       ['decoratedPlayerBarRenderer']
                       ['playerBar']
                       ['chapteredPlayerBarRenderer']
                       ['chapters'],
            list)
        if not chapters_list:
            return

        def chapter_time(chapter):
            return float_or_none(
                try_get(
                    chapter,
                    lambda x: x['chapterRenderer']['timeRangeStartMillis'],
                    int),
                scale=1000)
        chapters = []
        for next_num, chapter in enumerate(chapters_list, start=1):
            start_time = chapter_time(chapter)
            if start_time is None:
                continue
            end_time = (chapter_time(chapters_list[next_num])
                        if next_num < len(chapters_list) else duration)
            if end_time is None:
                continue
            title = try_get(
                chapter, lambda x: x['chapterRenderer']['title']['simpleText'],
                compat_str)
            chapters.append({
                'start_time': start_time,
                'end_time': end_time,
                'title': title,
            })
        return chapters

    def _extract_yt_initial_variable(self, webpage, regex, video_id, name):
        return self._parse_json(self._search_regex(
            (r'%s\s*%s' % (regex, self._YT_INITIAL_BOUNDARY_RE),
             regex), webpage, name, default='{}'), video_id, fatal=False)

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        base_url = self.http_scheme() + '//www.youtube.com/'
        webpage_url = base_url + 'watch?v=' + video_id
        webpage = self._download_webpage(
            webpage_url + '&bpctr=9999999999&has_verified=1', video_id, fatal=False)

        player_response = None
        player_url = None
        if webpage:
            player_response = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_PLAYER_RESPONSE_RE,
                video_id, 'initial player response')
        if not player_response:
            player_response = self._call_api(
                'player', {'videoId': video_id}, video_id)

        def is_agegated(playability):
            if not isinstance(playability, dict):
                return

            if playability.get('desktopLegacyAgeGateReason'):
                return True

            reasons = filter(None, (playability.get(r) for r in ('status', 'reason')))
            AGE_GATE_REASONS = (
                'confirm your age', 'age-restricted', 'inappropriate',  # reason
                'age_verification_required', 'age_check_required',  # status
            )
            return any(expected in reason for expected in AGE_GATE_REASONS for reason in reasons)

        def get_playability_status(response):
            return try_get(response, lambda x: x['playabilityStatus'], dict) or {}

        playability_status = get_playability_status(player_response)
        if (is_agegated(playability_status)
                and int_or_none(self._downloader.params.get('age_limit'), default=18) >= 18):

            self.report_age_confirmation()

            # Thanks: https://github.com/yt-dlp/yt-dlp/pull/3233
            pb_context = {'html5Preference': 'HTML5_PREF_WANTS'}

            # Use signatureTimestamp if available
            # Thanks https://github.com/ytdl-org/youtube-dl/issues/31034#issuecomment-1160718026
            player_url = self._extract_player_url(webpage)
            ytcfg = self._extract_ytcfg(video_id, webpage)
            sts = self._extract_signature_timestamp(video_id, player_url, ytcfg)
            if sts:
                pb_context['signatureTimestamp'] = sts

            query = {
                'playbackContext': {'contentPlaybackContext': pb_context},
                'contentCheckOk': True,
                'racyCheckOk': True,
                'context': {
                    'client': {'clientName': 'TVHTML5_SIMPLY_EMBEDDED_PLAYER', 'clientVersion': '2.0', 'hl': 'en', 'clientScreen': 'EMBED'},
                    'thirdParty': {'embedUrl': 'https://google.com'},
                },
                'videoId': video_id,
            }
            headers = {
                'X-YouTube-Client-Name': '85',
                'X-YouTube-Client-Version': '2.0',
                'Origin': 'https://www.youtube.com'
            }

            video_info = self._call_api('player', query, video_id, fatal=False, headers=headers)
            age_gate_status = get_playability_status(video_info)
            if age_gate_status.get('status') == 'OK':
                player_response = video_info
                playability_status = age_gate_status

        trailer_video_id = try_get(
            playability_status,
            lambda x: x['errorScreen']['playerLegacyDesktopYpcTrailerRenderer']['trailerVideoId'],
            compat_str)
        if trailer_video_id:
            return self.url_result(
                trailer_video_id, self.ie_key(), trailer_video_id)

        def get_text(x):
            if not x:
                return
            text = x.get('simpleText')
            if text and isinstance(text, compat_str):
                return text
            runs = x.get('runs')
            if not isinstance(runs, list):
                return
            return ''.join([r['text'] for r in runs if isinstance(r.get('text'), compat_str)])

        search_meta = (
            lambda x: self._html_search_meta(x, webpage, default=None)) \
            if webpage else lambda x: None

        video_details = player_response.get('videoDetails') or {}
        microformat = try_get(
            player_response,
            lambda x: x['microformat']['playerMicroformatRenderer'],
            dict) or {}
        video_title = video_details.get('title') \
            or get_text(microformat.get('title')) \
            or search_meta(['og:title', 'twitter:title', 'title'])
        video_description = video_details.get('shortDescription')

        if not smuggled_data.get('force_singlefeed', False):
            if not self._downloader.params.get('noplaylist'):
                multifeed_metadata_list = try_get(
                    player_response,
                    lambda x: x['multicamera']['playerLegacyMulticameraRenderer']['metadataList'],
                    compat_str)
                if multifeed_metadata_list:
                    entries = []
                    feed_ids = []
                    for feed in multifeed_metadata_list.split(','):
                        # Unquote should take place before split on comma (,) since textual
                        # fields may contain comma as well (see
                        # https://github.com/ytdl-org/youtube-dl/issues/8536)
                        feed_data = compat_parse_qs(
                            compat_urllib_parse_unquote_plus(feed))

                        def feed_entry(name):
                            return try_get(
                                feed_data, lambda x: x[name][0], compat_str)

                        feed_id = feed_entry('id')
                        if not feed_id:
                            continue
                        feed_title = feed_entry('title')
                        title = video_title
                        if feed_title:
                            title += ' (%s)' % feed_title
                        entries.append({
                            '_type': 'url_transparent',
                            'ie_key': 'Youtube',
                            'url': smuggle_url(
                                base_url + 'watch?v=' + feed_data['id'][0],
                                {'force_singlefeed': True}),
                            'title': title,
                        })
                        feed_ids.append(feed_id)
                    self.to_screen(
                        'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
                        % (', '.join(feed_ids), video_id))
                    return self.playlist_result(
                        entries, video_id, video_title, video_description)
            else:
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        formats = []
        itags = []
        itag_qualities = {}
        q = qualities(['tiny', 'small', 'medium', 'large', 'hd720', 'hd1080', 'hd1440', 'hd2160', 'hd2880', 'highres'])
        CHUNK_SIZE = 10 << 20

        streaming_data = player_response.get('streamingData') or {}
        streaming_formats = streaming_data.get('formats') or []
        streaming_formats.extend(streaming_data.get('adaptiveFormats') or [])

        def build_fragments(f):
            return LazyList({
                'url': update_url_query(f['url'], {
                    'range': '{0}-{1}'.format(range_start, min(range_start + CHUNK_SIZE - 1, f['filesize']))
                })
            } for range_start in range(0, f['filesize'], CHUNK_SIZE))

        for fmt in streaming_formats:
            if fmt.get('targetDurationSec') or fmt.get('drmFamilies'):
                continue

            itag = str_or_none(fmt.get('itag'))
            quality = fmt.get('quality')
            if itag and quality:
                itag_qualities[itag] = quality
            # FORMAT_STREAM_TYPE_OTF(otf=1) requires downloading the init fragment
            # (adding `&sq=0` to the URL) and parsing emsg box to determine the
            # number of fragment that would subsequently requested with (`&sq=N`)
            if fmt.get('type') == 'FORMAT_STREAM_TYPE_OTF':
                continue

            fmt_url = fmt.get('url')
            if not fmt_url:
                sc = compat_parse_qs(fmt.get('signatureCipher'))
                fmt_url = url_or_none(try_get(sc, lambda x: x['url'][0]))
                encrypted_sig = try_get(sc, lambda x: x['s'][0])
                if not (sc and fmt_url and encrypted_sig):
                    continue
                if not player_url:
                    player_url = self._extract_player_url(webpage)
                if not player_url:
                    continue
                signature = self._decrypt_signature(sc['s'][0], video_id, player_url)
                sp = try_get(sc, lambda x: x['sp'][0]) or 'signature'
                fmt_url += '&' + sp + '=' + signature

            if itag:
                itags.append(itag)
            tbr = float_or_none(
                fmt.get('averageBitrate') or fmt.get('bitrate'), 1000)
            dct = {
                'asr': int_or_none(fmt.get('audioSampleRate')),
                'filesize': int_or_none(fmt.get('contentLength')),
                'format_id': itag,
                'format_note': fmt.get('qualityLabel') or quality,
                'fps': int_or_none(fmt.get('fps')),
                'height': int_or_none(fmt.get('height')),
                'quality': q(quality),
                'tbr': tbr,
                'url': fmt_url,
                'width': fmt.get('width'),
            }
            mimetype = fmt.get('mimeType')
            if mimetype:
                mobj = re.match(
                    r'((?:[^/]+)/(?:[^;]+))(?:;\s*codecs="([^"]+)")?', mimetype)
                if mobj:
                    dct['ext'] = mimetype2ext(mobj.group(1))
                    dct.update(parse_codecs(mobj.group(2)))
            single_stream = 'none' in (dct.get(c) for c in ('acodec', 'vcodec'))
            if single_stream and dct.get('ext'):
                dct['container'] = dct['ext'] + '_dash'
            if single_stream or itag == '17':
                # avoid Youtube throttling
                dct.update({
                    'protocol': 'http_dash_segments',
                    'fragments': build_fragments(dct),
                } if dct['filesize'] else {
                    'downloader_options': {'http_chunk_size': CHUNK_SIZE}  # No longer useful?
                })

            formats.append(dct)

        hls_manifest_url = streaming_data.get('hlsManifestUrl')
        if hls_manifest_url:
            for f in self._extract_m3u8_formats(
                    hls_manifest_url, video_id, 'mp4', fatal=False):
                itag = self._search_regex(
                    r'/itag/(\d+)', f['url'], 'itag', default=None)
                if itag:
                    f['format_id'] = itag
                formats.append(f)

        if self._downloader.params.get('youtube_include_dash_manifest', True):
            dash_manifest_url = streaming_data.get('dashManifestUrl')
            if dash_manifest_url:
                for f in self._extract_mpd_formats(
                        dash_manifest_url, video_id, fatal=False):
                    itag = f['format_id']
                    if itag in itags:
                        continue
                    if itag in itag_qualities:
                        f['quality'] = q(itag_qualities[itag])
                    filesize = int_or_none(self._search_regex(
                        r'/clen/(\d+)', f.get('fragment_base_url')
                        or f['url'], 'file size', default=None))
                    if filesize:
                        f['filesize'] = filesize
                    formats.append(f)

        if not formats:
            if streaming_data.get('licenseInfos'):
                raise ExtractorError(
                    'This video is DRM protected.', expected=True)
            pemr = try_get(
                playability_status,
                lambda x: x['errorScreen']['playerErrorMessageRenderer'],
                dict) or {}
            reason = get_text(pemr.get('reason')) or playability_status.get('reason')
            subreason = pemr.get('subreason')
            if subreason:
                subreason = clean_html(get_text(subreason))
                if subreason == 'The uploader has not made this video available in your country.':
                    countries = microformat.get('availableCountries')
                    if not countries:
                        regions_allowed = search_meta('regionsAllowed')
                        countries = regions_allowed.split(',') if regions_allowed else None
                    self.raise_geo_restricted(
                        subreason, countries)
                reason += '\n' + subreason
            if reason:
                raise ExtractorError(reason, expected=True)

        self._sort_formats(formats)

        keywords = video_details.get('keywords') or []
        if not keywords and webpage:
            keywords = [
                unescapeHTML(m.group('content'))
                for m in re.finditer(self._meta_regex('og:video:tag'), webpage)]
        for keyword in keywords:
            if keyword.startswith('yt:stretch='):
                mobj = re.search(r'(\d+)\s*:\s*(\d+)', keyword)
                if mobj:
                    # NB: float is intentional for forcing float division
                    w, h = (float(v) for v in mobj.groups())
                    if w > 0 and h > 0:
                        ratio = w / h
                        for f in formats:
                            if f.get('vcodec') != 'none':
                                f['stretched_ratio'] = ratio
                        break

        thumbnails = []
        for container in (video_details, microformat):
            for thumbnail in try_get(
                    container,
                    lambda x: x['thumbnail']['thumbnails'], list) or []:
                thumbnail_url = url_or_none(thumbnail.get('url'))
                if not thumbnail_url:
                    continue
                thumbnails.append({
                    'height': int_or_none(thumbnail.get('height')),
                    'url': update_url(thumbnail_url, query=None, fragment=None),
                    'width': int_or_none(thumbnail.get('width')),
                })
            if thumbnails:
                break
        else:
            thumbnail = search_meta(['og:image', 'twitter:image'])
            if thumbnail:
                thumbnails = [{'url': thumbnail}]

        category = microformat.get('category') or search_meta('genre')
        channel_id = self._extract_channel_id(
            webpage, videodetails=video_details, metadata=microformat)
        duration = int_or_none(
            video_details.get('lengthSeconds')
            or microformat.get('lengthSeconds')) \
            or parse_duration(search_meta('duration'))
        is_live = video_details.get('isLive')

        owner_profile_url = self._yt_urljoin(self._extract_author_var(
            webpage, 'url', videodetails=video_details, metadata=microformat))

        uploader = self._extract_author_var(
            webpage, 'name', videodetails=video_details, metadata=microformat)

        if not player_url:
            player_url = self._extract_player_url(webpage)
        self._unthrottle_format_urls(video_id, player_url, formats)

        info = {
            'id': video_id,
            'title': self._live_title(video_title) if is_live else video_title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': video_description,
            'upload_date': unified_strdate(
                microformat.get('uploadDate')
                or search_meta('uploadDate')),
            'uploader': uploader,
            'channel_id': channel_id,
            'duration': duration,
            'view_count': int_or_none(
                video_details.get('viewCount')
                or microformat.get('viewCount')
                or search_meta('interactionCount')),
            'average_rating': float_or_none(video_details.get('averageRating')),
            'age_limit': 18 if (
                microformat.get('isFamilySafe') is False
                or search_meta('isFamilyFriendly') == 'false'
                or search_meta('og:restrictions:age') == '18+') else 0,
            'webpage_url': webpage_url,
            'categories': [category] if category else None,
            'tags': keywords,
            'is_live': is_live,
        }

        pctr = try_get(
            player_response,
            lambda x: x['captions']['playerCaptionsTracklistRenderer'], dict)
        if pctr:
            def process_language(container, base_url, lang_code, query):
                lang_subs = []
                for fmt in self._SUBTITLE_FORMATS:
                    query.update({
                        'fmt': fmt,
                    })
                    lang_subs.append({
                        'ext': fmt,
                        'url': update_url_query(base_url, query),
                    })
                container[lang_code] = lang_subs

            subtitles = {}
            for caption_track in (pctr.get('captionTracks') or []):
                base_url = caption_track.get('baseUrl')
                if not base_url:
                    continue
                if caption_track.get('kind') != 'asr':
                    lang_code = caption_track.get('languageCode')
                    if not lang_code:
                        continue
                    process_language(
                        subtitles, base_url, lang_code, {})
                    continue
                automatic_captions = {}
                for translation_language in (pctr.get('translationLanguages') or []):
                    translation_language_code = translation_language.get('languageCode')
                    if not translation_language_code:
                        continue
                    process_language(
                        automatic_captions, base_url, translation_language_code,
                        {'tlang': translation_language_code})
                info['automatic_captions'] = automatic_captions
            info['subtitles'] = subtitles

        parsed_url = compat_urllib_parse_urlparse(url)
        for component in [parsed_url.fragment, parsed_url.query]:
            query = compat_parse_qs(component)
            for k, v in query.items():
                for d_k, s_ks in [('start', ('start', 't')), ('end', ('end',))]:
                    d_k += '_time'
                    if d_k not in info and k in s_ks:
                        info[d_k] = parse_duration(query[k][0])

        if video_description:
            # Youtube Music Auto-generated description
            mobj = re.search(r'(?s)(?P<track>[^·\n]+)·(?P<artist>[^\n]+)\n+(?P<album>[^\n]+)(?:.+?℗\s*(?P<release_year>\d{4})(?!\d))?(?:.+?Released on\s*:\s*(?P<release_date>\d{4}-\d{2}-\d{2}))?(.+?\nArtist\s*:\s*(?P<clean_artist>[^\n]+))?.+\nAuto-generated by YouTube\.\s*$', video_description)
            if mobj:
                release_year = mobj.group('release_year')
                release_date = mobj.group('release_date')
                if release_date:
                    release_date = release_date.replace('-', '')
                    if not release_year:
                        release_year = release_date[:4]
                info.update({
                    'album': mobj.group('album'.strip()),
                    'artist': mobj.group('clean_artist') or ', '.join(a.strip() for a in mobj.group('artist').split('·')),
                    'track': mobj.group('track').strip(),
                    'release_date': release_date,
                    'release_year': int_or_none(release_year),
                })

        initial_data = None
        if webpage:
            initial_data = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_DATA_RE, video_id,
                'yt initial data')
        if not initial_data:
            initial_data = self._call_api(
                'next', {'videoId': video_id}, video_id, fatal=False)

        if initial_data:
            chapters = self._extract_chapters_from_json(
                initial_data, video_id, duration)
            if not chapters:
                for engagment_pannel in (initial_data.get('engagementPanels') or []):
                    contents = try_get(
                        engagment_pannel, lambda x: x['engagementPanelSectionListRenderer']['content']['macroMarkersListRenderer']['contents'],
                        list)
                    if not contents:
                        continue

                    def chapter_time(mmlir):
                        return parse_duration(
                            get_text(mmlir.get('timeDescription')))

                    chapters = []
                    for next_num, content in enumerate(contents, start=1):
                        mmlir = content.get('macroMarkersListItemRenderer') or {}
                        start_time = chapter_time(mmlir)
                        end_time = chapter_time(try_get(
                            contents, lambda x: x[next_num]['macroMarkersListItemRenderer'])) \
                            if next_num < len(contents) else duration
                        if start_time is None or end_time is None:
                            continue
                        chapters.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'title': get_text(mmlir.get('title')),
                        })
                    if chapters:
                        break
            if chapters:
                info['chapters'] = chapters

            contents = try_get(
                initial_data,
                lambda x: x['contents']['twoColumnWatchNextResults']['results']['results']['contents'],
                list) or []
            if not info['channel_id']:
                channel_id = self._extract_channel_id('', renderers=contents)
            if not info['uploader']:
                info['uploader'] = self._extract_author_var('', 'name', renderers=contents)
            if not owner_profile_url:
                owner_profile_url = self._yt_urljoin(self._extract_author_var('', 'url', renderers=contents))

            for content in contents:
                vpir = content.get('videoPrimaryInfoRenderer')
                if vpir:
                    stl = vpir.get('superTitleLink')
                    if stl:
                        stl = get_text(stl)
                        if try_get(
                                vpir,
                                lambda x: x['superTitleIcon']['iconType']) == 'LOCATION_PIN':
                            info['location'] = stl
                        else:
                            # •? doesn't match, but [•]? does; \xa0 = non-breaking space
                            mobj = re.search(r'([^\xa0\s].*?)[\xa0\s]*S(\d+)[\xa0\s]*[•]?[\xa0\s]*E(\d+)', stl)
                            if mobj:
                                info.update({
                                    'series': mobj.group(1),
                                    'season_number': int(mobj.group(2)),
                                    'episode_number': int(mobj.group(3)),
                                })
                    for tlb in (try_get(
                            vpir,
                            lambda x: x['videoActions']['menuRenderer']['topLevelButtons'],
                            list) or []):
                        tbr = traverse_obj(tlb, ('segmentedLikeDislikeButtonRenderer', 'likeButton', 'toggleButtonRenderer'), 'toggleButtonRenderer') or {}
                        for getter, regex in [(
                                lambda x: x['defaultText']['accessibility']['accessibilityData'],
                                r'(?P<count>[\d,]+)\s*(?P<type>(?:dis)?like)'), ([
                                    lambda x: x['accessibility'],
                                    lambda x: x['accessibilityData']['accessibilityData'],
                                ], r'(?P<type>(?:dis)?like) this video along with (?P<count>[\d,]+) other people')]:
                            label = (try_get(tbr, getter, dict) or {}).get('label')
                            if label:
                                mobj = re.match(regex, label)
                                if mobj:
                                    info[mobj.group('type') + '_count'] = str_to_int(mobj.group('count'))
                                    break
                    sbr_tooltip = try_get(
                        vpir, lambda x: x['sentimentBar']['sentimentBarRenderer']['tooltip'])
                    if sbr_tooltip:
                        # however dislike_count was hidden by YT, as if there could ever be dislikable content on YT
                        like_count, dislike_count = sbr_tooltip.split(' / ')
                        info.update({
                            'like_count': str_to_int(like_count),
                            'dislike_count': str_to_int(dislike_count),
                        })
                vsir = content.get('videoSecondaryInfoRenderer')
                if vsir:
                    rows = try_get(
                        vsir,
                        lambda x: x['metadataRowContainer']['metadataRowContainerRenderer']['rows'],
                        list) or []
                    multiple_songs = False
                    for row in rows:
                        if try_get(row, lambda x: x['metadataRowRenderer']['hasDividerLine']) is True:
                            multiple_songs = True
                            break
                    for row in rows:
                        mrr = row.get('metadataRowRenderer') or {}
                        mrr_title = mrr.get('title')
                        if not mrr_title:
                            continue
                        mrr_title = get_text(mrr['title'])
                        mrr_contents_text = get_text(mrr['contents'][0])
                        if mrr_title == 'License':
                            info['license'] = mrr_contents_text
                        elif not multiple_songs:
                            if mrr_title == 'Album':
                                info['album'] = mrr_contents_text
                            elif mrr_title == 'Artist':
                                info['artist'] = mrr_contents_text
                            elif mrr_title == 'Song':
                                info['track'] = mrr_contents_text

            # this is not extraction but spelunking!
            carousel_lockups = traverse_obj(
                initial_data,
                ('engagementPanels', Ellipsis, 'engagementPanelSectionListRenderer',
                 'content', 'structuredDescriptionContentRenderer', 'items', Ellipsis,
                 'videoDescriptionMusicSectionRenderer', 'carouselLockups', Ellipsis),
                expected_type=dict) or []
            # try to reproduce logic from metadataRowContainerRenderer above (if it still is)
            fields = (('ALBUM', 'album'), ('ARTIST', 'artist'), ('SONG', 'track'), ('LICENSES', 'license'))
            # multiple_songs ?
            if len(carousel_lockups) > 1:
                fields = fields[-1:]
            for info_row in traverse_obj(
                    carousel_lockups,
                    (0, 'carouselLockupRenderer', 'infoRows', Ellipsis, 'infoRowRenderer'),
                    expected_type=dict):
                row_title = traverse_obj(info_row, ('title', 'simpleText'))
                row_text = traverse_obj(info_row, 'defaultMetadata', 'expandedMetadata', expected_type=get_text)
                if not row_text:
                    continue
                for name, field in fields:
                    if name == row_title and not info.get(field):
                        info[field] = row_text

        for s_k, d_k in [('artist', 'creator'), ('track', 'alt_title')]:
            v = info.get(s_k)
            if v:
                info[d_k] = v

        self.mark_watched(video_id, player_response)

        return merge_dicts(
            info, {
                'uploader_id': self._extract_uploader_id(owner_profile_url),
                'uploader_url': owner_profile_url,
                'channel_id': channel_id,
                'channel_url': channel_id and self._yt_urljoin('/channel/' + channel_id),
                'channel': info['uploader'],
            })


class YoutubeTabIE(YoutubeBaseInfoExtractor):
    IE_DESC = 'YouTube.com tab'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:\w+\.)?
                        (?:
                            youtube(?:kids)?\.com|
                            invidio\.us
                        )/
                        (?:
                            (?:channel|c|user|feed|hashtag)/|
                            (?:playlist|watch)\?.*?\blist=|
                            (?!(?:watch|embed|v|e|results)\b)
                        )
                        (?P<id>[^/?\#&]+)
                    '''
    IE_NAME = 'youtube:tab'

    _TESTS = [{
        # Shorts
        'url': 'https://www.youtube.com/@SuperCooperShorts/shorts',
        'playlist_mincount': 5,
        'info_dict': {
            'description': 'Short clips from Super Cooper Sundays!',
            'id': 'UCKMA8kHZ8bPYpnMNaUSxfEQ',
            'title': 'Super Cooper Shorts - Shorts',
            'uploader': 'Super Cooper Shorts',
            'uploader_id': '@SuperCooperShorts',
        }
    }, {
        # Channel that does not have a Shorts tab. Test should just download videos on Home tab instead
        'url': 'https://www.youtube.com/@emergencyawesome/shorts',
        'info_dict': {
            'description': 'md5:592c080c06fef4de3c902c4a8eecd850',
            'id': 'UCDiFRMQWpcp8_KD4vwIVicw',
            'title': 'Emergency Awesome - Home',
        },
        'playlist_mincount': 5,
        'skip': 'new test page needed to replace `Emergency Awesome - Shorts`',
    }, {
        # playlists, multipage
        'url': 'https://www.youtube.com/c/ИгорьКлейнер/playlists?view=1&flow=grid',
        'playlist_mincount': 94,
        'info_dict': {
            'id': 'UCqj7Cz7revf5maW9g5pgNcg',
            'title': 'Igor Kleiner - Playlists',
            'description': 'md5:be97ee0f14ee314f1f002cf187166ee2',
            'uploader': 'Igor Kleiner',
            'uploader_id': '@IgorDataScience',
        },
    }, {
        # playlists, multipage, different order
        'url': 'https://www.youtube.com/user/igorkle1/playlists?view=1&sort=dd',
        'playlist_mincount': 94,
        'info_dict': {
            'id': 'UCqj7Cz7revf5maW9g5pgNcg',
            'title': 'Igor Kleiner - Playlists',
            'description': 'md5:be97ee0f14ee314f1f002cf187166ee2',
            'uploader': 'Igor Kleiner',
            'uploader_id': '@IgorDataScience',
        },
    }, {
        # playlists, series
        'url': 'https://www.youtube.com/c/3blue1brown/playlists?view=50&sort=dd&shelf_id=3',
        'playlist_mincount': 5,
        'info_dict': {
            'id': 'UCYO_jab_esuFRV4b17AJtAw',
            'title': '3Blue1Brown - Playlists',
            'description': 'md5:e1384e8a133307dd10edee76e875d62f',
            'uploader': '3Blue1Brown',
            'uploader_id': '@3blue1brown',
        },
    }, {
        # playlists, singlepage
        'url': 'https://www.youtube.com/user/ThirstForScience/playlists',
        'playlist_mincount': 4,
        'info_dict': {
            'id': 'UCAEtajcuhQ6an9WEzY9LEMQ',
            'title': 'ThirstForScience - Playlists',
            'description': 'md5:609399d937ea957b0f53cbffb747a14c',
            'uploader': 'ThirstForScience',
            'uploader_id': '@ThirstForScience',
        }
    }, {
        'url': 'https://www.youtube.com/c/ChristophLaimer/playlists',
        'only_matching': True,
    }, {
        # basic, single video playlist
        'url': 'https://www.youtube.com/playlist?list=PL4lCao7KL_QFVb7Iudeipvc2BCavECqzc',
        'info_dict': {
            'id': 'PL4lCao7KL_QFVb7Iudeipvc2BCavECqzc',
            'title': 'youtube-dl public playlist',
            'uploader': 'Sergey M.',
            'uploader_id': '@sergeym.6173',
            'channel_id': 'UCmlqkdCBesrv2Lak1mF_MxA',
        },
        'playlist_count': 1,
    }, {
        # empty playlist
        'url': 'https://www.youtube.com/playlist?list=PL4lCao7KL_QFodcLWhDpGCYnngnHtQ-Xf',
        'info_dict': {
            'id': 'PL4lCao7KL_QFodcLWhDpGCYnngnHtQ-Xf',
            'title': 'youtube-dl empty playlist',
            'uploader': 'Sergey M.',
            'uploader_id': '@sergeym.6173',
            'channel_id': 'UCmlqkdCBesrv2Lak1mF_MxA',
        },
        'playlist_count': 0,
    }, {
        # Home tab
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w/featured',
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'lex will - Home',
            'description': 'md5:2163c5d0ff54ed5f598d6a7e6211e488',
            'uploader': 'lex will',
            'uploader_id': '@lexwill718',
        },
        'playlist_mincount': 2,
    }, {
        # Videos tab
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w/videos',
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'lex will - Videos',
            'description': 'md5:2163c5d0ff54ed5f598d6a7e6211e488',
            'uploader': 'lex will',
            'uploader_id': '@lexwill718',
        },
        'playlist_mincount': 975,
    }, {
        # Videos tab, sorted by popular
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w/videos?view=0&sort=p&flow=grid',
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'lex will - Videos',
            'description': 'md5:2163c5d0ff54ed5f598d6a7e6211e488',
            'uploader': 'lex will',
            'uploader_id': '@lexwill718',
        },
        'playlist_mincount': 199,
    }, {
        # Playlists tab
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w/playlists',
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'lex will - Playlists',
            'description': 'md5:2163c5d0ff54ed5f598d6a7e6211e488',
            'uploader': 'lex will',
            'uploader_id': '@lexwill718',
        },
        'playlist_mincount': 17,
    }, {
        # Community tab
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w/community',
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'lex will - Community',
            'description': 'md5:2163c5d0ff54ed5f598d6a7e6211e488',
            'uploader': 'lex will',
            'uploader_id': '@lexwill718',
        },
        'playlist_mincount': 18,
    }, {
        # Channels tab
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w/channels',
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'lex will - Channels',
            'description': 'md5:2163c5d0ff54ed5f598d6a7e6211e488',
            'uploader': 'lex will',
            'uploader_id': '@lexwill718',
        },
        'playlist_mincount': 75,
    }, {
        'url': 'https://invidio.us/channel/UCmlqkdCBesrv2Lak1mF_MxA',
        'only_matching': True,
    }, {
        'url': 'https://www.youtubekids.com/channel/UCmlqkdCBesrv2Lak1mF_MxA',
        'only_matching': True,
    }, {
        'url': 'https://music.youtube.com/channel/UCmlqkdCBesrv2Lak1mF_MxA',
        'only_matching': True,
    }, {
        'note': 'Playlist with deleted videos (#651). As a bonus, the video #51 is also twice in this list.',
        'url': 'https://www.youtube.com/playlist?list=PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC',
        'info_dict': {
            'title': '29C3: Not my department',
            'id': 'PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC',
            'uploader': 'Christiaan008',
            'uploader_id': '@ChRiStIaAn008',
            'channel_id': 'UCEPzS1rYsrkqzSLNp76nrcg',
        },
        'playlist_count': 96,
    }, {
        'note': 'Large playlist',
        'url': 'https://www.youtube.com/playlist?list=UUBABnxM4Ar9ten8Mdjj1j0Q',
        'info_dict': {
            'title': 'Uploads from Cauchemar',
            'id': 'UUBABnxM4Ar9ten8Mdjj1j0Q',
            'uploader': 'Cauchemar',
            'uploader_id': '@Cauchemar89',
            'channel_id': 'UCBABnxM4Ar9ten8Mdjj1j0Q',
        },
        'playlist_mincount': 1123,
    }, {
        # even larger playlist, 8832 videos
        'url': 'http://www.youtube.com/user/NASAgovVideo/videos',
        'only_matching': True,
    }, {
        'note': 'Buggy playlist: the webpage has a "Load more" button but it doesn\'t have more videos',
        'url': 'https://www.youtube.com/playlist?list=UUXw-G3eDE9trcvY2sBMM_aA',
        'info_dict': {
            'title': 'Uploads from Interstellar Movie',
            'id': 'UUXw-G3eDE9trcvY2sBMM_aA',
            'uploader': 'Interstellar Movie',
            'uploader_id': '@InterstellarMovie',
            'channel_id': 'UCXw-G3eDE9trcvY2sBMM_aA',
        },
        'playlist_mincount': 21,
    }, {
        # https://github.com/ytdl-org/youtube-dl/issues/21844
        'url': 'https://www.youtube.com/playlist?list=PLzH6n4zXuckpfMu_4Ff8E7Z1behQks5ba',
        'info_dict': {
            'title': 'Data Analysis with Dr Mike Pound',
            'id': 'PLzH6n4zXuckpfMu_4Ff8E7Z1behQks5ba',
            'uploader': 'Computerphile',
            'uploader_id': '@Computerphile',
            'channel_id': 'UC9-y-6csu5WGm29I7JiwpnA',
        },
        'playlist_mincount': 11,
    }, {
        'url': 'https://invidio.us/playlist?list=PL4lCao7KL_QFVb7Iudeipvc2BCavECqzc',
        'only_matching': True,
    }, {
        # Playlist URL that does not actually serve a playlist
        'url': 'https://www.youtube.com/watch?v=FqZTN594JQw&list=PLMYEtVRpaqY00V9W81Cwmzp6N6vZqfUKD4',
        'info_dict': {
            'id': 'FqZTN594JQw',
            'ext': 'webm',
            'title': "Smiley's People 01 detective, Adventure Series, Action",
            'uploader': 'STREEM',
            'uploader_id': 'UCyPhqAZgwYWZfxElWVbVJng',
            'uploader_url': r're:https?://(?:www\.)?youtube\.com/channel/UCyPhqAZgwYWZfxElWVbVJng',
            'upload_date': '20150526',
            'license': 'Standard YouTube License',
            'description': 'md5:507cdcb5a49ac0da37a920ece610be80',
            'categories': ['People & Blogs'],
            'tags': list,
            'view_count': int,
            'like_count': int,
        },
        'params': {
            'skip_download': True,
        },
        'skip': 'This video is not available.',
        'add_ie': [YoutubeIE.ie_key()],
    }, {
        'url': 'https://www.youtubekids.com/watch?v=Agk7R8I8o5U&list=PUZ6jURNr1WQZCNHF0ao-c0g',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?v=MuAGGZNfUkU&list=RDMM',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/channel/UCoMdktPbSTixAyNGwb-UYkQ/live',
        'info_dict': {
            'id': r're:[\da-zA-Z_-]{8,}',
            'ext': 'mp4',
            'title': r're:(?s)[A-Z].{20,}',
            'uploader': 'Sky News',
            'uploader_id': '@SkyNews',
            'uploader_url': r're:https?://(?:www\.)?youtube\.com/@SkyNews',
            'upload_date': r're:\d{8}',
            'description': r're:(?s)(?:.*\n)+SUBSCRIBE to our YouTube channel for more videos: http://www\.youtube\.com/skynews *\n.*',
            'categories': ['News & Politics'],
            'tags': list,
            'like_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.youtube.com/user/TheYoungTurks/live',
        'info_dict': {
            'id': 'a48o2S1cPoo',
            'ext': 'mp4',
            'title': 'The Young Turks - Live Main Show',
            'uploader': 'The Young Turks',
            'uploader_id': 'TheYoungTurks',
            'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/TheYoungTurks',
            'upload_date': '20150715',
            'license': 'Standard YouTube License',
            'description': 'md5:438179573adcdff3c97ebb1ee632b891',
            'categories': ['News & Politics'],
            'tags': ['Cenk Uygur (TV Program Creator)', 'The Young Turks (Award-Winning Work)', 'Talk Show (TV Genre)'],
            'like_count': int,
        },
        'params': {
            'skip_download': True,
        },
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/channel/UC1yBKRuGpC1tSM73A0ZjYjQ/live',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/c/CommanderVideoHq/live',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/feed/trending',
        'only_matching': True,
    }, {
        # needs auth
        'url': 'https://www.youtube.com/feed/library',
        'only_matching': True,
    }, {
        # needs auth
        'url': 'https://www.youtube.com/feed/history',
        'only_matching': True,
    }, {
        # needs auth
        'url': 'https://www.youtube.com/feed/subscriptions',
        'only_matching': True,
    }, {
        # needs auth
        'url': 'https://www.youtube.com/feed/watch_later',
        'only_matching': True,
    }, {
        # no longer available?
        'url': 'https://www.youtube.com/feed/recommended',
        'only_matching': True,
    }, {
        # inline playlist with not always working continuations
        'url': 'https://www.youtube.com/watch?v=UC6u0Tct-Fo&list=PL36D642111D65BE7C',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/course?list=ECUl4u3cNGP61MdtwGTqZA0MreSaDybji8',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/course',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/zsecurity',
        'only_matching': True,
    }, {
        'url': 'http://www.youtube.com/NASAgovVideo/videos',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/TheYoungTurks/live',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/hashtag/cctv9',
        'info_dict': {
            'id': 'cctv9',
            'title': '#cctv9',
        },
        'playlist_mincount': 350,
    }, {
        'url': 'https://www.youtube.com/watch?list=PLW4dVinRY435CBE_JD3t-0SRXKfnZHS1P&feature=youtu.be&v=M9cJMXmQ_ZU',
        'only_matching': True,
    }, {
        'note': 'Search tab',
        'url': 'https://www.youtube.com/c/3blue1brown/search?query=linear%20algebra',
        'playlist_mincount': 20,
        'info_dict': {
            'id': 'UCYO_jab_esuFRV4b17AJtAw',
            'title': '3Blue1Brown - Search - linear algebra',
            'description': 'md5:e1384e8a133307dd10edee76e875d62f',
            'uploader': '3Blue1Brown',
            'uploader_id': '@3blue1brown',
            'channel_id': 'UCYO_jab_esuFRV4b17AJtAw',
        }
    }]

    @classmethod
    def suitable(cls, url):
        return not YoutubeIE.suitable(url) and super(
            YoutubeTabIE, cls).suitable(url)

    @staticmethod
    def _extract_grid_item_renderer(item):
        assert isinstance(item, dict)
        for key, renderer in item.items():
            if not key.startswith('grid') or not key.endswith('Renderer'):
                continue
            if not isinstance(renderer, dict):
                continue
            return renderer

    def _grid_entries(self, grid_renderer):
        for item in grid_renderer['items']:
            if not isinstance(item, dict):
                continue
            renderer = self._extract_grid_item_renderer(item)
            if not isinstance(renderer, dict):
                continue
            title = try_get(
                renderer, (lambda x: x['title']['runs'][0]['text'],
                           lambda x: x['title']['simpleText']), compat_str)
            # playlist
            playlist_id = renderer.get('playlistId')
            if playlist_id:
                yield self.url_result(
                    'https://www.youtube.com/playlist?list=%s' % playlist_id,
                    ie=YoutubeTabIE.ie_key(), video_id=playlist_id,
                    video_title=title)
                continue
            # video
            video_id = renderer.get('videoId')
            if video_id:
                yield self._extract_video(renderer)
                continue
            # channel
            channel_id = renderer.get('channelId')
            if channel_id:
                title = try_get(
                    renderer, lambda x: x['title']['simpleText'], compat_str)
                yield self.url_result(
                    'https://www.youtube.com/channel/%s' % channel_id,
                    ie=YoutubeTabIE.ie_key(), video_title=title)
                continue
            # generic endpoint URL support
            ep_url = urljoin('https://www.youtube.com/', try_get(
                renderer, lambda x: x['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url'],
                compat_str))
            if ep_url:
                for ie in (YoutubeTabIE, YoutubePlaylistIE, YoutubeIE):
                    if ie.suitable(ep_url):
                        yield self.url_result(
                            ep_url, ie=ie.ie_key(), video_id=ie._match_id(ep_url), video_title=title)
                        break

    def _shelf_entries_from_content(self, shelf_renderer):
        content = shelf_renderer.get('content')
        if not isinstance(content, dict):
            return
        renderer = content.get('gridRenderer')
        if renderer:
            # TODO: add support for nested playlists so each shelf is processed
            # as separate playlist
            # TODO: this includes only first N items
            for entry in self._grid_entries(renderer):
                yield entry
        renderer = content.get('horizontalListRenderer')
        if renderer:
            # TODO
            pass

    def _shelf_entries(self, shelf_renderer, skip_channels=False):
        ep = try_get(
            shelf_renderer, lambda x: x['endpoint']['commandMetadata']['webCommandMetadata']['url'],
            compat_str)
        shelf_url = urljoin('https://www.youtube.com', ep)
        if shelf_url:
            # Skipping links to another channels, note that checking for
            # endpoint.commandMetadata.webCommandMetadata.webPageTypwebPageType == WEB_PAGE_TYPE_CHANNEL
            # will not work
            if skip_channels and '/channels?' in shelf_url:
                return
            title = try_get(
                shelf_renderer, lambda x: x['title']['runs'][0]['text'], compat_str)
            yield self.url_result(shelf_url, video_title=title)
        # Shelf may not contain shelf URL, fallback to extraction from content
        for entry in self._shelf_entries_from_content(shelf_renderer):
            yield entry

    def _playlist_entries(self, video_list_renderer):
        for content in video_list_renderer['contents']:
            if not isinstance(content, dict):
                continue
            renderer = content.get('playlistVideoRenderer') or content.get('playlistPanelVideoRenderer')
            if not isinstance(renderer, dict):
                continue
            video_id = renderer.get('videoId')
            if not video_id:
                continue
            yield self._extract_video(renderer)

    def _video_entry(self, video_renderer):
        video_id = video_renderer.get('videoId')
        if video_id:
            return self._extract_video(video_renderer)

    def _post_thread_entries(self, post_thread_renderer):
        post_renderer = try_get(
            post_thread_renderer, lambda x: x['post']['backstagePostRenderer'], dict)
        if not post_renderer:
            return
        # video attachment
        video_renderer = try_get(
            post_renderer, lambda x: x['backstageAttachment']['videoRenderer'], dict)
        video_id = None
        if video_renderer:
            entry = self._video_entry(video_renderer)
            if entry:
                yield entry
        # inline video links
        runs = try_get(post_renderer, lambda x: x['contentText']['runs'], list) or []
        for run in runs:
            if not isinstance(run, dict):
                continue
            ep_url = try_get(
                run, lambda x: x['navigationEndpoint']['urlEndpoint']['url'], compat_str)
            if not ep_url:
                continue
            if not YoutubeIE.suitable(ep_url):
                continue
            ep_video_id = YoutubeIE._match_id(ep_url)
            if video_id == ep_video_id:
                continue
            yield self.url_result(ep_url, ie=YoutubeIE.ie_key(), video_id=video_id)

    def _post_thread_continuation_entries(self, post_thread_continuation):
        contents = post_thread_continuation.get('contents')
        if not isinstance(contents, list):
            return
        for content in contents:
            renderer = content.get('backstagePostThreadRenderer')
            if not isinstance(renderer, dict):
                continue
            for entry in self._post_thread_entries(renderer):
                yield entry

    def _rich_grid_entries(self, contents):
        for content in contents:
            video_renderer = try_get(
                content,
                (lambda x: x['richItemRenderer']['content']['videoRenderer'],
                 lambda x: x['richItemRenderer']['content']['reelItemRenderer']),
                dict)
            if video_renderer:
                entry = self._video_entry(video_renderer)
                if entry:
                    yield entry

    @staticmethod
    def _build_continuation_query(continuation, ctp=None):
        query = {
            'ctoken': continuation,
            'continuation': continuation,
        }
        if ctp:
            query['itct'] = ctp
        return query

    @staticmethod
    def _extract_next_continuation_data(renderer):
        next_continuation = try_get(
            renderer, lambda x: x['continuations'][0]['nextContinuationData'], dict)
        if not next_continuation:
            return
        continuation = next_continuation.get('continuation')
        if not continuation:
            return
        ctp = next_continuation.get('clickTrackingParams')
        return YoutubeTabIE._build_continuation_query(continuation, ctp)

    @classmethod
    def _extract_continuation(cls, renderer):
        next_continuation = cls._extract_next_continuation_data(renderer)
        if next_continuation:
            return next_continuation
        contents = []
        for key in ('contents', 'items'):
            contents.extend(try_get(renderer, lambda x: x[key], list) or [])
        for content in contents:
            if not isinstance(content, dict):
                continue
            continuation_ep = try_get(
                content, lambda x: x['continuationItemRenderer']['continuationEndpoint'],
                dict)
            if not continuation_ep:
                continue
            continuation = try_get(
                continuation_ep, lambda x: x['continuationCommand']['token'], compat_str)
            if not continuation:
                continue
            ctp = continuation_ep.get('clickTrackingParams')
            return YoutubeTabIE._build_continuation_query(continuation, ctp)

    def _entries(self, tab, item_id, webpage):
        tab_content = try_get(tab, lambda x: x['content'], dict)
        if not tab_content:
            return
        slr_renderer = try_get(tab_content, lambda x: x['sectionListRenderer'], dict)
        if slr_renderer:
            is_channels_tab = tab.get('title') == 'Channels'
            continuation = None
            slr_contents = try_get(slr_renderer, lambda x: x['contents'], list) or []
            for slr_content in slr_contents:
                if not isinstance(slr_content, dict):
                    continue
                is_renderer = try_get(slr_content, lambda x: x['itemSectionRenderer'], dict)
                if not is_renderer:
                    continue
                isr_contents = try_get(is_renderer, lambda x: x['contents'], list) or []
                for isr_content in isr_contents:
                    if not isinstance(isr_content, dict):
                        continue
                    renderer = isr_content.get('playlistVideoListRenderer')
                    if renderer:
                        for entry in self._playlist_entries(renderer):
                            yield entry
                        continuation = self._extract_continuation(renderer)
                        continue
                    renderer = isr_content.get('gridRenderer')
                    if renderer:
                        for entry in self._grid_entries(renderer):
                            yield entry
                        continuation = self._extract_continuation(renderer)
                        continue
                    renderer = isr_content.get('shelfRenderer')
                    if renderer:
                        for entry in self._shelf_entries(renderer, not is_channels_tab):
                            yield entry
                        continue
                    renderer = isr_content.get('backstagePostThreadRenderer')
                    if renderer:
                        for entry in self._post_thread_entries(renderer):
                            yield entry
                        continuation = self._extract_continuation(renderer)
                        continue
                    renderer = isr_content.get('videoRenderer')
                    if renderer:
                        entry = self._video_entry(renderer)
                        if entry:
                            yield entry

                if not continuation:
                    continuation = self._extract_continuation(is_renderer)
            if not continuation:
                continuation = self._extract_continuation(slr_renderer)
        else:
            rich_grid_renderer = tab_content.get('richGridRenderer')
            if not rich_grid_renderer:
                return
            for entry in self._rich_grid_entries(rich_grid_renderer.get('contents') or []):
                yield entry
            continuation = self._extract_continuation(rich_grid_renderer)

        ytcfg = self._extract_ytcfg(item_id, webpage)
        client_version = try_get(
            ytcfg, lambda x: x['INNERTUBE_CLIENT_VERSION'], compat_str) or '2.20210407.08.00'

        headers = {
            'x-youtube-client-name': '1',
            'x-youtube-client-version': client_version,
            'content-type': 'application/json',
        }

        context = try_get(ytcfg, lambda x: x['INNERTUBE_CONTEXT'], dict) or {
            'client': {
                'clientName': 'WEB',
                'clientVersion': client_version,
            }
        }
        visitor_data = try_get(context, lambda x: x['client']['visitorData'], compat_str)

        identity_token = self._extract_identity_token(ytcfg, webpage)
        if identity_token:
            headers['x-youtube-identity-token'] = identity_token

        data = {
            'context': context,
        }

        for page_num in itertools.count(1):
            if not continuation:
                break
            if visitor_data:
                headers['x-goog-visitor-id'] = visitor_data
            data['continuation'] = continuation['continuation']
            data['clickTracking'] = {
                'clickTrackingParams': continuation['itct']
            }
            count = 0
            retries = 3
            while count <= retries:
                try:
                    # Downloading page may result in intermittent 5xx HTTP error
                    # that is usually worked around with a retry
                    response = self._download_json(
                        'https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
                        None, 'Downloading page %d%s' % (page_num, ' (retry #%d)' % count if count else ''),
                        headers=headers, data=json.dumps(data).encode('utf8'))
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code in (500, 503):
                        count += 1
                        if count <= retries:
                            continue
                    raise
            if not response:
                break

            visitor_data = try_get(
                response, lambda x: x['responseContext']['visitorData'], compat_str) or visitor_data

            continuation_contents = try_get(
                response, lambda x: x['continuationContents'], dict)
            if continuation_contents:
                continuation_renderer = continuation_contents.get('playlistVideoListContinuation')
                if continuation_renderer:
                    for entry in self._playlist_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue
                continuation_renderer = continuation_contents.get('gridContinuation')
                if continuation_renderer:
                    for entry in self._grid_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue
                continuation_renderer = continuation_contents.get('itemSectionContinuation')
                if continuation_renderer:
                    for entry in self._post_thread_continuation_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue

            on_response_received = dict_get(response, ('onResponseReceivedActions', 'onResponseReceivedEndpoints'))
            continuation_items = try_get(
                on_response_received, lambda x: x[0]['appendContinuationItemsAction']['continuationItems'], list)
            if continuation_items:
                continuation_item = continuation_items[0]
                if not isinstance(continuation_item, dict):
                    continue
                renderer = self._extract_grid_item_renderer(continuation_item)
                if renderer:
                    grid_renderer = {'items': continuation_items}
                    for entry in self._grid_entries(grid_renderer):
                        yield entry
                    continuation = self._extract_continuation(grid_renderer)
                    continue
                renderer = continuation_item.get('playlistVideoRenderer') or continuation_item.get('itemSectionRenderer')
                if renderer:
                    video_list_renderer = {'contents': continuation_items}
                    for entry in self._playlist_entries(video_list_renderer):
                        yield entry
                    continuation = self._extract_continuation(video_list_renderer)
                    continue
                renderer = continuation_item.get('backstagePostThreadRenderer')
                if renderer:
                    continuation_renderer = {'contents': continuation_items}
                    for entry in self._post_thread_continuation_entries(continuation_renderer):
                        yield entry
                    continuation = self._extract_continuation(continuation_renderer)
                    continue
                renderer = continuation_item.get('richItemRenderer')
                if renderer:
                    for entry in self._rich_grid_entries(continuation_items):
                        yield entry
                    continuation = self._extract_continuation({'contents': continuation_items})
                    continue

            break

    @staticmethod
    def _extract_selected_tab(tabs):
        for tab in tabs:
            renderer = dict_get(tab, ('tabRenderer', 'expandableTabRenderer')) or {}
            if renderer.get('selected') is True:
                return renderer
        else:
            raise ExtractorError('Unable to find selected tab')

    def _extract_uploader(self, metadata, data):
        uploader = {}
        renderers = traverse_obj(data,
                                 ('sidebar', 'playlistSidebarRenderer', 'items'))
        uploader['channel_id'] = self._extract_channel_id('', metadata=metadata, renderers=renderers)
        uploader['uploader'] = (
            self._extract_author_var('', 'name', renderers=renderers)
            or self._extract_author_var('', 'name', metadata=metadata))
        uploader['uploader_url'] = self._yt_urljoin(
            self._extract_author_var('', 'url', metadata=metadata, renderers=renderers))
        uploader['uploader_id'] = self._extract_uploader_id(uploader['uploader_url'])
        uploader['channel'] = uploader['uploader']
        return uploader

    @staticmethod
    def _extract_alert(data):
        alerts = []
        for alert in try_get(data, lambda x: x['alerts'], list) or []:
            if not isinstance(alert, dict):
                continue
            alert_text = try_get(
                alert, lambda x: x['alertRenderer']['text'], dict)
            if not alert_text:
                continue
            text = try_get(
                alert_text,
                (lambda x: x['simpleText'], lambda x: x['runs'][0]['text']),
                compat_str)
            if text:
                alerts.append(text)
        return '\n'.join(alerts)

    def _extract_from_tabs(self, item_id, webpage, data, tabs):
        selected_tab = self._extract_selected_tab(tabs)
        renderer = try_get(
            data, lambda x: x['metadata']['channelMetadataRenderer'], dict)
        playlist_id = item_id
        title = description = None
        if renderer:
            channel_title = renderer.get('title') or item_id
            tab_title = selected_tab.get('title')
            title = channel_title or item_id
            if tab_title:
                title += ' - %s' % tab_title
            if selected_tab.get('expandedText'):
                title += ' - %s' % selected_tab['expandedText']
            description = renderer.get('description')
            playlist_id = renderer.get('externalId')
        else:
            renderer = try_get(
                data, lambda x: x['metadata']['playlistMetadataRenderer'], dict)
            if renderer:
                title = renderer.get('title')
            else:
                renderer = try_get(
                    data, lambda x: x['header']['hashtagHeaderRenderer'], dict)
                if renderer:
                    title = try_get(renderer, lambda x: x['hashtag']['simpleText'])
        playlist = self.playlist_result(
            self._entries(selected_tab, item_id, webpage),
            playlist_id=playlist_id, playlist_title=title,
            playlist_description=description)
        return merge_dicts(playlist, self._extract_uploader(renderer, data))

    def _extract_from_playlist(self, item_id, url, data, playlist):
        title = playlist.get('title') or try_get(
            data, lambda x: x['titleText']['simpleText'], compat_str)
        playlist_id = playlist.get('playlistId') or item_id
        # Inline playlist rendition continuation does not always work
        # at Youtube side, so delegating regular tab-based playlist URL
        # processing whenever possible.
        playlist_url = urljoin(url, try_get(
            playlist, lambda x: x['endpoint']['commandMetadata']['webCommandMetadata']['url'],
            compat_str))
        if playlist_url and playlist_url != url:
            return self.url_result(
                playlist_url, ie=YoutubeTabIE.ie_key(), video_id=playlist_id,
                video_title=title)
        return self.playlist_result(
            self._playlist_entries(playlist), playlist_id=playlist_id,
            playlist_title=title)

    def _extract_identity_token(self, ytcfg, webpage):
        if ytcfg:
            token = try_get(ytcfg, lambda x: x['ID_TOKEN'], compat_str)
            if token:
                return token
        return self._search_regex(
            r'\bID_TOKEN["\']\s*:\s*["\'](.+?)["\']', webpage,
            'identity token', default=None)

    def _real_extract(self, url):
        item_id = self._match_id(url)
        url = update_url(url, netloc='www.youtube.com')
        # Handle both video/playlist URLs
        qs = parse_qs(url)
        video_id = qs.get('v', [None])[0]
        playlist_id = qs.get('list', [None])[0]
        if video_id and playlist_id:
            if self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)
                return self.url_result(video_id, ie=YoutubeIE.ie_key(), video_id=video_id)
            self.to_screen('Downloading playlist %s - add --no-playlist to just download video %s' % (playlist_id, video_id))
        webpage = self._download_webpage(url, item_id)
        data = self._extract_yt_initial_data(item_id, webpage)
        tabs = try_get(
            data, lambda x: x['contents']['twoColumnBrowseResultsRenderer']['tabs'], list)
        if tabs:
            return self._extract_from_tabs(item_id, webpage, data, tabs)
        playlist = try_get(
            data, lambda x: x['contents']['twoColumnWatchNextResults']['playlist']['playlist'], dict)
        if playlist:
            return self._extract_from_playlist(item_id, url, data, playlist)
        # Fallback to video extraction if no playlist alike page is recognized.
        # First check for the current video then try the v attribute of URL query.
        video_id = try_get(
            data, lambda x: x['currentVideoEndpoint']['watchEndpoint']['videoId'],
            compat_str) or video_id
        if video_id:
            return self.url_result(video_id, ie=YoutubeIE.ie_key(), video_id=video_id)
        # Capture and output alerts
        alert = self._extract_alert(data)
        if alert:
            raise ExtractorError(alert, expected=True)
        # Failed to recognize
        raise ExtractorError('Unable to recognize tab page')


class YoutubePlaylistIE(InfoExtractor):
    IE_DESC = 'YouTube.com playlists'
    _VALID_URL = r'''(?x)(?:
                        (?:https?://)?
                        (?:\w+\.)?
                        (?:
                            (?:
                                youtube(?:kids)?\.com|
                                invidio\.us
                            )
                            /.*?\?.*?\blist=
                        )?
                        (?P<id>%(playlist_id)s)
                     )''' % {'playlist_id': YoutubeBaseInfoExtractor._PLAYLIST_ID_RE}
    IE_NAME = 'youtube:playlist'
    _TESTS = [{
        'note': 'issue #673',
        'url': 'PLBB231211A4F62143',
        'info_dict': {
            'title': '[OLD]Team Fortress 2 (Class-based LP)',
            'id': 'PLBB231211A4F62143',
            'uploader': 'Wickman',
            'uploader_id': '@WickmanVT',
            'channel_id': 'UCKSpbfbl5kRQpTdL7kMc-1Q',
        },
        'playlist_mincount': 29,
    }, {
        'url': 'PLtPgu7CB4gbY9oDN3drwC3cMbJggS7dKl',
        'info_dict': {
            'title': 'YDL_safe_search',
            'id': 'PLtPgu7CB4gbY9oDN3drwC3cMbJggS7dKl',
        },
        'playlist_count': 2,
        'skip': 'This playlist is private',
    }, {
        'note': 'embedded',
        'url': 'https://www.youtube.com/embed/videoseries?list=PL6IaIsEjSbf96XFRuNccS_RuEXwNdsoEu',
        # TODO: full playlist requires _reload_with_unavailable_videos()
        # 'playlist_count': 4,
        'playlist_mincount': 1,
        'info_dict': {
            'title': 'JODA15',
            'id': 'PL6IaIsEjSbf96XFRuNccS_RuEXwNdsoEu',
            'uploader': 'milan',
            'uploader_id': '@milan5503',
            'channel_id': 'UCEI1-PVPcYXjB73Hfelbmaw',
        }
    }, {
        'url': 'http://www.youtube.com/embed/_xDOZElKyNU?list=PLsyOSbh5bs16vubvKePAQ1x3PhKavfBIl',
        'playlist_mincount': 455,
        'info_dict': {
            'title': '2018 Chinese New Singles (11/6 updated)',
            'id': 'PLsyOSbh5bs16vubvKePAQ1x3PhKavfBIl',
            'uploader': 'LBK',
            'uploader_id': '@music_king',
            'channel_id': 'UC21nz3_MesPLqtDqwdvnoxA',
        }
    }, {
        'url': 'TLGGrESM50VT6acwMjAyMjAxNw',
        'only_matching': True,
    }, {
        # music album playlist
        'url': 'OLAK5uy_m4xAFdmMC5rX3Ji3g93pQe3hqLZw_9LhM',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        if YoutubeTabIE.suitable(url):
            return False
        if parse_qs(url).get('v', [None])[0]:
            return False
        return super(YoutubePlaylistIE, cls).suitable(url)

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        qs = parse_qs(url)
        if not qs:
            qs = {'list': playlist_id}
        return self.url_result(
            update_url_query('https://www.youtube.com/playlist', qs),
            ie=YoutubeTabIE.ie_key(), video_id=playlist_id)


class YoutubeYtBeIE(InfoExtractor):
    _VALID_URL = r'https?://youtu\.be/(?P<id>[0-9A-Za-z_-]{11})/*?.*?\blist=(?P<playlist_id>%(playlist_id)s)' % {'playlist_id': YoutubeBaseInfoExtractor._PLAYLIST_ID_RE}
    _TESTS = [{
        'url': 'https://youtu.be/yeWKywCrFtk?list=PL2qgrgXsNUG5ig9cat4ohreBjYLAPC0J5',
        'info_dict': {
            'id': 'yeWKywCrFtk',
            'ext': 'mp4',
            'title': 'Small Scale Baler and Braiding Rugs',
            'uploader': 'Backus-Page House Museum',
            'uploader_id': '@backuspagemuseum',
            'uploader_url': r're:https?://(?:www\.)?youtube\.com/@backuspagemuseum',
            'upload_date': '20161008',
            'description': 'md5:800c0c78d5eb128500bffd4f0b4f2e8a',
            'categories': ['Nonprofits & Activism'],
            'tags': list,
            'like_count': int,
        },
        'params': {
            'noplaylist': True,
            'skip_download': True,
        },
    }, {
        'url': 'https://youtu.be/uWyaPkt-VOI?list=PL9D9FC436B881BA21',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        playlist_id = mobj.group('playlist_id')
        return self.url_result(
            update_url_query('https://www.youtube.com/watch', {
                'v': video_id,
                'list': playlist_id,
                'feature': 'youtu.be',
            }), ie=YoutubeTabIE.ie_key(), video_id=playlist_id)


class YoutubeYtUserIE(InfoExtractor):
    _VALID_URL = r'ytuser:(?P<id>.+)'
    _TESTS = [{
        'url': 'ytuser:phihag',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        user_id = self._match_id(url)
        return self.url_result(
            'https://www.youtube.com/user/%s' % user_id,
            ie=YoutubeTabIE.ie_key(), video_id=user_id)


class YoutubeFavouritesIE(YoutubeBaseInfoExtractor):
    IE_NAME = 'youtube:favorites'
    IE_DESC = 'YouTube.com favourite videos, ":ytfav" for short (requires authentication)'
    _VALID_URL = r'https?://(?:www\.)?youtube\.com/my_favorites|:ytfav(?:ou?rites)?'
    _LOGIN_REQUIRED = True
    _TESTS = [{
        'url': ':ytfav',
        'only_matching': True,
    }, {
        'url': ':ytfavorites',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        return self.url_result(
            'https://www.youtube.com/playlist?list=LL',
            ie=YoutubeTabIE.ie_key())


class YoutubeSearchIE(SearchInfoExtractor, YoutubeBaseInfoExtractor):
    IE_DESC = 'YouTube.com searches'
    IE_NAME = 'youtube:search'
    _SEARCH_KEY = 'ytsearch'
    _SEARCH_PARAMS = 'EgIQAQ%3D%3D'  # Videos only
    _MAX_RESULTS = float('inf')
    _TESTS = [{
        'url': 'ytsearch10:youtube-dl test video',
        'playlist_count': 10,
        'info_dict': {
            'id': 'youtube-dl test video',
            'title': 'youtube-dl test video',
        }
    }]

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        entries = itertools.islice(self._search_results(query, self._SEARCH_PARAMS), 0, None if n == float('inf') else n)
        return self.playlist_result(entries, query, query)


class YoutubeSearchDateIE(YoutubeSearchIE):
    IE_NAME = YoutubeSearchIE.IE_NAME + ':date'
    _SEARCH_KEY = 'ytsearchdate'
    IE_DESC = 'YouTube.com searches, newest videos first'
    _SEARCH_PARAMS = 'CAISAhAB'  # Videos only, sorted by date
    _TESTS = [{
        'url': 'ytsearchdate10:youtube-dl test video',
        'playlist_count': 10,
        'info_dict': {
            'id': 'youtube-dl test video',
            'title': 'youtube-dl test video',
        }
    }]


class YoutubeSearchURLIE(YoutubeBaseInfoExtractor):
    IE_DESC = 'YouTube search URLs with sorting and filter support'
    IE_NAME = YoutubeSearchIE.IE_NAME + '_url'
    _VALID_URL = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?:[^&]+)(?:[&]|$)'
    _TESTS = [{
        'url': 'https://www.youtube.com/results?baz=bar&search_query=youtube-dl+test+video&filters=video&lclk=video',
        'playlist_mincount': 5,
        'info_dict': {
            'id': 'youtube-dl test video',
            'title': 'youtube-dl test video',
        },
        'params': {'playlistend': 5}
    }, {
        'url': 'https://www.youtube.com/results?q=test&sp=EgQIBBgB',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        qs = parse_qs(url)
        query = (qs.get('search_query') or qs.get('q'))[-1]
        params = qs.get('sp', ('',))[-1]
        return self.playlist_result(self._search_results(query, params), query, query)


class YoutubeFeedsInfoExtractor(YoutubeTabIE):
    """
    Base class for feed extractors
    Subclasses must define the _FEED_NAME property.
    """
    _LOGIN_REQUIRED = True

    @property
    def IE_NAME(self):
        return 'youtube:%s' % self._FEED_NAME

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        return self.url_result(
            'https://www.youtube.com/feed/%s' % self._FEED_NAME,
            ie=YoutubeTabIE.ie_key())


class YoutubeWatchLaterIE(InfoExtractor):
    IE_NAME = 'youtube:watchlater'
    IE_DESC = 'Youtube watch later list, ":ytwatchlater" for short (requires authentication)'
    _VALID_URL = r':ytwatchlater'
    _TESTS = [{
        'url': ':ytwatchlater',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        return self.url_result(
            'https://www.youtube.com/playlist?list=WL', ie=YoutubeTabIE.ie_key())


class YoutubeRecommendedIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'YouTube.com recommended videos, ":ytrec" for short (requires authentication)'
    _VALID_URL = r':ytrec(?:ommended)?'
    _FEED_NAME = 'recommended'
    _TESTS = [{
        'url': ':ytrec',
        'only_matching': True,
    }, {
        'url': ':ytrecommended',
        'only_matching': True,
    }]


class YoutubeSubscriptionsIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'YouTube.com subscriptions feed, "ytsubs" keyword (requires authentication)'
    _VALID_URL = r':ytsubs(?:criptions)?'
    _FEED_NAME = 'subscriptions'
    _TESTS = [{
        'url': ':ytsubs',
        'only_matching': True,
    }, {
        'url': ':ytsubscriptions',
        'only_matching': True,
    }]


class YoutubeHistoryIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'Youtube watch history, ":ythistory" for short (requires authentication)'
    _VALID_URL = r':ythistory'
    _FEED_NAME = 'history'
    _TESTS = [{
        'url': ':ythistory',
        'only_matching': True,
    }]


class YoutubeTruncatedURLIE(InfoExtractor):
    IE_NAME = 'youtube:truncated_url'
    IE_DESC = False  # Do not list
    _VALID_URL = r'''(?x)
        (?:https?://)?
        (?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie)?\.com/
        (?:watch\?(?:
            feature=[a-z_]+|
            annotation_id=annotation_[^&]+|
            x-yt-cl=[0-9]+|
            hl=[^&]*|
            t=[0-9]+
        )?
        |
            attribution_link\?a=[^&]+
        )
        $
    '''

    _TESTS = [{
        'url': 'https://www.youtube.com/watch?annotation_id=annotation_3951667041',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?x-yt-cl=84503534',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?feature=foo',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?hl=en-GB',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?t=2372',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        raise ExtractorError(
            'Did you forget to quote the URL? Remember that & is a meta '
            'character in most shells, so you want to put the URL in quotes, '
            'like  youtube-dl '
            '"https://www.youtube.com/watch?feature=foo&v=BaW_jenozKc" '
            ' or simply  youtube-dl BaW_jenozKc  .',
            expected=True)


class YoutubeTruncatedIDIE(InfoExtractor):
    IE_NAME = 'youtube:truncated_id'
    IE_DESC = False  # Do not list
    _VALID_URL = r'https?://(?:www\.)?youtube\.com/watch\?v=(?P<id>[0-9A-Za-z_-]{1,10})$'

    _TESTS = [{
        'url': 'https://www.youtube.com/watch?v=N_708QY7Ob',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        raise ExtractorError(
            'Incomplete YouTube ID %s. URL %s looks truncated.' % (video_id, url),
            expected=True)
