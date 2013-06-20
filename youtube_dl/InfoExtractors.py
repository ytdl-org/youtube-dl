#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import base64
import datetime
import itertools
import netrc
import os
import re
import socket
import time
import email.utils
import xml.etree.ElementTree
import random
import math
import operator
import hashlib
import binascii
import urllib

from .utils import *


class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information about the video (or videos) the URL refers to. This
    information includes the real video URL, the video title, author and
    others. The information is stored in a dictionary which is then
    passed to the FileDownloader. The FileDownloader processes this
    information possibly downloading the video to the file system, among
    other possible outcomes.

    The dictionaries must include the following fields:

    id:             Video identifier.
    url:            Final video URL.
    title:          Video title, unescaped.
    ext:            Video filename extension.

    The following fields are optional:

    format:         The video format, defaults to ext (used for --get-format)
    thumbnail:      Full URL to a video thumbnail image.
    description:    One-line video description.
    uploader:       Full name of the video uploader.
    upload_date:    Video upload date (YYYYMMDD).
    uploader_id:    Nickname or id of the video uploader.
    location:       Physical location of the video.
    player_url:     SWF Player URL (used for rtmpdump).
    subtitles:      The subtitle file contents.
    urlhandle:      [internal] The urlHandle to be used to download the file,
                    like returned by urllib.request.urlopen

    The fields should all be Unicode strings.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods and define a _VALID_URL regexp.
    Probably, they should also be added to the list of extractors.

    _real_extract() must return a *list* of information dictionaries as
    described above.

    Finally, the _WORKING attribute should be set to False for broken IEs
    in order to warn the users and skip the tests.
    """

    _ready = False
    _downloader = None
    _WORKING = True

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self.set_downloader(downloader)

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url) is not None

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        self.initialize()
        return self._real_extract(url)

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass

    @property
    def IE_NAME(self):
        return type(self).__name__[:-2]

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the response handle """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            self.to_screen(u'%s: %s' % (video_id, note))
        try:
            return compat_urllib_request.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if errnote is None:
                errnote = u'Unable to download webpage'
            raise ExtractorError(u'%s: %s' % (errnote, compat_str(err)), sys.exc_info()[2])

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns a tuple (page content as string, URL handle) """
        urlh = self._request_webpage(url_or_request, video_id, note, errnote)
        content_type = urlh.headers.get('Content-Type', '')
        m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
        if m:
            encoding = m.group(1)
        else:
            encoding = 'utf-8'
        webpage_bytes = urlh.read()
        if self._downloader.params.get('dump_intermediate_pages', False):
            try:
                url = url_or_request.get_full_url()
            except AttributeError:
                url = url_or_request
            self.to_screen(u'Dumping request to ' + url)
            dump = base64.b64encode(webpage_bytes).decode('ascii')
            self._downloader.to_screen(dump)
        content = webpage_bytes.decode(encoding, 'replace')
        return (content, urlh)

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the data of the page as a string """
        return self._download_webpage_handle(url_or_request, video_id, note, errnote)[0]

    def to_screen(self, msg):
        """Print msg to screen, prefixing it with '[ie_name]'"""
        self._downloader.to_screen(u'[%s] %s' % (self.IE_NAME, msg))

    def report_extraction(self, id_or_name):
        """Report information extraction."""
        self.to_screen(u'%s: Extracting information' % id_or_name)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self.to_screen(u'%s: Downloading webpage' % video_id)

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        self.to_screen(u'Confirming age')

    #Methods for following #608
    #They set the correct value of the '_type' key
    def video_result(self, video_info):
        """Returns a video"""
        video_info['_type'] = 'video'
        return video_info
    def url_result(self, url, ie=None):
        """Returns a url that points to a page that should be processed"""
        #TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        return video_info
    def playlist_result(self, entries, playlist_id=None, playlist_title=None):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        return video_info

    def _search_regex(self, pattern, string, name, default=None, fatal=True, flags=0):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        ExtractorError, depending on fatal, specifying the field name.
        """
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj: break

        if sys.stderr.isatty() and os.name != 'nt':
            _name = u'\033[0;34m%s\033[0m' % name
        else:
            _name = name

        if mobj:
            # return the first matching group
            return next(g for g in mobj.groups() if g is not None)
        elif default is not None:
            return default
        elif fatal:
            raise ExtractorError(u'Unable to extract %s' % _name)
        else:
            self._downloader.report_warning(u'unable to extract %s; '
                u'please report this issue on GitHub.' % _name)
            return None

    def _html_search_regex(self, pattern, string, name, default=None, fatal=True, flags=0):
        """
        Like _search_regex, but strips HTML tags and unescapes entities.
        """
        res = self._search_regex(pattern, string, name, default, fatal, flags)
        if res:
            return clean_html(res).strip()
        else:
            return res

class SearchInfoExtractor(InfoExtractor):
    """
    Base class for paged search queries extractors.
    They accept urls in the format _SEARCH_KEY(|all|[0-9]):{query}
    Instances should define _SEARCH_KEY and _MAX_RESULTS.
    """

    @classmethod
    def _make_valid_url(cls):
        return r'%s(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\s\S]+)' % cls._SEARCH_KEY

    @classmethod
    def suitable(cls, url):
        return re.match(cls._make_valid_url(), url) is not None

    def _real_extract(self, query):
        mobj = re.match(self._make_valid_url(), query)
        if mobj is None:
            raise ExtractorError(u'Invalid search query "%s"' % query)

        prefix = mobj.group('prefix')
        query = mobj.group('query')
        if prefix == '':
            return self._get_n_results(query, 1)
        elif prefix == 'all':
            return self._get_n_results(query, self._MAX_RESULTS)
        else:
            n = int(prefix)
            if n <= 0:
                raise ExtractorError(u'invalid download number %s for query "%s"' % (n, query))
            elif n > self._MAX_RESULTS:
                self._downloader.report_warning(u'%s returns max %i results (you requested %i)' % (self._SEARCH_KEY, self._MAX_RESULTS, n))
                n = self._MAX_RESULTS
            return self._get_n_results(query, n)

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        raise NotImplementedError("This method must be implemented by sublclasses")


class YoutubeIE(InfoExtractor):
    """Information extractor for youtube.com."""

    _VALID_URL = r"""^
                     (
                         (?:https?://)?                                       # http(s):// (optional)
                         (?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/|
                            tube\.majestyc\.net/)                             # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/)                               # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:watch(?:_popup)?(?:\.php)?)?              # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?&)?                                    # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         )?                                                   # optional -> youtube.com/xxxx is OK
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]+)                                         # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""
    _LANG_URL = r'https://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    _NETRC_MACHINE = 'youtube'
    # Listed in order of quality
    _available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '17', '13']
    _available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '17', '13']
    _video_extensions = {
        '13': '3gp',
        '17': 'mp4',
        '18': 'mp4',
        '22': 'mp4',
        '37': 'mp4',
        '38': 'video', # You actually don't know if this will be MOV, AVI or whatever
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',
    }
    _video_dimensions = {
        '5': '240x400',
        '6': '???',
        '13': '???',
        '17': '144x176',
        '18': '360x640',
        '22': '720x1280',
        '34': '360x640',
        '35': '480x854',
        '37': '1080x1920',
        '38': '3072x4096',
        '43': '360x640',
        '44': '480x854',
        '45': '720x1280',
        '46': '1080x1920',
    }
    IE_NAME = u'youtube'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        if YoutubePlaylistIE.suitable(url): return False
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def report_lang(self):
        """Report attempt to set language."""
        self.to_screen(u'Setting language')

    def report_login(self):
        """Report attempt to log in."""
        self.to_screen(u'Logging in')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self.to_screen(u'%s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Downloading video info webpage' % video_id)

    def report_video_subtitles_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Checking available subtitles' % video_id)

    def report_video_subtitles_request(self, video_id, sub_lang, format):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Downloading video subtitles for %s.%s' % (video_id, sub_lang, format))

    def report_video_subtitles_available(self, video_id, sub_lang_list):
        """Report available subtitles."""
        sub_lang = ",".join(list(sub_lang_list.keys()))
        self.to_screen(u'%s: Available subtitles for video: %s' % (video_id, sub_lang))

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self.to_screen(u'%s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        self.to_screen(u'%s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        self.to_screen(u'RTMP download detected')

    def _get_available_subtitles(self, video_id):
        self.report_video_subtitles_download(video_id)
        request = compat_urllib_request.Request('http://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id)
        try:
            sub_list = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            return (u'unable to download video subtitles: %s' % compat_str(err), None)
        sub_lang_list = re.findall(r'name="([^"]*)"[^>]+lang_code="([\w\-]+)"', sub_list)
        sub_lang_list = dict((l[1], l[0]) for l in sub_lang_list)
        if not sub_lang_list:
            return (u'video doesn\'t have subtitles', None)
        return sub_lang_list

    def _list_available_subtitles(self, video_id):
        sub_lang_list = self._get_available_subtitles(video_id)
        self.report_video_subtitles_available(video_id, sub_lang_list)

    def _request_subtitle(self, sub_lang, sub_name, video_id, format):
        """
        Return tuple:
        (error_message, sub_lang, sub)
        """
        self.report_video_subtitles_request(video_id, sub_lang, format)
        params = compat_urllib_parse.urlencode({
            'lang': sub_lang,
            'name': sub_name,
            'v': video_id,
            'fmt': format,
        })
        url = 'http://www.youtube.com/api/timedtext?' + params
        try:
            sub = compat_urllib_request.urlopen(url).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            return (u'unable to download video subtitles: %s' % compat_str(err), None, None)
        if not sub:
            return (u'Did not fetch video subtitles', None, None)
        return (None, sub_lang, sub)

    def _request_automatic_caption(self, video_id, webpage):
        """We need the webpage for getting the captions url, pass it as an
           argument to speed up the process."""
        sub_lang = self._downloader.params.get('subtitleslang')
        sub_format = self._downloader.params.get('subtitlesformat')
        self.to_screen(u'%s: Looking for automatic captions' % video_id)
        mobj = re.search(r';ytplayer.config = ({.*?});', webpage)
        err_msg = u'Couldn\'t find automatic captions for "%s"' % sub_lang
        if mobj is None:
            return [(err_msg, None, None)]
        player_config = json.loads(mobj.group(1))
        try:
            args = player_config[u'args']
            caption_url = args[u'ttsurl']
            timestamp = args[u'timestamp']
            params = compat_urllib_parse.urlencode({
                'lang': 'en',
                'tlang': sub_lang,
                'fmt': sub_format,
                'ts': timestamp,
                'kind': 'asr',
            })
            subtitles_url = caption_url + '&' + params
            sub = self._download_webpage(subtitles_url, video_id, u'Downloading automatic captions')
            return [(None, sub_lang, sub)]
        except KeyError:
            return [(err_msg, None, None)]

    def _extract_subtitle(self, video_id):
        """
        Return a list with a tuple:
        [(error_message, sub_lang, sub)]
        """
        sub_lang_list = self._get_available_subtitles(video_id)
        sub_format = self._downloader.params.get('subtitlesformat')
        if  isinstance(sub_lang_list,tuple): #There was some error, it didn't get the available subtitles
            return [(sub_lang_list[0], None, None)]
        if self._downloader.params.get('subtitleslang', False):
            sub_lang = self._downloader.params.get('subtitleslang')
        elif 'en' in sub_lang_list:
            sub_lang = 'en'
        else:
            sub_lang = list(sub_lang_list.keys())[0]
        if not sub_lang in sub_lang_list:
            return [(u'no closed captions found in the specified language "%s"' % sub_lang, None, None)]

        subtitle = self._request_subtitle(sub_lang, sub_lang_list[sub_lang].encode('utf-8'), video_id, sub_format)
        return [subtitle]

    def _extract_all_subtitles(self, video_id):
        sub_lang_list = self._get_available_subtitles(video_id)
        sub_format = self._downloader.params.get('subtitlesformat')
        if  isinstance(sub_lang_list,tuple): #There was some error, it didn't get the available subtitles
            return [(sub_lang_list[0], None, None)]
        subtitles = []
        for sub_lang in sub_lang_list:
            subtitle = self._request_subtitle(sub_lang, sub_lang_list[sub_lang].encode('utf-8'), video_id, sub_format)
            subtitles.append(subtitle)
        return subtitles

    def _print_formats(self, formats):
        print('Available formats:')
        for x in formats:
            print('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'flv'), self._video_dimensions.get(x, '???')))

    def _real_initialize(self):
        if self._downloader is None:
            return

        username = None
        password = None
        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get('username', None) is not None:
            username = downloader_params['username']
            password = downloader_params['password']
        elif downloader_params.get('usenetrc', False):
            try:
                info = netrc.netrc().authenticators(self._NETRC_MACHINE)
                if info is not None:
                    username = info[0]
                    password = info[2]
                else:
                    raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
            except (IOError, netrc.NetrcParseError) as err:
                self._downloader.report_warning(u'parsing .netrc: %s' % compat_str(err))
                return

        # Set language
        request = compat_urllib_request.Request(self._LANG_URL)
        try:
            self.report_lang()
            compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to set language: %s' % compat_str(err))
            return

        # No authentication to be performed
        if username is None:
            return

        request = compat_urllib_request.Request(self._LOGIN_URL)
        try:
            login_page = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to fetch login page: %s' % compat_str(err))
            return

        galx = None
        dsh = None
        match = re.search(re.compile(r'<input.+?name="GALX".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          galx = match.group(1)

        match = re.search(re.compile(r'<input.+?name="dsh".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          dsh = match.group(1)

        # Log in
        login_form_strs = {
                u'continue': u'https://www.youtube.com/signin?action_handle_signin=true&feature=sign_in_button&hl=en_US&nomobiletemp=1',
                u'Email': username,
                u'GALX': galx,
                u'Passwd': password,
                u'PersistentCookie': u'yes',
                u'_utf8': u'霱',
                u'bgresponse': u'js_disabled',
                u'checkConnection': u'',
                u'checkedDomains': u'youtube',
                u'dnConn': u'',
                u'dsh': dsh,
                u'pstMsg': u'0',
                u'rmShown': u'1',
                u'secTok': u'',
                u'signIn': u'Sign in',
                u'timeStmp': u'',
                u'service': u'youtube',
                u'uilel': u'3',
                u'hl': u'en_US',
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k,v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')
        request = compat_urllib_request.Request(self._LOGIN_URL, login_data)
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
            if re.search(r'(?i)<form[^>]* id="gaia_loginform"', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username or password')
                return
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return

        # Confirm age
        age_form = {
                'next_url':     '/',
                'action_confirm':   'Confirm',
                }
        request = compat_urllib_request.Request(self._AGE_URL, compat_urllib_parse.urlencode(age_form))
        try:
            self.report_age_confirmation()
            age_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to confirm age: %s' % compat_str(err))

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _real_extract(self, url):
        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = 'https://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self._extract_id(url)

        # Get video webpage
        self.report_video_webpage_download(video_id)
        url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
        request = compat_urllib_request.Request(url)
        try:
            video_webpage_bytes = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video webpage: %s' % compat_str(err))

        video_webpage = video_webpage_bytes.decode('utf-8', 'ignore')

        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = None

        # Get video info
        self.report_video_info_webpage_download(video_id)
        for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
            video_info_url = ('https://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                    % (video_id, el_type))
            video_info_webpage = self._download_webpage(video_info_url, video_id,
                                    note=False,
                                    errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
            if 'token' in video_info:
                break
        if 'token' not in video_info:
            if 'reason' in video_info:
                raise ExtractorError(u'YouTube said: %s' % video_info['reason'][0])
            else:
                raise ExtractorError(u'"token" parameter not in video info for unknown reason')

        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            raise ExtractorError(u'"rental" videos not supported')

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            raise ExtractorError(u'Unable to extract uploader name')
        video_uploader = compat_urllib_parse.unquote_plus(video_info['author'][0])

        # uploader_id
        video_uploader_id = None
        mobj = re.search(r'<link itemprop="url" href="http://www.youtube.com/(?:user|channel)/([^"]+)">', video_webpage)
        if mobj is not None:
            video_uploader_id = mobj.group(1)
        else:
            self._downloader.report_warning(u'unable to extract uploader nickname')

        # title
        if 'title' not in video_info:
            raise ExtractorError(u'Unable to extract video title')
        video_title = compat_urllib_parse.unquote_plus(video_info['title'][0])

        # thumbnail image
        if 'thumbnail_url' not in video_info:
            self._downloader.report_warning(u'unable to extract video thumbnail')
            video_thumbnail = ''
        else:   # don't panic if we can't find it
            video_thumbnail = compat_urllib_parse.unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = None
        mobj = re.search(r'id="eow-date.*?>(.*?)</span>', video_webpage, re.DOTALL)
        if mobj is not None:
            upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
            upload_date = unified_strdate(upload_date)

        # description
        video_description = get_element_by_id("eow-description", video_webpage)
        if video_description:
            video_description = clean_html(video_description)
        else:
            fd_mobj = re.search(r'<meta name="description" content="([^"]+)"', video_webpage)
            if fd_mobj:
                video_description = unescapeHTML(fd_mobj.group(1))
            else:
                video_description = u''

        # subtitles
        video_subtitles = None

        if self._downloader.params.get('writesubtitles', False):
            video_subtitles = self._extract_subtitle(video_id)
            if video_subtitles:
                (sub_error, sub_lang, sub) = video_subtitles[0]
                if sub_error:
                    # We try with the automatic captions
                    video_subtitles = self._request_automatic_caption(video_id, video_webpage)
                    (sub_error_auto, sub_lang, sub) = video_subtitles[0]
                    if sub is not None:
                        pass
                    else:
                        # We report the original error
                        self._downloader.report_error(sub_error)

        if self._downloader.params.get('allsubtitles', False):
            video_subtitles = self._extract_all_subtitles(video_id)
            for video_subtitle in video_subtitles:
                (sub_error, sub_lang, sub) = video_subtitle
                if sub_error:
                    self._downloader.report_error(sub_error)

        if self._downloader.params.get('listsubtitles', False):
            sub_lang_list = self._list_available_subtitles(video_id)
            return

        if 'length_seconds' not in video_info:
            self._downloader.report_warning(u'unable to extract video duration')
            video_duration = ''
        else:
            video_duration = compat_urllib_parse.unquote_plus(video_info['length_seconds'][0])

        # token
        video_token = compat_urllib_parse.unquote_plus(video_info['token'][0])

        # Decide which formats to download
        req_format = self._downloader.params.get('format', None)

        if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
            self.report_rtmp_download()
            video_url_list = [(None, video_info['conn'][0])]
        elif 'url_encoded_fmt_stream_map' in video_info and len(video_info['url_encoded_fmt_stream_map']) >= 1:
            url_map = {}
            for url_data_str in video_info['url_encoded_fmt_stream_map'][0].split(','):
                url_data = compat_parse_qs(url_data_str)
                if 'itag' in url_data and 'url' in url_data:
                    url = url_data['url'][0] + '&signature=' + url_data['sig'][0]
                    if not 'ratebypass' in url: url += '&ratebypass=yes'
                    url_map[url_data['itag'][0]] = url

            format_limit = self._downloader.params.get('format_limit', None)
            available_formats = self._available_formats_prefer_free if self._downloader.params.get('prefer_free_formats', False) else self._available_formats
            if format_limit is not None and format_limit in available_formats:
                format_list = available_formats[available_formats.index(format_limit):]
            else:
                format_list = available_formats
            existing_formats = [x for x in format_list if x in url_map]
            if len(existing_formats) == 0:
                raise ExtractorError(u'no known formats available for video')
            if self._downloader.params.get('listformats', None):
                self._print_formats(existing_formats)
                return
            if req_format is None or req_format == 'best':
                video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
            elif req_format == 'worst':
                video_url_list = [(existing_formats[len(existing_formats)-1], url_map[existing_formats[len(existing_formats)-1]])] # worst quality
            elif req_format in ('-1', 'all'):
                video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
            else:
                # Specific formats. We pick the first in a slash-delimeted sequence.
                # For example, if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
                req_formats = req_format.split('/')
                video_url_list = None
                for rf in req_formats:
                    if rf in url_map:
                        video_url_list = [(rf, url_map[rf])]
                        break
                if video_url_list is None:
                    raise ExtractorError(u'requested format not available')
        else:
            raise ExtractorError(u'no conn or url_encoded_fmt_stream_map information found in video info')

        results = []
        for format_param, video_real_url in video_url_list:
            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')

            video_format = '{0} - {1}'.format(format_param if format_param else video_extension,
                                              self._video_dimensions.get(format_param, '???'))

            results.append({
                'id':       video_id,
                'url':      video_real_url,
                'uploader': video_uploader,
                'uploader_id': video_uploader_id,
                'upload_date':  upload_date,
                'title':    video_title,
                'ext':      video_extension,
                'format':   video_format,
                'thumbnail':    video_thumbnail,
                'description':  video_description,
                'player_url':   player_url,
                'subtitles':    video_subtitles,
                'duration':     video_duration
            })
        return results


class MetacafeIE(InfoExtractor):
    """Information Extractor for metacafe.com."""

    _VALID_URL = r'(?:http://)?(?:www\.)?metacafe\.com/watch/([^/]+)/([^/]+)/.*'
    _DISCLAIMER = 'http://www.metacafe.com/family_filter/'
    _FILTER_POST = 'http://www.metacafe.com/f/index.php?inputType=filter&controllerGroup=user'
    IE_NAME = u'metacafe'

    def report_disclaimer(self):
        """Report disclaimer retrieval."""
        self.to_screen(u'Retrieving disclaimer')

    def _real_initialize(self):
        # Retrieve disclaimer
        request = compat_urllib_request.Request(self._DISCLAIMER)
        try:
            self.report_disclaimer()
            disclaimer = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve disclaimer: %s' % compat_str(err))

        # Confirm age
        disclaimer_form = {
            'filters': '0',
            'submit': "Continue - I'm over 18",
            }
        request = compat_urllib_request.Request(self._FILTER_POST, compat_urllib_parse.urlencode(disclaimer_form))
        try:
            self.report_age_confirmation()
            disclaimer = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to confirm age: %s' % compat_str(err))

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group(1)

        # Check if video comes from YouTube
        mobj2 = re.match(r'^yt-(.*)$', video_id)
        if mobj2 is not None:
            return [self.url_result('http://www.youtube.com/watch?v=%s' % mobj2.group(1), 'Youtube')]

        # Retrieve video webpage to extract further information
        webpage = self._download_webpage('http://www.metacafe.com/watch/%s/' % video_id, video_id)

        # Extract URL, uploader and title from webpage
        self.report_extraction(video_id)
        mobj = re.search(r'(?m)&mediaURL=([^&]+)', webpage)
        if mobj is not None:
            mediaURL = compat_urllib_parse.unquote(mobj.group(1))
            video_extension = mediaURL[-3:]

            # Extract gdaKey if available
            mobj = re.search(r'(?m)&gdaKey=(.*?)&', webpage)
            if mobj is None:
                video_url = mediaURL
            else:
                gdaKey = mobj.group(1)
                video_url = '%s?__gda__=%s' % (mediaURL, gdaKey)
        else:
            mobj = re.search(r' name="flashvars" value="(.*?)"', webpage)
            if mobj is None:
                raise ExtractorError(u'Unable to extract media URL')
            vardict = compat_parse_qs(mobj.group(1))
            if 'mediaData' not in vardict:
                raise ExtractorError(u'Unable to extract media URL')
            mobj = re.search(r'"mediaURL":"(?P<mediaURL>http.*?)",(.*?)"key":"(?P<key>.*?)"', vardict['mediaData'][0])
            if mobj is None:
                raise ExtractorError(u'Unable to extract media URL')
            mediaURL = mobj.group('mediaURL').replace('\\/', '/')
            video_extension = mediaURL[-3:]
            video_url = '%s?__gda__=%s' % (mediaURL, mobj.group('key'))

        mobj = re.search(r'(?im)<title>(.*) - Video</title>', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract title')
        video_title = mobj.group(1).decode('utf-8')

        mobj = re.search(r'submitter=(.*?);', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract uploader nickname')
        video_uploader = mobj.group(1)

        return [{
            'id':       video_id.decode('utf-8'),
            'url':      video_url.decode('utf-8'),
            'uploader': video_uploader.decode('utf-8'),
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension.decode('utf-8'),
        }]

class DailymotionIE(InfoExtractor):
    """Information Extractor for Dailymotion"""

    _VALID_URL = r'(?i)(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/video/([^/]+)'
    IE_NAME = u'dailymotion'

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group(1).split('_')[0].split('?')[0]

        video_extension = 'mp4'

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url)
        request.add_header('Cookie', 'family_filter=off')
        webpage = self._download_webpage(request, video_id)

        # Extract URL, uploader and title from webpage
        self.report_extraction(video_id)
        mobj = re.search(r'\s*var flashvars = (.*)', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract media URL')
        flashvars = compat_urllib_parse.unquote(mobj.group(1))

        for key in ['hd1080URL', 'hd720URL', 'hqURL', 'sdURL', 'ldURL', 'video_url']:
            if key in flashvars:
                max_quality = key
                self.to_screen(u'Using %s' % key)
                break
        else:
            raise ExtractorError(u'Unable to extract video URL')

        mobj = re.search(r'"' + max_quality + r'":"(.+?)"', flashvars)
        if mobj is None:
            raise ExtractorError(u'Unable to extract video URL')

        video_url = compat_urllib_parse.unquote(mobj.group(1)).replace('\\/', '/')

        # TODO: support choosing qualities

        mobj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract title')
        video_title = unescapeHTML(mobj.group('title'))

        video_uploader = None
        video_uploader = self._search_regex([r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a>',
                                             # Looking for official user
                                             r'<(?:span|a) .*?rel="author".*?>([^<]+?)</'],
                                            webpage, 'video uploader')

        video_upload_date = None
        mobj = re.search(r'<div class="[^"]*uploaded_cont[^"]*" title="[^"]*">([0-9]{2})-([0-9]{2})-([0-9]{4})</div>', webpage)
        if mobj is not None:
            video_upload_date = mobj.group(3) + mobj.group(2) + mobj.group(1)

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'upload_date':  video_upload_date,
            'title':    video_title,
            'ext':      video_extension,
        }]


class PhotobucketIE(InfoExtractor):
    """Information extractor for photobucket.com."""

    # TODO: the original _VALID_URL was:
    # r'(?:http://)?(?:[a-z0-9]+\.)?photobucket\.com/.*[\?\&]current=(.*\.flv)'
    # Check if it's necessary to keep the old extracion process
    _VALID_URL = r'(?:http://)?(?:[a-z0-9]+\.)?photobucket\.com/.*(([\?\&]current=)|_)(?P<id>.*)\.(?P<ext>(flv)|(mp4))'
    IE_NAME = u'photobucket'

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('id')

        video_extension = mobj.group('ext')

        # Retrieve video webpage to extract further information
        webpage = self._download_webpage(url, video_id)

        # Extract URL, uploader, and title from webpage
        self.report_extraction(video_id)
        # We try first by looking the javascript code:
        mobj = re.search(r'Pb\.Data\.Shared\.put\(Pb\.Data\.Shared\.MEDIA, (?P<json>.*?)\);', webpage)
        if mobj is not None:
            info = json.loads(mobj.group('json'))
            return [{
                'id':       video_id,
                'url':      info[u'downloadUrl'],
                'uploader': info[u'username'],
                'upload_date':  datetime.date.fromtimestamp(info[u'creationDate']).strftime('%Y%m%d'),
                'title':    info[u'title'],
                'ext':      video_extension,
                'thumbnail': info[u'thumbUrl'],
            }]

        # We try looking in other parts of the webpage
        video_url = self._search_regex(r'<link rel="video_src" href=".*\?file=([^"]+)" />',
            webpage, u'video URL')

        mobj = re.search(r'<title>(.*) video by (.*) - Photobucket</title>', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract title')
        video_title = mobj.group(1).decode('utf-8')
        video_uploader = mobj.group(2).decode('utf-8')

        return [{
            'id':       video_id.decode('utf-8'),
            'url':      video_url.decode('utf-8'),
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension.decode('utf-8'),
        }]


class YahooIE(InfoExtractor):
    """Information extractor for screen.yahoo.com."""
    _VALID_URL = r'http://screen\.yahoo\.com/.*?-(?P<id>\d*?)\.html'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        m_id = re.search(r'YUI\.namespace\("Media"\)\.CONTENT_ID = "(?P<new_id>.+?)";', webpage)

        if m_id is None: 
            # TODO: Check which url parameters are required
            info_url = 'http://cosmos.bcst.yahoo.com/rest/v2/pops;lmsoverride=1;outputformat=mrss;cb=974419660;id=%s;rd=news.yahoo.com;datacontext=mdb;lg=KCa2IihxG3qE60vQ7HtyUy' % video_id
            webpage = self._download_webpage(info_url, video_id, u'Downloading info webpage')
            info_re = r'''<title><!\[CDATA\[(?P<title>.*?)\]\]></title>.*
                        <description><!\[CDATA\[(?P<description>.*?)\]\]></description>.*
                        <media:pubStart><!\[CDATA\[(?P<date>.*?)\ .*\]\]></media:pubStart>.*
                        <media:content\ medium="image"\ url="(?P<thumb>.*?)"\ name="LARGETHUMB"
                        '''
            self.report_extraction(video_id)
            m_info = re.search(info_re, webpage, re.VERBOSE|re.DOTALL)
            if m_info is None:
                raise ExtractorError(u'Unable to extract video info')
            video_title = m_info.group('title')
            video_description = m_info.group('description')
            video_thumb = m_info.group('thumb')
            video_date = m_info.group('date')
            video_date = datetime.datetime.strptime(video_date, '%m/%d/%Y').strftime('%Y%m%d')
    
            # TODO: Find a way to get mp4 videos
            rest_url = 'http://cosmos.bcst.yahoo.com/rest/v2/pops;element=stream;outputformat=mrss;id=%s;lmsoverride=1;bw=375;dynamicstream=1;cb=83521105;tech=flv,mp4;rd=news.yahoo.com;datacontext=mdb;lg=KCa2IihxG3qE60vQ7HtyUy' % video_id
            webpage = self._download_webpage(rest_url, video_id, u'Downloading video url webpage')
            m_rest = re.search(r'<media:content url="(?P<url>.*?)" path="(?P<path>.*?)"', webpage)
            video_url = m_rest.group('url')
            video_path = m_rest.group('path')
            if m_rest is None:
                raise ExtractorError(u'Unable to extract video url')

        else: # We have to use a different method if another id is defined
            long_id = m_id.group('new_id')
            info_url = 'http://video.query.yahoo.com/v1/public/yql?q=SELECT%20*%20FROM%20yahoo.media.video.streams%20WHERE%20id%3D%22' + long_id + '%22%20AND%20format%3D%22mp4%2Cflv%22%20AND%20protocol%3D%22rtmp%2Chttp%22%20AND%20plrs%3D%2286Gj0vCaSzV_Iuf6hNylf2%22%20AND%20acctid%3D%22389%22%20AND%20plidl%3D%22%22%20AND%20pspid%3D%22792700001%22%20AND%20offnetwork%3D%22false%22%20AND%20site%3D%22ivy%22%20AND%20lang%3D%22en-US%22%20AND%20region%3D%22US%22%20AND%20override%3D%22none%22%3B&env=prod&format=json&callback=YUI.Env.JSONP.yui_3_8_1_1_1368368376830_335'
            webpage = self._download_webpage(info_url, video_id, u'Downloading info json')
            json_str = re.search(r'YUI.Env.JSONP.yui.*?\((.*?)\);', webpage).group(1)
            info = json.loads(json_str)
            res = info[u'query'][u'results'][u'mediaObj'][0]
            stream = res[u'streams'][0]
            video_path = stream[u'path']
            video_url = stream[u'host']
            meta = res[u'meta']
            video_title = meta[u'title']
            video_description = meta[u'description']
            video_thumb = meta[u'thumbnail']
            video_date = None # I can't find it

        info_dict = {
                     'id': video_id,
                     'url': video_url,
                     'play_path': video_path,
                     'title':video_title,
                     'description': video_description,
                     'thumbnail': video_thumb,
                     'upload_date': video_date,
                     'ext': 'flv',
                     }
        return info_dict

class VimeoIE(InfoExtractor):
    """Information extractor for vimeo.com."""

    # _VALID_URL matches Vimeo URLs
    _VALID_URL = r'(?P<proto>https?://)?(?:(?:www|player)\.)?vimeo(?P<pro>pro)?\.com/(?:(?:(?:groups|album)/[^/]+)|(?:.*?)/)?(?P<direct_link>play_redirect_hls\?clip_id=)?(?:videos?/)?(?P<id>[0-9]+)'
    IE_NAME = u'vimeo'

    def _real_extract(self, url, new_video=True):
        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('id')
        if not mobj.group('proto'):
            url = 'https://' + url
        if mobj.group('direct_link') or mobj.group('pro'):
            url = 'https://vimeo.com/' + video_id

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url, None, std_headers)
        webpage = self._download_webpage(request, video_id)

        # Now we begin extracting as much information as we can from what we
        # retrieved. First we extract the information common to all extractors,
        # and latter we extract those that are Vimeo specific.
        self.report_extraction(video_id)

        # Extract the config JSON
        try:
            config = webpage.split(' = {config:')[1].split(',assets:')[0]
            config = json.loads(config)
        except:
            if re.search('The creator of this video has not given you permission to embed it on this domain.', webpage):
                raise ExtractorError(u'The author has restricted the access to this video, try with the "--referer" option')
            else:
                raise ExtractorError(u'Unable to extract info section')

        # Extract title
        video_title = config["video"]["title"]

        # Extract uploader and uploader_id
        video_uploader = config["video"]["owner"]["name"]
        video_uploader_id = config["video"]["owner"]["url"].split('/')[-1] if config["video"]["owner"]["url"] else None

        # Extract video thumbnail
        video_thumbnail = config["video"]["thumbnail"]

        # Extract video description
        video_description = get_element_by_attribute("itemprop", "description", webpage)
        if video_description: video_description = clean_html(video_description)
        else: video_description = u''

        # Extract upload date
        video_upload_date = None
        mobj = re.search(r'<meta itemprop="dateCreated" content="(\d{4})-(\d{2})-(\d{2})T', webpage)
        if mobj is not None:
            video_upload_date = mobj.group(1) + mobj.group(2) + mobj.group(3)

        # Vimeo specific: extract request signature and timestamp
        sig = config['request']['signature']
        timestamp = config['request']['timestamp']

        # Vimeo specific: extract video codec and quality information
        # First consider quality, then codecs, then take everything
        # TODO bind to format param
        codecs = [('h264', 'mp4'), ('vp8', 'flv'), ('vp6', 'flv')]
        files = { 'hd': [], 'sd': [], 'other': []}
        for codec_name, codec_extension in codecs:
            if codec_name in config["video"]["files"]:
                if 'hd' in config["video"]["files"][codec_name]:
                    files['hd'].append((codec_name, codec_extension, 'hd'))
                elif 'sd' in config["video"]["files"][codec_name]:
                    files['sd'].append((codec_name, codec_extension, 'sd'))
                else:
                    files['other'].append((codec_name, codec_extension, config["video"]["files"][codec_name][0]))

        for quality in ('hd', 'sd', 'other'):
            if len(files[quality]) > 0:
                video_quality = files[quality][0][2]
                video_codec = files[quality][0][0]
                video_extension = files[quality][0][1]
                self.to_screen(u'%s: Downloading %s file at %s quality' % (video_id, video_codec.upper(), video_quality))
                break
        else:
            raise ExtractorError(u'No known codec found')

        video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=%s&type=moogaloop_local&embed_location=" \
                    %(video_id, sig, timestamp, video_quality, video_codec.upper())

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'uploader_id': video_uploader_id,
            'upload_date':  video_upload_date,
            'title':    video_title,
            'ext':      video_extension,
            'thumbnail':    video_thumbnail,
            'description':  video_description,
        }]


class ArteTvIE(InfoExtractor):
    """arte.tv information extractor."""

    _VALID_URL = r'(?:http://)?videos\.arte\.tv/(?:fr|de)/videos/.*'
    _LIVE_URL = r'index-[0-9]+\.html$'

    IE_NAME = u'arte.tv'

    def fetch_webpage(self, url):
        request = compat_urllib_request.Request(url)
        try:
            self.report_download_webpage(url)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve video webpage: %s' % compat_str(err))
        except ValueError as err:
            raise ExtractorError(u'Invalid URL: %s' % url)
        return webpage

    def grep_webpage(self, url, regex, regexFlags, matchTuples):
        page = self.fetch_webpage(url)
        mobj = re.search(regex, page, regexFlags)
        info = {}

        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        for (i, key, err) in matchTuples:
            if mobj.group(i) is None:
                raise ExtractorError(err)
            else:
                info[key] = mobj.group(i)

        return info

    def extractLiveStream(self, url):
        video_lang = url.split('/')[-4]
        info = self.grep_webpage(
            url,
            r'src="(.*?/videothek_js.*?\.js)',
            0,
            [
                (1, 'url', u'Invalid URL: %s' % url)
            ]
        )
        http_host = url.split('/')[2]
        next_url = 'http://%s%s' % (http_host, compat_urllib_parse.unquote(info.get('url')))
        info = self.grep_webpage(
            next_url,
            r'(s_artestras_scst_geoFRDE_' + video_lang + '.*?)\'.*?' +
                '(http://.*?\.swf).*?' +
                '(rtmp://.*?)\'',
            re.DOTALL,
            [
                (1, 'path',   u'could not extract video path: %s' % url),
                (2, 'player', u'could not extract video player: %s' % url),
                (3, 'url',    u'could not extract video url: %s' % url)
            ]
        )
        video_url = u'%s/%s' % (info.get('url'), info.get('path'))

    def extractPlus7Stream(self, url):
        video_lang = url.split('/')[-3]
        info = self.grep_webpage(
            url,
            r'param name="movie".*?videorefFileUrl=(http[^\'"&]*)',
            0,
            [
                (1, 'url', u'Invalid URL: %s' % url)
            ]
        )
        next_url = compat_urllib_parse.unquote(info.get('url'))
        info = self.grep_webpage(
            next_url,
            r'<video lang="%s" ref="(http[^\'"&]*)' % video_lang,
            0,
            [
                (1, 'url', u'Could not find <video> tag: %s' % url)
            ]
        )
        next_url = compat_urllib_parse.unquote(info.get('url'))

        info = self.grep_webpage(
            next_url,
            r'<video id="(.*?)".*?>.*?' +
                '<name>(.*?)</name>.*?' +
                '<dateVideo>(.*?)</dateVideo>.*?' +
                '<url quality="hd">(.*?)</url>',
            re.DOTALL,
            [
                (1, 'id',    u'could not extract video id: %s' % url),
                (2, 'title', u'could not extract video title: %s' % url),
                (3, 'date',  u'could not extract video date: %s' % url),
                (4, 'url',   u'could not extract video url: %s' % url)
            ]
        )

        return {
            'id':           info.get('id'),
            'url':          compat_urllib_parse.unquote(info.get('url')),
            'uploader':     u'arte.tv',
            'upload_date':  unified_strdate(info.get('date')),
            'title':        info.get('title').decode('utf-8'),
            'ext':          u'mp4',
            'format':       u'NA',
            'player_url':   None,
        }

    def _real_extract(self, url):
        video_id = url.split('/')[-1]
        self.report_extraction(video_id)

        if re.search(self._LIVE_URL, video_id) is not None:
            self.extractLiveStream(url)
            return
        else:
            info = self.extractPlus7Stream(url)

        return [info]


class GenericIE(InfoExtractor):
    """Generic last-resort information extractor."""

    _VALID_URL = r'.*'
    IE_NAME = u'generic'

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        if not self._downloader.params.get('test', False):
            self._downloader.report_warning(u'Falling back on generic information extractor.')
        super(GenericIE, self).report_download_webpage(video_id)

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen(u'[redirect] Following redirect to %s' % new_url)

    def _test_redirect(self, url):
        """Check if it is a redirect, like url shorteners, in case return the new url."""
        class HeadRequest(compat_urllib_request.Request):
            def get_method(self):
                return "HEAD"

        class HEADRedirectHandler(compat_urllib_request.HTTPRedirectHandler):
            """
            Subclass the HTTPRedirectHandler to make it use our
            HeadRequest also on the redirected URL
            """
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if code in (301, 302, 303, 307):
                    newurl = newurl.replace(' ', '%20')
                    newheaders = dict((k,v) for k,v in req.headers.items()
                                      if k.lower() not in ("content-length", "content-type"))
                    return HeadRequest(newurl,
                                       headers=newheaders,
                                       origin_req_host=req.get_origin_req_host(),
                                       unverifiable=True)
                else:
                    raise compat_urllib_error.HTTPError(req.get_full_url(), code, msg, headers, fp)

        class HTTPMethodFallback(compat_urllib_request.BaseHandler):
            """
            Fallback to GET if HEAD is not allowed (405 HTTP error)
            """
            def http_error_405(self, req, fp, code, msg, headers):
                fp.read()
                fp.close()

                newheaders = dict((k,v) for k,v in req.headers.items()
                                  if k.lower() not in ("content-length", "content-type"))
                return self.parent.open(compat_urllib_request.Request(req.get_full_url(),
                                                 headers=newheaders,
                                                 origin_req_host=req.get_origin_req_host(),
                                                 unverifiable=True))

        # Build our opener
        opener = compat_urllib_request.OpenerDirector()
        for handler in [compat_urllib_request.HTTPHandler, compat_urllib_request.HTTPDefaultErrorHandler,
                        HTTPMethodFallback, HEADRedirectHandler,
                        compat_urllib_request.HTTPErrorProcessor, compat_urllib_request.HTTPSHandler]:
            opener.add_handler(handler())

        response = opener.open(HeadRequest(url))
        if response is None:
            raise ExtractorError(u'Invalid URL protocol')
        new_url = response.geturl()

        if url == new_url:
            return False

        self.report_following_redirect(new_url)
        return new_url

    def _real_extract(self, url):
        new_url = self._test_redirect(url)
        if new_url: return [self.url_result(new_url)]

        video_id = url.split('/')[-1]
        try:
            webpage = self._download_webpage(url, video_id)
        except ValueError as err:
            # since this is the last-resort InfoExtractor, if
            # this error is thrown, it'll be thrown here
            raise ExtractorError(u'Invalid URL: %s' % url)

        self.report_extraction(video_id)
        # Start with something easy: JW Player in SWFObject
        mobj = re.search(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit
            mobj = re.search(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit: JWPlayer JS loader
            mobj = re.search(r'[^A-Za-z0-9]?file:\s*["\'](http[^\'"&]*)', webpage)
        if mobj is None:
            # Try to find twitter cards info
            mobj = re.search(r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # It's possible that one of the regexes
        # matched, but returned an empty group:
        if mobj.group(1) is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_url = compat_urllib_parse.unquote(mobj.group(1))
        video_id = os.path.basename(video_url)

        # here's a fun little line of code for you:
        video_extension = os.path.splitext(video_id)[1][1:]
        video_id = os.path.splitext(video_id)[0]

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._html_search_regex(r'<title>(.*)</title>',
            webpage, u'video title')

        # video uploader is domain name
        video_uploader = self._search_regex(r'(?:https?://)?([^/]*)/.*',
            url, u'video uploader')

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension,
        }]


class YoutubeSearchIE(SearchInfoExtractor):
    """Information Extractor for YouTube search queries."""
    _API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc'
    _MAX_RESULTS = 1000
    IE_NAME = u'youtube:search'
    _SEARCH_KEY = 'ytsearch'

    def report_download_page(self, query, pagenum):
        """Report attempt to download search page with given number."""
        self._downloader.to_screen(u'[youtube] query "%s": Downloading page %s' % (query, pagenum))

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        video_ids = []
        pagenum = 0
        limit = n

        while (50 * pagenum) < limit:
            self.report_download_page(query, pagenum+1)
            result_url = self._API_URL % (compat_urllib_parse.quote_plus(query), (50*pagenum)+1)
            request = compat_urllib_request.Request(result_url)
            try:
                data = compat_urllib_request.urlopen(request).read().decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to download API page: %s' % compat_str(err))
            api_response = json.loads(data)['data']

            if not 'items' in api_response:
                raise ExtractorError(u'[youtube] No video results')

            new_ids = list(video['id'] for video in api_response['items'])
            video_ids += new_ids

            limit = min(n, api_response['totalItems'])
            pagenum += 1

        if len(video_ids) > n:
            video_ids = video_ids[:n]
        videos = [self.url_result('http://www.youtube.com/watch?v=%s' % id, 'Youtube') for id in video_ids]
        return self.playlist_result(videos, query)


class GoogleSearchIE(SearchInfoExtractor):
    """Information Extractor for Google Video search queries."""
    _MORE_PAGES_INDICATOR = r'id="pnnext" class="pn"'
    _MAX_RESULTS = 1000
    IE_NAME = u'video.google:search'
    _SEARCH_KEY = 'gvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        res = {
            '_type': 'playlist',
            'id': query,
            'entries': []
        }

        for pagenum in itertools.count(1):
            result_url = u'http://www.google.com/search?tbm=vid&q=%s&start=%s&hl=en' % (compat_urllib_parse.quote_plus(query), pagenum*10)
            webpage = self._download_webpage(result_url, u'gvsearch:' + query,
                                             note='Downloading result page ' + str(pagenum))

            for mobj in re.finditer(r'<h3 class="r"><a href="([^"]+)"', webpage):
                e = {
                    '_type': 'url',
                    'url': mobj.group(1)
                }
                res['entries'].append(e)

            if (pagenum * 10 > n) or not re.search(self._MORE_PAGES_INDICATOR, webpage):
                return res

class YahooSearchIE(SearchInfoExtractor):
    """Information Extractor for Yahoo! Video search queries."""

    _MAX_RESULTS = 1000
    IE_NAME = u'screen.yahoo:search'
    _SEARCH_KEY = 'yvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        res = {
            '_type': 'playlist',
            'id': query,
            'entries': []
        }
        for pagenum in itertools.count(0): 
            result_url = u'http://video.search.yahoo.com/search/?p=%s&fr=screen&o=js&gs=0&b=%d' % (compat_urllib_parse.quote_plus(query), pagenum * 30)
            webpage = self._download_webpage(result_url, query,
                                             note='Downloading results page '+str(pagenum+1))
            info = json.loads(webpage)
            m = info[u'm']
            results = info[u'results']

            for (i, r) in enumerate(results):
                if (pagenum * 30) +i >= n:
                    break
                mobj = re.search(r'(?P<url>screen\.yahoo\.com/.*?-\d*?\.html)"', r)
                e = self.url_result('http://' + mobj.group('url'), 'Yahoo')
                res['entries'].append(e)
            if (pagenum * 30 +i >= n) or (m[u'last'] >= (m[u'total'] -1 )):
                break

        return res


class YoutubePlaylistIE(InfoExtractor):
    """Information Extractor for YouTube playlists."""

    _VALID_URL = r"""(?:
                        (?:https?://)?
                        (?:\w+\.)?
                        youtube\.com/
                        (?:
                           (?:course|view_play_list|my_playlists|artist|playlist|watch)
                           \? (?:.*?&)*? (?:p|a|list)=
                        |  p/
                        )
                        ((?:PL|EC|UU)?[0-9A-Za-z-_]{10,})
                        .*
                     |
                        ((?:PL|EC|UU)[0-9A-Za-z-_]{10,})
                     )"""
    _TEMPLATE_URL = 'https://gdata.youtube.com/feeds/api/playlists/%s?max-results=%i&start-index=%i&v=2&alt=json&safeSearch=none'
    _MAX_RESULTS = 50
    IE_NAME = u'youtube:playlist'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _real_extract(self, url):
        # Extract playlist id
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # Download playlist videos from API
        playlist_id = mobj.group(1) or mobj.group(2)
        page_num = 1
        videos = []

        while True:
            url = self._TEMPLATE_URL % (playlist_id, self._MAX_RESULTS, self._MAX_RESULTS * (page_num - 1) + 1)
            page = self._download_webpage(url, playlist_id, u'Downloading page #%s' % page_num)

            try:
                response = json.loads(page)
            except ValueError as err:
                raise ExtractorError(u'Invalid JSON in API response: ' + compat_str(err))

            if 'feed' not in response:
                raise ExtractorError(u'Got a malformed response from YouTube API')
            playlist_title = response['feed']['title']['$t']
            if 'entry' not in response['feed']:
                # Number of videos is a multiple of self._MAX_RESULTS
                break

            videos += [ (entry['yt$position']['$t'], entry['content']['src'])
                        for entry in response['feed']['entry']
                        if 'content' in entry ]

            if len(response['feed']['entry']) < self._MAX_RESULTS:
                break
            page_num += 1

        videos = [v[1] for v in sorted(videos)]

        url_results = [self.url_result(url, 'Youtube') for url in videos]
        return [self.playlist_result(url_results, playlist_id, playlist_title)]


class YoutubeChannelIE(InfoExtractor):
    """Information Extractor for YouTube channels."""

    _VALID_URL = r"^(?:https?://)?(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/([0-9A-Za-z_-]+)"
    _TEMPLATE_URL = 'http://www.youtube.com/channel/%s/videos?sort=da&flow=list&view=0&page=%s&gl=US&hl=en'
    _MORE_PAGES_INDICATOR = 'yt-uix-load-more'
    _MORE_PAGES_URL = 'http://www.youtube.com/channel_ajax?action_load_more_videos=1&flow=list&paging=%s&view=0&sort=da&channel_id=%s'
    IE_NAME = u'youtube:channel'

    def extract_videos_from_page(self, page):
        ids_in_page = []
        for mobj in re.finditer(r'href="/watch\?v=([0-9A-Za-z_-]+)&?', page):
            if mobj.group(1) not in ids_in_page:
                ids_in_page.append(mobj.group(1))
        return ids_in_page

    def _real_extract(self, url):
        # Extract channel id
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # Download channel page
        channel_id = mobj.group(1)
        video_ids = []
        pagenum = 1

        url = self._TEMPLATE_URL % (channel_id, pagenum)
        page = self._download_webpage(url, channel_id,
                                      u'Downloading page #%s' % pagenum)

        # Extract video identifiers
        ids_in_page = self.extract_videos_from_page(page)
        video_ids.extend(ids_in_page)

        # Download any subsequent channel pages using the json-based channel_ajax query
        if self._MORE_PAGES_INDICATOR in page:
            while True:
                pagenum = pagenum + 1

                url = self._MORE_PAGES_URL % (pagenum, channel_id)
                page = self._download_webpage(url, channel_id,
                                              u'Downloading page #%s' % pagenum)

                page = json.loads(page)

                ids_in_page = self.extract_videos_from_page(page['content_html'])
                video_ids.extend(ids_in_page)

                if self._MORE_PAGES_INDICATOR  not in page['load_more_widget_html']:
                    break

        self._downloader.to_screen(u'[youtube] Channel %s: Found %i videos' % (channel_id, len(video_ids)))

        urls = ['http://www.youtube.com/watch?v=%s' % id for id in video_ids]
        url_entries = [self.url_result(url, 'Youtube') for url in urls]
        return [self.playlist_result(url_entries, channel_id)]


class YoutubeUserIE(InfoExtractor):
    """Information Extractor for YouTube users."""

    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/user/)|ytuser:)([A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'http://gdata.youtube.com/feeds/api/users/%s'
    _GDATA_PAGE_SIZE = 50
    _GDATA_URL = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d'
    _VIDEO_INDICATOR = r'/watch\?v=(.+?)[\<&]'
    IE_NAME = u'youtube:user'

    def _real_extract(self, url):
        # Extract username
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        username = mobj.group(1)

        # Download video ids using YouTube Data API. Result size per
        # query is limited (currently to 50 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        video_ids = []
        pagenum = 0

        while True:
            start_index = pagenum * self._GDATA_PAGE_SIZE + 1

            gdata_url = self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index)
            page = self._download_webpage(gdata_url, username,
                                          u'Downloading video ids from %d to %d' % (start_index, start_index + self._GDATA_PAGE_SIZE))

            # Extract video identifiers
            ids_in_page = []

            for mobj in re.finditer(self._VIDEO_INDICATOR, page):
                if mobj.group(1) not in ids_in_page:
                    ids_in_page.append(mobj.group(1))

            video_ids.extend(ids_in_page)

            # A little optimization - if current page is not
            # "full", ie. does not contain PAGE_SIZE video ids then
            # we can assume that this page is the last one - there
            # are no more ids on further pages - no need to query
            # again.

            if len(ids_in_page) < self._GDATA_PAGE_SIZE:
                break

            pagenum += 1

        urls = ['http://www.youtube.com/watch?v=%s' % video_id for video_id in video_ids]
        url_results = [self.url_result(url, 'Youtube') for url in urls]
        return [self.playlist_result(url_results, playlist_title = username)]


class BlipTVUserIE(InfoExtractor):
    """Information Extractor for blip.tv users."""

    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?blip\.tv/)|bliptvuser:)([^/]+)/*$'
    _PAGE_SIZE = 12
    IE_NAME = u'blip.tv:user'

    def _real_extract(self, url):
        # Extract username
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        username = mobj.group(1)

        page_base = 'http://m.blip.tv/pr/show_get_full_episode_list?users_id=%s&lite=0&esi=1'

        page = self._download_webpage(url, username, u'Downloading user page')
        mobj = re.search(r'data-users-id="([^"]+)"', page)
        page_base = page_base % mobj.group(1)


        # Download video ids using BlipTV Ajax calls. Result size per
        # query is limited (currently to 12 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        video_ids = []
        pagenum = 1

        while True:
            url = page_base + "&page=" + str(pagenum)
            page = self._download_webpage(url, username,
                                          u'Downloading video ids from page %d' % pagenum)

            # Extract video identifiers
            ids_in_page = []

            for mobj in re.finditer(r'href="/([^"]+)"', page):
                if mobj.group(1) not in ids_in_page:
                    ids_in_page.append(unescapeHTML(mobj.group(1)))

            video_ids.extend(ids_in_page)

            # A little optimization - if current page is not
            # "full", ie. does not contain PAGE_SIZE video ids then
            # we can assume that this page is the last one - there
            # are no more ids on further pages - no need to query
            # again.

            if len(ids_in_page) < self._PAGE_SIZE:
                break

            pagenum += 1

        urls = [u'http://blip.tv/%s' % video_id for video_id in video_ids]
        url_entries = [self.url_result(url, 'BlipTV') for url in urls]
        return [self.playlist_result(url_entries, playlist_title = username)]


class DepositFilesIE(InfoExtractor):
    """Information extractor for depositfiles.com"""

    _VALID_URL = r'(?:http://)?(?:\w+\.)?depositfiles\.com/(?:../(?#locale))?files/(.+)'

    def _real_extract(self, url):
        file_id = url.split('/')[-1]
        # Rebuild url in english locale
        url = 'http://depositfiles.com/en/files/' + file_id

        # Retrieve file webpage with 'Free download' button pressed
        free_download_indication = { 'gateway_result' : '1' }
        request = compat_urllib_request.Request(url, compat_urllib_parse.urlencode(free_download_indication))
        try:
            self.report_download_webpage(file_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve file webpage: %s' % compat_str(err))

        # Search for the real file URL
        mobj = re.search(r'<form action="(http://fileshare.+?)"', webpage)
        if (mobj is None) or (mobj.group(1) is None):
            # Try to figure out reason of the error.
            mobj = re.search(r'<strong>(Attention.*?)</strong>', webpage, re.DOTALL)
            if (mobj is not None) and (mobj.group(1) is not None):
                restriction_message = re.sub('\s+', ' ', mobj.group(1)).strip()
                raise ExtractorError(u'%s' % restriction_message)
            else:
                raise ExtractorError(u'Unable to extract download URL from: %s' % url)

        file_url = mobj.group(1)
        file_extension = os.path.splitext(file_url)[1][1:]

        # Search for file title
        file_title = self._search_regex(r'<b title="(.*?)">', webpage, u'title')

        return [{
            'id':       file_id.decode('utf-8'),
            'url':      file_url.decode('utf-8'),
            'uploader': None,
            'upload_date':  None,
            'title':    file_title,
            'ext':      file_extension.decode('utf-8'),
        }]


class FacebookIE(InfoExtractor):
    """Information Extractor for Facebook"""

    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?facebook\.com/(?:video/video|photo)\.php\?(?:.*?)v=(?P<ID>\d+)(?:.*)'
    _LOGIN_URL = 'https://login.facebook.com/login.php?m&next=http%3A%2F%2Fm.facebook.com%2Fhome.php&'
    _NETRC_MACHINE = 'facebook'
    IE_NAME = u'facebook'

    def report_login(self):
        """Report attempt to log in."""
        self.to_screen(u'Logging in')

    def _real_initialize(self):
        if self._downloader is None:
            return

        useremail = None
        password = None
        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get('username', None) is not None:
            useremail = downloader_params['username']
            password = downloader_params['password']
        elif downloader_params.get('usenetrc', False):
            try:
                info = netrc.netrc().authenticators(self._NETRC_MACHINE)
                if info is not None:
                    useremail = info[0]
                    password = info[2]
                else:
                    raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
            except (IOError, netrc.NetrcParseError) as err:
                self._downloader.report_warning(u'parsing .netrc: %s' % compat_str(err))
                return

        if useremail is None:
            return

        # Log in
        login_form = {
            'email': useremail,
            'pass': password,
            'login': 'Log+In'
            }
        request = compat_urllib_request.Request(self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read()
            if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username/password, or exceded login rate limit (~3/min). Check credentials or wait.')
                return
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('ID')

        url = 'https://www.facebook.com/video/video.php?v=%s' % video_id
        webpage = self._download_webpage(url, video_id)

        BEFORE = '{swf.addParam(param[0], param[1]);});\n'
        AFTER = '.forEach(function(variable) {swf.addVariable(variable[0], variable[1]);});'
        m = re.search(re.escape(BEFORE) + '(.*?)' + re.escape(AFTER), webpage)
        if not m:
            raise ExtractorError(u'Cannot parse data')
        data = dict(json.loads(m.group(1)))
        params_raw = compat_urllib_parse.unquote(data['params'])
        params = json.loads(params_raw)
        video_data = params['video_data'][0]
        video_url = video_data.get('hd_src')
        if not video_url:
            video_url = video_data['sd_src']
        if not video_url:
            raise ExtractorError(u'Cannot find video URL')
        video_duration = int(video_data['video_duration'])
        thumbnail = video_data['thumbnail_src']

        video_title = self._html_search_regex('<h2 class="uiHeaderTitle">([^<]+)</h2>',
            webpage, u'title')

        info = {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': 'mp4',
            'duration': video_duration,
            'thumbnail': thumbnail,
        }
        return [info]


class BlipTVIE(InfoExtractor):
    """Information extractor for blip.tv"""

    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?blip\.tv/((.+/)|(play/)|(api\.swf#))(.+)$'
    _URL_EXT = r'^.*\.([a-z0-9]+)$'
    IE_NAME = u'blip.tv'

    def report_direct_download(self, title):
        """Report information extraction."""
        self.to_screen(u'%s: Direct download detected' % title)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # See https://github.com/rg3/youtube-dl/issues/857
        api_mobj = re.match(r'http://a\.blip\.tv/api\.swf#(?P<video_id>[\d\w]+)', url)
        if api_mobj is not None:
            url = 'http://blip.tv/play/g_%s' % api_mobj.group('video_id')
        urlp = compat_urllib_parse_urlparse(url)
        if urlp.path.startswith('/play/'):
            request = compat_urllib_request.Request(url)
            response = compat_urllib_request.urlopen(request)
            redirecturl = response.geturl()
            rurlp = compat_urllib_parse_urlparse(redirecturl)
            file_id = compat_parse_qs(rurlp.fragment)['file'][0].rpartition('/')[2]
            url = 'http://blip.tv/a/a-' + file_id
            return self._real_extract(url)


        if '?' in url:
            cchar = '&'
        else:
            cchar = '?'
        json_url = url + cchar + 'skin=json&version=2&no_wrap=1'
        request = compat_urllib_request.Request(json_url)
        request.add_header('User-Agent', 'iTunes/10.6.1')
        self.report_extraction(mobj.group(1))
        info = None
        try:
            urlh = compat_urllib_request.urlopen(request)
            if urlh.headers.get('Content-Type', '').startswith('video/'): # Direct download
                basename = url.split('/')[-1]
                title,ext = os.path.splitext(basename)
                title = title.decode('UTF-8')
                ext = ext.replace('.', '')
                self.report_direct_download(title)
                info = {
                    'id': title,
                    'url': url,
                    'uploader': None,
                    'upload_date': None,
                    'title': title,
                    'ext': ext,
                    'urlhandle': urlh
                }
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'ERROR: unable to download video info webpage: %s' % compat_str(err))
        if info is None: # Regular URL
            try:
                json_code_bytes = urlh.read()
                json_code = json_code_bytes.decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to read video info webpage: %s' % compat_str(err))

            try:
                json_data = json.loads(json_code)
                if 'Post' in json_data:
                    data = json_data['Post']
                else:
                    data = json_data

                upload_date = datetime.datetime.strptime(data['datestamp'], '%m-%d-%y %H:%M%p').strftime('%Y%m%d')
                video_url = data['media']['url']
                umobj = re.match(self._URL_EXT, video_url)
                if umobj is None:
                    raise ValueError('Can not determine filename extension')
                ext = umobj.group(1)

                info = {
                    'id': data['item_id'],
                    'url': video_url,
                    'uploader': data['display_name'],
                    'upload_date': upload_date,
                    'title': data['title'],
                    'ext': ext,
                    'format': data['media']['mimeType'],
                    'thumbnail': data['thumbnailUrl'],
                    'description': data['description'],
                    'player_url': data['embedUrl'],
                    'user_agent': 'iTunes/10.6.1',
                }
            except (ValueError,KeyError) as err:
                raise ExtractorError(u'Unable to parse video information: %s' % repr(err))

        return [info]


class MyVideoIE(InfoExtractor):
    """Information Extractor for myvideo.de."""

    _VALID_URL = r'(?:http://)?(?:www\.)?myvideo\.de/watch/([0-9]+)/([^?/]+).*'
    IE_NAME = u'myvideo'

    # Original Code from: https://github.com/dersphere/plugin.video.myvideo_de.git
    # Released into the Public Domain by Tristan Fischer on 2013-05-19
    # https://github.com/rg3/youtube-dl/pull/842
    def __rc4crypt(self,data, key):
        x = 0
        box = list(range(256))
        for i in list(range(256)):
            x = (x + box[i] + compat_ord(key[i % len(key)])) % 256
            box[i], box[x] = box[x], box[i]
        x = 0
        y = 0
        out = ''
        for char in data:
            x = (x + 1) % 256
            y = (y + box[x]) % 256
            box[x], box[y] = box[y], box[x]
            out += chr(compat_ord(char) ^ box[(box[x] + box[y]) % 256])
        return out

    def __md5(self,s):
        return hashlib.md5(s).hexdigest().encode()

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'invalid URL: %s' % url)

        video_id = mobj.group(1)

        GK = (
          b'WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakpt'
          b'TW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3'
          b'TnpsbA0KTVRkbU1tSTRNdz09'
        )

        # Get video webpage
        webpage_url = 'http://www.myvideo.de/watch/%s' % video_id
        webpage = self._download_webpage(webpage_url, video_id)

        mobj = re.search('source src=\'(.+?)[.]([^.]+)\'', webpage)
        if mobj is not None:
            self.report_extraction(video_id)
            video_url = mobj.group(1) + '.flv'

            video_title = self._html_search_regex('<title>([^<]+)</title>',
                webpage, u'title')

            video_ext = self._search_regex('[.](.+?)$', video_url, u'extension')

            return [{
                'id':       video_id,
                'url':      video_url,
                'uploader': None,
                'upload_date':  None,
                'title':    video_title,
                'ext':      u'flv',
            }]

        # try encxml
        mobj = re.search('var flashvars={(.+?)}', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract video')

        params = {}
        encxml = ''
        sec = mobj.group(1)
        for (a, b) in re.findall('(.+?):\'(.+?)\',?', sec):
            if not a == '_encxml':
                params[a] = b
            else:
                encxml = compat_urllib_parse.unquote(b)
        if not params.get('domain'):
            params['domain'] = 'www.myvideo.de'
        xmldata_url = '%s?%s' % (encxml, compat_urllib_parse.urlencode(params))
        if 'flash_playertype=MTV' in xmldata_url:
            self._downloader.report_warning(u'avoiding MTV player')
            xmldata_url = (
                'http://www.myvideo.de/dynamic/get_player_video_xml.php'
                '?flash_playertype=D&ID=%s&_countlimit=4&autorun=yes'
            ) % video_id

        # get enc data
        enc_data = self._download_webpage(xmldata_url, video_id).split('=')[1]
        enc_data_b = binascii.unhexlify(enc_data)
        sk = self.__md5(
            base64.b64decode(base64.b64decode(GK)) +
            self.__md5(
                str(video_id).encode('utf-8')
            )
        )
        dec_data = self.__rc4crypt(enc_data_b, sk)

        # extracting infos
        self.report_extraction(video_id)

        video_url = None
        mobj = re.search('connectionurl=\'(.*?)\'', dec_data)
        if mobj:
            video_url = compat_urllib_parse.unquote(mobj.group(1))
            if 'myvideo2flash' in video_url:
                self._downloader.report_warning(u'forcing RTMPT ...')
                video_url = video_url.replace('rtmpe://', 'rtmpt://')

        if not video_url:
            # extract non rtmp videos
            mobj = re.search('path=\'(http.*?)\' source=\'(.*?)\'', dec_data)
            if mobj is None:
                raise ExtractorError(u'unable to extract url')
            video_url = compat_urllib_parse.unquote(mobj.group(1)) + compat_urllib_parse.unquote(mobj.group(2))

        video_file = self._search_regex('source=\'(.*?)\'', dec_data, u'video file')
        video_file = compat_urllib_parse.unquote(video_file)

        if not video_file.endswith('f4m'):
            ppath, prefix = video_file.split('.')
            video_playpath = '%s:%s' % (prefix, ppath)
            video_hls_playlist = ''
        else:
            video_playpath = ''
            video_hls_playlist = (
                video_filepath + video_file
            ).replace('.f4m', '.m3u8')

        video_swfobj = self._search_regex('swfobject.embedSWF\(\'(.+?)\'', webpage, u'swfobj')
        video_swfobj = compat_urllib_parse.unquote(video_swfobj)

        video_title = self._html_search_regex("<h1(?: class='globalHd')?>(.*?)</h1>",
            webpage, u'title')

        return [{
            'id':                 video_id,
            'url':                video_url,
            'tc_url':             video_url,
            'uploader':           None,
            'upload_date':        None,
            'title':              video_title,
            'ext':                u'flv',
            'play_path':          video_playpath,
            'video_file':         video_file,
            'video_hls_playlist': video_hls_playlist,
            'player_url':         video_swfobj,
        }]


class ComedyCentralIE(InfoExtractor):
    """Information extractor for The Daily Show and Colbert Report """

    # urls can be abbreviations like :thedailyshow or :colbert
    # urls for episodes like:
    # or urls for clips like: http://www.thedailyshow.com/watch/mon-december-10-2012/any-given-gun-day
    #                     or: http://www.colbertnation.com/the-colbert-report-videos/421667/november-29-2012/moon-shattering-news
    #                     or: http://www.colbertnation.com/the-colbert-report-collections/422008/festival-of-lights/79524
    _VALID_URL = r"""^(:(?P<shortname>tds|thedailyshow|cr|colbert|colbertnation|colbertreport)
                      |(https?://)?(www\.)?
                          (?P<showname>thedailyshow|colbertnation)\.com/
                         (full-episodes/(?P<episode>.*)|
                          (?P<clip>
                              (the-colbert-report-(videos|collections)/(?P<clipID>[0-9]+)/[^/]*/(?P<cntitle>.*?))
                              |(watch/(?P<date>[^/]*)/(?P<tdstitle>.*)))))
                     $"""

    _available_formats = ['3500', '2200', '1700', '1200', '750', '400']

    _video_extensions = {
        '3500': 'mp4',
        '2200': 'mp4',
        '1700': 'mp4',
        '1200': 'mp4',
        '750': 'mp4',
        '400': 'mp4',
    }
    _video_dimensions = {
        '3500': '1280x720',
        '2200': '960x540',
        '1700': '768x432',
        '1200': '640x360',
        '750': '512x288',
        '400': '384x216',
    }

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _print_formats(self, formats):
        print('Available formats:')
        for x in formats:
            print('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'mp4'), self._video_dimensions.get(x, '???')))


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        if mobj.group('shortname'):
            if mobj.group('shortname') in ('tds', 'thedailyshow'):
                url = u'http://www.thedailyshow.com/full-episodes/'
            else:
                url = u'http://www.colbertnation.com/full-episodes/'
            mobj = re.match(self._VALID_URL, url, re.VERBOSE)
            assert mobj is not None

        if mobj.group('clip'):
            if mobj.group('showname') == 'thedailyshow':
                epTitle = mobj.group('tdstitle')
            else:
                epTitle = mobj.group('cntitle')
            dlNewest = False
        else:
            dlNewest = not mobj.group('episode')
            if dlNewest:
                epTitle = mobj.group('showname')
            else:
                epTitle = mobj.group('episode')

        self.report_extraction(epTitle)
        webpage,htmlHandle = self._download_webpage_handle(url, epTitle)
        if dlNewest:
            url = htmlHandle.geturl()
            mobj = re.match(self._VALID_URL, url, re.VERBOSE)
            if mobj is None:
                raise ExtractorError(u'Invalid redirected URL: ' + url)
            if mobj.group('episode') == '':
                raise ExtractorError(u'Redirected URL is still not specific: ' + url)
            epTitle = mobj.group('episode')

        mMovieParams = re.findall('(?:<param name="movie" value="|var url = ")(http://media.mtvnservices.com/([^"]*(?:episode|video).*?:.*?))"', webpage)

        if len(mMovieParams) == 0:
            # The Colbert Report embeds the information in a without
            # a URL prefix; so extract the alternate reference
            # and then add the URL prefix manually.

            altMovieParams = re.findall('data-mgid="([^"]*(?:episode|video).*?:.*?)"', webpage)
            if len(altMovieParams) == 0:
                raise ExtractorError(u'unable to find Flash URL in webpage ' + url)
            else:
                mMovieParams = [("http://media.mtvnservices.com/" + altMovieParams[0], altMovieParams[0])]

        uri = mMovieParams[0][1]
        indexUrl = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?' + compat_urllib_parse.urlencode({'uri': uri})
        indexXml = self._download_webpage(indexUrl, epTitle,
                                          u'Downloading show index',
                                          u'unable to download episode index')

        results = []

        idoc = xml.etree.ElementTree.fromstring(indexXml)
        itemEls = idoc.findall('.//item')
        for partNum,itemEl in enumerate(itemEls):
            mediaId = itemEl.findall('./guid')[0].text
            shortMediaId = mediaId.split(':')[-1]
            showId = mediaId.split(':')[-2].replace('.com', '')
            officialTitle = itemEl.findall('./title')[0].text
            officialDate = unified_strdate(itemEl.findall('./pubDate')[0].text)

            configUrl = ('http://www.comedycentral.com/global/feeds/entertainment/media/mediaGenEntertainment.jhtml?' +
                        compat_urllib_parse.urlencode({'uri': mediaId}))
            configXml = self._download_webpage(configUrl, epTitle,
                                               u'Downloading configuration for %s' % shortMediaId)

            cdoc = xml.etree.ElementTree.fromstring(configXml)
            turls = []
            for rendition in cdoc.findall('.//rendition'):
                finfo = (rendition.attrib['bitrate'], rendition.findall('./src')[0].text)
                turls.append(finfo)

            if len(turls) == 0:
                self._downloader.report_error(u'unable to download ' + mediaId + ': No videos found')
                continue

            if self._downloader.params.get('listformats', None):
                self._print_formats([i[0] for i in turls])
                return

            # For now, just pick the highest bitrate
            format,rtmp_video_url = turls[-1]

            # Get the format arg from the arg stream
            req_format = self._downloader.params.get('format', None)

            # Select format if we can find one
            for f,v in turls:
                if f == req_format:
                    format, rtmp_video_url = f, v
                    break

            m = re.match(r'^rtmpe?://.*?/(?P<finalid>gsp.comedystor/.*)$', rtmp_video_url)
            if not m:
                raise ExtractorError(u'Cannot transform RTMP url')
            base = 'http://mtvnmobile.vo.llnwd.net/kip0/_pxn=1+_pxI0=Ripod-h264+_pxL0=undefined+_pxM0=+_pxK=18639+_pxE=mp4/44620/mtvnorigin/'
            video_url = base + m.group('finalid')

            effTitle = showId + u'-' + epTitle + u' part ' + compat_str(partNum+1)
            info = {
                'id': shortMediaId,
                'url': video_url,
                'uploader': showId,
                'upload_date': officialDate,
                'title': effTitle,
                'ext': 'mp4',
                'format': format,
                'thumbnail': None,
                'description': officialTitle,
            }
            results.append(info)

        return results


class EscapistIE(InfoExtractor):
    """Information extractor for The Escapist """

    _VALID_URL = r'^(https?://)?(www\.)?escapistmagazine\.com/videos/view/(?P<showname>[^/]+)/(?P<episode>[^/?]+)[/?]?.*$'
    IE_NAME = u'escapist'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        showName = mobj.group('showname')
        videoId = mobj.group('episode')

        self.report_extraction(videoId)
        webpage = self._download_webpage(url, videoId)

        videoDesc = self._html_search_regex('<meta name="description" content="([^"]*)"',
            webpage, u'description', fatal=False)

        imgUrl = self._html_search_regex('<meta property="og:image" content="([^"]*)"',
            webpage, u'thumbnail', fatal=False)

        playerUrl = self._html_search_regex('<meta property="og:video" content="([^"]*)"',
            webpage, u'player url')

        title = self._html_search_regex('<meta name="title" content="([^"]*)"',
            webpage, u'player url').split(' : ')[-1]

        configUrl = self._search_regex('config=(.*)$', playerUrl, u'config url')
        configUrl = compat_urllib_parse.unquote(configUrl)

        configJSON = self._download_webpage(configUrl, videoId,
                                            u'Downloading configuration',
                                            u'unable to download configuration')

        # Technically, it's JavaScript, not JSON
        configJSON = configJSON.replace("'", '"')

        try:
            config = json.loads(configJSON)
        except (ValueError,) as err:
            raise ExtractorError(u'Invalid JSON in configuration file: ' + compat_str(err))

        playlist = config['playlist']
        videoUrl = playlist[1]['url']

        info = {
            'id': videoId,
            'url': videoUrl,
            'uploader': showName,
            'upload_date': None,
            'title': title,
            'ext': 'mp4',
            'thumbnail': imgUrl,
            'description': videoDesc,
            'player_url': playerUrl,
        }

        return [info]

class CollegeHumorIE(InfoExtractor):
    """Information extractor for collegehumor.com"""

    _WORKING = False
    _VALID_URL = r'^(?:https?://)?(?:www\.)?collegehumor\.com/video/(?P<videoid>[0-9]+)/(?P<shorttitle>.*)$'
    IE_NAME = u'collegehumor'

    def report_manifest(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Downloading XML manifest' % video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('videoid')

        info = {
            'id': video_id,
            'uploader': None,
            'upload_date': None,
        }

        self.report_extraction(video_id)
        xmlUrl = 'http://www.collegehumor.com/moogaloop/video/' + video_id
        try:
            metaXml = compat_urllib_request.urlopen(xmlUrl).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video info XML: %s' % compat_str(err))

        mdoc = xml.etree.ElementTree.fromstring(metaXml)
        try:
            videoNode = mdoc.findall('./video')[0]
            info['description'] = videoNode.findall('./description')[0].text
            info['title'] = videoNode.findall('./caption')[0].text
            info['thumbnail'] = videoNode.findall('./thumbnail')[0].text
            manifest_url = videoNode.findall('./file')[0].text
        except IndexError:
            raise ExtractorError(u'Invalid metadata XML file')

        manifest_url += '?hdcore=2.10.3'
        self.report_manifest(video_id)
        try:
            manifestXml = compat_urllib_request.urlopen(manifest_url).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video info XML: %s' % compat_str(err))

        adoc = xml.etree.ElementTree.fromstring(manifestXml)
        try:
            media_node = adoc.findall('./{http://ns.adobe.com/f4m/1.0}media')[0]
            node_id = media_node.attrib['url']
            video_id = adoc.findall('./{http://ns.adobe.com/f4m/1.0}id')[0].text
        except IndexError as err:
            raise ExtractorError(u'Invalid manifest file')

        url_pr = compat_urllib_parse_urlparse(manifest_url)
        url = url_pr.scheme + '://' + url_pr.netloc + '/z' + video_id[:-2] + '/' + node_id + 'Seg1-Frag1'

        info['url'] = url
        info['ext'] = 'f4f'
        return [info]


class XVideosIE(InfoExtractor):
    """Information extractor for xvideos.com"""

    _VALID_URL = r'^(?:https?://)?(?:www\.)?xvideos\.com/video([0-9]+)(?:.*)'
    IE_NAME = u'xvideos'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(1)

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        # Extract video URL
        video_url = compat_urllib_parse.unquote(self._search_regex(r'flv_url=(.+?)&',
            webpage, u'video URL'))

        # Extract title
        video_title = self._html_search_regex(r'<title>(.*?)\s+-\s+XVID',
            webpage, u'title')

        # Extract video thumbnail
        video_thumbnail = self._search_regex(r'http://(?:img.*?\.)xvideos.com/videos/thumbs/[a-fA-F0-9]+/[a-fA-F0-9]+/[a-fA-F0-9]+/[a-fA-F0-9]+/([a-fA-F0-9.]+jpg)',
            webpage, u'thumbnail', fatal=False)

        info = {
            'id': video_id,
            'url': video_url,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'description': None,
        }

        return [info]


class SoundcloudIE(InfoExtractor):
    """Information extractor for soundcloud.com
       To access the media, the uid of the song and a stream token
       must be extracted from the page source and the script must make
       a request to media.soundcloud.com/crossdomain.xml. Then
       the media can be grabbed by requesting from an url composed
       of the stream token and uid
     """

    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/([\w\d-]+)'
    IE_NAME = u'soundcloud'

    def report_resolve(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Resolving id' % video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # extract uploader (which is in the url)
        uploader = mobj.group(1)
        # extract simple title (uploader + slug of song title)
        slug_title =  mobj.group(2)
        simple_title = uploader + u'-' + slug_title
        full_title = '%s/%s' % (uploader, slug_title)

        self.report_resolve(full_title)

        url = 'http://soundcloud.com/%s/%s' % (uploader, slug_title)
        resolv_url = 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        info_json = self._download_webpage(resolv_url, full_title, u'Downloading info JSON')

        info = json.loads(info_json)
        video_id = info['id']
        self.report_extraction(full_title)

        streams_url = 'https://api.sndcdn.com/i1/tracks/' + str(video_id) + '/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        stream_json = self._download_webpage(streams_url, full_title,
                                             u'Downloading stream definitions',
                                             u'unable to download stream definitions')

        streams = json.loads(stream_json)
        mediaURL = streams['http_mp3_128_url']
        upload_date = unified_strdate(info['created_at'])

        return [{
            'id':       info['id'],
            'url':      mediaURL,
            'uploader': info['user']['username'],
            'upload_date': upload_date,
            'title':    info['title'],
            'ext':      u'mp3',
            'description': info['description'],
        }]

class SoundcloudSetIE(InfoExtractor):
    """Information extractor for soundcloud.com sets
       To access the media, the uid of the song and a stream token
       must be extracted from the page source and the script must make
       a request to media.soundcloud.com/crossdomain.xml. Then
       the media can be grabbed by requesting from an url composed
       of the stream token and uid
     """

    _VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/sets/([\w\d-]+)'
    IE_NAME = u'soundcloud:set'

    def report_resolve(self, video_id):
        """Report information extraction."""
        self.to_screen(u'%s: Resolving id' % video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # extract uploader (which is in the url)
        uploader = mobj.group(1)
        # extract simple title (uploader + slug of song title)
        slug_title =  mobj.group(2)
        simple_title = uploader + u'-' + slug_title
        full_title = '%s/sets/%s' % (uploader, slug_title)

        self.report_resolve(full_title)

        url = 'http://soundcloud.com/%s/sets/%s' % (uploader, slug_title)
        resolv_url = 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        info_json = self._download_webpage(resolv_url, full_title)

        videos = []
        info = json.loads(info_json)
        if 'errors' in info:
            for err in info['errors']:
                self._downloader.report_error(u'unable to download video webpage: %s' % compat_str(err['error_message']))
            return

        self.report_extraction(full_title)
        for track in info['tracks']:
            video_id = track['id']

            streams_url = 'https://api.sndcdn.com/i1/tracks/' + str(video_id) + '/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
            stream_json = self._download_webpage(streams_url, video_id, u'Downloading track info JSON')

            self.report_extraction(video_id)
            streams = json.loads(stream_json)
            mediaURL = streams['http_mp3_128_url']

            videos.append({
                'id':       video_id,
                'url':      mediaURL,
                'uploader': track['user']['username'],
                'upload_date':  unified_strdate(track['created_at']),
                'title':    track['title'],
                'ext':      u'mp3',
                'description': track['description'],
            })
        return videos


class InfoQIE(InfoExtractor):
    """Information extractor for infoq.com"""
    _VALID_URL = r'^(?:https?://)?(?:www\.)?infoq\.com/[^/]+/[^/]+$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        webpage = self._download_webpage(url, video_id=url)
        self.report_extraction(url)

        # Extract video URL
        mobj = re.search(r"jsclassref ?= ?'([^']*)'", webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract video url')
        real_id = compat_urllib_parse.unquote(base64.b64decode(mobj.group(1).encode('ascii')).decode('utf-8'))
        video_url = 'rtmpe://video.infoq.com/cfx/st/' + real_id

        # Extract title
        video_title = self._search_regex(r'contentTitle = "(.*?)";',
            webpage, u'title')

        # Extract description
        video_description = self._html_search_regex(r'<meta name="description" content="(.*)"(?:\s*/)?>',
            webpage, u'description', fatal=False)

        video_filename = video_url.split('/')[-1]
        video_id, extension = video_filename.split('.')

        info = {
            'id': video_id,
            'url': video_url,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'ext': extension, # Extension is always(?) mp4, but seems to be flv
            'thumbnail': None,
            'description': video_description,
        }

        return [info]

class MixcloudIE(InfoExtractor):
    """Information extractor for www.mixcloud.com"""

    _WORKING = False # New API, but it seems good http://www.mixcloud.com/developers/documentation/
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([\w\d-]+)/([\w\d-]+)'
    IE_NAME = u'mixcloud'

    def report_download_json(self, file_id):
        """Report JSON download."""
        self.to_screen(u'Downloading json')

    def get_urls(self, jsonData, fmt, bitrate='best'):
        """Get urls from 'audio_formats' section in json"""
        file_url = None
        try:
            bitrate_list = jsonData[fmt]
            if bitrate is None or bitrate == 'best' or bitrate not in bitrate_list:
                bitrate = max(bitrate_list) # select highest

            url_list = jsonData[fmt][bitrate]
        except TypeError: # we have no bitrate info.
            url_list = jsonData[fmt]
        return url_list

    def check_urls(self, url_list):
        """Returns 1st active url from list"""
        for url in url_list:
            try:
                compat_urllib_request.urlopen(url)
                return url
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                url = None

        return None

    def _print_formats(self, formats):
        print('Available formats:')
        for fmt in formats.keys():
            for b in formats[fmt]:
                try:
                    ext = formats[fmt][b][0]
                    print('%s\t%s\t[%s]' % (fmt, b, ext.split('.')[-1]))
                except TypeError: # we have no bitrate info
                    ext = formats[fmt][0]
                    print('%s\t%s\t[%s]' % (fmt, '??', ext.split('.')[-1]))
                    break

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        # extract uploader & filename from url
        uploader = mobj.group(1).decode('utf-8')
        file_id = uploader + "-" + mobj.group(2).decode('utf-8')

        # construct API request
        file_url = 'http://www.mixcloud.com/api/1/cloudcast/' + '/'.join(url.split('/')[-3:-1]) + '.json'
        # retrieve .json file with links to files
        request = compat_urllib_request.Request(file_url)
        try:
            self.report_download_json(file_url)
            jsonData = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to retrieve file: %s' % compat_str(err))

        # parse JSON
        json_data = json.loads(jsonData)
        player_url = json_data['player_swf_url']
        formats = dict(json_data['audio_formats'])

        req_format = self._downloader.params.get('format', None)
        bitrate = None

        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        if req_format is None or req_format == 'best':
            for format_param in formats.keys():
                url_list = self.get_urls(formats, format_param)
                # check urls
                file_url = self.check_urls(url_list)
                if file_url is not None:
                    break # got it!
        else:
            if req_format not in formats:
                raise ExtractorError(u'Format is not available')

            url_list = self.get_urls(formats, req_format)
            file_url = self.check_urls(url_list)
            format_param = req_format

        return [{
            'id': file_id.decode('utf-8'),
            'url': file_url.decode('utf-8'),
            'uploader': uploader.decode('utf-8'),
            'upload_date': None,
            'title': json_data['name'],
            'ext': file_url.split('.')[-1].decode('utf-8'),
            'format': (format_param is None and u'NA' or format_param.decode('utf-8')),
            'thumbnail': json_data['thumbnail_url'],
            'description': json_data['description'],
            'player_url': player_url.decode('utf-8'),
        }]

class StanfordOpenClassroomIE(InfoExtractor):
    """Information extractor for Stanford's Open ClassRoom"""

    _VALID_URL = r'^(?:https?://)?openclassroom.stanford.edu(?P<path>/?|(/MainFolder/(?:HomePage|CoursePage|VideoPage)\.php([?]course=(?P<course>[^&]+)(&video=(?P<video>[^&]+))?(&.*)?)?))$'
    IE_NAME = u'stanfordoc'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        if mobj.group('course') and mobj.group('video'): # A specific video
            course = mobj.group('course')
            video = mobj.group('video')
            info = {
                'id': course + '_' + video,
                'uploader': None,
                'upload_date': None,
            }

            self.report_extraction(info['id'])
            baseUrl = 'http://openclassroom.stanford.edu/MainFolder/courses/' + course + '/videos/'
            xmlUrl = baseUrl + video + '.xml'
            try:
                metaXml = compat_urllib_request.urlopen(xmlUrl).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to download video info XML: %s' % compat_str(err))
            mdoc = xml.etree.ElementTree.fromstring(metaXml)
            try:
                info['title'] = mdoc.findall('./title')[0].text
                info['url'] = baseUrl + mdoc.findall('./videoFile')[0].text
            except IndexError:
                raise ExtractorError(u'Invalid metadata XML file')
            info['ext'] = info['url'].rpartition('.')[2]
            return [info]
        elif mobj.group('course'): # A course page
            course = mobj.group('course')
            info = {
                'id': course,
                'type': 'playlist',
                'uploader': None,
                'upload_date': None,
            }

            coursepage = self._download_webpage(url, info['id'],
                                        note='Downloading course info page',
                                        errnote='Unable to download course info page')

            info['title'] = self._html_search_regex('<h1>([^<]+)</h1>', coursepage, 'title', default=info['id'])

            info['description'] = self._html_search_regex('<description>([^<]+)</description>',
                coursepage, u'description', fatal=False)

            links = orderedSet(re.findall('<a href="(VideoPage.php\?[^"]+)">', coursepage))
            info['list'] = [
                {
                    'type': 'reference',
                    'url': 'http://openclassroom.stanford.edu/MainFolder/' + unescapeHTML(vpage),
                }
                    for vpage in links]
            results = []
            for entry in info['list']:
                assert entry['type'] == 'reference'
                results += self.extract(entry['url'])
            return results
        else: # Root page
            info = {
                'id': 'Stanford OpenClassroom',
                'type': 'playlist',
                'uploader': None,
                'upload_date': None,
            }

            self.report_download_webpage(info['id'])
            rootURL = 'http://openclassroom.stanford.edu/MainFolder/HomePage.php'
            try:
                rootpage = compat_urllib_request.urlopen(rootURL).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to download course info page: ' + compat_str(err))

            info['title'] = info['id']

            links = orderedSet(re.findall('<a href="(CoursePage.php\?[^"]+)">', rootpage))
            info['list'] = [
                {
                    'type': 'reference',
                    'url': 'http://openclassroom.stanford.edu/MainFolder/' + unescapeHTML(cpage),
                }
                    for cpage in links]

            results = []
            for entry in info['list']:
                assert entry['type'] == 'reference'
                results += self.extract(entry['url'])
            return results

class MTVIE(InfoExtractor):
    """Information extractor for MTV.com"""

    _VALID_URL = r'^(?P<proto>https?://)?(?:www\.)?mtv\.com/videos/[^/]+/(?P<videoid>[0-9]+)/[^/]+$'
    IE_NAME = u'mtv'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        if not mobj.group('proto'):
            url = 'http://' + url
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)

        song_name = self._html_search_regex(r'<meta name="mtv_vt" content="([^"]+)"/>',
            webpage, u'song name', fatal=False)

        video_title = self._html_search_regex(r'<meta name="mtv_an" content="([^"]+)"/>',
            webpage, u'title')

        mtvn_uri = self._html_search_regex(r'<meta name="mtvn_uri" content="([^"]+)"/>',
            webpage, u'mtvn_uri', fatal=False)

        content_id = self._search_regex(r'MTVN.Player.defaultPlaylistId = ([0-9]+);',
            webpage, u'content id', fatal=False)

        videogen_url = 'http://www.mtv.com/player/includes/mediaGen.jhtml?uri=' + mtvn_uri + '&id=' + content_id + '&vid=' + video_id + '&ref=www.mtvn.com&viewUri=' + mtvn_uri
        self.report_extraction(video_id)
        request = compat_urllib_request.Request(videogen_url)
        try:
            metadataXml = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video metadata: %s' % compat_str(err))

        mdoc = xml.etree.ElementTree.fromstring(metadataXml)
        renditions = mdoc.findall('.//rendition')

        # For now, always pick the highest quality.
        rendition = renditions[-1]

        try:
            _,_,ext = rendition.attrib['type'].partition('/')
            format = ext + '-' + rendition.attrib['width'] + 'x' + rendition.attrib['height'] + '_' + rendition.attrib['bitrate']
            video_url = rendition.find('./src').text
        except KeyError:
            raise ExtractorError('Invalid rendition field.')

        info = {
            'id': video_id,
            'url': video_url,
            'uploader': performer,
            'upload_date': None,
            'title': video_title,
            'ext': ext,
            'format': format,
        }

        return [info]


class YoukuIE(InfoExtractor):
    _VALID_URL =  r'(?:http://)?v\.youku\.com/v_show/id_(?P<ID>[A-Za-z0-9]+)\.html'

    def _gen_sid(self):
        nowTime = int(time.time() * 1000)
        random1 = random.randint(1000,1998)
        random2 = random.randint(1000,9999)

        return "%d%d%d" %(nowTime,random1,random2)

    def _get_file_ID_mix_string(self, seed):
        mixed = []
        source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\:._-1234567890")
        seed = float(seed)
        for i in range(len(source)):
            seed  =  (seed * 211 + 30031 ) % 65536
            index  =  math.floor(seed / 65536 * len(source) )
            mixed.append(source[int(index)])
            source.remove(source[int(index)])
        #return ''.join(mixed)
        return mixed

    def _get_file_id(self, fileId, seed):
        mixed = self._get_file_ID_mix_string(seed)
        ids = fileId.split('*')
        realId = []
        for ch in ids:
            if ch:
                realId.append(mixed[int(ch)])
        return ''.join(realId)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('ID')

        info_url = 'http://v.youku.com/player/getPlayList/VideoIDS/' + video_id

        jsondata = self._download_webpage(info_url, video_id)

        self.report_extraction(video_id)
        try:
            config = json.loads(jsondata)

            video_title =  config['data'][0]['title']
            seed = config['data'][0]['seed']

            format = self._downloader.params.get('format', None)
            supported_format = list(config['data'][0]['streamfileids'].keys())

            if format is None or format == 'best':
                if 'hd2' in supported_format:
                    format = 'hd2'
                else:
                    format = 'flv'
                ext = u'flv'
            elif format == 'worst':
                format = 'mp4'
                ext = u'mp4'
            else:
                format = 'flv'
                ext = u'flv'


            fileid = config['data'][0]['streamfileids'][format]
            keys = [s['k'] for s in config['data'][0]['segs'][format]]
        except (UnicodeDecodeError, ValueError, KeyError):
            raise ExtractorError(u'Unable to extract info section')

        files_info=[]
        sid = self._gen_sid()
        fileid = self._get_file_id(fileid, seed)

        #column 8,9 of fileid represent the segment number
        #fileid[7:9] should be changed
        for index, key in enumerate(keys):

            temp_fileid = '%s%02X%s' % (fileid[0:8], index, fileid[10:])
            download_url = 'http://f.youku.com/player/getFlvPath/sid/%s_%02X/st/flv/fileid/%s?k=%s' % (sid, index, temp_fileid, key)

            info = {
                'id': '%s_part%02d' % (video_id, index),
                'url': download_url,
                'uploader': None,
                'upload_date': None,
                'title': video_title,
                'ext': ext,
            }
            files_info.append(info)

        return files_info


class XNXXIE(InfoExtractor):
    """Information extractor for xnxx.com"""

    _VALID_URL = r'^(?:https?://)?video\.xnxx\.com/video([0-9]+)/(.*)'
    IE_NAME = u'xnxx'
    VIDEO_URL_RE = r'flv_url=(.*?)&amp;'
    VIDEO_TITLE_RE = r'<title>(.*?)\s+-\s+XNXX.COM'
    VIDEO_THUMB_RE = r'url_bigthumb=(.*?)&amp;'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(1)

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(self.VIDEO_URL_RE,
            webpage, u'video URL')
        video_url = compat_urllib_parse.unquote(video_url)

        video_title = self._html_search_regex(self.VIDEO_TITLE_RE,
            webpage, u'title')

        video_thumbnail = self._search_regex(self.VIDEO_THUMB_RE,
            webpage, u'thumbnail', fatal=False)

        return [{
            'id': video_id,
            'url': video_url,
            'uploader': None,
            'upload_date': None,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'description': None,
        }]


class GooglePlusIE(InfoExtractor):
    """Information extractor for plus.google.com."""

    _VALID_URL = r'(?:https://)?plus\.google\.com/(?:[^/]+/)*?posts/(\w+)'
    IE_NAME = u'plus.google'

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        post_url = mobj.group(0)
        video_id = mobj.group(1)

        video_extension = 'flv'

        # Step 1, Retrieve post webpage to extract further information
        webpage = self._download_webpage(post_url, video_id, u'Downloading entry webpage')

        self.report_extraction(video_id)

        # Extract update date
        upload_date = self._html_search_regex('title="Timestamp">(.*?)</a>',
            webpage, u'upload date', fatal=False)
        if upload_date:
            # Convert timestring to a format suitable for filename
            upload_date = datetime.datetime.strptime(upload_date, "%Y-%m-%d")
            upload_date = upload_date.strftime('%Y%m%d')

        # Extract uploader
        uploader = self._html_search_regex(r'rel\="author".*?>(.*?)</a>',
            webpage, u'uploader', fatal=False)

        # Extract title
        # Get the first line for title
        video_title = self._html_search_regex(r'<meta name\=\"Description\" content\=\"(.*?)[\n<"]',
            webpage, 'title', default=u'NA')

        # Step 2, Stimulate clicking the image box to launch video
        video_page = self._search_regex('"(https\://plus\.google\.com/photos/.*?)",,"image/jpeg","video"\]',
            webpage, u'video page URL')
        webpage = self._download_webpage(video_page, video_id, u'Downloading video page')

        # Extract video links on video page
        """Extract video links of all sizes"""
        pattern = '\d+,\d+,(\d+),"(http\://redirector\.googlevideo\.com.*?)"'
        mobj = re.findall(pattern, webpage)
        if len(mobj) == 0:
            raise ExtractorError(u'Unable to extract video links')

        # Sort in resolution
        links = sorted(mobj)

        # Choose the lowest of the sort, i.e. highest resolution
        video_url = links[-1]
        # Only get the url. The resolution part in the tuple has no use anymore
        video_url = video_url[-1]
        # Treat escaped \u0026 style hex
        try:
            video_url = video_url.decode("unicode_escape")
        except AttributeError: # Python 3
            video_url = bytes(video_url, 'ascii').decode('unicode-escape')


        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': uploader,
            'upload_date':  upload_date,
            'title':    video_title,
            'ext':      video_extension,
        }]

class NBAIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:watch\.|www\.)?nba\.com/(?:nba/)?video(/[^?]*?)(?:/index\.html)?(?:\?.*)?$'
    IE_NAME = u'nba'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group(1)

        webpage = self._download_webpage(url, video_id)

        video_url = u'http://ht-mobile.cdn.turner.com/nba/big' + video_id + '_nba_1280x720.mp4'

        shortened_video_id = video_id.rpartition('/')[2]
        title = self._html_search_regex(r'<meta property="og:title" content="(.*?)"',
            webpage, 'title', default=shortened_video_id).replace('NBA.com: ', '')

        # It isn't there in the HTML it returns to us
        # uploader_date = self._html_search_regex(r'<b>Date:</b> (.*?)</div>', webpage, 'upload_date', fatal=False)

        description = self._html_search_regex(r'<meta name="description" (?:content|value)="(.*?)" />', webpage, 'description', fatal=False)

        info = {
            'id': shortened_video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            # 'uploader_date': uploader_date,
            'description': description,
        }
        return [info]

class JustinTVIE(InfoExtractor):
    """Information extractor for justin.tv and twitch.tv"""
    # TODO: One broadcast may be split into multiple videos. The key
    # 'broadcast_id' is the same for all parts, and 'broadcast_part'
    # starts at 1 and increases. Can we treat all parts as one video?

    _VALID_URL = r"""(?x)^(?:http://)?(?:www\.)?(?:twitch|justin)\.tv/
        (?:
            (?P<channelid>[^/]+)|
            (?:(?:[^/]+)/b/(?P<videoid>[^/]+))|
            (?:(?:[^/]+)/c/(?P<chapterid>[^/]+))
        )
        /?(?:\#.*)?$
        """
    _JUSTIN_PAGE_LIMIT = 100
    IE_NAME = u'justin.tv'

    def report_download_page(self, channel, offset):
        """Report attempt to download a single page of videos."""
        self.to_screen(u'%s: Downloading video information from %d to %d' %
                (channel, offset, offset + self._JUSTIN_PAGE_LIMIT))

    # Return count of items, list of *valid* items
    def _parse_page(self, url, video_id):
        webpage = self._download_webpage(url, video_id,
                                         u'Downloading video info JSON',
                                         u'unable to download video info JSON')

        response = json.loads(webpage)
        if type(response) != list:
            error_text = response.get('error', 'unknown error')
            raise ExtractorError(u'Justin.tv API: %s' % error_text)
        info = []
        for clip in response:
            video_url = clip['video_file_url']
            if video_url:
                video_extension = os.path.splitext(video_url)[1][1:]
                video_date = re.sub('-', '', clip['start_time'][:10])
                video_uploader_id = clip.get('user_id', clip.get('channel_id'))
                video_id = clip['id']
                video_title = clip.get('title', video_id)
                info.append({
                    'id': video_id,
                    'url': video_url,
                    'title': video_title,
                    'uploader': clip.get('channel_name', video_uploader_id),
                    'uploader_id': video_uploader_id,
                    'upload_date': video_date,
                    'ext': video_extension,
                })
        return (len(response), info)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'invalid URL: %s' % url)

        api_base = 'http://api.justin.tv'
        paged = False
        if mobj.group('channelid'):
            paged = True
            video_id = mobj.group('channelid')
            api = api_base + '/channel/archives/%s.json' % video_id
        elif mobj.group('chapterid'):
            chapter_id = mobj.group('chapterid')

            webpage = self._download_webpage(url, chapter_id)
            m = re.search(r'PP\.archive_id = "([0-9]+)";', webpage)
            if not m:
                raise ExtractorError(u'Cannot find archive of a chapter')
            archive_id = m.group(1)

            api = api_base + '/broadcast/by_chapter/%s.xml' % chapter_id
            chapter_info_xml = self._download_webpage(api, chapter_id,
                                             note=u'Downloading chapter information',
                                             errnote=u'Chapter information download failed')
            doc = xml.etree.ElementTree.fromstring(chapter_info_xml)
            for a in doc.findall('.//archive'):
                if archive_id == a.find('./id').text:
                    break
            else:
                raise ExtractorError(u'Could not find chapter in chapter information')

            video_url = a.find('./video_file_url').text
            video_ext = video_url.rpartition('.')[2] or u'flv'

            chapter_api_url = u'https://api.twitch.tv/kraken/videos/c' + chapter_id
            chapter_info_json = self._download_webpage(chapter_api_url, u'c' + chapter_id,
                                   note='Downloading chapter metadata',
                                   errnote='Download of chapter metadata failed')
            chapter_info = json.loads(chapter_info_json)

            bracket_start = int(doc.find('.//bracket_start').text)
            bracket_end = int(doc.find('.//bracket_end').text)

            # TODO determine start (and probably fix up file)
            #  youtube-dl -v http://www.twitch.tv/firmbelief/c/1757457
            #video_url += u'?start=' + TODO:start_timestamp
            # bracket_start is 13290, but we want 51670615
            self._downloader.report_warning(u'Chapter detected, but we can just download the whole file. '
                                            u'Chapter starts at %s and ends at %s' % (formatSeconds(bracket_start), formatSeconds(bracket_end)))

            info = {
                'id': u'c' + chapter_id,
                'url': video_url,
                'ext': video_ext,
                'title': chapter_info['title'],
                'thumbnail': chapter_info['preview'],
                'description': chapter_info['description'],
                'uploader': chapter_info['channel']['display_name'],
                'uploader_id': chapter_info['channel']['name'],
            }
            return [info]
        else:
            video_id = mobj.group('videoid')
            api = api_base + '/broadcast/by_archive/%s.json' % video_id

        self.report_extraction(video_id)

        info = []
        offset = 0
        limit = self._JUSTIN_PAGE_LIMIT
        while True:
            if paged:
                self.report_download_page(video_id, offset)
            page_url = api + ('?offset=%d&limit=%d' % (offset, limit))
            page_count, page_info = self._parse_page(page_url, video_id)
            info.extend(page_info)
            if not paged or page_count != limit:
                break
            offset += limit
        return info

class FunnyOrDieIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?funnyordie\.com/videos/(?P<id>[0-9a-f]+)/.*$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'invalid URL: %s' % url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_regex(r'<video[^>]*>\s*<source[^>]*>\s*<source src="(?P<url>[^"]+)"',
            webpage, u'video URL', flags=re.DOTALL)

        title = self._html_search_regex((r"<h1 class='player_page_h1'.*?>(?P<title>.*?)</h1>",
            r'<title>(?P<title>[^<]+?)</title>'), webpage, 'title', flags=re.DOTALL)

        video_description = self._html_search_regex(r'<meta property="og:description" content="(?P<desc>.*?)"',
            webpage, u'description', fatal=False, flags=re.DOTALL)

        info = {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': video_description,
        }
        return [info]

class SteamIE(InfoExtractor):
    _VALID_URL = r"""http://store\.steampowered\.com/
                (agecheck/)?
                (?P<urltype>video|app)/ #If the page is only for videos or for a game
                (?P<gameID>\d+)/?
                (?P<videoID>\d*)(?P<extra>\??) #For urltype == video we sometimes get the videoID
                """
    _VIDEO_PAGE_TEMPLATE = 'http://store.steampowered.com/video/%s/'
    _AGECHECK_TEMPLATE = 'http://store.steampowered.com/agecheck/video/%s/?snr=1_agecheck_agecheck__age-gate&ageDay=1&ageMonth=January&ageYear=1970'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url, re.VERBOSE)
        gameID = m.group('gameID')

        videourl = self._VIDEO_PAGE_TEMPLATE % gameID
        webpage = self._download_webpage(videourl, gameID)

        if re.search('<h2>Please enter your birth date to continue:</h2>', webpage) is not None:
            videourl = self._AGECHECK_TEMPLATE % gameID
            self.report_age_confirmation()
            webpage = self._download_webpage(videourl, gameID)

        self.report_extraction(gameID)
        game_title = self._html_search_regex(r'<h2 class="pageheader">(.*?)</h2>',
                                             webpage, 'game title')

        urlRE = r"'movie_(?P<videoID>\d+)': \{\s*FILENAME: \"(?P<videoURL>[\w:/\.\?=]+)\"(,\s*MOVIE_NAME: \"(?P<videoName>[\w:/\.\?=\+-]+)\")?\s*\},"
        mweb = re.finditer(urlRE, webpage)
        namesRE = r'<span class="title">(?P<videoName>.+?)</span>'
        titles = re.finditer(namesRE, webpage)
        thumbsRE = r'<img class="movie_thumb" src="(?P<thumbnail>.+?)">'
        thumbs = re.finditer(thumbsRE, webpage)
        videos = []
        for vid,vtitle,thumb in zip(mweb,titles,thumbs):
            video_id = vid.group('videoID')
            title = vtitle.group('videoName')
            video_url = vid.group('videoURL')
            video_thumb = thumb.group('thumbnail')
            if not video_url:
                raise ExtractorError(u'Cannot find video url for %s' % video_id)
            info = {
                'id':video_id,
                'url':video_url,
                'ext': 'flv',
                'title': unescapeHTML(title),
                'thumbnail': video_thumb
                  }
            videos.append(info)
        return [self.playlist_result(videos, gameID, game_title)]

class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/recorded/(?P<videoID>\d+)'
    IE_NAME = u'ustream'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        video_url = u'http://tcdn.ustream.tv/video/%s' % video_id
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'data-title="(?P<title>.+)"',
            webpage, u'title')

        uploader = self._html_search_regex(r'data-content-type="channel".*?>(?P<uploader>.*?)</a>',
            webpage, u'uploader', fatal=False, flags=re.DOTALL)

        thumbnail = self._html_search_regex(r'<link rel="image_src" href="(?P<thumb>.*?)"',
            webpage, u'thumbnail', fatal=False)

        info = {
                'id': video_id,
                'url': video_url,
                'ext': 'flv',
                'title': video_title,
                'uploader': uploader,
                'thumbnail': thumbnail,
               }
        return info

class WorldStarHipHopIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|m)\.worldstar(?:candy|hiphop)\.com/videos/video\.php\?v=(?P<id>.*)'
    IE_NAME = u'WorldStarHipHop'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        webpage_src = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'so\.addVariable\("file","(.*?)"\)',
            webpage_src, u'video URL')

        if 'mp4' in video_url:
            ext = 'mp4'
        else:
            ext = 'flv'

        video_title = self._html_search_regex(r"<title>(.*)</title>",
            webpage_src, u'title')

        # Getting thumbnail and if not thumbnail sets correct title for WSHH candy video.
        thumbnail = self._html_search_regex(r'rel="image_src" href="(.*)" />',
            webpage_src, u'thumbnail', fatal=False)

        if not thumbnail:
            _title = r"""candytitles.*>(.*)</span>"""
            mobj = re.search(_title, webpage_src)
            if mobj is not None:
                video_title = mobj.group(1)

        results = [{
                    'id': video_id,
                    'url' : video_url,
                    'title' : video_title,
                    'thumbnail' : thumbnail,
                    'ext' : ext,
                    }]
        return results

class RBMARadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rbmaradio\.com/shows/(?P<videoID>[^/]+)$'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        json_data = self._search_regex(r'window\.gon.*?gon\.show=(.+?);$',
            webpage, u'json data', flags=re.MULTILINE)

        try:
            data = json.loads(json_data)
        except ValueError as e:
            raise ExtractorError(u'Invalid JSON: ' + str(e))

        video_url = data['akamai_url'] + '&cbr=256'
        url_parts = compat_urllib_parse_urlparse(video_url)
        video_ext = url_parts.path.rpartition('.')[2]
        info = {
                'id': video_id,
                'url': video_url,
                'ext': video_ext,
                'title': data['title'],
                'description': data.get('teaser_text'),
                'location': data.get('country_of_origin'),
                'uploader': data.get('host', {}).get('name'),
                'uploader_id': data.get('host', {}).get('slug'),
                'thumbnail': data.get('image', {}).get('large_url_2x'),
                'duration': data.get('duration'),
        }
        return [info]


class YouPornIE(InfoExtractor):
    """Information extractor for youporn.com."""
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?youporn\.com/watch/(?P<videoid>[0-9]+)/(?P<title>[^/]+)'

    def _print_formats(self, formats):
        """Print all available formats"""
        print(u'Available formats:')
        print(u'ext\t\tformat')
        print(u'---------------------------------')
        for format in formats:
            print(u'%s\t\t%s'  % (format['ext'], format['format']))

    def _specific(self, req_format, formats):
        for x in formats:
            if(x["format"]==req_format):
                return x
        return None

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('videoid')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        # Get JSON parameters
        json_params = self._search_regex(r'var currentVideo = new Video\((.*)\);', webpage, u'JSON parameters')
        try:
            params = json.loads(json_params)
        except:
            raise ExtractorError(u'Invalid JSON')

        self.report_extraction(video_id)
        try:
            video_title = params['title']
            upload_date = unified_strdate(params['release_date_f'])
            video_description = params['description']
            video_uploader = params['submitted_by']
            thumbnail = params['thumbnails'][0]['image']
        except KeyError:
            raise ExtractorError('Missing JSON parameter: ' + sys.exc_info()[1])

        # Get all of the formats available
        DOWNLOAD_LIST_RE = r'(?s)<ul class="downloadList">(?P<download_list>.*?)</ul>'
        download_list_html = self._search_regex(DOWNLOAD_LIST_RE,
            webpage, u'download list').strip()

        # Get all of the links from the page
        LINK_RE = r'(?s)<a href="(?P<url>[^"]+)">'
        links = re.findall(LINK_RE, download_list_html)
        if(len(links) == 0):
            raise ExtractorError(u'ERROR: no known formats available for video')

        self.to_screen(u'Links found: %d' % len(links))

        formats = []
        for link in links:

            # A link looks like this:
            # http://cdn1.download.youporn.phncdn.com/201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4?nvb=20121113051249&nva=20121114051249&ir=1200&sr=1200&hash=014b882080310e95fb6a0
            # A path looks like this:
            # /201210/31/8004515/480p_370k_8004515/YouPorn%20-%20Nubile%20Films%20The%20Pillow%20Fight.mp4
            video_url = unescapeHTML( link )
            path = compat_urllib_parse_urlparse( video_url ).path
            extension = os.path.splitext( path )[1][1:]
            format = path.split('/')[4].split('_')[:2]
            size = format[0]
            bitrate = format[1]
            format = "-".join( format )
            # title = u'%s-%s-%s' % (video_title, size, bitrate)

            formats.append({
                'id': video_id,
                'url': video_url,
                'uploader': video_uploader,
                'upload_date': upload_date,
                'title': video_title,
                'ext': extension,
                'format': format,
                'thumbnail': thumbnail,
                'description': video_description
            })

        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        req_format = self._downloader.params.get('format', None)
        self.to_screen(u'Format: %s' % req_format)

        if req_format is None or req_format == 'best':
            return [formats[0]]
        elif req_format == 'worst':
            return [formats[-1]]
        elif req_format in ('-1', 'all'):
            return formats
        else:
            format = self._specific( req_format, formats )
            if result is None:
                raise ExtractorError(u'Requested format not available')
            return [format]



class PornotubeIE(InfoExtractor):
    """Information extractor for pornotube.com."""
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?pornotube\.com(/c/(?P<channel>[0-9]+))?(/m/(?P<videoid>[0-9]+))(/(?P<title>.+))$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('videoid')
        video_title = mobj.group('title')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video URL
        VIDEO_URL_RE = r'url: "(?P<url>http://video[0-9].pornotube.com/.+\.flv)",'
        video_url = self._search_regex(VIDEO_URL_RE, webpage, u'video url')
        video_url = compat_urllib_parse.unquote(video_url)

        #Get the uploaded date
        VIDEO_UPLOADED_RE = r'<div class="video_added_by">Added (?P<date>[0-9\/]+) by'
        upload_date = self._html_search_regex(VIDEO_UPLOADED_RE, webpage, u'upload date', fatal=False)
        if upload_date: upload_date = unified_strdate(upload_date)

        info = {'id': video_id,
                'url': video_url,
                'uploader': None,
                'upload_date': upload_date,
                'title': video_title,
                'ext': 'flv',
                'format': 'flv'}

        return [info]

class YouJizzIE(InfoExtractor):
    """Information extractor for youjizz.com."""
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?youjizz\.com/videos/(?P<videoid>[^.]+).html$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video title
        video_title = self._html_search_regex(r'<title>(?P<title>.*)</title>',
            webpage, u'title').strip()

        # Get the embed page
        result = re.search(r'https?://www.youjizz.com/videos/embed/(?P<videoid>[0-9]+)', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract embed page')

        embed_page_url = result.group(0).strip()
        video_id = result.group('videoid')

        webpage = self._download_webpage(embed_page_url, video_id)

        # Get the video URL
        video_url = self._search_regex(r'so.addVariable\("file",encodeURIComponent\("(?P<source>[^"]+)"\)\);',
            webpage, u'video URL')

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'ext': 'flv',
                'format': 'flv',
                'player_url': embed_page_url}

        return [info]

class EightTracksIE(InfoExtractor):
    IE_NAME = '8tracks'
    _VALID_URL = r'https?://8tracks.com/(?P<user>[^/]+)/(?P<id>[^/#]+)(?:#.*)?$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        playlist_id = mobj.group('id')

        webpage = self._download_webpage(url, playlist_id)

        json_like = self._search_regex(r"PAGE.mix = (.*?);\n", webpage, u'trax information', flags=re.DOTALL)
        data = json.loads(json_like)

        session = str(random.randint(0, 1000000000))
        mix_id = data['id']
        track_count = data['tracks_count']
        first_url = 'http://8tracks.com/sets/%s/play?player=sm&mix_id=%s&format=jsonh' % (session, mix_id)
        next_url = first_url
        res = []
        for i in itertools.count():
            api_json = self._download_webpage(next_url, playlist_id,
                note=u'Downloading song information %s/%s' % (str(i+1), track_count),
                errnote=u'Failed to download song information')
            api_data = json.loads(api_json)
            track_data = api_data[u'set']['track']
            info = {
                'id': track_data['id'],
                'url': track_data['track_file_stream_url'],
                'title': track_data['performer'] + u' - ' + track_data['name'],
                'raw_title': track_data['name'],
                'uploader_id': data['user']['login'],
                'ext': 'm4a',
            }
            res.append(info)
            if api_data['set']['at_last_track']:
                break
            next_url = 'http://8tracks.com/sets/%s/next?player=sm&mix_id=%s&format=jsonh&track_id=%s' % (session, mix_id, track_data['id'])
        return res

class KeekIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?keek\.com/(?:!|\w+/keeks/)(?P<videoID>\w+)'
    IE_NAME = u'keek'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        video_url = u'http://cdn.keek.com/keek/video/%s' % video_id
        thumbnail = u'http://cdn.keek.com/keek/thumbnail/%s/w100/h75' % video_id
        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<meta property="og:title" content="(?P<title>.*?)"',
            webpage, u'title')

        uploader = self._html_search_regex(r'<div class="user-name-and-bio">[\S\s]+?<h2>(?P<uploader>.+?)</h2>',
            webpage, u'uploader', fatal=False)

        info = {
                'id': video_id,
                'url': video_url,
                'ext': 'mp4',
                'title': video_title,
                'thumbnail': thumbnail,
                'uploader': uploader
        }
        return [info]

class TEDIE(InfoExtractor):
    _VALID_URL=r'''http://www\.ted\.com/
                   (
                        ((?P<type_playlist>playlists)/(?P<playlist_id>\d+)) # We have a playlist
                        |
                        ((?P<type_talk>talks)) # We have a simple talk
                   )
                   (/lang/(.*?))? # The url may contain the language
                   /(?P<name>\w+) # Here goes the name and then ".html"
                   '''

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _real_extract(self, url):
        m=re.match(self._VALID_URL, url, re.VERBOSE)
        if m.group('type_talk'):
            return [self._talk_info(url)]
        else :
            playlist_id=m.group('playlist_id')
            name=m.group('name')
            self.to_screen(u'Getting info of playlist %s: "%s"' % (playlist_id,name))
            return [self._playlist_videos_info(url,name,playlist_id)]

    def _playlist_videos_info(self,url,name,playlist_id=0):
        '''Returns the videos of the playlist'''
        video_RE=r'''
                     <li\ id="talk_(\d+)"([.\s]*?)data-id="(?P<video_id>\d+)"
                     ([.\s]*?)data-playlist_item_id="(\d+)"
                     ([.\s]*?)data-mediaslug="(?P<mediaSlug>.+?)"
                     '''
        video_name_RE=r'<p\ class="talk-title"><a href="(?P<talk_url>/talks/(.+).html)">(?P<fullname>.+?)</a></p>'
        webpage=self._download_webpage(url, playlist_id, 'Downloading playlist webpage')
        m_videos=re.finditer(video_RE,webpage,re.VERBOSE)
        m_names=re.finditer(video_name_RE,webpage)

        playlist_title = self._html_search_regex(r'div class="headline">\s*?<h1>\s*?<span>(.*?)</span>',
                                                 webpage, 'playlist title')

        playlist_entries = []
        for m_video, m_name in zip(m_videos,m_names):
            video_id=m_video.group('video_id')
            talk_url='http://www.ted.com%s' % m_name.group('talk_url')
            playlist_entries.append(self.url_result(talk_url, 'TED'))
        return self.playlist_result(playlist_entries, playlist_id = playlist_id, playlist_title = playlist_title)

    def _talk_info(self, url, video_id=0):
        """Return the video for the talk in the url"""
        m = re.match(self._VALID_URL, url,re.VERBOSE)
        video_name = m.group('name')
        webpage = self._download_webpage(url, video_id, 'Downloading \"%s\" page' % video_name)
        self.report_extraction(video_name)
        # If the url includes the language we get the title translated
        title = self._html_search_regex(r'<span id="altHeadline" >(?P<title>.*)</span>',
                                        webpage, 'title')
        json_data = self._search_regex(r'<script.*?>var talkDetails = ({.*?})</script>',
                                    webpage, 'json data')
        info = json.loads(json_data)
        desc = self._html_search_regex(r'<div class="talk-intro">.*?<p.*?>(.*?)</p>',
                                       webpage, 'description', flags = re.DOTALL)
        
        thumbnail = self._search_regex(r'</span>[\s.]*</div>[\s.]*<img src="(.*?)"',
                                       webpage, 'thumbnail')
        info = {
                'id': info['id'],
                'url': info['htmlStreams'][-1]['file'],
                'ext': 'mp4',
                'title': title,
                'thumbnail': thumbnail,
                'description': desc,
                }
        return info

class MySpassIE(InfoExtractor):
    _VALID_URL = r'http://www.myspass.de/.*'

    def _real_extract(self, url):
        META_DATA_URL_TEMPLATE = 'http://www.myspass.de/myspass/includes/apps/video/getvideometadataxml.php?id=%s'

        # video id is the last path element of the URL
        # usually there is a trailing slash, so also try the second but last
        url_path = compat_urllib_parse_urlparse(url).path
        url_parent_path, video_id = os.path.split(url_path)
        if not video_id:
            _, video_id = os.path.split(url_parent_path)

        # get metadata
        metadata_url = META_DATA_URL_TEMPLATE % video_id
        metadata_text = self._download_webpage(metadata_url, video_id)
        metadata = xml.etree.ElementTree.fromstring(metadata_text.encode('utf-8'))

        # extract values from metadata
        url_flv_el = metadata.find('url_flv')
        if url_flv_el is None:
            raise ExtractorError(u'Unable to extract download url')
        video_url = url_flv_el.text
        extension = os.path.splitext(video_url)[1][1:]
        title_el = metadata.find('title')
        if title_el is None:
            raise ExtractorError(u'Unable to extract title')
        title = title_el.text
        format_id_el = metadata.find('format_id')
        if format_id_el is None:
            format = ext
        else:
            format = format_id_el.text
        description_el = metadata.find('description')
        if description_el is not None:
            description = description_el.text
        else:
            description = None
        imagePreview_el = metadata.find('imagePreview')
        if imagePreview_el is not None:
            thumbnail = imagePreview_el.text
        else:
            thumbnail = None
        info = {
            'id': video_id,
            'url': video_url,
            'title': title,
            'ext': extension,
            'format': format,
            'thumbnail': thumbnail,
            'description': description
        }
        return [info]

class SpiegelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/video/[^/]*-(?P<videoID>[0-9]+)(?:\.html)?(?:#.*)?$'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<div class="module-title">(.*?)</div>',
            webpage, u'title')

        xml_url = u'http://video2.spiegel.de/flash/' + video_id + u'.xml'
        xml_code = self._download_webpage(xml_url, video_id,
                    note=u'Downloading XML', errnote=u'Failed to download XML')

        idoc = xml.etree.ElementTree.fromstring(xml_code)
        last_type = idoc[-1]
        filename = last_type.findall('./filename')[0].text
        duration = float(last_type.findall('./duration')[0].text)

        video_url = 'http://video2.spiegel.de/flash/' + filename
        video_ext = filename.rpartition('.')[2]
        info = {
            'id': video_id,
            'url': video_url,
            'ext': video_ext,
            'title': video_title,
            'duration': duration,
        }
        return [info]

class LiveLeakIE(InfoExtractor):

    _VALID_URL = r'^(?:http?://)?(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<video_id>[\w_]+)(?:.*)'
    IE_NAME = u'liveleak'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('video_id')

        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'file: "(.*?)",',
            webpage, u'video URL')

        video_title = self._html_search_regex(r'<meta property="og:title" content="(?P<title>.*?)"',
            webpage, u'title').replace('LiveLeak.com -', '').strip()

        video_description = self._html_search_regex(r'<meta property="og:description" content="(?P<desc>.*?)"',
            webpage, u'description', fatal=False)

        video_uploader = self._html_search_regex(r'By:.*?(\w+)</a>',
            webpage, u'uploader', fatal=False)

        info = {
            'id':  video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': video_title,
            'description': video_description,
            'uploader': video_uploader
        }

        return [info]

class ARDIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:(?:www\.)?ardmediathek\.de|mediathek\.daserste\.de)/(?:.*/)(?P<video_id>[^/\?]+)(?:\?.*)?'
    _TITLE = r'<h1(?: class="boxTopHeadline")?>(?P<title>.*)</h1>'
    _MEDIA_STREAM = r'mediaCollection\.addMediaStream\((?P<media_type>\d+), (?P<quality>\d+), "(?P<rtmp_url>[^"]*)", "(?P<video_url>[^"]*)", "[^"]*"\)'

    def _real_extract(self, url):
        # determine video id from url
        m = re.match(self._VALID_URL, url)

        numid = re.search(r'documentId=([0-9]+)', url)
        if numid:
            video_id = numid.group(1)
        else:
            video_id = m.group('video_id')

        # determine title and media streams from webpage
        html = self._download_webpage(url, video_id)
        title = re.search(self._TITLE, html).group('title')
        streams = [m.groupdict() for m in re.finditer(self._MEDIA_STREAM, html)]
        if not streams:
            assert '"fsk"' in html
            raise ExtractorError(u'This video is only available after 8:00 pm')

        # choose default media type and highest quality for now
        stream = max([s for s in streams if int(s["media_type"]) == 0],
                     key=lambda s: int(s["quality"]))

        # there's two possibilities: RTMP stream or HTTP download
        info = {'id': video_id, 'title': title, 'ext': 'mp4'}
        if stream['rtmp_url']:
            self.to_screen(u'RTMP download detected')
            assert stream['video_url'].startswith('mp4:')
            info["url"] = stream["rtmp_url"]
            info["play_path"] = stream['video_url']
        else:
            assert stream["video_url"].endswith('.mp4')
            info["url"] = stream["video_url"]
        return [info]

class ZDFIE(InfoExtractor):
    _VALID_URL = r'^http://www\.zdf\.de\/ZDFmediathek\/(.*beitrag\/video\/)(?P<video_id>[^/\?]+)(?:\?.*)?'
    _TITLE = r'<h1(?: class="beitragHeadline")?>(?P<title>.*)</h1>'
    _MEDIA_STREAM = r'<a href="(?P<video_url>.+(?P<media_type>.streaming).+/zdf/(?P<quality>[^\/]+)/[^"]*)".+class="play".+>'
    _MMS_STREAM = r'href="(?P<video_url>mms://[^"]*)"'
    _RTSP_STREAM = r'(?P<video_url>rtsp://[^"]*.mp4)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('video_id')

        html = self._download_webpage(url, video_id)
        streams = [m.groupdict() for m in re.finditer(self._MEDIA_STREAM, html)]
        if streams is None:
            raise ExtractorError(u'No media url found.')

        # s['media_type'] == 'wstreaming' -> use 'Windows Media Player' and mms url
        # s['media_type'] == 'hstreaming' -> use 'Quicktime' and rtsp url
        # choose first/default media type and highest quality for now
        for s in streams:        #find 300 - dsl1000mbit
            if s['quality'] == '300' and s['media_type'] == 'wstreaming':
                stream_=s
                break
        for s in streams:        #find veryhigh - dsl2000mbit
            if s['quality'] == 'veryhigh' and s['media_type'] == 'wstreaming': # 'hstreaming' - rtsp is not working
                stream_=s
                break
        if stream_ is None:
            raise ExtractorError(u'No stream found.')

        media_link = self._download_webpage(stream_['video_url'], video_id,'Get stream URL')

        self.report_extraction(video_id)
        mobj = re.search(self._TITLE, html)
        if mobj is None:
            raise ExtractorError(u'Cannot extract title')
        title = unescapeHTML(mobj.group('title'))

        mobj = re.search(self._MMS_STREAM, media_link)
        if mobj is None:
            mobj = re.search(self._RTSP_STREAM, media_link)
            if mobj is None:
                raise ExtractorError(u'Cannot extract mms:// or rtsp:// URL')
        mms_url = mobj.group('video_url')

        mobj = re.search('(.*)[.](?P<ext>[^.]+)', mms_url)
        if mobj is None:
            raise ExtractorError(u'Cannot extract extention')
        ext = mobj.group('ext')

        return [{'id': video_id,
                 'url': mms_url,
                 'title': title,
                 'ext': ext
                 }]

class TumblrIE(InfoExtractor):
    _VALID_URL = r'http://(?P<blog_name>.*?)\.tumblr\.com/((post)|(video))/(?P<id>\d*)/(.*?)'

    def _real_extract(self, url):
        m_url = re.match(self._VALID_URL, url)
        video_id = m_url.group('id')
        blog = m_url.group('blog_name')

        url = 'http://%s.tumblr.com/post/%s/' % (blog, video_id)
        webpage = self._download_webpage(url, video_id)

        re_video = r'src=\\x22(?P<video_url>http://%s\.tumblr\.com/video_file/%s/(.*?))\\x22 type=\\x22video/(?P<ext>.*?)\\x22' % (blog, video_id)
        video = re.search(re_video, webpage)
        if video is None:
           raise ExtractorError(u'Unable to extract video')
        video_url = video.group('video_url')
        ext = video.group('ext')

        video_thumbnail = self._search_regex(r'posters(.*?)\[\\x22(?P<thumb>.*?)\\x22',
            webpage, u'thumbnail', fatal=False)  # We pick the first poster
        if video_thumbnail: video_thumbnail = video_thumbnail.replace('\\', '')

        # The only place where you can get a title, it's not complete,
        # but searching in other places doesn't work for all videos
        video_title = self._html_search_regex(r'<title>(?P<title>.*?)</title>',
            webpage, u'title', flags=re.DOTALL)

        return [{'id': video_id,
                 'url': video_url,
                 'title': video_title,
                 'thumbnail': video_thumbnail,
                 'ext': ext
                 }]

class BandcampIE(InfoExtractor):
    _VALID_URL = r'http://.*?\.bandcamp\.com/track/(?P<title>.*)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        # We get the link to the free download page
        m_download = re.search(r'freeDownloadPage: "(.*?)"', webpage)
        if m_download is None:
            raise ExtractorError(u'No free songs found')

        download_link = m_download.group(1)
        id = re.search(r'var TralbumData = {(.*?)id: (?P<id>\d*?)$', 
                       webpage, re.MULTILINE|re.DOTALL).group('id')

        download_webpage = self._download_webpage(download_link, id,
                                                  'Downloading free downloads page')
        # We get the dictionary of the track from some javascrip code
        info = re.search(r'items: (.*?),$',
                         download_webpage, re.MULTILINE).group(1)
        info = json.loads(info)[0]
        # We pick mp3-320 for now, until format selection can be easily implemented.
        mp3_info = info[u'downloads'][u'mp3-320']
        # If we try to use this url it says the link has expired
        initial_url = mp3_info[u'url']
        re_url = r'(?P<server>http://(.*?)\.bandcamp\.com)/download/track\?enc=mp3-320&fsig=(?P<fsig>.*?)&id=(?P<id>.*?)&ts=(?P<ts>.*)$'
        m_url = re.match(re_url, initial_url)
        #We build the url we will use to get the final track url
        # This url is build in Bandcamp in the script download_bunde_*.js
        request_url = '%s/statdownload/track?enc=mp3-320&fsig=%s&id=%s&ts=%s&.rand=665028774616&.vrs=1' % (m_url.group('server'), m_url.group('fsig'), id, m_url.group('ts'))
        final_url_webpage = self._download_webpage(request_url, id, 'Requesting download url')
        # If we could correctly generate the .rand field the url would be
        #in the "download_url" key
        final_url = re.search(r'"retry_url":"(.*?)"', final_url_webpage).group(1)

        track_info = {'id':id,
                      'title' : info[u'title'],
                      'ext' :   'mp3',
                      'url' :   final_url,
                      'thumbnail' : info[u'thumb_url'],
                      'uploader' :  info[u'artist']
                      }

        return [track_info]

class RedTubeIE(InfoExtractor):
    """Information Extractor for redtube"""
    _VALID_URL = r'(?:http://)?(?:www\.)?redtube\.com/(?P<id>[0-9]+)'

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('id')
        video_extension = 'mp4'        
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'<source src="(.+?)" type="video/mp4">',
            webpage, u'video URL')

        video_title = self._html_search_regex('<h1 class="videoTitle slidePanelMovable">(.+?)</h1>',
            webpage, u'title')

        return [{
            'id':       video_id,
            'url':      video_url,
            'ext':      video_extension,
            'title':    video_title,
        }]
        
class InaIE(InfoExtractor):
    """Information Extractor for Ina.fr"""
    _VALID_URL = r'(?:http://)?(?:www\.)?ina\.fr/video/(?P<id>I[0-9]+)/.*'

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        mrss_url='http://player.ina.fr/notices/%s.mrss' % video_id
        video_extension = 'mp4'
        webpage = self._download_webpage(mrss_url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'<media:player url="(?P<mp4url>http://mp4.ina.fr/[^"]+\.mp4)',
            webpage, u'video URL')

        video_title = self._search_regex(r'<title><!\[CDATA\[(?P<titre>.*?)]]></title>',
            webpage, u'title')

        return [{
            'id':       video_id,
            'url':      video_url,
            'ext':      video_extension,
            'title':    video_title,
        }]

class HowcastIE(InfoExtractor):
    """Information Extractor for Howcast.com"""
    _VALID_URL = r'(?:https?://)?(?:www\.)?howcast\.com/videos/(?P<id>\d+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://www.howcast.com/videos/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        video_url = self._search_regex(r'\'?file\'?: "(http://mobile-media\.howcast\.com/[0-9]+\.mp4)',
            webpage, u'video URL')

        video_title = self._html_search_regex(r'<meta content=(?:"([^"]+)"|\'([^\']+)\') property=\'og:title\'',
            webpage, u'title')

        video_description = self._html_search_regex(r'<meta content=(?:"([^"]+)"|\'([^\']+)\') name=\'description\'',
            webpage, u'description', fatal=False)

        thumbnail = self._html_search_regex(r'<meta content=\'(.+?)\' property=\'og:image\'',
            webpage, u'thumbnail', fatal=False)

        return [{
            'id':       video_id,
            'url':      video_url,
            'ext':      'mp4',
            'title':    video_title,
            'description': video_description,
            'thumbnail': thumbnail,
        }]

class VineIE(InfoExtractor):
    """Information Extractor for Vine.co"""
    _VALID_URL = r'(?:https?://)?(?:www\.)?vine\.co/v/(?P<id>\w+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'https://vine.co/v/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'<meta property="twitter:player:stream" content="(.+?)"',
            webpage, u'video URL')

        video_title = self._html_search_regex(r'<meta property="og:title" content="(.+?)"',
            webpage, u'title')

        thumbnail = self._html_search_regex(r'<meta property="og:image" content="(.+?)(\?.*?)?"',
            webpage, u'thumbnail', fatal=False)

        uploader = self._html_search_regex(r'<div class="user">.*?<h2>(.+?)</h2>',
            webpage, u'uploader', fatal=False, flags=re.DOTALL)

        return [{
            'id':        video_id,
            'url':       video_url,
            'ext':       'mp4',
            'title':     video_title,
            'thumbnail': thumbnail,
            'uploader':  uploader,
        }]

class FlickrIE(InfoExtractor):
    """Information Extractor for Flickr videos"""
    _VALID_URL = r'(?:https?://)?(?:www\.)?flickr\.com/photos/(?P<uploader_id>[\w\-_@]+)/(?P<id>\d+).*'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        video_uploader_id = mobj.group('uploader_id')
        webpage_url = 'http://www.flickr.com/photos/' + video_uploader_id + '/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        secret = self._search_regex(r"photo_secret: '(\w+)'", webpage, u'secret')

        first_url = 'https://secure.flickr.com/apps/video/video_mtl_xml.gne?v=x&photo_id=' + video_id + '&secret=' + secret + '&bitrate=700&target=_self'
        first_xml = self._download_webpage(first_url, video_id, 'Downloading first data webpage')

        node_id = self._html_search_regex(r'<Item id="id">(\d+-\d+)</Item>',
            first_xml, u'node_id')

        second_url = 'https://secure.flickr.com/video_playlist.gne?node_id=' + node_id + '&tech=flash&mode=playlist&bitrate=700&secret=' + secret + '&rd=video.yahoo.com&noad=1'
        second_xml = self._download_webpage(second_url, video_id, 'Downloading second data webpage')

        self.report_extraction(video_id)

        mobj = re.search(r'<STREAM APP="(.+?)" FULLPATH="(.+?)"', second_xml)
        if mobj is None:
            raise ExtractorError(u'Unable to extract video url')
        video_url = mobj.group(1) + unescapeHTML(mobj.group(2))

        video_title = self._html_search_regex(r'<meta property="og:title" content=(?:"([^"]+)"|\'([^\']+)\')',
            webpage, u'video title')

        video_description = self._html_search_regex(r'<meta property="og:description" content=(?:"([^"]+)"|\'([^\']+)\')',
            webpage, u'description', fatal=False)

        thumbnail = self._html_search_regex(r'<meta property="og:image" content=(?:"([^"]+)"|\'([^\']+)\')',
            webpage, u'thumbnail', fatal=False)

        return [{
            'id':          video_id,
            'url':         video_url,
            'ext':         'mp4',
            'title':       video_title,
            'description': video_description,
            'thumbnail':   thumbnail,
            'uploader_id': video_uploader_id,
        }]

class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<url_title>.*)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        url_title = mobj.group('url_title')
        webpage = self._download_webpage(url, url_title)

        video_id = self._html_search_regex(r'<article class="video" data-id="(\d+?)"',
            webpage, u'video id')

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'<meta property="og:title" content="(.+?)"',
            webpage, u'title')

        thumbnail = self._html_search_regex(r'<meta property="og:image" content="(.+?)"',
            webpage, u'thumbnail', fatal=False)

        video_description = self._html_search_regex(r'<meta property="og:description" content="(.*?)"',
            webpage, u'description', fatal=False)

        data_url = 'http://teamcoco.com/cvp/2.0/%s.xml' % video_id
        data = self._download_webpage(data_url, video_id, 'Downloading data webpage')

        video_url = self._html_search_regex(r'<file type="high".*?>(.*?)</file>',
            data, u'video URL')

        return [{
            'id':          video_id,
            'url':         video_url,
            'ext':         'mp4',
            'title':       video_title,
            'thumbnail':   thumbnail,
            'description': video_description,
        }]

class XHamsterIE(InfoExtractor):
    """Information Extractor for xHamster"""
    _VALID_URL = r'(?:http://)?(?:www.)?xhamster\.com/movies/(?P<id>[0-9]+)/.*\.html'

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        mrss_url = 'http://xhamster.com/movies/%s/.html' % video_id
        webpage = self._download_webpage(mrss_url, video_id)

        mobj = re.search(r'\'srv\': \'(?P<server>[^\']*)\',\s*\'file\': \'(?P<file>[^\']+)\',', webpage)
        if mobj is None:
            raise ExtractorError(u'Unable to extract media URL')
        if len(mobj.group('server')) == 0:
            video_url = compat_urllib_parse.unquote(mobj.group('file'))
        else:
            video_url = mobj.group('server')+'/key='+mobj.group('file')
        video_extension = video_url.split('.')[-1]

        video_title = self._html_search_regex(r'<title>(?P<title>.+?) - xHamster\.com</title>',
            webpage, u'title')

        # Can't see the description anywhere in the UI
        # video_description = self._html_search_regex(r'<span>Description: </span>(?P<description>[^<]+)',
        #     webpage, u'description', fatal=False)
        # if video_description: video_description = unescapeHTML(video_description)

        mobj = re.search(r'hint=\'(?P<upload_date_Y>[0-9]{4})-(?P<upload_date_m>[0-9]{2})-(?P<upload_date_d>[0-9]{2}) [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{3,4}\'', webpage)
        if mobj:
            video_upload_date = mobj.group('upload_date_Y')+mobj.group('upload_date_m')+mobj.group('upload_date_d')
        else:
            video_upload_date = None
            self._downloader.report_warning(u'Unable to extract upload date')

        video_uploader_id = self._html_search_regex(r'<a href=\'/user/[^>]+>(?P<uploader_id>[^<]+)',
            webpage, u'uploader id', default=u'anonymous')

        video_thumbnail = self._search_regex(r'\'image\':\'(?P<thumbnail>[^\']+)\'',
            webpage, u'thumbnail', fatal=False)

        return [{
            'id':       video_id,
            'url':      video_url,
            'ext':      video_extension,
            'title':    video_title,
            # 'description': video_description,
            'upload_date': video_upload_date,
            'uploader_id': video_uploader_id,
            'thumbnail': video_thumbnail
        }]

class HypemIE(InfoExtractor):
    """Information Extractor for hypem"""
    _VALID_URL = r'(?:http://)?(?:www\.)?hypem\.com/track/([^/]+)/([^/]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        track_id = mobj.group(1)

        data = { 'ax': 1, 'ts': time.time() }
        data_encoded = compat_urllib_parse.urlencode(data)
        complete_url = url + "?" + data_encoded
        request = compat_urllib_request.Request(complete_url)
        response, urlh = self._download_webpage_handle(request, track_id, u'Downloading webpage with the url')
        cookie = urlh.headers.get('Set-Cookie', '')

        self.report_extraction(track_id)

        html_tracks = self._html_search_regex(r'<script type="application/json" id="displayList-data">(.*?)</script>',
            response, u'tracks', flags=re.MULTILINE|re.DOTALL).strip()
        try:
            track_list = json.loads(html_tracks)
            track = track_list[u'tracks'][0]
        except ValueError:
            raise ExtractorError(u'Hypemachine contained invalid JSON.')

        key = track[u"key"]
        track_id = track[u"id"]
        artist = track[u"artist"]
        title = track[u"song"]

        serve_url = "http://hypem.com/serve/source/%s/%s" % (compat_str(track_id), compat_str(key))
        request = compat_urllib_request.Request(serve_url, "" , {'Content-Type': 'application/json'})
        request.add_header('cookie', cookie)
        song_data_json = self._download_webpage(request, track_id, u'Downloading metadata')
        try:
            song_data = json.loads(song_data_json)
        except ValueError:
            raise ExtractorError(u'Hypemachine contained invalid JSON.')
        final_url = song_data[u"url"]

        return [{
            'id':       track_id,
            'url':      final_url,
            'ext':      "mp3",
            'title':    title,
            'artist':   artist,
        }]

class Vbox7IE(InfoExtractor):
    """Information Extractor for Vbox7"""
    _VALID_URL = r'(?:http://)?(?:www\.)?vbox7\.com/play:([^/]+)'

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(1)

        redirect_page, urlh = self._download_webpage_handle(url, video_id)
        new_location = self._search_regex(r'window\.location = \'(.*)\';', redirect_page, u'redirect location')
        redirect_url = urlh.geturl() + new_location
        webpage = self._download_webpage(redirect_url, video_id, u'Downloading redirect page')

        title = self._html_search_regex(r'<title>(.*)</title>',
            webpage, u'title').split('/')[0].strip()

        ext = "flv"
        info_url = "http://vbox7.com/play/magare.do"
        data = compat_urllib_parse.urlencode({'as3':'1','vid':video_id})
        info_request = compat_urllib_request.Request(info_url, data)
        info_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        info_response = self._download_webpage(info_request, video_id, u'Downloading info webpage')
        if info_response is None:
            raise ExtractorError(u'Unable to extract the media url')
        (final_url, thumbnail_url) = map(lambda x: x.split('=')[1], info_response.split('&'))

        return [{
            'id':        video_id,
            'url':       final_url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail_url,
        }]

class GametrailersIE(InfoExtractor):
    _VALID_URL = r'http://www.gametrailers.com/(?P<type>videos|reviews|full-episodes)/(?P<id>.*?)/(?P<title>.*)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('id')
        video_type = mobj.group('type')
        webpage = self._download_webpage(url, video_id)
        if video_type == 'full-episodes':
            mgid_re = r'data-video="(?P<mgid>mgid:.*?)"'
        else:
            mgid_re = r'data-contentId=\'(?P<mgid>mgid:.*?)\''
        mgid = self._search_regex(mgid_re, webpage, u'mgid')
        data = compat_urllib_parse.urlencode({'uri': mgid, 'acceptMethods': 'fms'})

        info_page = self._download_webpage('http://www.gametrailers.com/feeds/mrss?' + data,
                                           video_id, u'Downloading video info')
        links_webpage = self._download_webpage('http://www.gametrailers.com/feeds/mediagen/?' + data,
                                               video_id, u'Downloading video urls info')

        self.report_extraction(video_id)
        info_re = r'''<title><!\[CDATA\[(?P<title>.*?)\]\]></title>.*
                      <description><!\[CDATA\[(?P<description>.*?)\]\]></description>.*
                      <image>.*
                        <url>(?P<thumb>.*?)</url>.*
                      </image>'''

        m_info = re.search(info_re, info_page, re.VERBOSE|re.DOTALL)
        if m_info is None:
            raise ExtractorError(u'Unable to extract video info')
        video_title = m_info.group('title')
        video_description = m_info.group('description')
        video_thumb = m_info.group('thumb')

        m_urls = list(re.finditer(r'<src>(?P<url>.*)</src>', links_webpage))
        if m_urls is None or len(m_urls) == 0:
            raise ExtractError(u'Unable to extrat video url')
        # They are sorted from worst to best quality
        video_url = m_urls[-1].group('url')

        return {'url':         video_url,
                'id':          video_id,
                'title':       video_title,
                # Videos are actually flv not mp4
                'ext':         'flv',
                'thumbnail':   video_thumb,
                'description': video_description,
                }

def gen_extractors():
    """ Return a list of an instance of every supported extractor.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    return [
        YoutubePlaylistIE(),
        YoutubeChannelIE(),
        YoutubeUserIE(),
        YoutubeSearchIE(),
        YoutubeIE(),
        MetacafeIE(),
        DailymotionIE(),
        GoogleSearchIE(),
        PhotobucketIE(),
        YahooIE(),
        YahooSearchIE(),
        DepositFilesIE(),
        FacebookIE(),
        BlipTVIE(),
        BlipTVUserIE(),
        VimeoIE(),
        MyVideoIE(),
        ComedyCentralIE(),
        EscapistIE(),
        CollegeHumorIE(),
        XVideosIE(),
        SoundcloudSetIE(),
        SoundcloudIE(),
        InfoQIE(),
        MixcloudIE(),
        StanfordOpenClassroomIE(),
        MTVIE(),
        YoukuIE(),
        XNXXIE(),
        YouJizzIE(),
        PornotubeIE(),
        YouPornIE(),
        GooglePlusIE(),
        ArteTvIE(),
        NBAIE(),
        WorldStarHipHopIE(),
        JustinTVIE(),
        FunnyOrDieIE(),
        SteamIE(),
        UstreamIE(),
        RBMARadioIE(),
        EightTracksIE(),
        KeekIE(),
        TEDIE(),
        MySpassIE(),
        SpiegelIE(),
        LiveLeakIE(),
        ARDIE(),
        ZDFIE(),
        TumblrIE(),
        BandcampIE(),
        RedTubeIE(),
        InaIE(),
        HowcastIE(),
        VineIE(),
        FlickrIE(),
        TeamcocoIE(),
        XHamsterIE(),
        HypemIE(),
        Vbox7IE(),
        GametrailersIE(),
        GenericIE()
    ]

def get_info_extractor(ie_name):
    """Returns the info extractor class with the given ie_name"""
    return globals()[ie_name+'IE']
