import json
import re
import itertools

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,

    clean_html,
    get_element_by_attribute,
    ExtractorError,
    std_headers,
    unsmuggle_url,
)

class VimeoIE(InfoExtractor):
    """Information extractor for vimeo.com."""

    # _VALID_URL matches Vimeo URLs
    _VALID_URL = r'(?P<proto>https?://)?(?:(?:www|player)\.)?vimeo(?P<pro>pro)?\.com/(?:(?:(?:groups|album)/[^/]+)|(?:.*?)/)?(?P<direct_link>play_redirect_hls\?clip_id=)?(?:videos?/)?(?P<id>[0-9]+)/?(?:[?].*)?$'
    _NETRC_MACHINE = 'vimeo'
    IE_NAME = u'vimeo'
    _TESTS = [
        {
            u'url': u'http://vimeo.com/56015672',
            u'file': u'56015672.mp4',
            u'md5': u'8879b6cc097e987f02484baf890129e5',
            u'info_dict': {
                u"upload_date": u"20121220", 
                u"description": u"This is a test case for youtube-dl.\nFor more information, see github.com/rg3/youtube-dl\nTest chars: \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550", 
                u"uploader_id": u"user7108434", 
                u"uploader": u"Filippo Valsorda", 
                u"title": u"youtube-dl test video - \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550",
            },
        },
        {
            u'url': u'http://vimeopro.com/openstreetmapus/state-of-the-map-us-2013/video/68093876',
            u'file': u'68093876.mp4',
            u'md5': u'3b5ca6aa22b60dfeeadf50b72e44ed82',
            u'note': u'Vimeo Pro video (#1197)',
            u'info_dict': {
                u'uploader_id': u'openstreetmapus', 
                u'uploader': u'OpenStreetMap US', 
                u'title': u'Andy Allan - Putting the Carto into OpenStreetMap Cartography',
            },
        },
        {
            u'url': u'http://player.vimeo.com/video/54469442',
            u'file': u'54469442.mp4',
            u'md5': u'619b811a4417aa4abe78dc653becf511',
            u'note': u'Videos that embed the url in the player page',
            u'info_dict': {
                u'title': u'Kathy Sierra: Building the minimum Badass User, Business of Software',
                u'uploader': u'The BLN & Business of Software',
            },
        }
    ]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        self.report_login()
        login_url = 'https://vimeo.com/log_in'
        webpage = self._download_webpage(login_url, None, False)
        token = re.search(r'xsrft: \'(.*?)\'', webpage).group(1)
        data = compat_urllib_parse.urlencode({'email': username,
                                              'password': password,
                                              'action': 'login',
                                              'service': 'vimeo',
                                              'token': token,
                                              })
        login_request = compat_urllib_request.Request(login_url, data)
        login_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        login_request.add_header('Cookie', 'xsrft=%s' % token)
        self._download_webpage(login_request, None, False, u'Wrong login info')

    def _verify_video_password(self, url, video_id, webpage):
        password = self._downloader.params.get('videopassword', None)
        if password is None:
            raise ExtractorError(u'This video is protected by a password, use the --video-password option')
        token = re.search(r'xsrft: \'(.*?)\'', webpage).group(1)
        data = compat_urllib_parse.urlencode({'password': password,
                                              'token': token})
        # I didn't manage to use the password with https
        if url.startswith('https'):
            pass_url = url.replace('https','http')
        else:
            pass_url = url
        password_request = compat_urllib_request.Request(pass_url+'/password', data)
        password_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        password_request.add_header('Cookie', 'xsrft=%s' % token)
        self._download_webpage(password_request, video_id,
                               u'Verifying the password',
                               u'Wrong password')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url, new_video=True):
        url, data = unsmuggle_url(url)
        headers = std_headers
        if data is not None:
            headers = headers.copy()
            headers.update(data)

        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group('id')
        if not mobj.group('proto'):
            url = 'https://' + url
        elif mobj.group('pro'):
            url = 'http://player.vimeo.com/video/' + video_id
        elif mobj.group('direct_link'):
            url = 'https://vimeo.com/' + video_id

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url, None, headers)
        webpage = self._download_webpage(request, video_id)

        # Now we begin extracting as much information as we can from what we
        # retrieved. First we extract the information common to all extractors,
        # and latter we extract those that are Vimeo specific.
        self.report_extraction(video_id)

        # Extract the config JSON
        try:
            config = self._search_regex([r' = {config:({.+?}),assets:', r'c=({.+?);'],
                webpage, u'info section', flags=re.DOTALL)
            config = json.loads(config)
        except:
            if re.search('The creator of this video has not given you permission to embed it on this domain.', webpage):
                raise ExtractorError(u'The author has restricted the access to this video, try with the "--referer" option')

            if re.search('If so please provide the correct password.', webpage):
                self._verify_video_password(url, video_id, webpage)
                return self._real_extract(url)
            else:
                raise ExtractorError(u'Unable to extract info section')

        # Extract title
        video_title = config["video"]["title"]

        # Extract uploader and uploader_id
        video_uploader = config["video"]["owner"]["name"]
        video_uploader_id = config["video"]["owner"]["url"].split('/')[-1] if config["video"]["owner"]["url"] else None

        # Extract video thumbnail
        video_thumbnail = config["video"].get("thumbnail")
        if video_thumbnail is None:
            _, video_thumbnail = sorted((int(width), t_url) for (width, t_url) in config["video"]["thumbs"].items())[-1]

        # Extract video description
        video_description = None
        try:
            video_description = get_element_by_attribute("itemprop", "description", webpage)
            if video_description: video_description = clean_html(video_description)
        except AssertionError as err:
            # On some pages like (http://player.vimeo.com/video/54469442) the
            # html tags are not closed, python 2.6 cannot handle it
            if err.args[0] == 'we should not get here!':
                pass
            else:
                raise

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
        codecs = [('vp6', 'flv'), ('vp8', 'flv'), ('h264', 'mp4')]
        files = { 'hd': [], 'sd': [], 'other': []}
        config_files = config["video"].get("files") or config["request"].get("files")
        for codec_name, codec_extension in codecs:
            for quality in config_files.get(codec_name, []):
                format_id = '-'.join((codec_name, quality)).lower()
                key = quality if quality in files else 'other'
                video_url = None
                if isinstance(config_files[codec_name], dict):
                    file_info = config_files[codec_name][quality]
                    video_url = file_info.get('url')
                else:
                    file_info = {}
                if video_url is None:
                    video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=%s&type=moogaloop_local&embed_location=" \
                        %(video_id, sig, timestamp, quality, codec_name.upper())

                files[key].append({
                    'ext': codec_extension,
                    'url': video_url,
                    'format_id': format_id,
                    'width': file_info.get('width'),
                    'height': file_info.get('height'),
                })
        formats = []
        for key in ('other', 'sd', 'hd'):
            formats += files[key]
        if len(formats) == 0:
            raise ExtractorError(u'No known codec found')

        return [{
            'id':       video_id,
            'uploader': video_uploader,
            'uploader_id': video_uploader_id,
            'upload_date':  video_upload_date,
            'title':    video_title,
            'thumbnail':    video_thumbnail,
            'description':  video_description,
            'formats': formats,
        }]


class VimeoChannelIE(InfoExtractor):
    IE_NAME = u'vimeo:channel'
    _VALID_URL = r'(?:https?://)?vimeo.\com/channels/(?P<id>[^/]+)'
    _MORE_PAGES_INDICATOR = r'<a.+?rel="next"'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id =  mobj.group('id')
        video_ids = []

        for pagenum in itertools.count(1):
            webpage = self._download_webpage('http://vimeo.com/channels/%s/videos/page:%d' % (channel_id, pagenum),
                                             channel_id, u'Downloading page %s' % pagenum)
            video_ids.extend(re.findall(r'id="clip_(\d+?)"', webpage))
            if re.search(self._MORE_PAGES_INDICATOR, webpage, re.DOTALL) is None:
                break

        entries = [self.url_result('http://vimeo.com/%s' % video_id, 'Vimeo')
                   for video_id in video_ids]
        channel_title = self._html_search_regex(r'<a href="/channels/%s">(.*?)</a>' % channel_id,
                                                webpage, u'channel title')
        return {'_type': 'playlist',
                'id': channel_id,
                'title': channel_title,
                'entries': entries,
                }
