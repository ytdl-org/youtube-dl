# coding: utf-8
'''
This plugin works for videos from www.joemonster.org using 'Monster Player'

Most (~70%) of them are single embedded youtube videos:
http://www.joemonster.org/filmy/28773/Sposob_na_Euro_2012
This plugin doesn't directly support them,
so youtube-dl fallbacks to youtube method, which works just fine.
Pages with multiple youtube videos are also supported by youtube method:
http://www.joemonster.org/filmy/4551/Terapia_masazem

This plugin claims to support a page when it contains at least one video
embedded with Monster Player.
Pages with mixed providers, like this (Monster Player+youtube):
http://www.joemonster.org/filmy/5496/Kolo_Smierci
only download first Monster Player video, the rest is discarded for now.

There are three versions of Monster Player:
* fat
** single video:
   joemonster.org/filmy/28784/Genialny_wystep_mlodego_iluzjonisty_w_Mam_talent
** multi videos:
   joemonster.org/filmy/28693/Dave_Chappelle_w_San_Francisco_
* slim
  joemonster.org/filmy/28372/Wszyscy_kochamy_Polske_czesc_
* html5
  joemonster.org/filmy/65314/Przyciemniane_szyby_Jakie_przy

About 5% of videos are embedded from external providers (different
than youtube), they should work if youtube-dl has appropriate method.
'''
from __future__ import unicode_literals

import re

from ..compat import compat_urlparse, compat_urllib_request
from .common import InfoExtractor


class NoRedirectHandler(compat_urllib_request.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        infourl = \
            compat_urllib_request.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_301 = http_error_302


class JoeMonsterIE(InfoExtractor):
    _VALID_URL = (r'https?://(?:www\.)?joemonster\.org/filmy/(?P<id>[0-9]+)/'
                  r'(?P<display_id>.*)')

    _TESTS = [{'url': ('http://www.joemonster.org/filmy/28784/'
                       'Genialny_wystep_mlodego_iluzjonisty_w_Mam_talent'),
               'md5': 'aaf9200a593564cf0b011f192be339d8',
               'info_dict': {'id': '28784',
                             'ext': 'flv',
                             'title': (u'Genialny występ młodego '
                                       u'iluzjonisty w Mam talent')}},
              {'url': ('http://www.joemonster.org/filmy/28372/'
                       'Wszyscy_kochamy_Polske_czesc_'),
               'md5': 'b0366db631952a3f18507d42a9b62b2d',
               'info_dict': {'id': '28372',
                             'ext': 'flv',
                             'title': u'Wszyscy kochamy Polskę - część 7'}},
              {'url': ('http://www.joemonster.org/filmy/65314/'
                       'Przyciemniane_szyby_Jakie_przy'),
               'md5': 'e3c5a40e72bc589fb277f8d1663f7580',
               'info_dict': {'id': '65314',
                             'ext': 'mp4',
                             'title': (u'Przyciemniane szyby? '
                                       u'Jakie przyciemnane szyby?')}}]

    _FAT_MONSTER_PLAYER_REGEX = \
        (r'<\s*?div\s+?id\s*?=\s*?"fileFile"\s*?>\s*?'
         r'<\s*?iframe.*?src\s*?=\s*?"(.*?/emb/[^"]+?)"')

    _SLIM_MONSTER_PLAYER_REGEX = \
        (r'<\s*embed\s*src\s*=\s*"\s*(http://(?:www\.)?joemonster\.org/'
         r'flvplayer\d*\.swf\?file=.*?)\s*?"')

    _HTML5_MONSTER_PLAYER_REGEX = \
        (r'<\s*?div\s+?id\s*?=\s*?"fileFile"\s*?>\s*?<\s*?iframe'
         r'.*?src\s*?=\s*?"(.*?/embtv\.php[^"]+?)"')

    def __init__(self, downloader=None):
        super(JoeMonsterIE, self).__init__(downloader)
        self._FAT_MONSTER_PLAYER_REGEX_RE = None
        self._SLIM_MONSTER_PLAYER_REGEX_RE = None
        self._HTML5_MONSTER_PLAYER_REGEX_RE = None
        self._head_wo_redirects_opener = None

    def _get_redirect_url(self, url):
        '''
        Issue a HEAD request to target url and return value
        of Location response header.
        '''
        if self._head_wo_redirects_opener is None:
            self._head_wo_redirects_opener = \
                compat_urllib_request.build_opener(NoRedirectHandler())
        request = compat_urllib_request.Request(url)
        request.get_method = lambda: 'HEAD'
        response = self._head_wo_redirects_opener.open(request)
        return response.headers['location']

    def _is_fat_monster_player(self, webpage):
        if self._FAT_MONSTER_PLAYER_REGEX_RE is None:
            self._FAT_MONSTER_PLAYER_REGEX_RE = \
                re.compile(self._FAT_MONSTER_PLAYER_REGEX)
        return self._FAT_MONSTER_PLAYER_REGEX_RE.search(webpage) is not None

    def _is_slim_monster_player(self, webpage):
        if self._SLIM_MONSTER_PLAYER_REGEX_RE is None:
            self._SLIM_MONSTER_PLAYER_REGEX_RE = \
                re.compile(self._SLIM_MONSTER_PLAYER_REGEX)
        return self._SLIM_MONSTER_PLAYER_REGEX_RE.search(webpage) is not None

    def _is_html5_monster_player(self, webpage):
        if self._HTML5_MONSTER_PLAYER_REGEX_RE is None:
            self._HTML5_MONSTER_PLAYER_REGEX_RE = \
                re.compile(self._HTML5_MONSTER_PLAYER_REGEX)
        return self._HTML5_MONSTER_PLAYER_REGEX_RE.search(webpage) is not None

    def _extract_video_url_from_flvplayer_url(self, url):
        '''
        Return real video url from url to flvplayer.

        E.g:
        http://joemonster.org/flvplayer44.swf?file=http://vader.joemonster.org/
               upload/zht/vid_446297011cac033_odcinek_Mam_talent.flv&...
        ->
        http://vader.joemonster.org/upload/zht/vid_446297011cac033_odcinek_Mam_talent.flv
        '''
        query_params = compat_urlparse.urlparse(url).query
        return compat_urlparse.parse_qs(query_params)['file'][0]

    def _extract_fat_monster_player_url(self, webpage):
        if self._FAT_MONSTER_PLAYER_REGEX_RE is None:
            self._FAT_MONSTER_PLAYER_REGEX_RE = \
                re.compile(self._FAT_MONSTER_PLAYER_REGEX)
        url = self._FAT_MONSTER_PLAYER_REGEX_RE.search(webpage).group(1)
        # url looks like:
        # http://www.joemonster.org/emb/446297/Genialny_wystep_mlodego_iluzjonisty_w_Mam_talent/ex
        # GETing it results in 301 with a redirect (dropping www prefix)
        url = self._get_redirect_url(url)
        # now url looks like:
        # http://joemonster.org/emb/446297/Genialny_wystep_mlodego_iluzjonisty_w_Mam_talent/ex
        # GETing it results in 302 with a redirect to flash object
        url = self._get_redirect_url(url)
        return self._extract_video_url_from_flvplayer_url(url)

    def _extract_slim_monster_player_url(self, webpage):
        if self._SLIM_MONSTER_PLAYER_REGEX_RE is None:
            self._SLIM_MONSTER_PLAYER_REGEX_RE = \
                re.compile(self._SLIM_MONSTER_PLAYER_REGEX)
        url = self._SLIM_MONSTER_PLAYER_REGEX_RE.search(webpage).group(1)
        return self._extract_video_url_from_flvplayer_url(url)

    def _extract_html5_monster_player_url(self, webpage, video_id):
        if self._HTML5_MONSTER_PLAYER_REGEX_RE is None:
            self._HTML5_MONSTER_PLAYER_REGEX_RE = \
                re.compile(self._HTML5_MONSTER_PLAYER_REGEX)
        iframe_url = \
            self._HTML5_MONSTER_PLAYER_REGEX_RE.search(webpage).group(1)
        iframe_content = self._download_webpage(iframe_url, video_id)
        regex = re.compile((r'<\s*video\s+class\s*=\s*"html5videobox-action"'
                            r'.*?<\s*source\s+src\s*=\s*"([^"]+?)"'),
                           re.DOTALL)
        return regex.search(iframe_content).group(1)

    def suitable(self, url):
        # override class method as an object method
        # (it's always called on real instances anyway)
        # we have to check the html content to see if this plugin
        # supports this video, otherwise falling back to generic
        # plugin will work fine, because if it's not JoeMonster player,
        # it's probably embedded YouTube video.

        # First, check if the url is on joemonster.org domain
        if not super(JoeMonsterIE, self.__class__).suitable(url):
            return False

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        return (self._is_fat_monster_player(webpage) or
                self._is_slim_monster_player(webpage) or
                self._is_html5_monster_player(webpage))

    def _extract_title(self, webpage):
        title_re = re.compile(r'<title>(.*?)</title>').search(webpage)
        if title_re is None:
            self._downloader.report_warning('Unable to extract video title')
            return '_'
        title = title_re.group(1)
        title_suffix = u' - Joe Monster'
        if title.endswith(title_suffix):
            title = title[:-len(title_suffix)]
        return title

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        if self._is_fat_monster_player(webpage):
            video_url = self._extract_fat_monster_player_url(webpage)
        elif self._is_slim_monster_player(webpage):
            video_url = self._extract_slim_monster_player_url(webpage)
        elif self._is_html5_monster_player(webpage):
            video_url = \
                self._extract_html5_monster_player_url(webpage, video_id)

        return {'id': video_id,
                'title': self._extract_title(webpage),
                'url': video_url}
