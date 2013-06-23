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
from .extractor.common import InfoExtractor, SearchInfoExtractor

from .extractor.ard import ARDIE
from .extractor.arte import ArteTvIE
from .extractor.bliptv import BlipTVIE, BlipTVUserIE
from .extractor.comedycentral import ComedyCentralIE
from .extractor.dailymotion import DailymotionIE
from .extractor.facebook import FacebookIE
from .extractor.gametrailers import GametrailersIE
from .extractor.generic import GenericIE
from .extractor.googleplus import GooglePlusIE
from .extractor.googlesearch import GoogleSearchIE
from .extractor.metacafe import MetacafeIE
from .extractor.myvideo import MyVideoIE
from .extractor.statigram import StatigramIE
from .extractor.photobucket import PhotobucketIE
from .extractor.soundcloud import SoundcloudIE, SoundcloudSetIE
from .extractor.vimeo import VimeoIE
from .extractor.yahoo import YahooIE, YahooSearchIE
from .extractor.youtube import YoutubeIE, YoutubePlaylistIE, YoutubeSearchIE, YoutubeUserIE, YoutubeChannelIE
from .extractor.zdf import ZDFIE



















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
        StatigramIE(),
        GenericIE()
    ]

def get_info_extractor(ie_name):
    """Returns the info extractor class with the given ie_name"""
    return globals()[ie_name+'IE']
