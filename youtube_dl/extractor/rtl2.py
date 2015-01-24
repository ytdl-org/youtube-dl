# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    unified_strdate,
    int_or_none,
)


class RTL2IE(InfoExtractor):
    """Information Extractor for RTL NOW, RTL2 NOW, RTL NITRO, SUPER RTL NOW, VOX NOW and n-tv NOW"""
    _VALID_URL = r'http?://(?P<url>(?P<domain>(www\.)?rtl2\.de)/.*/(?P<video_id>.*))'
    _TEST = {
        'url': 'http://www.rtl2.de/sendung/grip-das-motormagazin/folge/folge-203-0',
        'md5': 'dsadasdada',
        'info_dict': {
            'id': 'folge-203-0',
            'ext': 'f4v',
            'title': 'GRIP sucht den Sommerk\xf6nig',
	    'description' : 'Matthias, Det und Helge treten gegeneinander an.'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        },
	#'params': {
                # rtmp download
        #	'skip_download': True,
	#},
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_page_url = 'http://%s/' % mobj.group('domain')
        video_id = mobj.group('video_id')
	
        webpage = self._download_webpage('http://' + mobj.group('url'), video_id)

	vico_id = self._html_search_regex(r'vico_id: ([0-9]+)', webpage, '%s');
	vivi_id = self._html_search_regex(r'vivi_id: ([0-9]+)', webpage, '%s');

	info_url = 'http://www.rtl2.de/video/php/get_video.php?vico_id=' + vico_id + '&vivi_id=' + vivi_id
	webpage = self._download_webpage(info_url, '')

	video_info = json.loads(webpage.decode("latin1"))
	print video_info


	#self._download_webpage('http://cp108781.edgefcs.net/crossdomain.xml', '')

	download_url = video_info["video"]["streamurl"] # self._html_search_regex(r'streamurl\":\"(.*?)\"', webpage, '%s');
	title = video_info["video"]["titel"] # self._html_search_regex(r'titel\":\"(.*?)\"', webpage, '%s');
	description = video_info["video"]["beschreibung"] # self._html_search_regex(r'beschreibung\":\"(.*?)\"', webpage, '%s');
	#ext = self._html_search_regex(r'streamurl\":\".*?(\..{2,4})\"', webpage, '%s');

	thumbnail = video_info["video"]["image"]

	download_url = download_url.replace("\\", "")

	stream_url = 'mp4:' + self._html_search_regex(r'ondemand/(.*)', download_url, '%s');

	#upload_date = self._html_search_regex(r'property=\"dc:date\".*?datatype=\"xsd:dateTime\".*?content=\"(.*?)\"', webpage, 'title')
	#download_url += " -y " + stream_url
	
	#print stream_url
	#print download_url
	#print description
	#print title
	#print ext

	formats = []

	fmt = {
	    'url' : download_url,
            #'app': 'ondemand?_fcs_vhost=cp108781.edgefcs.net',
            'play_path': stream_url,
            #'player_url': 'http://www.cbsnews.com/[[IMPORT]]/vidtech.cbsinteractive.com/player/3_3_0/CBSI_PLAYER_HD.swf',
            #'page_url': 'http://www.cbsnews.com',
            #'ext': ext,	
        }

	formats.append(fmt)


        return {
	    'id': video_id,
            'title': title,
	    'thumbnail' : thumbnail,
	    'description' : description,
            'formats': formats,
        }
