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
from .extractor.xhamster import XHamsterIE
from .extractor.xvideos import XVideosIE
from .extractor.yahoo import YahooIE, YahooSearchIE
from .extractor.youjizz import YouJizzIE
from .extractor.youku import YoukuIE
from .extractor.youporn import YouPornIE
from .extractor.youtube import YoutubeIE, YoutubePlaylistIE, YoutubeSearchIE, YoutubeUserIE, YoutubeChannelIE
from .extractor.zdf import ZDFIE

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
