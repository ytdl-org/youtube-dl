# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import parse_duration

class MakoIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.)?mako\.co\.il/([-\w]+/){2}Video-(?P<id>[0-9a-f]+)\.htm'
    _TEST = {
            'url': 'https://www.mako.co.il/tv-erez-nehederet/season14-shauli-and-irena/Video-6c53a12777d9c51006.htm',
            'info_dict': {
                'id': '6c53a12777d9c510VgnVCM2000002a0c10acRCRD',
                'title': u'\u05e9\u05d0\u05d5\u05dc\u05d9 \u05d5\u05d0\u05d9\u05e8\u05e0\u05d4 \u05d1\u05d1\u05d9\u05ea \u05d7\u05d5\u05dc\u05d9\u05dd \u2013 \u05e4\u05e8\u05e7 \u05d4\u05e1\u05d9\u05d5\u05dd',
                'description': u'האם שאולי הולך למות?',
                'ext': 'm3u8',
                }
            }

    @staticmethod
    def parse_urls(json_list):
        out_list = []
        for d in json_list:
            out_list.append({
                'url': d['url'],
                })
        return out_list

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # get video identifiers, later used to request it.
        vcmid = self._search_regex(r"var vcmidOfContent ?= ?'(\w+)'", webpage, "vcmid")
        videoChannelId = self._search_regex(r"var currentChannelId ?= ?'(\w+)'", webpage, "videoChannelId")

        # get an authentication token
        rbzid_page = self._download_webpage('https://www.mako.co.il/hankschrader/jessepinkman/heisenberg', video_id)
        rbzid = rbzid_page[14:-3]

        # get video details and stream urls from ajax
        js = self._download_json('https://mako.co.il/AjaxPage?jspName=playlist.jsp&vcmid={}&videoChannelId={}&galleryChannelId={}&encryption=no'.format(
            vcmid, videoChannelId, vcmid), video_id)

        print self.parse_urls(js['media'])

        return {
            'id': js['videoDetails']['guid'],
            'title': js['videoDetails']['title'],
            'description': js['videoDetails']['desc'],
            'duration': parse_duration(js['videoDetails']['duration']),
            'formats': self.parse_urls(js['media']),
            'view_count': js['videoDetails']['numViews'],
            }

