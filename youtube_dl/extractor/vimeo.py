import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,

    clean_html,
    get_element_by_attribute,
    ExtractorError,
    std_headers,
)

class VimeoIE(InfoExtractor):
    """Information extractor for vimeo.com."""

    # _VALID_URL matches Vimeo URLs
    _VALID_URL = r'(?P<proto>https?://)?(?:(?:www|player)\.)?vimeo(?P<pro>pro)?\.com/(?:(?:(?:groups|album)/[^/]+)|(?:.*?)/)?(?P<direct_link>play_redirect_hls\?clip_id=)?(?:videos?/)?(?P<id>[0-9]+)(?:[?].*)?$'
    IE_NAME = u'vimeo'
    _TEST = {
        u'url': u'http://vimeo.com/56015672',
        u'file': u'56015672.mp4',
        u'md5': u'8879b6cc097e987f02484baf890129e5',
        u'info_dict': {
            u"upload_date": u"20121220", 
            u"description": u"This is a test case for youtube-dl.\nFor more information, see github.com/rg3/youtube-dl\nTest chars: \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550", 
            u"uploader_id": u"user7108434", 
            u"uploader": u"Filippo Valsorda", 
            u"title": u"youtube-dl test video - \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550"
        }
    }

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

    def _print_formats(self, formats):
        print('Available formats:')
        width = max([len(f['id']) for f in formats])
        for f in formats:
            print('%-*s\t:\t%s' % (width, f['id'], f['ext']))

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
        codecs = [('h264', 'mp4'), ('vp8', 'flv'), ('vp6', 'flv')]
        files = { 'hd': [], 'sd': [], 'other': []}
        for codec_name, codec_extension in codecs:
            for quality in config["video"]["files"].get(codec_name, []):
                format_id = '-'.join((codec_name, quality)).lower()
                key = quality if quality in files else 'other'
                files[key].append({
                    'codec': codec_name,
                    'ext': codec_extension,
                    'quality': quality,
                    'id': format_id,
                })
        formats = []
        for key in ('hd', 'sd', 'other'):
            formats += files[key]
        if len(formats) == 0:
            raise ExtractorError(u'No known codec found')

        if self._downloader.params.get('listformats', None):
            self._print_formats(formats)
            return

        # Decide which formats to download
        req_format = self._downloader.params.get('format', None)
        if req_format is None or req_format == 'best':
            req_format_list = [formats[0]]  # Best quality
        elif req_format == 'worst':
            req_format_list = [formats[-1]]  # worst quality (maybe?)
        elif req_format in ('-1', 'all'):
            req_format_list = formats  # All formats
        else:
            # Specific formats. We pick the first in a slash-delimeted sequence.
            # For example, if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
            req_formats = req_format.lower().split('/')
            format_map = dict([(c['id'], c) for c in formats])
            req_format_list = None
            for rf in req_formats:
                if rf in format_map:
                    req_format_list = [format_map[rf]]
                    break
            if req_format_list is None:
                raise ExtractorError(u'requested format not available')

        results = []
        for format in req_format_list:
            video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=%s&type=moogaloop_local&embed_location=" \
                        %(video_id, sig, timestamp, format['quality'], format['codec'].upper())
            results.append({
                'id':       video_id,
                'url':      video_url,
                'uploader': video_uploader,
                'uploader_id': video_uploader_id,
                'upload_date':  video_upload_date,
                'title':    video_title,
                'ext':      format['ext'],
                'format':   format['id'],
                'thumbnail':    video_thumbnail,
                'description':  video_description,
            })
        return results
