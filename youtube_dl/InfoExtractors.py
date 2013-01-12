#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import base64
import datetime
import netrc
import os
import re
import socket
import time
import email.utils
import xml.etree.ElementTree
import random
import math

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
    subtitles:      The .srt file contents.
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

    def suitable(self, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(self._VALID_URL, url) is not None

    def working(self):
        """Getter method for _WORKING."""
        return self._WORKING

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
            note = u'Downloading video webpage'
        self._downloader.to_screen(u'[%s] %s: %s' % (self.IE_NAME, video_id, note))
        try:
            return compat_urllib_request.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if errnote is None:
                errnote = u'Unable to download webpage'
            raise ExtractorError(u'%s: %s' % (errnote, compat_str(err)), sys.exc_info()[2])

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the data of the page as a string """
        urlh = self._request_webpage(url_or_request, video_id, note, errnote)
        webpage_bytes = urlh.read()
        return webpage_bytes.decode('utf-8', 'replace')


class YoutubeIE(InfoExtractor):
    """Information extractor for youtube.com."""

    _VALID_URL = r"""^
                     (
                         (?:https?://)?                                       # http(s):// (optional)
                         (?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/|
                            tube\.majestyc\.net/)                             # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?!view_play_list|my_playlists|artist|playlist)      # ignore playlist URLs
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
    _LANG_URL = r'http://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _LOGIN_URL = 'https://www.youtube.com/signup?next=/&gl=US&hl=en'
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

    def suitable(self, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(self._VALID_URL, url, re.VERBOSE) is not None

    def report_lang(self):
        """Report attempt to set language."""
        self._downloader.to_screen(u'[youtube] Setting language')

    def report_login(self):
        """Report attempt to log in."""
        self._downloader.to_screen(u'[youtube] Logging in')

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        self._downloader.to_screen(u'[youtube] Confirming age')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self._downloader.to_screen(u'[youtube] %s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self._downloader.to_screen(u'[youtube] %s: Downloading video info webpage' % video_id)

    def report_video_subtitles_download(self, video_id):
        """Report attempt to download video info webpage."""
        self._downloader.to_screen(u'[youtube] %s: Downloading video subtitles' % video_id)

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self._downloader.to_screen(u'[youtube] %s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        self._downloader.to_screen(u'[youtube] %s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        self._downloader.to_screen(u'[youtube] RTMP download detected')

    def _closed_captions_xml_to_srt(self, xml_string):
        srt = ''
        texts = re.findall(r'<text start="([\d\.]+)"( dur="([\d\.]+)")?>([^<]+)</text>', xml_string, re.MULTILINE)
        # TODO parse xml instead of regex
        for n, (start, dur_tag, dur, caption) in enumerate(texts):
            if not dur: dur = '4'
            start = float(start)
            end = start + float(dur)
            start = "%02i:%02i:%02i,%03i" %(start/(60*60), start/60%60, start%60, start%1*1000)
            end = "%02i:%02i:%02i,%03i" %(end/(60*60), end/60%60, end%60, end%1*1000)
            caption = unescapeHTML(caption)
            caption = unescapeHTML(caption) # double cycle, intentional
            srt += str(n+1) + '\n'
            srt += start + ' --> ' + end + '\n'
            srt += caption + '\n\n'
        return srt

    def _extract_subtitles(self, video_id):
        self.report_video_subtitles_download(video_id)
        request = compat_urllib_request.Request('http://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id)
        try:
            srt_list = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            return (u'WARNING: unable to download video subtitles: %s' % compat_str(err), None)
        srt_lang_list = re.findall(r'name="([^"]*)"[^>]+lang_code="([\w\-]+)"', srt_list)
        srt_lang_list = dict((l[1], l[0]) for l in srt_lang_list)
        if not srt_lang_list:
            return (u'WARNING: video has no closed captions', None)
        if self._downloader.params.get('subtitleslang', False):
            srt_lang = self._downloader.params.get('subtitleslang')
        elif 'en' in srt_lang_list:
            srt_lang = 'en'
        else:
            srt_lang = list(srt_lang_list.keys())[0]
        if not srt_lang in srt_lang_list:
            return (u'WARNING: no closed captions found in the specified language', None)
        request = compat_urllib_request.Request('http://www.youtube.com/api/timedtext?lang=%s&name=%s&v=%s' % (srt_lang, srt_lang_list[srt_lang], video_id))
        try:
            srt_xml = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            return (u'WARNING: unable to download video subtitles: %s' % compat_str(err), None)
        if not srt_xml:
            return (u'WARNING: unable to download video subtitles', None)
        return (None, self._closed_captions_xml_to_srt(srt_xml))

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
                self._downloader.to_stderr(u'WARNING: parsing .netrc: %s' % compat_str(err))
                return

        # Set language
        request = compat_urllib_request.Request(self._LANG_URL)
        try:
            self.report_lang()
            compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.to_stderr(u'WARNING: unable to set language: %s' % compat_str(err))
            return

        # No authentication to be performed
        if username is None:
            return

        # Log in
        login_form = {
                'current_form': 'loginForm',
                'next':     '/',
                'action_login': 'Log In',
                'username': username,
                'password': password,
                }
        request = compat_urllib_request.Request(self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
            if re.search(r'(?i)<form[^>]* name="loginForm"', login_results) is not None:
                self._downloader.to_stderr(u'WARNING: unable to log in: bad username or password')
                return
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.to_stderr(u'WARNING: unable to log in: %s' % compat_str(err))
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
            self._downloader.trouble(u'ERROR: unable to confirm age: %s' % compat_str(err))
            return

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group(2)
        return video_id

    def _real_extract(self, url):
        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = 'http://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self._extract_id(url)

        # Get video webpage
        self.report_video_webpage_download(video_id)
        url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
        request = compat_urllib_request.Request(url)
        try:
            video_webpage_bytes = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % compat_str(err))
            return

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
            video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                    % (video_id, el_type))
            request = compat_urllib_request.Request(video_info_url)
            try:
                video_info_webpage_bytes = compat_urllib_request.urlopen(request).read()
                video_info_webpage = video_info_webpage_bytes.decode('utf-8', 'ignore')
                video_info = compat_parse_qs(video_info_webpage)
                if 'token' in video_info:
                    break
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download video info webpage: %s' % compat_str(err))
                return
        if 'token' not in video_info:
            if 'reason' in video_info:
                self._downloader.trouble(u'ERROR: YouTube said: %s' % video_info['reason'][0])
            else:
                self._downloader.trouble(u'ERROR: "token" parameter not in video info for unknown reason')
            return

        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            self._downloader.trouble(u'ERROR: "rental" videos not supported')
            return

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            self._downloader.trouble(u'ERROR: unable to extract uploader name')
            return
        video_uploader = compat_urllib_parse.unquote_plus(video_info['author'][0])

        # uploader_id
        video_uploader_id = None
        mobj = re.search(r'<link itemprop="url" href="http://www.youtube.com/(?:user|channel)/([^"]+)">', video_webpage)
        if mobj is not None:
            video_uploader_id = mobj.group(1)
        else:
            self._downloader.trouble(u'WARNING: unable to extract uploader nickname')

        # title
        if 'title' not in video_info:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = compat_urllib_parse.unquote_plus(video_info['title'][0])

        # thumbnail image
        if 'thumbnail_url' not in video_info:
            self._downloader.trouble(u'WARNING: unable to extract video thumbnail')
            video_thumbnail = ''
        else:   # don't panic if we can't find it
            video_thumbnail = compat_urllib_parse.unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = None
        mobj = re.search(r'id="eow-date.*?>(.*?)</span>', video_webpage, re.DOTALL)
        if mobj is not None:
            upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
            format_expressions = ['%d %B %Y', '%B %d %Y', '%b %d %Y']
            for expression in format_expressions:
                try:
                    upload_date = datetime.datetime.strptime(upload_date, expression).strftime('%Y%m%d')
                except:
                    pass

        # description
        video_description = get_element_by_id("eow-description", video_webpage)
        if video_description:
            video_description = clean_html(video_description)
        else:
            video_description = ''

        # closed captions
        video_subtitles = None
        if self._downloader.params.get('writesubtitles', False):
            (srt_error, video_subtitles) = self._extract_subtitles(video_id)
            if srt_error:
                self._downloader.trouble(srt_error)

        if 'length_seconds' not in video_info:
            self._downloader.trouble(u'WARNING: unable to extract video duration')
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
            url_data_strs = video_info['url_encoded_fmt_stream_map'][0].split(',')
            url_data = [compat_parse_qs(uds) for uds in url_data_strs]
            url_data = [ud for ud in url_data if 'itag' in ud and 'url' in ud]
            url_map = dict((ud['itag'][0], ud['url'][0] + '&signature=' + ud['sig'][0]) for ud in url_data)

            format_limit = self._downloader.params.get('format_limit', None)
            available_formats = self._available_formats_prefer_free if self._downloader.params.get('prefer_free_formats', False) else self._available_formats
            if format_limit is not None and format_limit in available_formats:
                format_list = available_formats[available_formats.index(format_limit):]
            else:
                format_list = available_formats
            existing_formats = [x for x in format_list if x in url_map]
            if len(existing_formats) == 0:
                self._downloader.trouble(u'ERROR: no known formats available for video')
                return
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
                    self._downloader.trouble(u'ERROR: requested format not available')
                    return
        else:
            self._downloader.trouble(u'ERROR: no conn or url_encoded_fmt_stream_map information found in video info')
            return

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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_disclaimer(self):
        """Report disclaimer retrieval."""
        self._downloader.to_screen(u'[metacafe] Retrieving disclaimer')

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        self._downloader.to_screen(u'[metacafe] Confirming age')

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[metacafe] %s: Downloading webpage' % video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[metacafe] %s: Extracting information' % video_id)

    def _real_initialize(self):
        # Retrieve disclaimer
        request = compat_urllib_request.Request(self._DISCLAIMER)
        try:
            self.report_disclaimer()
            disclaimer = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to retrieve disclaimer: %s' % compat_str(err))
            return

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
            self._downloader.trouble(u'ERROR: unable to confirm age: %s' % compat_str(err))
            return

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group(1)

        # Check if video comes from YouTube
        mobj2 = re.match(r'^yt-(.*)$', video_id)
        if mobj2 is not None:
            self._downloader.download(['http://www.youtube.com/watch?v=%s' % mobj2.group(1)])
            return

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request('http://www.metacafe.com/watch/%s/' % video_id)
        try:
            self.report_download_webpage(video_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable retrieve video webpage: %s' % compat_str(err))
            return

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
                self._downloader.trouble(u'ERROR: unable to extract media URL')
                return
            vardict = compat_parse_qs(mobj.group(1))
            if 'mediaData' not in vardict:
                self._downloader.trouble(u'ERROR: unable to extract media URL')
                return
            mobj = re.search(r'"mediaURL":"(http.*?)","key":"(.*?)"', vardict['mediaData'][0])
            if mobj is None:
                self._downloader.trouble(u'ERROR: unable to extract media URL')
                return
            mediaURL = mobj.group(1).replace('\\/', '/')
            video_extension = mediaURL[-3:]
            video_url = '%s?__gda__=%s' % (mediaURL, mobj.group(2))

        mobj = re.search(r'(?im)<title>(.*) - Video</title>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return
        video_title = mobj.group(1).decode('utf-8')

        mobj = re.search(r'submitter=(.*?);', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
            return
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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[dailymotion] %s: Extracting information' % video_id)

    def _real_extract(self, url):
        # Extract id and simplified title from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

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
            self._downloader.trouble(u'ERROR: unable to extract media URL')
            return
        flashvars = compat_urllib_parse.unquote(mobj.group(1))

        for key in ['hd1080URL', 'hd720URL', 'hqURL', 'sdURL', 'ldURL', 'video_url']:
            if key in flashvars:
                max_quality = key
                self._downloader.to_screen(u'[dailymotion] Using %s' % key)
                break
        else:
            self._downloader.trouble(u'ERROR: unable to extract video URL')
            return

        mobj = re.search(r'"' + max_quality + r'":"(.+?)"', flashvars)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video URL')
            return

        video_url = compat_urllib_parse.unquote(mobj.group(1)).replace('\\/', '/')

        # TODO: support choosing qualities

        mobj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return
        video_title = unescapeHTML(mobj.group('title'))

        video_uploader = None
        mobj = re.search(r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a>', webpage)
        if mobj is None:
            # lookin for official user
            mobj_official = re.search(r'<span rel="author"[^>]+?>([^<]+?)</span>', webpage)
            if mobj_official is None:
                self._downloader.trouble(u'WARNING: unable to extract uploader nickname')
            else:
                video_uploader = mobj_official.group(1)
        else:
            video_uploader = mobj.group(1)

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

    _VALID_URL = r'(?:http://)?(?:[a-z0-9]+\.)?photobucket\.com/.*[\?\&]current=(.*\.flv)'
    IE_NAME = u'photobucket'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[photobucket] %s: Downloading webpage' % video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[photobucket] %s: Extracting information' % video_id)

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        video_id = mobj.group(1)

        video_extension = 'flv'

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url)
        try:
            self.report_download_webpage(video_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return

        # Extract URL, uploader, and title from webpage
        self.report_extraction(video_id)
        mobj = re.search(r'<link rel="video_src" href=".*\?file=([^"]+)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract media URL')
            return
        mediaURL = compat_urllib_parse.unquote(mobj.group(1))

        video_url = mediaURL

        mobj = re.search(r'<title>(.*) video by (.*) - Photobucket</title>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return
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
    """Information extractor for video.yahoo.com."""

    _WORKING = False
    # _VALID_URL matches all Yahoo! Video URLs
    # _VPAGE_URL matches only the extractable '/watch/' URLs
    _VALID_URL = r'(?:http://)?(?:[a-z]+\.)?video\.yahoo\.com/(?:watch|network)/([0-9]+)(?:/|\?v=)([0-9]+)(?:[#\?].*)?'
    _VPAGE_URL = r'(?:http://)?video\.yahoo\.com/watch/([0-9]+)/([0-9]+)(?:[#\?].*)?'
    IE_NAME = u'video.yahoo'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[video.yahoo] %s: Downloading webpage' % video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[video.yahoo] %s: Extracting information' % video_id)

    def _real_extract(self, url, new_video=True):
        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        video_id = mobj.group(2)
        video_extension = 'flv'

        # Rewrite valid but non-extractable URLs as
        # extractable English language /watch/ URLs
        if re.match(self._VPAGE_URL, url) is None:
            request = compat_urllib_request.Request(url)
            try:
                webpage = compat_urllib_request.urlopen(request).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
                return

            mobj = re.search(r'\("id", "([0-9]+)"\);', webpage)
            if mobj is None:
                self._downloader.trouble(u'ERROR: Unable to extract id field')
                return
            yahoo_id = mobj.group(1)

            mobj = re.search(r'\("vid", "([0-9]+)"\);', webpage)
            if mobj is None:
                self._downloader.trouble(u'ERROR: Unable to extract vid field')
                return
            yahoo_vid = mobj.group(1)

            url = 'http://video.yahoo.com/watch/%s/%s' % (yahoo_vid, yahoo_id)
            return self._real_extract(url, new_video=False)

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url)
        try:
            self.report_download_webpage(video_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return

        # Extract uploader and title from webpage
        self.report_extraction(video_id)
        mobj = re.search(r'<meta name="title" content="(.*)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = mobj.group(1).decode('utf-8')

        mobj = re.search(r'<h2 class="ti-5"><a href="http://video\.yahoo\.com/(people|profile)/[0-9]+" beacon=".*">(.*)</a></h2>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video uploader')
            return
        video_uploader = mobj.group(1).decode('utf-8')

        # Extract video thumbnail
        mobj = re.search(r'<link rel="image_src" href="(.*)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video thumbnail')
            return
        video_thumbnail = mobj.group(1).decode('utf-8')

        # Extract video description
        mobj = re.search(r'<meta name="description" content="(.*)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video description')
            return
        video_description = mobj.group(1).decode('utf-8')
        if not video_description:
            video_description = 'No description available.'

        # Extract video height and width
        mobj = re.search(r'<meta name="video_height" content="([0-9]+)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video height')
            return
        yv_video_height = mobj.group(1)

        mobj = re.search(r'<meta name="video_width" content="([0-9]+)" />', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video width')
            return
        yv_video_width = mobj.group(1)

        # Retrieve video playlist to extract media URL
        # I'm not completely sure what all these options are, but we
        # seem to need most of them, otherwise the server sends a 401.
        yv_lg = 'R0xx6idZnW2zlrKP8xxAIR'  # not sure what this represents
        yv_bitrate = '700'  # according to Wikipedia this is hard-coded
        request = compat_urllib_request.Request('http://cosmos.bcst.yahoo.com/up/yep/process/getPlaylistFOP.php?node_id=' + video_id +
                '&tech=flash&mode=playlist&lg=' + yv_lg + '&bitrate=' + yv_bitrate + '&vidH=' + yv_video_height +
                '&vidW=' + yv_video_width + '&swf=as3&rd=video.yahoo.com&tk=null&adsupported=v1,v2,&eventid=1301797')
        try:
            self.report_download_webpage(video_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return

        # Extract media URL from playlist XML
        mobj = re.search(r'<STREAM APP="(http://.*)" FULLPATH="/?(/.*\.flv\?[^"]*)"', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: Unable to extract media URL')
            return
        video_url = compat_urllib_parse.unquote(mobj.group(1) + mobj.group(2)).decode('utf-8')
        video_url = unescapeHTML(video_url)

        return [{
            'id':       video_id.decode('utf-8'),
            'url':      video_url,
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension.decode('utf-8'),
            'thumbnail':    video_thumbnail.decode('utf-8'),
            'description':  video_description,
        }]


class VimeoIE(InfoExtractor):
    """Information extractor for vimeo.com."""

    # _VALID_URL matches Vimeo URLs
    _VALID_URL = r'(?:https?://)?(?:(?:www|player).)?vimeo\.com/(?:(?:groups|album)/[^/]+/)?(?:videos?/)?([0-9]+)'
    IE_NAME = u'vimeo'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[vimeo] %s: Downloading webpage' % video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[vimeo] %s: Extracting information' % video_id)

    def _real_extract(self, url, new_video=True):
        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        video_id = mobj.group(1)

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url, None, std_headers)
        try:
            self.report_download_webpage(video_id)
            webpage_bytes = compat_urllib_request.urlopen(request).read()
            webpage = webpage_bytes.decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return

        # Now we begin extracting as much information as we can from what we
        # retrieved. First we extract the information common to all extractors,
        # and latter we extract those that are Vimeo specific.
        self.report_extraction(video_id)

        # Extract the config JSON
        try:
            config = webpage.split(' = {config:')[1].split(',assets:')[0]
            config = json.loads(config)
        except:
            self._downloader.trouble(u'ERROR: unable to extract info section')
            return

        # Extract title
        video_title = config["video"]["title"]

        # Extract uploader and uploader_id
        video_uploader = config["video"]["owner"]["name"]
        video_uploader_id = config["video"]["owner"]["url"].split('/')[-1]

        # Extract video thumbnail
        video_thumbnail = config["video"]["thumbnail"]

        # Extract video description
        video_description = get_element_by_attribute("itemprop", "description", webpage)
        if video_description: video_description = clean_html(video_description)
        else: video_description = ''

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
                self._downloader.to_screen(u'[vimeo] %s: Downloading %s file at %s quality' % (video_id, video_codec.upper(), video_quality))
                break
        else:
            self._downloader.trouble(u'ERROR: no known codec found')
            return

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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[arte.tv] %s: Downloading webpage' % video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[arte.tv] %s: Extracting information' % video_id)

    def fetch_webpage(self, url):
        request = compat_urllib_request.Request(url)
        try:
            self.report_download_webpage(url)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return
        except ValueError as err:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return
        return webpage

    def grep_webpage(self, url, regex, regexFlags, matchTuples):
        page = self.fetch_webpage(url)
        mobj = re.search(regex, page, regexFlags)
        info = {}

        if mobj is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        for (i, key, err) in matchTuples:
            if mobj.group(i) is None:
                self._downloader.trouble(err)
                return
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
                (1, 'url', u'ERROR: Invalid URL: %s' % url)
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
                (1, 'path',   u'ERROR: could not extract video path: %s' % url),
                (2, 'player', u'ERROR: could not extract video player: %s' % url),
                (3, 'url',    u'ERROR: could not extract video url: %s' % url)
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
                (1, 'url', u'ERROR: Invalid URL: %s' % url)
            ]
        )
        next_url = compat_urllib_parse.unquote(info.get('url'))
        info = self.grep_webpage(
            next_url,
            r'<video lang="%s" ref="(http[^\'"&]*)' % video_lang,
            0,
            [
                (1, 'url', u'ERROR: Could not find <video> tag: %s' % url)
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
                (1, 'id',    u'ERROR: could not extract video id: %s' % url),
                (2, 'title', u'ERROR: could not extract video title: %s' % url),
                (3, 'date',  u'ERROR: could not extract video date: %s' % url),
                (4, 'url',   u'ERROR: could not extract video url: %s' % url)
            ]
        )

        return {
            'id':           info.get('id'),
            'url':          compat_urllib_parse.unquote(info.get('url')),
            'uploader':     u'arte.tv',
            'upload_date':  info.get('date'),
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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self._downloader.to_screen(u'WARNING: Falling back on generic information extractor.')
        self._downloader.to_screen(u'[generic] %s: Downloading webpage' % video_id)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[generic] %s: Extracting information' % video_id)

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen(u'[redirect] Following redirect to %s' % new_url)

    def _test_redirect(self, url):
        """Check if it is a redirect, like url shorteners, in case restart chain."""
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
                        compat_urllib_error.HTTPErrorProcessor, compat_urllib_request.HTTPSHandler]:
            opener.add_handler(handler())

        response = opener.open(HeadRequest(url))
        new_url = response.geturl()

        if url == new_url:
            return False

        self.report_following_redirect(new_url)
        self._downloader.download([new_url])
        return True

    def _real_extract(self, url):
        if self._test_redirect(url): return

        video_id = url.split('/')[-1]
        request = compat_urllib_request.Request(url)
        try:
            self.report_download_webpage(video_id)
            webpage = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return
        except ValueError as err:
            # since this is the last-resort InfoExtractor, if
            # this error is thrown, it'll be thrown here
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        self.report_extraction(video_id)
        # Start with something easy: JW Player in SWFObject
        mobj = re.search(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage)
        if mobj is None:
            # Broaden the search a little bit
            mobj = re.search(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        # It's possible that one of the regexes
        # matched, but returned an empty group:
        if mobj.group(1) is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

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
        mobj = re.search(r'<title>(.*)</title>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return
        video_title = mobj.group(1)

        # video uploader is domain name
        mobj = re.match(r'(?:https?://)?([^/]*)/.*', url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return
        video_uploader = mobj.group(1)

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': video_uploader,
            'upload_date':  None,
            'title':    video_title,
            'ext':      video_extension,
        }]


class YoutubeSearchIE(InfoExtractor):
    """Information Extractor for YouTube search queries."""
    _VALID_URL = r'ytsearch(\d+|all)?:[\s\S]+'
    _API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc'
    _max_youtube_results = 1000
    IE_NAME = u'youtube:search'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_page(self, query, pagenum):
        """Report attempt to download search page with given number."""
        query = query.decode(preferredencoding())
        self._downloader.to_screen(u'[youtube] query "%s": Downloading page %s' % (query, pagenum))

    def _real_extract(self, query):
        mobj = re.match(self._VALID_URL, query)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid search query "%s"' % query)
            return

        prefix, query = query.split(':')
        prefix = prefix[8:]
        query = query.encode('utf-8')
        if prefix == '':
            self._download_n_results(query, 1)
            return
        elif prefix == 'all':
            self._download_n_results(query, self._max_youtube_results)
            return
        else:
            try:
                n = int(prefix)
                if n <= 0:
                    self._downloader.trouble(u'ERROR: invalid download number %s for query "%s"' % (n, query))
                    return
                elif n > self._max_youtube_results:
                    self._downloader.to_stderr(u'WARNING: ytsearch returns max %i results (you requested %i)' % (self._max_youtube_results, n))
                    n = self._max_youtube_results
                self._download_n_results(query, n)
                return
            except ValueError: # parsing prefix as integer fails
                self._download_n_results(query, 1)
                return

    def _download_n_results(self, query, n):
        """Downloads a specified number of results for a query"""

        video_ids = []
        pagenum = 0
        limit = n

        while (50 * pagenum) < limit:
            self.report_download_page(query, pagenum+1)
            result_url = self._API_URL % (compat_urllib_parse.quote_plus(query), (50*pagenum)+1)
            request = compat_urllib_request.Request(result_url)
            try:
                data = compat_urllib_request.urlopen(request).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download API page: %s' % compat_str(err))
                return
            api_response = json.loads(data)['data']

            new_ids = list(video['id'] for video in api_response['items'])
            video_ids += new_ids

            limit = min(n, api_response['totalItems'])
            pagenum += 1

        if len(video_ids) > n:
            video_ids = video_ids[:n]
        for id in video_ids:
            self._downloader.download(['http://www.youtube.com/watch?v=%s' % id])
        return


class GoogleSearchIE(InfoExtractor):
    """Information Extractor for Google Video search queries."""
    _VALID_URL = r'gvsearch(\d+|all)?:[\s\S]+'
    _TEMPLATE_URL = 'http://video.google.com/videosearch?q=%s+site:video.google.com&start=%s&hl=en'
    _VIDEO_INDICATOR = r'<a href="http://video\.google\.com/videoplay\?docid=([^"\&]+)'
    _MORE_PAGES_INDICATOR = r'class="pn" id="pnnext"'
    _max_google_results = 1000
    IE_NAME = u'video.google:search'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_page(self, query, pagenum):
        """Report attempt to download playlist page with given number."""
        query = query.decode(preferredencoding())
        self._downloader.to_screen(u'[video.google] query "%s": Downloading page %s' % (query, pagenum))

    def _real_extract(self, query):
        mobj = re.match(self._VALID_URL, query)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid search query "%s"' % query)
            return

        prefix, query = query.split(':')
        prefix = prefix[8:]
        query = query.encode('utf-8')
        if prefix == '':
            self._download_n_results(query, 1)
            return
        elif prefix == 'all':
            self._download_n_results(query, self._max_google_results)
            return
        else:
            try:
                n = int(prefix)
                if n <= 0:
                    self._downloader.trouble(u'ERROR: invalid download number %s for query "%s"' % (n, query))
                    return
                elif n > self._max_google_results:
                    self._downloader.to_stderr(u'WARNING: gvsearch returns max %i results (you requested %i)' % (self._max_google_results, n))
                    n = self._max_google_results
                self._download_n_results(query, n)
                return
            except ValueError: # parsing prefix as integer fails
                self._download_n_results(query, 1)
                return

    def _download_n_results(self, query, n):
        """Downloads a specified number of results for a query"""

        video_ids = []
        pagenum = 0

        while True:
            self.report_download_page(query, pagenum)
            result_url = self._TEMPLATE_URL % (compat_urllib_parse.quote_plus(query), pagenum*10)
            request = compat_urllib_request.Request(result_url)
            try:
                page = compat_urllib_request.urlopen(request).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
                return

            # Extract video identifiers
            for mobj in re.finditer(self._VIDEO_INDICATOR, page):
                video_id = mobj.group(1)
                if video_id not in video_ids:
                    video_ids.append(video_id)
                    if len(video_ids) == n:
                        # Specified n videos reached
                        for id in video_ids:
                            self._downloader.download(['http://video.google.com/videoplay?docid=%s' % id])
                        return

            if re.search(self._MORE_PAGES_INDICATOR, page) is None:
                for id in video_ids:
                    self._downloader.download(['http://video.google.com/videoplay?docid=%s' % id])
                return

            pagenum = pagenum + 1


class YahooSearchIE(InfoExtractor):
    """Information Extractor for Yahoo! Video search queries."""

    _WORKING = False
    _VALID_URL = r'yvsearch(\d+|all)?:[\s\S]+'
    _TEMPLATE_URL = 'http://video.yahoo.com/search/?p=%s&o=%s'
    _VIDEO_INDICATOR = r'href="http://video\.yahoo\.com/watch/([0-9]+/[0-9]+)"'
    _MORE_PAGES_INDICATOR = r'\s*Next'
    _max_yahoo_results = 1000
    IE_NAME = u'video.yahoo:search'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_page(self, query, pagenum):
        """Report attempt to download playlist page with given number."""
        query = query.decode(preferredencoding())
        self._downloader.to_screen(u'[video.yahoo] query "%s": Downloading page %s' % (query, pagenum))

    def _real_extract(self, query):
        mobj = re.match(self._VALID_URL, query)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid search query "%s"' % query)
            return

        prefix, query = query.split(':')
        prefix = prefix[8:]
        query = query.encode('utf-8')
        if prefix == '':
            self._download_n_results(query, 1)
            return
        elif prefix == 'all':
            self._download_n_results(query, self._max_yahoo_results)
            return
        else:
            try:
                n = int(prefix)
                if n <= 0:
                    self._downloader.trouble(u'ERROR: invalid download number %s for query "%s"' % (n, query))
                    return
                elif n > self._max_yahoo_results:
                    self._downloader.to_stderr(u'WARNING: yvsearch returns max %i results (you requested %i)' % (self._max_yahoo_results, n))
                    n = self._max_yahoo_results
                self._download_n_results(query, n)
                return
            except ValueError: # parsing prefix as integer fails
                self._download_n_results(query, 1)
                return

    def _download_n_results(self, query, n):
        """Downloads a specified number of results for a query"""

        video_ids = []
        already_seen = set()
        pagenum = 1

        while True:
            self.report_download_page(query, pagenum)
            result_url = self._TEMPLATE_URL % (compat_urllib_parse.quote_plus(query), pagenum)
            request = compat_urllib_request.Request(result_url)
            try:
                page = compat_urllib_request.urlopen(request).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
                return

            # Extract video identifiers
            for mobj in re.finditer(self._VIDEO_INDICATOR, page):
                video_id = mobj.group(1)
                if video_id not in already_seen:
                    video_ids.append(video_id)
                    already_seen.add(video_id)
                    if len(video_ids) == n:
                        # Specified n videos reached
                        for id in video_ids:
                            self._downloader.download(['http://video.yahoo.com/watch/%s' % id])
                        return

            if re.search(self._MORE_PAGES_INDICATOR, page) is None:
                for id in video_ids:
                    self._downloader.download(['http://video.yahoo.com/watch/%s' % id])
                return

            pagenum = pagenum + 1


class YoutubePlaylistIE(InfoExtractor):
    """Information Extractor for YouTube playlists."""

    _VALID_URL = r'(?:(?:https?://)?(?:\w+\.)?youtube\.com/(?:(?:course|view_play_list|my_playlists|artist|playlist)\?.*?(p|a|list)=|user/.*?/user/|p/|user/.*?#[pg]/c/)(?:PL|EC)?|PL|EC)([0-9A-Za-z-_]{10,})(?:/.*?/([0-9A-Za-z_-]+))?.*'
    _TEMPLATE_URL = 'http://www.youtube.com/%s?%s=%s&page=%s&gl=US&hl=en'
    _VIDEO_INDICATOR_TEMPLATE = r'/watch\?v=(.+?)&amp;([^&"]+&amp;)*list=.*?%s'
    _MORE_PAGES_INDICATOR = u"Next \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    IE_NAME = u'youtube:playlist'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_page(self, playlist_id, pagenum):
        """Report attempt to download playlist page with given number."""
        self._downloader.to_screen(u'[youtube] PL %s: Downloading page #%s' % (playlist_id, pagenum))

    def _real_extract(self, url):
        # Extract playlist id
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid url: %s' % url)
            return

        # Single video case
        if mobj.group(3) is not None:
            self._downloader.download([mobj.group(3)])
            return

        # Download playlist pages
        # prefix is 'p' as default for playlists but there are other types that need extra care
        playlist_prefix = mobj.group(1)
        if playlist_prefix == 'a':
            playlist_access = 'artist'
        else:
            playlist_prefix = 'p'
            playlist_access = 'view_play_list'
        playlist_id = mobj.group(2)
        video_ids = []
        pagenum = 1

        while True:
            self.report_download_page(playlist_id, pagenum)
            url = self._TEMPLATE_URL % (playlist_access, playlist_prefix, playlist_id, pagenum)
            request = compat_urllib_request.Request(url)
            try:
                page = compat_urllib_request.urlopen(request).read().decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
                return

            # Extract video identifiers
            ids_in_page = []
            for mobj in re.finditer(self._VIDEO_INDICATOR_TEMPLATE % playlist_id, page):
                if mobj.group(1) not in ids_in_page:
                    ids_in_page.append(mobj.group(1))
            video_ids.extend(ids_in_page)

            if self._MORE_PAGES_INDICATOR not in page:
                break
            pagenum = pagenum + 1

        total = len(video_ids)

        playliststart = self._downloader.params.get('playliststart', 1) - 1
        playlistend = self._downloader.params.get('playlistend', -1)
        if playlistend == -1:
            video_ids = video_ids[playliststart:]
        else:
            video_ids = video_ids[playliststart:playlistend]

        if len(video_ids) == total:
            self._downloader.to_screen(u'[youtube] PL %s: Found %i videos' % (playlist_id, total))
        else:
            self._downloader.to_screen(u'[youtube] PL %s: Found %i videos, downloading %i' % (playlist_id, total, len(video_ids)))

        for id in video_ids:
            self._downloader.download(['http://www.youtube.com/watch?v=%s' % id])
        return


class YoutubeChannelIE(InfoExtractor):
    """Information Extractor for YouTube channels."""

    _VALID_URL = r"^(?:https?://)?(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/([0-9A-Za-z_-]+)(?:/.*)?$"
    _TEMPLATE_URL = 'http://www.youtube.com/channel/%s/videos?sort=da&flow=list&view=0&page=%s&gl=US&hl=en'
    _MORE_PAGES_INDICATOR = u"Next \N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}"
    IE_NAME = u'youtube:channel'

    def report_download_page(self, channel_id, pagenum):
        """Report attempt to download channel page with given number."""
        self._downloader.to_screen(u'[youtube] Channel %s: Downloading page #%s' % (channel_id, pagenum))

    def _real_extract(self, url):
        # Extract channel id
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid url: %s' % url)
            return

        # Download channel pages
        channel_id = mobj.group(1)
        video_ids = []
        pagenum = 1

        while True:
            self.report_download_page(channel_id, pagenum)
            url = self._TEMPLATE_URL % (channel_id, pagenum)
            request = compat_urllib_request.Request(url)
            try:
                page = compat_urllib_request.urlopen(request).read().decode('utf8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
                return

            # Extract video identifiers
            ids_in_page = []
            for mobj in re.finditer(r'href="/watch\?v=([0-9A-Za-z_-]+)&', page):
                if mobj.group(1) not in ids_in_page:
                    ids_in_page.append(mobj.group(1))
            video_ids.extend(ids_in_page)

            if self._MORE_PAGES_INDICATOR not in page:
                break
            pagenum = pagenum + 1

        self._downloader.to_screen(u'[youtube] Channel %s: Found %i videos' % (channel_id, len(video_ids)))

        for id in video_ids:
            self._downloader.download(['http://www.youtube.com/watch?v=%s' % id])
        return


class YoutubeUserIE(InfoExtractor):
    """Information Extractor for YouTube users."""

    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/user/)|ytuser:)([A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'http://gdata.youtube.com/feeds/api/users/%s'
    _GDATA_PAGE_SIZE = 50
    _GDATA_URL = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d'
    _VIDEO_INDICATOR = r'/watch\?v=(.+?)[\<&]'
    IE_NAME = u'youtube:user'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_page(self, username, start_index):
        """Report attempt to download user page."""
        self._downloader.to_screen(u'[youtube] user %s: Downloading video ids from %d to %d' %
                (username, start_index, start_index + self._GDATA_PAGE_SIZE))

    def _real_extract(self, url):
        # Extract username
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid url: %s' % url)
            return

        username = mobj.group(1)

        # Download video ids using YouTube Data API. Result size per
        # query is limited (currently to 50 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        video_ids = []
        pagenum = 0

        while True:
            start_index = pagenum * self._GDATA_PAGE_SIZE + 1
            self.report_download_page(username, start_index)

            request = compat_urllib_request.Request(self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index))

            try:
                page = compat_urllib_request.urlopen(request).read().decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
                return

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

        all_ids_count = len(video_ids)
        playliststart = self._downloader.params.get('playliststart', 1) - 1
        playlistend = self._downloader.params.get('playlistend', -1)

        if playlistend == -1:
            video_ids = video_ids[playliststart:]
        else:
            video_ids = video_ids[playliststart:playlistend]

        self._downloader.to_screen(u"[youtube] user %s: Collected %d video ids (downloading %d of them)" %
                (username, all_ids_count, len(video_ids)))

        for video_id in video_ids:
            self._downloader.download(['http://www.youtube.com/watch?v=%s' % video_id])


class BlipTVUserIE(InfoExtractor):
    """Information Extractor for blip.tv users."""

    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?blip\.tv/)|bliptvuser:)([^/]+)/*$'
    _PAGE_SIZE = 12
    IE_NAME = u'blip.tv:user'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_page(self, username, pagenum):
        """Report attempt to download user page."""
        self._downloader.to_screen(u'[%s] user %s: Downloading video ids from page %d' %
                (self.IE_NAME, username, pagenum))

    def _real_extract(self, url):
        # Extract username
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid url: %s' % url)
            return

        username = mobj.group(1)

        page_base = 'http://m.blip.tv/pr/show_get_full_episode_list?users_id=%s&lite=0&esi=1'

        request = compat_urllib_request.Request(url)

        try:
            page = compat_urllib_request.urlopen(request).read().decode('utf-8')
            mobj = re.search(r'data-users-id="([^"]+)"', page)
            page_base = page_base % mobj.group(1)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
            return


        # Download video ids using BlipTV Ajax calls. Result size per
        # query is limited (currently to 12 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        video_ids = []
        pagenum = 1

        while True:
            self.report_download_page(username, pagenum)

            request = compat_urllib_request.Request( page_base + "&page=" + str(pagenum) )

            try:
                page = compat_urllib_request.urlopen(request).read().decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % str(err))
                return

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

        all_ids_count = len(video_ids)
        playliststart = self._downloader.params.get('playliststart', 1) - 1
        playlistend = self._downloader.params.get('playlistend', -1)

        if playlistend == -1:
            video_ids = video_ids[playliststart:]
        else:
            video_ids = video_ids[playliststart:playlistend]

        self._downloader.to_screen(u"[%s] user %s: Collected %d video ids (downloading %d of them)" %
                (self.IE_NAME, username, all_ids_count, len(video_ids)))

        for video_id in video_ids:
            self._downloader.download([u'http://blip.tv/'+video_id])


class DepositFilesIE(InfoExtractor):
    """Information extractor for depositfiles.com"""

    _VALID_URL = r'(?:http://)?(?:\w+\.)?depositfiles\.com/(?:../(?#locale))?files/(.+)'

    def report_download_webpage(self, file_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[DepositFiles] %s: Downloading webpage' % file_id)

    def report_extraction(self, file_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[DepositFiles] %s: Extracting information' % file_id)

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
            self._downloader.trouble(u'ERROR: Unable to retrieve file webpage: %s' % compat_str(err))
            return

        # Search for the real file URL
        mobj = re.search(r'<form action="(http://fileshare.+?)"', webpage)
        if (mobj is None) or (mobj.group(1) is None):
            # Try to figure out reason of the error.
            mobj = re.search(r'<strong>(Attention.*?)</strong>', webpage, re.DOTALL)
            if (mobj is not None) and (mobj.group(1) is not None):
                restriction_message = re.sub('\s+', ' ', mobj.group(1)).strip()
                self._downloader.trouble(u'ERROR: %s' % restriction_message)
            else:
                self._downloader.trouble(u'ERROR: unable to extract download URL from: %s' % url)
            return

        file_url = mobj.group(1)
        file_extension = os.path.splitext(file_url)[1][1:]

        # Search for file title
        mobj = re.search(r'<b title="(.*?)">', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return
        file_title = mobj.group(1).decode('utf-8')

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

    _WORKING = False
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?facebook\.com/(?:video/video|photo)\.php\?(?:.*?)v=(?P<ID>\d+)(?:.*)'
    _LOGIN_URL = 'https://login.facebook.com/login.php?m&next=http%3A%2F%2Fm.facebook.com%2Fhome.php&'
    _NETRC_MACHINE = 'facebook'
    _available_formats = ['video', 'highqual', 'lowqual']
    _video_extensions = {
        'video': 'mp4',
        'highqual': 'mp4',
        'lowqual': 'mp4',
    }
    IE_NAME = u'facebook'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def _reporter(self, message):
        """Add header and report message."""
        self._downloader.to_screen(u'[facebook] %s' % message)

    def report_login(self):
        """Report attempt to log in."""
        self._reporter(u'Logging in')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self._reporter(u'%s: Downloading video webpage' % video_id)

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self._reporter(u'%s: Extracting video information' % video_id)

    def _parse_page(self, video_webpage):
        """Extract video information from page"""
        # General data
        data = {'title': r'\("video_title", "(.*?)"\)',
            'description': r'<div class="datawrap">(.*?)</div>',
            'owner': r'\("video_owner_name", "(.*?)"\)',
            'thumbnail':  r'\("thumb_url", "(?P<THUMB>.*?)"\)',
            }
        video_info = {}
        for piece in data.keys():
            mobj = re.search(data[piece], video_webpage)
            if mobj is not None:
                video_info[piece] = compat_urllib_parse.unquote_plus(mobj.group(1).decode("unicode_escape"))

        # Video urls
        video_urls = {}
        for fmt in self._available_formats:
            mobj = re.search(r'\("%s_src\", "(.+?)"\)' % fmt, video_webpage)
            if mobj is not None:
                # URL is in a Javascript segment inside an escaped Unicode format within
                # the generally utf-8 page
                video_urls[fmt] = compat_urllib_parse.unquote_plus(mobj.group(1).decode("unicode_escape"))
        video_info['video_urls'] = video_urls

        return video_info

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
                self._downloader.to_stderr(u'WARNING: parsing .netrc: %s' % compat_str(err))
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
                self._downloader.to_stderr(u'WARNING: unable to log in: bad username/password, or exceded login rate limit (~3/min). Check credentials or wait.')
                return
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.to_stderr(u'WARNING: unable to log in: %s' % compat_str(err))
            return

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group('ID')

        # Get video webpage
        self.report_video_webpage_download(video_id)
        request = compat_urllib_request.Request('https://www.facebook.com/video/video.php?v=%s' % video_id)
        try:
            page = compat_urllib_request.urlopen(request)
            video_webpage = page.read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % compat_str(err))
            return

        # Start extracting information
        self.report_information_extraction(video_id)

        # Extract information
        video_info = self._parse_page(video_webpage)

        # uploader
        if 'owner' not in video_info:
            self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
            return
        video_uploader = video_info['owner']

        # title
        if 'title' not in video_info:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = video_info['title']
        video_title = video_title.decode('utf-8')

        # thumbnail image
        if 'thumbnail' not in video_info:
            self._downloader.trouble(u'WARNING: unable to extract video thumbnail')
            video_thumbnail = ''
        else:
            video_thumbnail = video_info['thumbnail']

        # upload date
        upload_date = None
        if 'upload_date' in video_info:
            upload_time = video_info['upload_date']
            timetuple = email.utils.parsedate_tz(upload_time)
            if timetuple is not None:
                try:
                    upload_date = time.strftime('%Y%m%d', timetuple[0:9])
                except:
                    pass

        # description
        video_description = video_info.get('description', 'No description available.')

        url_map = video_info['video_urls']
        if url_map:
            # Decide which formats to download
            req_format = self._downloader.params.get('format', None)
            format_limit = self._downloader.params.get('format_limit', None)

            if format_limit is not None and format_limit in self._available_formats:
                format_list = self._available_formats[self._available_formats.index(format_limit):]
            else:
                format_list = self._available_formats
            existing_formats = [x for x in format_list if x in url_map]
            if len(existing_formats) == 0:
                self._downloader.trouble(u'ERROR: no known formats available for video')
                return
            if req_format is None:
                video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
            elif req_format == 'worst':
                video_url_list = [(existing_formats[len(existing_formats)-1], url_map[existing_formats[len(existing_formats)-1]])] # worst quality
            elif req_format == '-1':
                video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
            else:
                # Specific format
                if req_format not in url_map:
                    self._downloader.trouble(u'ERROR: requested format not available')
                    return
                video_url_list = [(req_format, url_map[req_format])] # Specific format

        results = []
        for format_param, video_real_url in video_url_list:
            # Extension
            video_extension = self._video_extensions.get(format_param, 'mp4')

            results.append({
                'id':       video_id.decode('utf-8'),
                'url':      video_real_url.decode('utf-8'),
                'uploader': video_uploader.decode('utf-8'),
                'upload_date':  upload_date,
                'title':    video_title,
                'ext':      video_extension.decode('utf-8'),
                'format':   (format_param is None and u'NA' or format_param.decode('utf-8')),
                'thumbnail':    video_thumbnail.decode('utf-8'),
                'description':  video_description.decode('utf-8'),
            })
        return results

class BlipTVIE(InfoExtractor):
    """Information extractor for blip.tv"""

    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?blip\.tv(/.+)$'
    _URL_EXT = r'^.*\.([a-z0-9]+)$'
    IE_NAME = u'blip.tv'

    def report_extraction(self, file_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, file_id))

    def report_direct_download(self, title):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Direct download detected' % (self.IE_NAME, title))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

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
                self._downloader.trouble(u'ERROR: unable to read video info webpage: %s' % compat_str(err))
                return

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
                self._downloader.trouble(u'ERROR: unable to parse video information: %s' % repr(err))
                return

        return [info]


class MyVideoIE(InfoExtractor):
    """Information Extractor for myvideo.de."""

    _VALID_URL = r'(?:http://)?(?:www\.)?myvideo\.de/watch/([0-9]+)/([^?/]+).*'
    IE_NAME = u'myvideo'

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[myvideo] %s: Extracting information' % video_id)

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._download.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group(1)

        # Get video webpage
        webpage_url = 'http://www.myvideo.de/watch/%s' % video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)
        mobj = re.search(r'<link rel=\'image_src\' href=\'(http://is[0-9].myvideo\.de/de/movie[0-9]+/[a-f0-9]+)/thumbs/[^.]+\.jpg\' />',
                 webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract media URL')
            return
        video_url = mobj.group(1) + ('/%s.flv' % video_id)

        mobj = re.search('<title>([^<]+)</title>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract title')
            return

        video_title = mobj.group(1)

        return [{
            'id':       video_id,
            'url':      video_url,
            'uploader': None,
            'upload_date':  None,
            'title':    video_title,
            'ext':      u'flv',
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

    def suitable(self, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(self._VALID_URL, url, re.VERBOSE) is not None

    def report_extraction(self, episode_id):
        self._downloader.to_screen(u'[comedycentral] %s: Extracting information' % episode_id)

    def report_config_download(self, episode_id, media_id):
        self._downloader.to_screen(u'[comedycentral] %s: Downloading configuration for %s' % (episode_id, media_id))

    def report_index_download(self, episode_id):
        self._downloader.to_screen(u'[comedycentral] %s: Downloading show index' % episode_id)

    def _print_formats(self, formats):
        print('Available formats:')
        for x in formats:
            print('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'mp4'), self._video_dimensions.get(x, '???')))


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

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

        req = compat_urllib_request.Request(url)
        self.report_extraction(epTitle)
        try:
            htmlHandle = compat_urllib_request.urlopen(req)
            html = htmlHandle.read()
            webpage = html.decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
            return
        if dlNewest:
            url = htmlHandle.geturl()
            mobj = re.match(self._VALID_URL, url, re.VERBOSE)
            if mobj is None:
                self._downloader.trouble(u'ERROR: Invalid redirected URL: ' + url)
                return
            if mobj.group('episode') == '':
                self._downloader.trouble(u'ERROR: Redirected URL is still not specific: ' + url)
                return
            epTitle = mobj.group('episode')

        mMovieParams = re.findall('(?:<param name="movie" value="|var url = ")(http://media.mtvnservices.com/([^"]*(?:episode|video).*?:.*?))"', webpage)

        if len(mMovieParams) == 0:
            # The Colbert Report embeds the information in a without
            # a URL prefix; so extract the alternate reference
            # and then add the URL prefix manually.

            altMovieParams = re.findall('data-mgid="([^"]*(?:episode|video).*?:.*?)"', webpage)
            if len(altMovieParams) == 0:
                self._downloader.trouble(u'ERROR: unable to find Flash URL in webpage ' + url)
                return
            else:
                mMovieParams = [("http://media.mtvnservices.com/" + altMovieParams[0], altMovieParams[0])]

        uri = mMovieParams[0][1]
        indexUrl = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?' + compat_urllib_parse.urlencode({'uri': uri})
        self.report_index_download(epTitle)
        try:
            indexXml = compat_urllib_request.urlopen(indexUrl).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download episode index: ' + compat_str(err))
            return

        results = []

        idoc = xml.etree.ElementTree.fromstring(indexXml)
        itemEls = idoc.findall('.//item')
        for partNum,itemEl in enumerate(itemEls):
            mediaId = itemEl.findall('./guid')[0].text
            shortMediaId = mediaId.split(':')[-1]
            showId = mediaId.split(':')[-2].replace('.com', '')
            officialTitle = itemEl.findall('./title')[0].text
            officialDate = itemEl.findall('./pubDate')[0].text

            configUrl = ('http://www.comedycentral.com/global/feeds/entertainment/media/mediaGenEntertainment.jhtml?' +
                        compat_urllib_parse.urlencode({'uri': mediaId}))
            configReq = compat_urllib_request.Request(configUrl)
            self.report_config_download(epTitle, shortMediaId)
            try:
                configXml = compat_urllib_request.urlopen(configReq).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download webpage: %s' % compat_str(err))
                return

            cdoc = xml.etree.ElementTree.fromstring(configXml)
            turls = []
            for rendition in cdoc.findall('.//rendition'):
                finfo = (rendition.attrib['bitrate'], rendition.findall('./src')[0].text)
                turls.append(finfo)

            if len(turls) == 0:
                self._downloader.trouble(u'\nERROR: unable to download ' + mediaId + ': No videos found')
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

    def report_extraction(self, showName):
        self._downloader.to_screen(u'[escapist] %s: Extracting information' % showName)

    def report_config_download(self, showName):
        self._downloader.to_screen(u'[escapist] %s: Downloading configuration' % showName)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        showName = mobj.group('showname')
        videoId = mobj.group('episode')

        self.report_extraction(showName)
        try:
            webPage = compat_urllib_request.urlopen(url)
            webPageBytes = webPage.read()
            m = re.match(r'text/html; charset="?([^"]+)"?', webPage.headers['Content-Type'])
            webPage = webPageBytes.decode(m.group(1) if m else 'utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download webpage: ' + compat_str(err))
            return

        descMatch = re.search('<meta name="description" content="([^"]*)"', webPage)
        description = unescapeHTML(descMatch.group(1))
        imgMatch = re.search('<meta property="og:image" content="([^"]*)"', webPage)
        imgUrl = unescapeHTML(imgMatch.group(1))
        playerUrlMatch = re.search('<meta property="og:video" content="([^"]*)"', webPage)
        playerUrl = unescapeHTML(playerUrlMatch.group(1))
        configUrlMatch = re.search('config=(.*)$', playerUrl)
        configUrl = compat_urllib_parse.unquote(configUrlMatch.group(1))

        self.report_config_download(showName)
        try:
            configJSON = compat_urllib_request.urlopen(configUrl)
            m = re.match(r'text/html; charset="?([^"]+)"?', configJSON.headers['Content-Type'])
            configJSON = configJSON.read().decode(m.group(1) if m else 'utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download configuration: ' + compat_str(err))
            return

        # Technically, it's JavaScript, not JSON
        configJSON = configJSON.replace("'", '"')

        try:
            config = json.loads(configJSON)
        except (ValueError,) as err:
            self._downloader.trouble(u'ERROR: Invalid JSON in configuration file: ' + compat_str(err))
            return

        playlist = config['playlist']
        videoUrl = playlist[1]['url']

        info = {
            'id': videoId,
            'url': videoUrl,
            'uploader': showName,
            'upload_date': None,
            'title': showName,
            'ext': 'flv',
            'thumbnail': imgUrl,
            'description': description,
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
        self._downloader.to_screen(u'[%s] %s: Downloading XML manifest' % (self.IE_NAME, video_id))

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
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
            self._downloader.trouble(u'ERROR: unable to download video info XML: %s' % compat_str(err))
            return

        mdoc = xml.etree.ElementTree.fromstring(metaXml)
        try:
            videoNode = mdoc.findall('./video')[0]
            info['description'] = videoNode.findall('./description')[0].text
            info['title'] = videoNode.findall('./caption')[0].text
            info['thumbnail'] = videoNode.findall('./thumbnail')[0].text
            manifest_url = videoNode.findall('./file')[0].text
        except IndexError:
            self._downloader.trouble(u'\nERROR: Invalid metadata XML file')
            return

        manifest_url += '?hdcore=2.10.3'
        self.report_manifest(video_id)
        try:
            manifestXml = compat_urllib_request.urlopen(manifest_url).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video info XML: %s' % compat_str(err))
            return

        adoc = xml.etree.ElementTree.fromstring(manifestXml)
        try:
            media_node = adoc.findall('./{http://ns.adobe.com/f4m/1.0}media')[0]
            node_id = media_node.attrib['url']
            video_id = adoc.findall('./{http://ns.adobe.com/f4m/1.0}id')[0].text
        except IndexError as err:
            self._downloader.trouble(u'\nERROR: Invalid manifest file')
            return

        url_pr = compat_urllib_parse_urlparse(manifest_url)
        url = url_pr.scheme + '://' + url_pr.netloc + '/z' + video_id[:-2] + '/' + node_id + 'Seg1-Frag1'

        info['url'] = url
        info['ext'] = 'f4f'
        return [info]


class XVideosIE(InfoExtractor):
    """Information extractor for xvideos.com"""

    _VALID_URL = r'^(?:https?://)?(?:www\.)?xvideos\.com/video([0-9]+)(?:.*)'
    IE_NAME = u'xvideos'

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group(1)

        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)


        # Extract video URL
        mobj = re.search(r'flv_url=(.+?)&', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video url')
            return
        video_url = compat_urllib_parse.unquote(mobj.group(1))


        # Extract title
        mobj = re.search(r'<title>(.*?)\s+-\s+XVID', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = mobj.group(1)


        # Extract video thumbnail
        mobj = re.search(r'http://(?:img.*?\.)xvideos.com/videos/thumbs/[a-fA-F0-9]+/[a-fA-F0-9]+/[a-fA-F0-9]+/[a-fA-F0-9]+/([a-fA-F0-9.]+jpg)', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video thumbnail')
            return
        video_thumbnail = mobj.group(0)

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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_resolve(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Resolving id' % (self.IE_NAME, video_id))

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Retrieving stream' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        # extract uploader (which is in the url)
        uploader = mobj.group(1)
        # extract simple title (uploader + slug of song title)
        slug_title =  mobj.group(2)
        simple_title = uploader + u'-' + slug_title

        self.report_resolve('%s/%s' % (uploader, slug_title))

        url = 'http://soundcloud.com/%s/%s' % (uploader, slug_title)
        resolv_url = 'http://api.soundcloud.com/resolve.json?url=' + url + '&client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        request = compat_urllib_request.Request(resolv_url)
        try:
            info_json_bytes = compat_urllib_request.urlopen(request).read()
            info_json = info_json_bytes.decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % compat_str(err))
            return

        info = json.loads(info_json)
        video_id = info['id']
        self.report_extraction('%s/%s' % (uploader, slug_title))

        streams_url = 'https://api.sndcdn.com/i1/tracks/' + str(video_id) + '/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28'
        request = compat_urllib_request.Request(streams_url)
        try:
            stream_json_bytes = compat_urllib_request.urlopen(request).read()
            stream_json = stream_json_bytes.decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download stream definitions: %s' % compat_str(err))
            return

        streams = json.loads(stream_json)
        mediaURL = streams['http_mp3_128_url']

        return [{
            'id':       info['id'],
            'url':      mediaURL,
            'uploader': info['user']['username'],
            'upload_date':  info['created_at'],
            'title':    info['title'],
            'ext':      u'mp3',
            'description': info['description'],
        }]


class InfoQIE(InfoExtractor):
    """Information extractor for infoq.com"""
    _VALID_URL = r'^(?:https?://)?(?:www\.)?infoq\.com/[^/]+/[^/]+$'

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        webpage = self._download_webpage(url, video_id=url)
        self.report_extraction(url)

        # Extract video URL
        mobj = re.search(r"jsclassref='([^']*)'", webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video url')
            return
        real_id = compat_urllib_parse.unquote(base64.b64decode(mobj.group(1).encode('ascii')).decode('utf-8'))
        video_url = 'rtmpe://video.infoq.com/cfx/st/' + real_id

        # Extract title
        mobj = re.search(r'contentTitle = "(.*?)";', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = mobj.group(1)

        # Extract description
        video_description = u'No description available.'
        mobj = re.search(r'<meta name="description" content="(.*)"(?:\s*/)?>', webpage)
        if mobj is not None:
            video_description = mobj.group(1)

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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_download_json(self, file_id):
        """Report JSON download."""
        self._downloader.to_screen(u'[%s] Downloading json' % self.IE_NAME)

    def report_extraction(self, file_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, file_id))

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
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
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
            self._downloader.trouble(u'ERROR: Unable to retrieve file: %s' % compat_str(err))
            return

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
                self._downloader.trouble(u'ERROR: format is not available')
                return

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

    def report_download_webpage(self, objid):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, objid))

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

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
                self._downloader.trouble(u'ERROR: unable to download video info XML: %s' % compat_str(err))
                return
            mdoc = xml.etree.ElementTree.fromstring(metaXml)
            try:
                info['title'] = mdoc.findall('./title')[0].text
                info['url'] = baseUrl + mdoc.findall('./videoFile')[0].text
            except IndexError:
                self._downloader.trouble(u'\nERROR: Invalid metadata XML file')
                return
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

            self.report_download_webpage(info['id'])
            try:
                coursepage = compat_urllib_request.urlopen(url).read()
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self._downloader.trouble(u'ERROR: unable to download course info page: ' + compat_str(err))
                return

            m = re.search('<h1>([^<]+)</h1>', coursepage)
            if m:
                info['title'] = unescapeHTML(m.group(1))
            else:
                info['title'] = info['id']

            m = re.search('<description>([^<]+)</description>', coursepage)
            if m:
                info['description'] = unescapeHTML(m.group(1))

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
                self._downloader.trouble(u'ERROR: unable to download course info page: ' + compat_str(err))
                return

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

    def report_extraction(self, video_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        if not mobj.group('proto'):
            url = 'http://' + url
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<meta name="mtv_vt" content="([^"]+)"/>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract song name')
            return
        song_name = unescapeHTML(mobj.group(1).decode('iso-8859-1'))
        mobj = re.search(r'<meta name="mtv_an" content="([^"]+)"/>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract performer')
            return
        performer = unescapeHTML(mobj.group(1).decode('iso-8859-1'))
        video_title = performer + ' - ' + song_name

        mobj = re.search(r'<meta name="mtvn_uri" content="([^"]+)"/>', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to mtvn_uri')
            return
        mtvn_uri = mobj.group(1)

        mobj = re.search(r'MTVN.Player.defaultPlaylistId = ([0-9]+);', webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract content id')
            return
        content_id = mobj.group(1)

        videogen_url = 'http://www.mtv.com/player/includes/mediaGen.jhtml?uri=' + mtvn_uri + '&id=' + content_id + '&vid=' + video_id + '&ref=www.mtvn.com&viewUri=' + mtvn_uri
        self.report_extraction(video_id)
        request = compat_urllib_request.Request(videogen_url)
        try:
            metadataXml = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video metadata: %s' % compat_str(err))
            return

        mdoc = xml.etree.ElementTree.fromstring(metadataXml)
        renditions = mdoc.findall('.//rendition')

        # For now, always pick the highest quality.
        rendition = renditions[-1]

        try:
            _,_,ext = rendition.attrib['type'].partition('/')
            format = ext + '-' + rendition.attrib['width'] + 'x' + rendition.attrib['height'] + '_' + rendition.attrib['bitrate']
            video_url = rendition.find('./src').text
        except KeyError:
            self._downloader.trouble('Invalid rendition field.')
            return

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

    def report_download_webpage(self, file_id):
        """Report webpage download."""
        self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, file_id))

    def report_extraction(self, file_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, file_id))

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
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group('ID')

        info_url = 'http://v.youku.com/player/getPlayList/VideoIDS/' + video_id

        request = compat_urllib_request.Request(info_url, None, std_headers)
        try:
            self.report_download_webpage(video_id)
            jsondata = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return

        self.report_extraction(video_id)
        try:
            jsonstr = jsondata.decode('utf-8')
            config = json.loads(jsonstr)

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
            self._downloader.trouble(u'ERROR: unable to extract info section')
            return

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

    def report_webpage(self, video_id):
        """Report information extraction"""
        self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, video_id))

    def report_extraction(self, video_id):
        """Report information extraction"""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return
        video_id = mobj.group(1)

        self.report_webpage(video_id)

        # Get webpage content
        try:
            webpage_bytes = compat_urllib_request.urlopen(url).read()
            webpage = webpage_bytes.decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % err)
            return

        result = re.search(self.VIDEO_URL_RE, webpage)
        if result is None:
            self._downloader.trouble(u'ERROR: unable to extract video url')
            return
        video_url = compat_urllib_parse.unquote(result.group(1))

        result = re.search(self.VIDEO_TITLE_RE, webpage)
        if result is None:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        video_title = result.group(1)

        result = re.search(self.VIDEO_THUMB_RE, webpage)
        if result is None:
            self._downloader.trouble(u'ERROR: unable to extract video thumbnail')
            return
        video_thumbnail = result.group(1)

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

    def __init__(self, downloader=None):
        InfoExtractor.__init__(self, downloader)

    def report_extract_entry(self, url):
        """Report downloading extry"""
        self._downloader.to_screen(u'[plus.google] Downloading entry: %s' % url)

    def report_date(self, upload_date):
        """Report downloading extry"""
        self._downloader.to_screen(u'[plus.google] Entry date: %s' % upload_date)

    def report_uploader(self, uploader):
        """Report downloading extry"""
        self._downloader.to_screen(u'[plus.google] Uploader: %s' % uploader)

    def report_title(self, video_title):
        """Report downloading extry"""
        self._downloader.to_screen(u'[plus.google] Title: %s' % video_title)

    def report_extract_vid_page(self, video_page):
        """Report information extraction."""
        self._downloader.to_screen(u'[plus.google] Extracting video page: %s' % video_page)

    def _real_extract(self, url):
        # Extract id from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
            return

        post_url = mobj.group(0)
        video_id = mobj.group(1)

        video_extension = 'flv'

        # Step 1, Retrieve post webpage to extract further information
        self.report_extract_entry(post_url)
        request = compat_urllib_request.Request(post_url)
        try:
            webpage = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve entry webpage: %s' % compat_str(err))
            return

        # Extract update date
        upload_date = None
        pattern = 'title="Timestamp">(.*?)</a>'
        mobj = re.search(pattern, webpage)
        if mobj:
            upload_date = mobj.group(1)
            # Convert timestring to a format suitable for filename
            upload_date = datetime.datetime.strptime(upload_date, "%Y-%m-%d")
            upload_date = upload_date.strftime('%Y%m%d')
        self.report_date(upload_date)

        # Extract uploader
        uploader = None
        pattern = r'rel\="author".*?>(.*?)</a>'
        mobj = re.search(pattern, webpage)
        if mobj:
            uploader = mobj.group(1)
        self.report_uploader(uploader)

        # Extract title
        # Get the first line for title
        video_title = u'NA'
        pattern = r'<meta name\=\"Description\" content\=\"(.*?)[\n<"]'
        mobj = re.search(pattern, webpage)
        if mobj:
            video_title = mobj.group(1)
        self.report_title(video_title)

        # Step 2, Stimulate clicking the image box to launch video
        pattern = '"(https\://plus\.google\.com/photos/.*?)",,"image/jpeg","video"\]'
        mobj = re.search(pattern, webpage)
        if mobj is None:
            self._downloader.trouble(u'ERROR: unable to extract video page URL')

        video_page = mobj.group(1)
        request = compat_urllib_request.Request(video_page)
        try:
            webpage = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % compat_str(err))
            return
        self.report_extract_vid_page(video_page)


        # Extract video links on video page
        """Extract video links of all sizes"""
        pattern = '\d+,\d+,(\d+),"(http\://redirector\.googlevideo\.com.*?)"'
        mobj = re.findall(pattern, webpage)
        if len(mobj) == 0:
            self._downloader.trouble(u'ERROR: unable to extract video links')

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
    _VALID_URL = r'^(?:https?://)?(?:watch\.|www\.)?nba\.com/(?:nba/)?video(/[^?]*)(\?.*)?$'
    IE_NAME = u'nba'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group(1)
        if video_id.endswith('/index.html'):
            video_id = video_id[:-len('/index.html')]

        webpage = self._download_webpage(url, video_id)

        video_url = u'http://ht-mobile.cdn.turner.com/nba/big' + video_id + '_nba_1280x720.mp4'
        def _findProp(rexp, default=None):
            m = re.search(rexp, webpage)
            if m:
                return unescapeHTML(m.group(1))
            else:
                return default

        shortened_video_id = video_id.rpartition('/')[2]
        title = _findProp(r'<meta property="og:title" content="(.*?)"', shortened_video_id).replace('NBA.com: ', '')
        info = {
            'id': shortened_video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'uploader_date': _findProp(r'<b>Date:</b> (.*?)</div>'),
            'description': _findProp(r'<div class="description">(.*?)</h1>'),
        }
        return [info]

class JustinTVIE(InfoExtractor):
    """Information extractor for justin.tv and twitch.tv"""
    # TODO: One broadcast may be split into multiple videos. The key
    # 'broadcast_id' is the same for all parts, and 'broadcast_part'
    # starts at 1 and increases. Can we treat all parts as one video?

    _VALID_URL = r"""(?x)^(?:http://)?(?:www\.)?(?:twitch|justin)\.tv/
        ([^/]+)(?:/b/([^/]+))?/?(?:\#.*)?$"""
    _JUSTIN_PAGE_LIMIT = 100
    IE_NAME = u'justin.tv'

    def report_extraction(self, file_id):
        """Report information extraction."""
        self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, file_id))

    def report_download_page(self, channel, offset):
        """Report attempt to download a single page of videos."""
        self._downloader.to_screen(u'[%s] %s: Downloading video information from %d to %d' %
                (self.IE_NAME, channel, offset, offset + self._JUSTIN_PAGE_LIMIT))

    # Return count of items, list of *valid* items
    def _parse_page(self, url):
        try:
            urlh = compat_urllib_request.urlopen(url)
            webpage_bytes = urlh.read()
            webpage = webpage_bytes.decode('utf-8', 'ignore')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.trouble(u'ERROR: unable to download video info JSON: %s' % compat_str(err))
            return

        response = json.loads(webpage)
        if type(response) != list:
            error_text = response.get('error', 'unknown error')
            self._downloader.trouble(u'ERROR: Justin.tv API: %s' % error_text)
            return
        info = []
        for clip in response:
            video_url = clip['video_file_url']
            if video_url:
                video_extension = os.path.splitext(video_url)[1][1:]
                video_date = re.sub('-', '', clip['start_time'][:10])
                video_uploader_id = clip.get('user_id', clip.get('channel_id'))
                info.append({
                    'id': clip['id'],
                    'url': video_url,
                    'title': clip['title'],
                    'uploader': clip.get('channel_name', video_uploader_id),
                    'uploader_id': video_uploader_id,
                    'upload_date': video_date,
                    'ext': video_extension,
                })
        return (len(response), info)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        api = 'http://api.justin.tv'
        video_id = mobj.group(mobj.lastindex)
        paged = False
        if mobj.lastindex == 1:
            paged = True
            api += '/channel/archives/%s.json'
        else:
            api += '/broadcast/by_archive/%s.json'
        api = api % (video_id,)

        self.report_extraction(video_id)

        info = []
        offset = 0
        limit = self._JUSTIN_PAGE_LIMIT
        while True:
            if paged:
                self.report_download_page(video_id, offset)
            page_url = api + ('?offset=%d&limit=%d' % (offset, limit))
            page_count, page_info = self._parse_page(page_url)
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
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        m = re.search(r'<video[^>]*>\s*<source[^>]*>\s*<source src="(?P<url>[^"]+)"', webpage, re.DOTALL)
        if not m:
            self._downloader.trouble(u'ERROR: unable to find video information')
        video_url = unescapeHTML(m.group('url'))

        m = re.search(r"class='player_page_h1'>\s+<a.*?>(?P<title>.*?)</a>", webpage)
        if not m:
            self._downloader.trouble(u'Cannot find video title')
        title = unescapeHTML(m.group('title'))

        m = re.search(r'<meta property="og:description" content="(?P<desc>.*?)"', webpage)
        if m:
            desc = unescapeHTML(m.group('desc'))
        else:
            desc = None

        info = {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': desc,
        }
        return [info]

class TweetReelIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?tweetreel\.com/[?](?P<id>[0-9a-z]+)$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        m = re.search(r'<div id="left" status_id="([0-9]+)">', webpage)
        if not m:
            self._downloader.trouble(u'ERROR: Cannot find status ID')
        status_id = m.group(1)

        m = re.search(r'<div class="tweet_text">(.*?)</div>', webpage, flags=re.DOTALL)
        if not m:
            self._downloader.trouble(u'WARNING: Cannot find description')
        desc = unescapeHTML(re.sub('<a.*?</a>', '', m.group(1))).strip()

        m = re.search(r'<div class="tweet_info">.*?from <a target="_blank" href="https?://twitter.com/(?P<uploader_id>.+?)">(?P<uploader>.+?)</a>', webpage, flags=re.DOTALL)
        if not m:
            self._downloader.trouble(u'ERROR: Cannot find uploader')
        uploader = unescapeHTML(m.group('uploader'))
        uploader_id = unescapeHTML(m.group('uploader_id'))

        m = re.search(r'<span unixtime="([0-9]+)"', webpage)
        if not m:
            self._downloader.trouble(u'ERROR: Cannot find upload date')
        upload_date = datetime.datetime.fromtimestamp(int(m.group(1))).strftime('%Y%m%d')

        title = desc
        video_url = 'http://files.tweetreel.com/video/' + status_id + '.mov'

        info = {
            'id': video_id,
            'url': video_url,
            'ext': 'mov',
            'title': title,
            'description': desc,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'internal_id': status_id,
            'upload_date': upload_date
        }
        return [info]
        
class SteamIE(InfoExtractor):
    _VALID_URL = r"""http://store.steampowered.com/ 
                (?P<urltype>video|app)/ #If the page is only for videos or for a game
                (?P<gameID>\d+)/?
                (?P<videoID>\d*)(?P<extra>\??) #For urltype == video we sometimes get the videoID
                """

    def suitable(self, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(self._VALID_URL, url, re.VERBOSE) is not None

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url, re.VERBOSE)
        urlRE = r"'movie_(?P<videoID>\d+)': \{\s*FILENAME: \"(?P<videoURL>[\w:/\.\?=]+)\"(,\s*MOVIE_NAME: \"(?P<videoName>[\w:/\.\?=\+-]+)\")?\s*\},"
        gameID = m.group('gameID')
        videourl = 'http://store.steampowered.com/video/%s/' % gameID
        webpage = self._download_webpage(videourl, gameID)
        mweb = re.finditer(urlRE, webpage)
        namesRE = r'<span class="title">(?P<videoName>.+?)</span>'
        titles = re.finditer(namesRE, webpage)
        videos = []
        for vid,vtitle in zip(mweb,titles):
            video_id = vid.group('videoID')
            title = vtitle.group('videoName')
            video_url = vid.group('videoURL')
            if not video_url:
                self._downloader.trouble(u'ERROR: Cannot find video url for %s' % video_id)
            info = {
                'id':video_id,
                'url':video_url,
                'ext': 'flv',
                'title': unescapeHTML(title)
                  }
            videos.append(info)
        return videos

class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/recorded/(?P<videoID>\d+)'
    IE_NAME = u'ustream'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')
        video_url = u'http://tcdn.ustream.tv/video/%s' % video_id
        webpage = self._download_webpage(url, video_id)
        m = re.search(r'data-title="(?P<title>.+)"',webpage)
        title = m.group('title')
        m = re.search(r'<a class="state" data-content-type="channel" data-content-id="(?P<uploader>\d+)"',webpage)
        uploader = m.group('uploader')
        info = {
                'id':video_id,
                'url':video_url,
                'ext': 'flv',
                'title': title,
                'uploader': uploader
                  }
        return [info]

class RBMARadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rbmaradio\.com/shows/(?P<videoID>[^/]+)$'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)
        m = re.search(r'<script>window.gon = {.*?};gon\.show=(.+?);</script>', webpage)
        if not m:
            raise ExtractorError(u'Cannot find metadata')
        json_data = m.group(1)

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
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group('videoid')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        # Get the video title
        result = re.search(r'videoTitleArea">(?P<title>.*)</h1>', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract video title')
        video_title = result.group('title').strip()

        # Get the video date
        result = re.search(r'Date:</b>(?P<date>.*)</li>', webpage)
        if result is None:
            self._downloader.to_stderr(u'WARNING: unable to extract video date')
            upload_date = None
        else:
            upload_date = result.group('date').strip()

        # Get the video uploader
        result = re.search(r'Submitted:</b>(?P<uploader>.*)</li>', webpage)
        if result is None:
            self._downloader.to_stderr(u'ERROR: unable to extract uploader')
            video_uploader = None
        else:
            video_uploader = result.group('uploader').strip()
            video_uploader = clean_html( video_uploader )

        # Get all of the formats available
        DOWNLOAD_LIST_RE = r'(?s)<ul class="downloadList">(?P<download_list>.*?)</ul>'
        result = re.search(DOWNLOAD_LIST_RE, webpage)
        if result is None:
            raise ExtractorError(u'Unable to extract download list')
        download_list_html = result.group('download_list').strip()

        # Get all of the links from the page
        LINK_RE = r'(?s)<a href="(?P<url>[^"]+)">'
        links = re.findall(LINK_RE, download_list_html)
        if(len(links) == 0):
            raise ExtractorError(u'ERROR: no known formats available for video')
        
        self._downloader.to_screen(u'[youporn] Links found: %d' % len(links))   

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
            title = u'%s-%s-%s' % (video_title, size, bitrate)

            formats.append({
                'id': video_id,
                'url': video_url,
                'uploader': video_uploader,
                'upload_date': upload_date,
                'title': title,
                'ext': extension,
                'format': format,
                'thumbnail': None,
                'description': None,
                'player_url': None
            })

        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        req_format = self._downloader.params.get('format', None)
        self._downloader.to_screen(u'[youporn] Format: %s' % req_format)

        if req_format is None or req_format == 'best':
            return [formats[0]]
        elif req_format == 'worst':
            return [formats[-1]]
        elif req_format in ('-1', 'all'):
            return formats
        else:
            format = self._specific( req_format, formats )
            if result is None:
                self._downloader.trouble(u'ERROR: requested format not available')
                return
            return [format]

        

class PornotubeIE(InfoExtractor):
    """Information extractor for pornotube.com."""
    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?pornotube\.com(/c/(?P<channel>[0-9]+))?(/m/(?P<videoid>[0-9]+))(/(?P<title>.+))$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group('videoid')
        video_title = mobj.group('title')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video URL
        VIDEO_URL_RE = r'url: "(?P<url>http://video[0-9].pornotube.com/.+\.flv)",'
        result = re.search(VIDEO_URL_RE, webpage)
        if result is None:
            self._downloader.trouble(u'ERROR: unable to extract video url')
            return
        video_url = compat_urllib_parse.unquote(result.group('url'))

        #Get the uploaded date
        VIDEO_UPLOADED_RE = r'<div class="video_added_by">Added (?P<date>[0-9\/]+) by'
        result = re.search(VIDEO_UPLOADED_RE, webpage)
        if result is None:
            self._downloader.trouble(u'ERROR: unable to extract video title')
            return
        upload_date = result.group('date')

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
            self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
            return

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video title
        result = re.search(r'<title>(?P<title>.*)</title>', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract video title')
        video_title = result.group('title').strip()

        # Get the embed page
        result = re.search(r'https?://www.youjizz.com/videos/embed/(?P<videoid>[0-9]+)', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract embed page')

        embed_page_url = result.group(0).strip()
        video_id = result.group('videoid')
    
        webpage = self._download_webpage(embed_page_url, video_id)

        # Get the video URL
        result = re.search(r'so.addVariable\("file",encodeURIComponent\("(?P<source>[^"]+)"\)\);', webpage)
        if result is None:
            raise ExtractorError(u'ERROR: unable to extract video url')
        video_url = result.group('source')

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'ext': 'flv',
                'format': 'flv',
                'player_url': embed_page_url}

        return [info]


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
        BlipTVUserIE(),
        BlipTVIE(),
        VimeoIE(),
        MyVideoIE(),
        ComedyCentralIE(),
        EscapistIE(),
        CollegeHumorIE(),
        XVideosIE(),
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
        JustinTVIE(),
        FunnyOrDieIE(),
        TweetReelIE(),
        SteamIE(),
        UstreamIE(),
        RBMARadioIE(),
        GenericIE()
    ]


