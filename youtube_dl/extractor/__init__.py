from .appletrailers import AppleTrailersIE
from .addanime import AddAnimeIE
from .archiveorg import ArchiveOrgIE
from .ard import ARDIE
from .arte import ArteTvIE
from .auengine import AUEngineIE
from .bandcamp import BandcampIE
from .bliptv import BlipTVIE, BlipTVUserIE
from .breakcom import BreakIE
from .brightcove import BrightcoveIE
from .c56 import C56IE
from .canalplus import CanalplusIE
from .canalc2 import Canalc2IE
from .cnn import CNNIE
from .collegehumor import CollegeHumorIE
from .comedycentral import ComedyCentralIE
from .condenast import CondeNastIE
from .criterion import CriterionIE
from .cspan import CSpanIE
from .dailymotion import DailymotionIE, DailymotionPlaylistIE
from .daum import DaumIE
from .depositfiles import DepositFilesIE
from .dotsub import DotsubIE
from .dreisat import DreiSatIE
from .defense import DefenseGouvFrIE
from .ehow import EHowIE
from .eighttracks import EightTracksIE
from .escapist import EscapistIE
from .exfm import ExfmIE
from .facebook import FacebookIE
from .flickr import FlickrIE
from .freesound import FreesoundIE
from .funnyordie import FunnyOrDieIE
from .gamespot import GameSpotIE
from .gametrailers import GametrailersIE
from .generic import GenericIE
from .googleplus import GooglePlusIE
from .googlesearch import GoogleSearchIE
from .hark import HarkIE
from .hotnewhiphop import HotNewHipHopIE
from .howcast import HowcastIE
from .hypem import HypemIE
from .ign import IGNIE, OneUPIE
from .ina import InaIE
from .infoq import InfoQIE
from .instagram import InstagramIE
from .jeuxvideo import JeuxVideoIE
from .jukebox import JukeboxIE
from .justintv import JustinTVIE
from .kankan import KankanIE
from .keek import KeekIE
from .liveleak import LiveLeakIE
from .livestream import LivestreamIE
from .metacafe import MetacafeIE
from .metacritic import MetacriticIE
from .mit import TechTVMITIE, MITIE
from .mixcloud import MixcloudIE
from .mtv import MTVIE
from .muzu import MuzuTVIE
from .myspass import MySpassIE
from .myvideo import MyVideoIE
from .naver import NaverIE
from .nba import NBAIE
from .nbc import NBCNewsIE
from .ooyala import OoyalaIE
from .orf import ORFIE
from .pbs import PBSIE
from .photobucket import PhotobucketIE
from .pornotube import PornotubeIE
from .rbmaradio import RBMARadioIE
from .redtube import RedTubeIE
from .ringtv import RingTVIE
from .ro220 import Ro220IE
from .roxwel import RoxwelIE
from .rtlnow import RTLnowIE
from .sina import SinaIE
from .slashdot import SlashdotIE
from .slideshare import SlideshareIE
from .sohu import SohuIE
from .soundcloud import SoundcloudIE, SoundcloudSetIE
from .spiegel import SpiegelIE
from .stanfordoc import StanfordOpenClassroomIE
from .statigram import StatigramIE
from .steam import SteamIE
from .teamcoco import TeamcocoIE
from .ted import TEDIE
from .tf1 import TF1IE
from .thisav import ThisAVIE
from .traileraddict import TrailerAddictIE
from .trilulilu import TriluliluIE
from .tudou import TudouIE
from .tumblr import TumblrIE
from .tutv import TutvIE
from .unistra import UnistraIE
from .ustream import UstreamIE
from .vbox7 import Vbox7IE
from .veehd import VeeHDIE
from .veoh import VeohIE
from .vevo import VevoIE
from .videofyme import VideofyMeIE
from .vimeo import VimeoIE, VimeoChannelIE
from .vine import VineIE
from .wat import WatIE
from .weibo import WeiboIE
from .wimp import WimpIE
from .worldstarhiphop import WorldStarHipHopIE
from .xhamster import XHamsterIE
from .xnxx import XNXXIE
from .xvideos import XVideosIE
from .yahoo import YahooIE, YahooSearchIE
from .youjizz import YouJizzIE
from .youku import YoukuIE
from .youporn import YouPornIE
from .youtube import (
    YoutubeIE,
    YoutubePlaylistIE,
    YoutubeSearchIE,
    YoutubeUserIE,
    YoutubeChannelIE,
    YoutubeShowIE,
    YoutubeSubscriptionsIE,
    YoutubeRecommendedIE,
    YoutubeWatchLaterIE,
    YoutubeFavouritesIE,
)
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
