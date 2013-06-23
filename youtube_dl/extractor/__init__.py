
from .ard import ARDIE
from .arte import ArteTvIE
from .bandcamp import BandcampIE
from .bliptv import BlipTVIE, BlipTVUserIE
from .breakcom import BreakIE
from .comedycentral import ComedyCentralIE
from .collegehumor import CollegeHumorIE
from .dailymotion import DailymotionIE
from .depositfiles import DepositFilesIE
from .eighttracks import EightTracksIE
from .escapist import EscapistIE
from .facebook import FacebookIE
from .flickr import FlickrIE
from .funnyordie import FunnyOrDieIE
from .gametrailers import GametrailersIE
from .generic import GenericIE
from .googleplus import GooglePlusIE
from .googlesearch import GoogleSearchIE
from .howcast import HowcastIE
from .hypem import HypemIE
from .ina import InaIE
from .infoq import InfoQIE
from .justintv import JustinTVIE
from .keek import KeekIE
from .liveleak import LiveLeakIE
from .metacafe import MetacafeIE
from .mixcloud import MixcloudIE
from .mtv import MTVIE
from .myspass import MySpassIE
from .myvideo import MyVideoIE
from .nba import NBAIE
from .statigram import StatigramIE
from .photobucket import PhotobucketIE
from .pornotube import PornotubeIE
from .rbmaradio import RBMARadioIE
from .redtube import RedTubeIE
from .soundcloud import SoundcloudIE, SoundcloudSetIE
from .spiegel import SpiegelIE
from .stanfordoc import StanfordOpenClassroomIE
from .steam import SteamIE
from .teamcoco import TeamcocoIE
from .ted import TEDIE
from .tumblr import TumblrIE
from .ustream import UstreamIE
from .vbox7 import Vbox7IE
from .vimeo import VimeoIE
from .vine import VineIE
from .worldstarhiphop import WorldStarHipHopIE
from .xnxx import XNXXIE
from .xhamster import XHamsterIE
from .xvideos import XVideosIE
from .yahoo import YahooIE, YahooSearchIE
from .youjizz import YouJizzIE
from .youku import YoukuIE
from .youporn import YouPornIE
from .youtube import YoutubeIE, YoutubePlaylistIE, YoutubeSearchIE, YoutubeUserIE, YoutubeChannelIE
from .zdf import ZDFIE

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
        BreakIE(),
        GenericIE()
    ]

def get_info_extractor(ie_name):
    """Returns the info extractor class with the given ie_name"""
    return globals()[ie_name+'IE']
