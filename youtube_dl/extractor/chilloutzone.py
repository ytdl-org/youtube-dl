import re
import base64
import urllib
import json

from .common import InfoExtractor

video_container = ('.mp4', '.mkv', '.flv')

class ChilloutzoneIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?chilloutzone\.net/video/(?P<id>[\w|-]+).html'

    _TEST = {
    	u'url': u'http://www.chilloutzone.net/video/enemene-meck-alle-katzen-weg.html',
    	u'file': u'18088-enemene-meck-alle-katzen-weg.mp4',
    	u'md5': u'a76f3457e813ea0037e5244f509e66d1',
    	u'info_dict': {
        	u"id": u"18088",
        	u"ext": u"mp4",
        	u"title": u"Enemene Meck - Alle Katzen weg"
    	}
	}

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
    	video_id = mobj.group('id')

    	webpage_url = 'http://www.chilloutzone.net/video/' + video_id + '.html'

    	# Log that we are starting to download the page
    	self.report_download_webpage(webpage_url)
    	webpage = self._download_webpage(webpage_url, video_id)
	


    	# Log that we are starting to parse the page
    	self.report_extraction(video_id)    	
    	# Find base64 decoded file info
    	base64_video_info = self._html_search_regex(r'var cozVidData = "(.+?)";', webpage, u'video Data')
    	# decode string and find video file
    	decoded_video_info = base64.b64decode(base64_video_info)
    	video_info_dict = json.loads(decoded_video_info)
    	# get video information from dict
    	media_url = video_info_dict['mediaUrl']
    	description = video_info_dict['description']
    	title = video_info_dict['title']
    	native_platform = video_info_dict['nativePlatform']
    	native_video_id = video_info_dict['nativeVideoId']
    	source_priority = video_info_dict['sourcePriority']


    	# Start video extraction
    	video_url = ''
    	# If nativePlatform is None a fallback mechanism is used (i.e. youtube embed)
    	if native_platform == None:
    		# Look for other video urls
    		video_url = self._html_search_regex(r'<iframe.* src="(.+?)".*', webpage, u'fallback Video URL')
    		if 'youtube' in video_url:
    			self.to_screen(u'Youtube video detected:')
    			print video_url
    			return self.url_result(video_url, ie='Youtube')

    	# For debugging purposes
    	#print video_info_dict
    	#print native_platform
    	#print native_video_id
    	#print source_priority
    	#print media_url

    	# Non Fallback: Decide to use native source (e.g. youtube or vimeo) or
    	# the own CDN
    	if source_priority == 'native':
    	    if native_platform == 'youtube':
                self.to_screen(u'Youtube video detected:')
                video_url = 'https://www.youtube.com/watch?v=' + native_video_id
                print video_url
                return self.url_result(video_url, ie='Youtube') 
            if native_platform == 'vimeo':
    	        self.to_screen(u'Vimeo video detected:')
                video_url = 'http://vimeo.com/' + native_video_id
                print video_url
                return self.url_result(video_url, ie='Vimeo')

        # No redirect, use coz media url
        video_url = media_url
        if video_url.endswith('.mp4') == False:
			self.report_warning(u'Url does not contain a video container')
			return []


        return [{
    		'id':        video_id,
    		'url':       video_url,
    		'ext':       'mp4',
    		'title':     title,
    		'description': description
		}]



