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
from .extractor.bandcamp import BandcampIE
from .extractor.bliptv import BlipTVIE, BlipTVUserIE
from .extractor.comedycentral import ComedyCentralIE
from .extractor.collegehumor import CollegeHumorIE
from .extractor.dailymotion import DailymotionIE
from .extractor.depositfiles import DepositFilesIE
from .extractor.eighttracks import EightTracksIE
from .extractor.escapist import EscapistIE
from .extractor.facebook import FacebookIE
from .extractor.funnyordie import FunnyOrDieIE
from .extractor.gametrailers import GametrailersIE
from .extractor.generic import GenericIE
from .extractor.googleplus import GooglePlusIE
from .extractor.googlesearch import GoogleSearchIE
from .extractor.ina import InaIE
from .extractor.infoq import InfoQIE
from .extractor.justintv import JustinTVIE
from .extractor.keek import KeekIE
from .extractor.liveleak import LiveLeakIE
from .extractor.metacafe import MetacafeIE
from .extractor.mixcloud import MixcloudIE
from .extractor.mtv import MTVIE
from .extractor.myspass import MySpassIE
from .extractor.myvideo import MyVideoIE
from .extractor.nba import NBAIE
from .extractor.statigram import StatigramIE
from .extractor.photobucket import PhotobucketIE
from .extractor.pornotube import PornotubeIE
from .extractor.rbmaradio import RBMARadioIE
from .extractor.redtube import RedTubeIE
from .extractor.soundcloud import SoundcloudIE, SoundcloudSetIE
from .extractor.spiegel import SpiegelIE
from .extractor.stanfordoc import StanfordOpenClassroomIE
from .extractor.steam import SteamIE
from .extractor.ted import TEDIE
from .extractor.tumblr import TumblrIE
from .extractor.ustream import UstreamIE
from .extractor.vbox7 import Vbox7IE
from .extractor.vimeo import VimeoIE
from .extractor.vine import VineIE
from .extractor.worldstarhiphop import WorldStarHipHopIE
from .extractor.xnxx import XNXXIE
from .extractor.xvideos import XVideosIE
from .extractor.yahoo import YahooIE, YahooSearchIE
from .extractor.youjizz import YouJizzIE
from .extractor.youku import YoukuIE
from .extractor.youporn import YouPornIE
from .extractor.youtube import YoutubeIE, YoutubePlaylistIE, YoutubeSearchIE, YoutubeUserIE, YoutubeChannelIE
from .extractor.zdf import ZDFIE




































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
