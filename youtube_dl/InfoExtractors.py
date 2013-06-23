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
from .extractor.flickr import FlickrIE
from .extractor.funnyordie import FunnyOrDieIE
from .extractor.gametrailers import GametrailersIE
from .extractor.generic import GenericIE
from .extractor.googleplus import GooglePlusIE
from .extractor.googlesearch import GoogleSearchIE
from .extractor.howcast import HowcastIE
from .extractor.hypem import HypemIE
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
from .extractor.teamcoco import TeamcocoIE
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
