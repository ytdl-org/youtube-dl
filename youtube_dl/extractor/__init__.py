
from .ard import ARDIE
from .arte import ArteTvIE
from .auengine import AUEngineIE
from .bandcamp import BandcampIE
from .bliptv import BlipTVIE, BlipTVUserIE
from .breakcom import BreakIE
from .collegehumor import CollegeHumorIE
from .comedycentral import ComedyCentralIE
from .cspan import CSpanIE
from .dailymotion import DailymotionIE
from .depositfiles import DepositFilesIE
from .eighttracks import EightTracksIE
from .escapist import EscapistIE
from .facebook import FacebookIE
from .flickr import FlickrIE
from .funnyordie import FunnyOrDieIE
from .gamespot import GameSpotIE
from .gametrailers import GametrailersIE
from .generic import GenericIE
from .googleplus import GooglePlusIE
from .googlesearch import GoogleSearchIE
from .hotnewhiphop import HotNewHipHopIE
from .howcast import HowcastIE
from .hypem import HypemIE
from .ina import InaIE
from .infoq import InfoQIE
from .instagram import InstagramIE
from .jukebox import JukeboxIE
from .justintv import JustinTVIE
from .keek import KeekIE
from .liveleak import LiveLeakIE
from .metacafe import MetacafeIE
from .mixcloud import MixcloudIE
from .mtv import MTVIE
from .myspass import MySpassIE
from .myvideo import MyVideoIE
from .nba import NBAIE
from .photobucket import PhotobucketIE
from .pornotube import PornotubeIE
from .rbmaradio import RBMARadioIE
from .redtube import RedTubeIE
from .ringtv import RingTVIE
from .soundcloud import SoundcloudIE, SoundcloudSetIE
from .spiegel import SpiegelIE
from .stanfordoc import StanfordOpenClassroomIE
from .statigram import StatigramIE
from .steam import SteamIE
from .teamcoco import TeamcocoIE
from .ted import TEDIE
from .tf1 import TF1IE
from .traileraddict import TrailerAddictIE
from .tudou import TudouIE
from .tumblr import TumblrIE
from .tutv import TutvIE
from .ustream import UstreamIE
from .vbox7 import Vbox7IE
from .vevo import VevoIE
from .vimeo import VimeoIE
from .vine import VineIE
from .wat import WatIE
from .wimp import WimpIE
from .worldstarhiphop import WorldStarHipHopIE
from .xhamster import XHamsterIE
from .xnxx import XNXXIE
from .xvideos import XVideosIE
from .yahoo import YahooIE, YahooSearchIE
from .youjizz import YouJizzIE
from .youku import YoukuIE
from .youporn import YouPornIE
from .youtube import YoutubeIE, YoutubePlaylistIE, YoutubeSearchIE, YoutubeUserIE, YoutubeChannelIE, YoutubeShowIE
from .zdf import ZDFIE


_ALL_CLASSES = [
    klass
    for name, klass in globals().items()
    if name.endswith('IE') and name != 'GenericIE'
]
_ALL_CLASSES.append(GenericIE)

def gen_extractors():
    """ Return a list of an instance of every supported extractor.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    return [klass() for klass in _ALL_CLASSES]

def get_info_extractor(ie_name):
    """Returns the info extractor class with the given ie_name"""
    return globals()[ie_name+'IE']
