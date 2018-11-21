# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NarandoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?narando\.com/articles/(?P<id>([a-zA-Z]|-)+)'
    _TEST = {
        'url': 'https://narando.com/articles/an-ihrem-selbstlob-erkennt-man-sie',
        'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
        'info_dict': {
            'id': 'an-ihrem-selbstlob-erkennt-man-sie',
            'ext': 'mp3',
            'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
            'url': 'https://static.narando.com/sounds/10492/original.mp3',
            'description': u'omnisophie.com: Kaum  eine  Woche  vergeht,  dass  nicht  jemand  mir  gegenüber  seine  Mathematik-Unkenntnisse  tränenlos  beweint.  „In  Mathe  war  ich  niemals  gut.“  Diese  Leute  sagen  mir  das  wohl,  weil  ich  Mathematiker  bin,  und  da  gehört  so  ein  fröhliches „Understatement“  zum  Small  Talk.  So  wie  wenn  ich  selbst  bedauernd-entschuldigend  auf  meine  grauen  Haare  zeige.  Ich  kann  eben  auch  nicht  alles  bieten...  „Mathe  kann  ich  nicht“,  „Ich  habe  kein  Internet“  oder  „Ich  will  auch  bewusst  nicht  alles  können“  wird  fast  wie  Eigenlob  vorgetragen.',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
#        webpage = self._download_webpage(url,"?")
#        print(url)
#        print('https://narando.com/articles/'+video_id)
        webpage = self._download_webpage('https://narando.com/articles/' + video_id, video_id)
        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1 class="visible-xs h3">(.+?)</h1>', webpage, 'title')
#        print(title)
        player_id = self._html_search_regex(r'[\n\r].*https:\/\/narando.com\/r\/\s*([^"]*)', webpage, 'player_id')
        player_page = self._download_webpage('https://narando.com/widget?r=' + player_id, player_id)
        download_url = self._html_search_regex(r'.<div class="stream_url hide">\s*([^?]*)', player_page, 'download_url')
        description = self._html_search_regex(r'<meta content="(.+?)" property="og:description" />', webpage, 'description')
        return {
            'id': video_id,
            'title': title,
            'url': download_url,
            'description': description,
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
