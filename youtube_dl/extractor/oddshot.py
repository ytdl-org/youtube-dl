import re
from .common import InfoExtractor
from youtube_dl.utils import compat_str

class OddshotIE(InfoExtractor):
	_VALID_URL = r'(?:https?://)?(?:www\.)?oddshot\.tv/shot/.+/(?P<id>.+)'
	_TEST = {
		'url': 'https://oddshot.tv/shot/IzakOOO/UzoKaNE4KaNBtJu8zTVvomJd',
		'md5': '1a927556df771148d20657120f096af5',
		'info_dict': {
			'id': 			'UzoKaNE4KaNBtJu8zTVvomJd',
			'ext':			'mp4',
			'title': 		'pozamiatane',
			'description':	'Twitch - Counter-Strike: Global Offensive - IzakOOO'
		}
	}

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		# Using compat_str for running test  : if not isinstance(info_dict['id'], compat_str): YoutubeDL.py l1235
		video_id = compat_str(mobj.group('id'))
		# Default User-Agent not working, but working with curl User-Agent
		webpage = self._download_webpage(url,video_id,headers={'User-Agent':'curl/7.8 (i386-redhat-linux-gnu) libcurl 7.8 (OpenSSL 0.9.6b) (ipv6 enabled)'})
		self.report_extraction(video_id)
		# Perhaps a proper way with helpers but 'data-react-helmet="true"' ruins
		title = self._html_search_regex(r'property="og:title" content="(.+?)"', webpage, u'video Title')
		url = self._html_search_regex(r'property="og:video:secure_url" content="(.+?)"', webpage, u'video URL')
		description = self._html_search_regex(r'property="og:description" content="(.+?)"', webpage, u'video Description')
		thumbnail = self._html_search_regex(r'property="og:image" content="(.+?)"', webpage, u'video Thumbnail')
		return {
			'id':        	video_id,
			'url':       	url,
			'description':	description,
			'title':     	title,
			'thumbnail':	thumbnail
		}
