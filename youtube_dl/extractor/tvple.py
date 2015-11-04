# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from hashlib import sha1
import re,zlib

from ..compat import (
    compat_urllib_request
)

class tvpleIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<url>(?:www\.)?tvple\.com/(?P<id>[0-9]+))'
    _TEST = {
        'url': 'http://tvple.com/311090',
        'md5': '02e384fd3c3c6884e1bb997f6afd51e2',
        'info_dict': {
            'id': '311090',
            'ext': 'mp4',
            'uploader': '[디지털 드럭] 나비붙이',
	    'uploader_id': 'jack1609',
            'title': '팜플렛으로 yee를 연주하는 김병만',
            'description': '자작입니다. 첫 조교..인가..? 조교라긴 애매하지만, 어쨋든 노래로 만드는 건 이번이 처음입니다.\n원본 영상 출처: https://www.youtube.com/watch?v=E4BPHBL35dE\nyee는 유튜브에 치면 원본 영상이 나오는데 다들 아시죠??? 저작권 문제가 될 경우는 지우겠습니다...\n\n병만로이드라고 불러야 하나??'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def decodetvple(self,key):
      """based on decompiled tvple player v2.50401"""
      #1st key checker
      #if((key[:4] != "feff") | (key[20:21] != "_")):
      # print("error:wrong key")
      
      #descramble key
      deckey = list(key[69:85])
      code = key[125:][::-1]
      
      #descrambling
      hexed = code.replace(deckey[5], "g").replace(deckey[4], "h").replace(deckey[3], "i").replace(deckey[2], "j").replace(deckey[1], "k").replace(deckey[6], deckey[5]).replace(deckey[7], deckey[4]).replace(deckey[8], deckey[3]).replace(deckey[9], deckey[2]).replace(deckey[10], deckey[1]).replace("g", deckey[6]).replace("h", deckey[7]).replace("i", deckey[8]).replace("j", deckey[9]).replace("k", deckey[10])
      decoded = hexed.decode("hex")
      
      #2nd key checker
      #if( sha1(decoded).hexdigest() != key[85:125]):
      # print("error:key checksum failed")
      return decoded
    
    #def downloadgurum(misc):
      
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        playurl = self._html_search_regex(r'http://tvple.com/crossdomain.xml\n(.*)\n1', self.decodetvple(re.search(r'data-key="(.*)"', webpage).group(1)), "playurl")
        playpage = self._download_webpage(playurl, "playurl_%d" % int(video_id))
        videourl = re.search("<video><page_url>http://tvple.com/[0-9]+</page_url><url>(.*)</url>.*<preview>.*<url>(.*)</url>", self.decodetvple(playpage), re.DOTALL)
        # TODO more code goes here, for example ...
                
        title = re.search("<h2.*title=\"(.*)\"", webpage).group(1) #title
        uploader = re.search(r'personacon-sm".*/>\s*(.*)\s*</a>', webpage).group(1) #username
        uploader_id = re.search(r'"/ch/(.*)/videos"', webpage).group(1) #userid
        description = re.search(r'break-word">\s*(.*)\s*<button', webpage, re.DOTALL).group(1).replace(" <br />", "").replace("<br />", "").replace("\n            ", "") #description
        resolution = re.search(r'fa-television"></i></span>\s*([0-9]*)x([0-9]*)\s*</li>', webpage) #resolution
        point = re.search(r'fa-bar-chart"></i></span>\s*(.*)p\s*</li>', webpage).group(1).replace(",", "") #point?
        view_count = int(re.search(r'fa-play"></i></span>\s*(.*)\s*</li>', webpage).group(1).replace(",", "")) #played
        duration = int(re.search(r'fa-video-camera"></i></span>\s*(\d*):(\d*)\s*</li>', webpage).group(1))*60+int(re.search(r'fa-video-camera"></i></span>\s*(\d*):(\d*)\s*</li>', webpage).group(2)) #duration
        #date = re.search(r'<small>\s*(\d{4}-\d{2}-\d{2}) (\d{1,2}:\d{1,2}:\d{1,2}).*\s*</small>', webpage).group(1).replace("-", "") #date FIXME-sometimes not w
        #time = re.search(r'<small>\s*(\d{4}-\d{2}-\d{2}) (\d{1,2}:\d{1,2}:\d{1,2}).*\s*</small>', webpage).group(2) #time FIXME-sometimes not working
        group = re.search(r'badge-info">(.*)</span>', webpage).group(1) #group
        tags = re.findall(r'"/tag/(.*)" class="tag user-added">', webpage) #tags
        formats = [{
	  'url' : videourl.group(1),
	  'ext' : 'mp4',
	  'format_id' : 'mp4_h264_aac',
	  'width' : int(resolution.group(1)),
	  'height' : int(resolution.group(2)),
	  'no_resume' : True
	  }]
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': videourl.group(2),
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'view_count': view_count,
            #'comment_count': comment_count,
            'formats': formats,
            #'subtitles': subtitles,
            'tags' : tags
            
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
