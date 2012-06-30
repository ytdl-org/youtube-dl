#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import HTMLParser
import httplib
import netrc
import os
import re
import socket
import time
import urllib
import urllib2
import email.utils
import xml.etree.ElementTree
from urlparse import parse_qs

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

from utils import *


class InfoExtractor(object):
	"""Information Extractor class.

	Information extractors are the classes that, given a URL, extract
	information from the video (or videos) the URL refers to. This
	information includes the real video URL, the video title and simplified
	title, author and others. The information is stored in a dictionary
	which is then passed to the FileDownloader. The FileDownloader
	processes this information possibly downloading the video to the file
	system, among other possible outcomes. The dictionaries must include
	the following fields:

	id:		Video identifier.
	url:		Final video URL.
	uploader:	Nickname of the video uploader.
	title:		Literal title.
	ext:		Video filename extension.
	format:		Video format.
	player_url:	SWF Player URL (may be None).

	The following fields are optional. Their primary purpose is to allow
	youtube-dl to serve as the backend for a video search function, such
	as the one in youtube2mp3.  They are only used when their respective
	forced printing functions are called:

	thumbnail:	Full URL to a video thumbnail image.
	description:	One-line video description.

	Subclasses of this one should re-define the _real_initialize() and
	_real_extract() methods and define a _VALID_URL regexp.
	Probably, they should also be added to the list of extractors.
	"""

	_ready = False
	_downloader = None

	def __init__(self, downloader=None):
		"""Constructor. Receives an optional downloader."""
		self._ready = False
		self.set_downloader(downloader)

	def suitable(self, url):
		"""Receives a URL and returns True if suitable for this IE."""
		return re.match(self._VALID_URL, url) is not None

	def initialize(self):
		"""Initializes an instance (authentication, etc)."""
		if not self._ready:
			self._real_initialize()
			self._ready = True

	def extract(self, url):
		"""Extracts URL information and returns it in list of dicts."""
		self.initialize()
		return self._real_extract(url)

	def set_downloader(self, downloader):
		"""Sets the downloader for this IE."""
		self._downloader = downloader

	def _real_initialize(self):
		"""Real initialization process. Redefine in subclasses."""
		pass

	def _real_extract(self, url):
		"""Real extraction process. Redefine in subclasses."""
		pass


class YoutubeIE(InfoExtractor):
	"""Information extractor for youtube.com."""

	_VALID_URL = r'^((?:https?://)?(?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/)(?!view_play_list|my_playlists|artist|playlist)(?:(?:(?:v|embed|e)/)|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?v=))?)?([0-9A-Za-z_-]+)(?(1).+)?$'
	_LANG_URL = r'http://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
	_LOGIN_URL = 'https://www.youtube.com/signup?next=/&gl=US&hl=en'
	_AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
	_NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
	_NETRC_MACHINE = 'youtube'
	# Listed in order of quality
	_available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '17', '13']
	_available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '17', '13']
	_video_extensions = {
		'13': '3gp',
		'17': 'mp4',
		'18': 'mp4',
		'22': 'mp4',
		'37': 'mp4',
		'38': 'video', # You actually don't know if this will be MOV, AVI or whatever
		'43': 'webm',
		'44': 'webm',
		'45': 'webm',
		'46': 'webm',
	}
	_video_dimensions = {
		'5': '240x400',
		'6': '???',
		'13': '???',
		'17': '144x176',
		'18': '360x640',
		'22': '720x1280',
		'34': '360x640',
		'35': '480x854',
		'37': '1080x1920',
		'38': '3072x4096',
		'43': '360x640',
		'44': '480x854',
		'45': '720x1280',
		'46': '1080x1920',
	}	
	IE_NAME = u'youtube'

	def report_lang(self):
		"""Report attempt to set language."""
		self._downloader.to_screen(u'[youtube] Setting language')

	def report_login(self):
		"""Report attempt to log in."""
		self._downloader.to_screen(u'[youtube] Logging in')

	def report_age_confirmation(self):
		"""Report attempt to confirm age."""
		self._downloader.to_screen(u'[youtube] Confirming age')

	def report_video_webpage_download(self, video_id):
		"""Report attempt to download video webpage."""
		self._downloader.to_screen(u'[youtube] %s: Downloading video webpage' % video_id)

	def report_video_info_webpage_download(self, video_id):
		"""Report attempt to download video info webpage."""
		self._downloader.to_screen(u'[youtube] %s: Downloading video info webpage' % video_id)

	def report_video_subtitles_download(self, video_id):
		"""Report attempt to download video info webpage."""
		self._downloader.to_screen(u'[youtube] %s: Downloading video subtitles' % video_id)

	def report_information_extraction(self, video_id):
		"""Report attempt to extract video information."""
		self._downloader.to_screen(u'[youtube] %s: Extracting video information' % video_id)

	def report_unavailable_format(self, video_id, format):
		"""Report extracted video URL."""
		self._downloader.to_screen(u'[youtube] %s: Format %s not available' % (video_id, format))

	def report_rtmp_download(self):
		"""Indicate the download will use the RTMP protocol."""
		self._downloader.to_screen(u'[youtube] RTMP download detected')

	def _closed_captions_xml_to_srt(self, xml_string):
		srt = ''
		texts = re.findall(r'<text start="([\d\.]+)"( dur="([\d\.]+)")?>([^<]+)</text>', xml_string, re.MULTILINE)
		# TODO parse xml instead of regex
		for n, (start, dur_tag, dur, caption) in enumerate(texts):
			if not dur: dur = '4'
			start = float(start)
			end = start + float(dur)
			start = "%02i:%02i:%02i,%03i" %(start/(60*60), start/60%60, start%60, start%1*1000)
			end = "%02i:%02i:%02i,%03i" %(end/(60*60), end/60%60, end%60, end%1*1000)
			caption = unescapeHTML(caption)
			caption = unescapeHTML(caption) # double cycle, intentional
			srt += str(n+1) + '\n'
			srt += start + ' --> ' + end + '\n'
			srt += caption + '\n\n'
		return srt

	def _print_formats(self, formats):
		print 'Available formats:'
		for x in formats:
			print '%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'flv'), self._video_dimensions.get(x, '???'))

	def _real_initialize(self):
		if self._downloader is None:
			return

		username = None
		password = None
		downloader_params = self._downloader.params

		# Attempt to use provided username and password or .netrc data
		if downloader_params.get('username', None) is not None:
			username = downloader_params['username']
			password = downloader_params['password']
		elif downloader_params.get('usenetrc', False):
			try:
				info = netrc.netrc().authenticators(self._NETRC_MACHINE)
				if info is not None:
					username = info[0]
					password = info[2]
				else:
					raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
			except (IOError, netrc.NetrcParseError), err:
				self._downloader.to_stderr(u'WARNING: parsing .netrc: %s' % str(err))
				return

		# Set language
		request = urllib2.Request(self._LANG_URL)
		try:
			self.report_lang()
			urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.to_stderr(u'WARNING: unable to set language: %s' % str(err))
			return

		# No authentication to be performed
		if username is None:
			return

		# Log in
		login_form = {
				'current_form': 'loginForm',
				'next':		'/',
				'action_login':	'Log In',
				'username':	username,
				'password':	password,
				}
		request = urllib2.Request(self._LOGIN_URL, urllib.urlencode(login_form))
		try:
			self.report_login()
			login_results = urllib2.urlopen(request).read()
			if re.search(r'(?i)<form[^>]* name="loginForm"', login_results) is not None:
				self._downloader.to_stderr(u'WARNING: unable to log in: bad username or password')
				return
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.to_stderr(u'WARNING: unable to log in: %s' % str(err))
			return

		# Confirm age
		age_form = {
				'next_url':		'/',
				'action_confirm':	'Confirm',
				}
		request = urllib2.Request(self._AGE_URL, urllib.urlencode(age_form))
		try:
			self.report_age_confirmation()
			age_results = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to confirm age: %s' % str(err))
			return

	def _real_extract(self, url):
		# Extract original video URL from URL with redirection, like age verification, using next_url parameter
		mobj = re.search(self._NEXT_URL_RE, url)
		if mobj:
			url = 'http://www.youtube.com/' + urllib.unquote(mobj.group(1)).lstrip('/')

		# Extract video id from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		video_id = mobj.group(2)

		# Get video webpage
		self.report_video_webpage_download(video_id)
		request = urllib2.Request('http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id)
		try:
			video_webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		# Attempt to extract SWF player URL
		mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
		if mobj is not None:
			player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
		else:
			player_url = None

		# Get video info
		self.report_video_info_webpage_download(video_id)
		for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
			video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
					% (video_id, el_type))
			request = urllib2.Request(video_info_url)
			try:
				video_info_webpage = urllib2.urlopen(request).read()
				video_info = parse_qs(video_info_webpage)
				if 'token' in video_info:
					break
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download video info webpage: %s' % str(err))
				return
		if 'token' not in video_info:
			if 'reason' in video_info:
				self._downloader.trouble(u'ERROR: YouTube said: %s' % video_info['reason'][0].decode('utf-8'))
			else:
				self._downloader.trouble(u'ERROR: "token" parameter not in video info for unknown reason')
			return

		# Check for "rental" videos
		if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
			self._downloader.trouble(u'ERROR: "rental" videos not supported')
			return

		# Start extracting information
		self.report_information_extraction(video_id)

		# uploader
		if 'author' not in video_info:
			self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
			return
		video_uploader = urllib.unquote_plus(video_info['author'][0])

		# title
		if 'title' not in video_info:
			self._downloader.trouble(u'ERROR: unable to extract video title')
			return
		video_title = urllib.unquote_plus(video_info['title'][0])
		video_title = video_title.decode('utf-8')

		# thumbnail image
		if 'thumbnail_url' not in video_info:
			self._downloader.trouble(u'WARNING: unable to extract video thumbnail')
			video_thumbnail = ''
		else:	# don't panic if we can't find it
			video_thumbnail = urllib.unquote_plus(video_info['thumbnail_url'][0])

		# upload date
		upload_date = u'NA'
		mobj = re.search(r'id="eow-date.*?>(.*?)</span>', video_webpage, re.DOTALL)
		if mobj is not None:
			upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
			format_expressions = ['%d %B %Y', '%B %d %Y', '%b %d %Y']
			for expression in format_expressions:
				try:
					upload_date = datetime.datetime.strptime(upload_date, expression).strftime('%Y%m%d')
				except:
					pass

		# description
		video_description = get_element_by_id("eow-description", video_webpage.decode('utf8'))
		if video_description: video_description = clean_html(video_description)
		else: video_description = ''
			
		# closed captions
		video_subtitles = None
		if self._downloader.params.get('writesubtitles', False):
			try:
				self.report_video_subtitles_download(video_id)
				request = urllib2.Request('http://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id)
				try:
					srt_list = urllib2.urlopen(request).read()
				except (urllib2.URLError, httplib.HTTPException, socket.error), err:
					raise Trouble(u'WARNING: unable to download video subtitles: %s' % str(err))
				srt_lang_list = re.findall(r'lang_code="([\w\-]+)"', srt_list)
				if not srt_lang_list:
					raise Trouble(u'WARNING: video has no closed captions')
				if self._downloader.params.get('subtitleslang', False):
					srt_lang = self._downloader.params.get('subtitleslang')
				elif 'en' in srt_lang_list:
					srt_lang = 'en'
				else:
					srt_lang = srt_lang_list[0]
				if not srt_lang in srt_lang_list:
					raise Trouble(u'WARNING: no closed captions found in the specified language')
				request = urllib2.Request('http://video.google.com/timedtext?hl=en&lang=%s&v=%s' % (srt_lang, video_id))
				try:
					srt_xml = urllib2.urlopen(request).read()
				except (urllib2.URLError, httplib.HTTPException, socket.error), err:
					raise Trouble(u'WARNING: unable to download video subtitles: %s' % str(err))
				video_subtitles = self._closed_captions_xml_to_srt(srt_xml.decode('utf-8'))
			except Trouble as trouble:
				self._downloader.trouble(trouble[0])

		# token
		video_token = urllib.unquote_plus(video_info['token'][0])

		# Decide which formats to download
		req_format = self._downloader.params.get('format', None)

		if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
			self.report_rtmp_download()
			video_url_list = [(None, video_info['conn'][0])]
		elif 'url_encoded_fmt_stream_map' in video_info and len(video_info['url_encoded_fmt_stream_map']) >= 1:
			url_data_strs = video_info['url_encoded_fmt_stream_map'][0].split(',')
			url_data = [parse_qs(uds) for uds in url_data_strs]
			url_data = filter(lambda ud: 'itag' in ud and 'url' in ud, url_data)
			url_map = dict((ud['itag'][0], ud['url'][0]) for ud in url_data)

			format_limit = self._downloader.params.get('format_limit', None)
			available_formats = self._available_formats_prefer_free if self._downloader.params.get('prefer_free_formats', False) else self._available_formats
			if format_limit is not None and format_limit in available_formats:
				format_list = available_formats[available_formats.index(format_limit):]
			else:
				format_list = available_formats
			existing_formats = [x for x in format_list if x in url_map]
			if len(existing_formats) == 0:
				self._downloader.trouble(u'ERROR: no known formats available for video')
				return
			if self._downloader.params.get('listformats', None):
				self._print_formats(existing_formats)
				return
			if req_format is None or req_format == 'best':
				video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
			elif req_format == 'worst':
				video_url_list = [(existing_formats[len(existing_formats)-1], url_map[existing_formats[len(existing_formats)-1]])] # worst quality
			elif req_format in ('-1', 'all'):
				video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
			else:
				# Specific formats. We pick the first in a slash-delimeted sequence.
				# For example, if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
				req_formats = req_format.split('/')
				video_url_list = None
				for rf in req_formats:
					if rf in url_map:
						video_url_list = [(rf, url_map[rf])]
						break
				if video_url_list is None:
					self._downloader.trouble(u'ERROR: requested format not available')
					return
		else:
			self._downloader.trouble(u'ERROR: no conn or url_encoded_fmt_stream_map information found in video info')
			return

		results = []
		for format_param, video_real_url in video_url_list:
			# Extension
			video_extension = self._video_extensions.get(format_param, 'flv')

			results.append({
				'id':		video_id.decode('utf-8'),
				'url':		video_real_url.decode('utf-8'),
				'uploader':	video_uploader.decode('utf-8'),
				'upload_date':	upload_date,
				'title':	video_title,
				'ext':		video_extension.decode('utf-8'),
				'format':	(format_param is None and u'NA' or format_param.decode('utf-8')),
				'thumbnail':	video_thumbnail.decode('utf-8'),
				'description':	video_description,
				'player_url':	player_url,
				'subtitles':	video_subtitles
			})
		return results


class MetacafeIE(InfoExtractor):
	"""Information Extractor for metacafe.com."""

	_VALID_URL = r'(?:http://)?(?:www\.)?metacafe\.com/watch/([^/]+)/([^/]+)/.*'
	_DISCLAIMER = 'http://www.metacafe.com/family_filter/'
	_FILTER_POST = 'http://www.metacafe.com/f/index.php?inputType=filter&controllerGroup=user'
	IE_NAME = u'metacafe'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_disclaimer(self):
		"""Report disclaimer retrieval."""
		self._downloader.to_screen(u'[metacafe] Retrieving disclaimer')

	def report_age_confirmation(self):
		"""Report attempt to confirm age."""
		self._downloader.to_screen(u'[metacafe] Confirming age')

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[metacafe] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[metacafe] %s: Extracting information' % video_id)

	def _real_initialize(self):
		# Retrieve disclaimer
		request = urllib2.Request(self._DISCLAIMER)
		try:
			self.report_disclaimer()
			disclaimer = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to retrieve disclaimer: %s' % str(err))
			return

		# Confirm age
		disclaimer_form = {
			'filters': '0',
			'submit': "Continue - I'm over 18",
			}
		request = urllib2.Request(self._FILTER_POST, urllib.urlencode(disclaimer_form))
		try:
			self.report_age_confirmation()
			disclaimer = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to confirm age: %s' % str(err))
			return

	def _real_extract(self, url):
		# Extract id and simplified title from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		video_id = mobj.group(1)

		# Check if video comes from YouTube
		mobj2 = re.match(r'^yt-(.*)$', video_id)
		if mobj2 is not None:
			self._downloader.download(['http://www.youtube.com/watch?v=%s' % mobj2.group(1)])
			return

		# Retrieve video webpage to extract further information
		request = urllib2.Request('http://www.metacafe.com/watch/%s/' % video_id)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable retrieve video webpage: %s' % str(err))
			return

		# Extract URL, uploader and title from webpage
		self.report_extraction(video_id)
		mobj = re.search(r'(?m)&mediaURL=([^&]+)', webpage)
		if mobj is not None:
			mediaURL = urllib.unquote(mobj.group(1))
			video_extension = mediaURL[-3:]

			# Extract gdaKey if available
			mobj = re.search(r'(?m)&gdaKey=(.*?)&', webpage)
			if mobj is None:
				video_url = mediaURL
			else:
				gdaKey = mobj.group(1)
				video_url = '%s?__gda__=%s' % (mediaURL, gdaKey)
		else:
			mobj = re.search(r' name="flashvars" value="(.*?)"', webpage)
			if mobj is None:
				self._downloader.trouble(u'ERROR: unable to extract media URL')
				return
			vardict = parse_qs(mobj.group(1))
			if 'mediaData' not in vardict:
				self._downloader.trouble(u'ERROR: unable to extract media URL')
				return
			mobj = re.search(r'"mediaURL":"(http.*?)","key":"(.*?)"', vardict['mediaData'][0])
			if mobj is None:
				self._downloader.trouble(u'ERROR: unable to extract media URL')
				return
			mediaURL = mobj.group(1).replace('\\/', '/')
			video_extension = mediaURL[-3:]
			video_url = '%s?__gda__=%s' % (mediaURL, mobj.group(2))

		mobj = re.search(r'(?im)<title>(.*) - Video</title>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		video_title = mobj.group(1).decode('utf-8')

		mobj = re.search(r'(?ms)By:\s*<a .*?>(.+?)<', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
			return
		video_uploader = mobj.group(1)

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	video_uploader.decode('utf-8'),
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url':	None,
		}]


class DailymotionIE(InfoExtractor):
	"""Information Extractor for Dailymotion"""

	_VALID_URL = r'(?i)(?:https?://)?(?:www\.)?dailymotion\.[a-z]{2,3}/video/([^_/]+)_([^/]+)'
	IE_NAME = u'dailymotion'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[dailymotion] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[dailymotion] %s: Extracting information' % video_id)

	def _real_extract(self, url):
		# Extract id and simplified title from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		video_id = mobj.group(1)

		video_extension = 'flv'

		# Retrieve video webpage to extract further information
		request = urllib2.Request(url)
		request.add_header('Cookie', 'family_filter=off')
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable retrieve video webpage: %s' % str(err))
			return

		# Extract URL, uploader and title from webpage
		self.report_extraction(video_id)
		mobj = re.search(r'(?i)addVariable\(\"sequence\"\s*,\s*\"([^\"]+?)\"\)', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract media URL')
			return
		sequence = urllib.unquote(mobj.group(1))
		mobj = re.search(r',\"sdURL\"\:\"([^\"]+?)\",', sequence)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract media URL')
			return
		mediaURL = urllib.unquote(mobj.group(1)).replace('\\', '')

		# if needed add http://www.dailymotion.com/ if relative URL

		video_url = mediaURL

		mobj = re.search(r'<meta property="og:title" content="(?P<title>[^"]*)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		video_title = unescapeHTML(mobj.group('title').decode('utf-8'))

		mobj = re.search(r'(?im)<span class="owner[^\"]+?">[^<]+?<a [^>]+?>([^<]+?)</a></span>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
			return
		video_uploader = mobj.group(1)

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	video_uploader.decode('utf-8'),
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url':	None,
		}]


class GoogleIE(InfoExtractor):
	"""Information extractor for video.google.com."""

	_VALID_URL = r'(?:http://)?video\.google\.(?:com(?:\.au)?|co\.(?:uk|jp|kr|cr)|ca|de|es|fr|it|nl|pl)/videoplay\?docid=([^\&]+).*'
	IE_NAME = u'video.google'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[video.google] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[video.google] %s: Extracting information' % video_id)

	def _real_extract(self, url):
		# Extract id from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		video_id = mobj.group(1)

		video_extension = 'mp4'

		# Retrieve video webpage to extract further information
		request = urllib2.Request('http://video.google.com/videoplay?docid=%s&hl=en&oe=utf-8' % video_id)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return

		# Extract URL, uploader, and title from webpage
		self.report_extraction(video_id)
		mobj = re.search(r"download_url:'([^']+)'", webpage)
		if mobj is None:
			video_extension = 'flv'
			mobj = re.search(r"(?i)videoUrl\\x3d(.+?)\\x26", webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract media URL')
			return
		mediaURL = urllib.unquote(mobj.group(1))
		mediaURL = mediaURL.replace('\\x3d', '\x3d')
		mediaURL = mediaURL.replace('\\x26', '\x26')

		video_url = mediaURL

		mobj = re.search(r'<title>(.*)</title>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		video_title = mobj.group(1).decode('utf-8')

		# Extract video description
		mobj = re.search(r'<span id=short-desc-content>([^<]*)</span>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video description')
			return
		video_description = mobj.group(1).decode('utf-8')
		if not video_description:
			video_description = 'No description available.'

		# Extract video thumbnail
		if self._downloader.params.get('forcethumbnail', False):
			request = urllib2.Request('http://video.google.com/videosearch?q=%s+site:video.google.com&hl=en' % abs(int(video_id)))
			try:
				webpage = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
				return
			mobj = re.search(r'<img class=thumbnail-img (?:.* )?src=(http.*)>', webpage)
			if mobj is None:
				self._downloader.trouble(u'ERROR: unable to extract video thumbnail')
				return
			video_thumbnail = mobj.group(1)
		else:	# we need something to pass to process_info
			video_thumbnail = ''

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	u'NA',
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url':	None,
		}]


class PhotobucketIE(InfoExtractor):
	"""Information extractor for photobucket.com."""

	_VALID_URL = r'(?:http://)?(?:[a-z0-9]+\.)?photobucket\.com/.*[\?\&]current=(.*\.flv)'
	IE_NAME = u'photobucket'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[photobucket] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[photobucket] %s: Extracting information' % video_id)

	def _real_extract(self, url):
		# Extract id from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		video_id = mobj.group(1)

		video_extension = 'flv'

		# Retrieve video webpage to extract further information
		request = urllib2.Request(url)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return

		# Extract URL, uploader, and title from webpage
		self.report_extraction(video_id)
		mobj = re.search(r'<link rel="video_src" href=".*\?file=([^"]+)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract media URL')
			return
		mediaURL = urllib.unquote(mobj.group(1))

		video_url = mediaURL

		mobj = re.search(r'<title>(.*) video by (.*) - Photobucket</title>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		video_title = mobj.group(1).decode('utf-8')

		video_uploader = mobj.group(2).decode('utf-8')

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	video_uploader,
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url':	None,
		}]


class YahooIE(InfoExtractor):
	"""Information extractor for video.yahoo.com."""

	# _VALID_URL matches all Yahoo! Video URLs
	# _VPAGE_URL matches only the extractable '/watch/' URLs
	_VALID_URL = r'(?:http://)?(?:[a-z]+\.)?video\.yahoo\.com/(?:watch|network)/([0-9]+)(?:/|\?v=)([0-9]+)(?:[#\?].*)?'
	_VPAGE_URL = r'(?:http://)?video\.yahoo\.com/watch/([0-9]+)/([0-9]+)(?:[#\?].*)?'
	IE_NAME = u'video.yahoo'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[video.yahoo] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[video.yahoo] %s: Extracting information' % video_id)

	def _real_extract(self, url, new_video=True):
		# Extract ID from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		video_id = mobj.group(2)
		video_extension = 'flv'

		# Rewrite valid but non-extractable URLs as
		# extractable English language /watch/ URLs
		if re.match(self._VPAGE_URL, url) is None:
			request = urllib2.Request(url)
			try:
				webpage = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
				return

			mobj = re.search(r'\("id", "([0-9]+)"\);', webpage)
			if mobj is None:
				self._downloader.trouble(u'ERROR: Unable to extract id field')
				return
			yahoo_id = mobj.group(1)

			mobj = re.search(r'\("vid", "([0-9]+)"\);', webpage)
			if mobj is None:
				self._downloader.trouble(u'ERROR: Unable to extract vid field')
				return
			yahoo_vid = mobj.group(1)

			url = 'http://video.yahoo.com/watch/%s/%s' % (yahoo_vid, yahoo_id)
			return self._real_extract(url, new_video=False)

		# Retrieve video webpage to extract further information
		request = urllib2.Request(url)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return

		# Extract uploader and title from webpage
		self.report_extraction(video_id)
		mobj = re.search(r'<meta name="title" content="(.*)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video title')
			return
		video_title = mobj.group(1).decode('utf-8')

		mobj = re.search(r'<h2 class="ti-5"><a href="http://video\.yahoo\.com/(people|profile)/[0-9]+" beacon=".*">(.*)</a></h2>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video uploader')
			return
		video_uploader = mobj.group(1).decode('utf-8')

		# Extract video thumbnail
		mobj = re.search(r'<link rel="image_src" href="(.*)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video thumbnail')
			return
		video_thumbnail = mobj.group(1).decode('utf-8')

		# Extract video description
		mobj = re.search(r'<meta name="description" content="(.*)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video description')
			return
		video_description = mobj.group(1).decode('utf-8')
		if not video_description:
			video_description = 'No description available.'

		# Extract video height and width
		mobj = re.search(r'<meta name="video_height" content="([0-9]+)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video height')
			return
		yv_video_height = mobj.group(1)

		mobj = re.search(r'<meta name="video_width" content="([0-9]+)" />', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video width')
			return
		yv_video_width = mobj.group(1)

		# Retrieve video playlist to extract media URL
		# I'm not completely sure what all these options are, but we
		# seem to need most of them, otherwise the server sends a 401.
		yv_lg = 'R0xx6idZnW2zlrKP8xxAIR'  # not sure what this represents
		yv_bitrate = '700'  # according to Wikipedia this is hard-coded
		request = urllib2.Request('http://cosmos.bcst.yahoo.com/up/yep/process/getPlaylistFOP.php?node_id=' + video_id +
				'&tech=flash&mode=playlist&lg=' + yv_lg + '&bitrate=' + yv_bitrate + '&vidH=' + yv_video_height +
				'&vidW=' + yv_video_width + '&swf=as3&rd=video.yahoo.com&tk=null&adsupported=v1,v2,&eventid=1301797')
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return

		# Extract media URL from playlist XML
		mobj = re.search(r'<STREAM APP="(http://.*)" FULLPATH="/?(/.*\.flv\?[^"]*)"', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: Unable to extract media URL')
			return
		video_url = urllib.unquote(mobj.group(1) + mobj.group(2)).decode('utf-8')
		video_url = unescapeHTML(video_url)

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url,
			'uploader':	video_uploader,
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'thumbnail':	video_thumbnail.decode('utf-8'),
			'description':	video_description,
			'thumbnail':	video_thumbnail,
			'player_url':	None,
		}]


class VimeoIE(InfoExtractor):
	"""Information extractor for vimeo.com."""

	# _VALID_URL matches Vimeo URLs
	_VALID_URL = r'(?:https?://)?(?:(?:www|player).)?vimeo\.com/(?:groups/[^/]+/)?(?:videos?/)?([0-9]+)'
	IE_NAME = u'vimeo'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[vimeo] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[vimeo] %s: Extracting information' % video_id)

	def _real_extract(self, url, new_video=True):
		# Extract ID from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		video_id = mobj.group(1)

		# Retrieve video webpage to extract further information
		request = urllib2.Request(url, None, std_headers)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return

		# Now we begin extracting as much information as we can from what we
		# retrieved. First we extract the information common to all extractors,
		# and latter we extract those that are Vimeo specific.
		self.report_extraction(video_id)

		# Extract the config JSON
		config = webpage.split(' = {config:')[1].split(',assets:')[0]
		try:
			config = json.loads(config)
		except:
			self._downloader.trouble(u'ERROR: unable to extract info section')
			return
		
		# Extract title
		video_title = config["video"]["title"]

		# Extract uploader
		video_uploader = config["video"]["owner"]["name"]

		# Extract video thumbnail
		video_thumbnail = config["video"]["thumbnail"]

		# Extract video description
		video_description = get_element_by_id("description", webpage.decode('utf8'))
		if video_description: video_description = clean_html(video_description)
		else: video_description = ''

		# Extract upload date
		video_upload_date = u'NA'
		mobj = re.search(r'<span id="clip-date" style="display:none">[^:]*: (.*?)( \([^\(]*\))?</span>', webpage)
		if mobj is not None:
			video_upload_date = mobj.group(1)

		# Vimeo specific: extract request signature and timestamp
		sig = config['request']['signature']
		timestamp = config['request']['timestamp']

		# Vimeo specific: extract video codec and quality information
		# TODO bind to format param
		codecs = [('h264', 'mp4'), ('vp8', 'flv'), ('vp6', 'flv')]
		for codec in codecs:
			if codec[0] in config["video"]["files"]:
				video_codec = codec[0]
				video_extension = codec[1]
				if 'hd' in config["video"]["files"][codec[0]]: quality = 'hd'
				else: quality = 'sd'
				break
		else:
			self._downloader.trouble(u'ERROR: no known codec found')
			return

		video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=%s&type=moogaloop_local&embed_location=" \
					%(video_id, sig, timestamp, quality, video_codec.upper())

		return [{
			'id':		video_id,
			'url':		video_url,
			'uploader':	video_uploader,
			'upload_date':	video_upload_date,
			'title':	video_title,
			'ext':		video_extension,
			'thumbnail':	video_thumbnail,
			'description':	video_description,
			'player_url':	None,
		}]


class GenericIE(InfoExtractor):
	"""Generic last-resort information extractor."""

	_VALID_URL = r'.*'
	IE_NAME = u'generic'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'WARNING: Falling back on generic information extractor.')
		self._downloader.to_screen(u'[generic] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[generic] %s: Extracting information' % video_id)

	def report_following_redirect(self, new_url):
		"""Report information extraction."""
		self._downloader.to_screen(u'[redirect] Following redirect to %s' % new_url)
		
	def _test_redirect(self, url):
		"""Check if it is a redirect, like url shorteners, in case restart chain."""
		class HeadRequest(urllib2.Request):
			def get_method(self):
				return "HEAD"

		class HEADRedirectHandler(urllib2.HTTPRedirectHandler):
			"""
			Subclass the HTTPRedirectHandler to make it use our 
			HeadRequest also on the redirected URL
			"""
			def redirect_request(self, req, fp, code, msg, headers, newurl): 
				if code in (301, 302, 303, 307):
					newurl = newurl.replace(' ', '%20') 
					newheaders = dict((k,v) for k,v in req.headers.items()
									  if k.lower() not in ("content-length", "content-type"))
					return HeadRequest(newurl, 
									   headers=newheaders,
									   origin_req_host=req.get_origin_req_host(), 
									   unverifiable=True) 
				else: 
					raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp) 

		class HTTPMethodFallback(urllib2.BaseHandler):
			"""
			Fallback to GET if HEAD is not allowed (405 HTTP error)
			"""
			def http_error_405(self, req, fp, code, msg, headers): 
				fp.read()
				fp.close()

				newheaders = dict((k,v) for k,v in req.headers.items()
								  if k.lower() not in ("content-length", "content-type"))
				return self.parent.open(urllib2.Request(req.get_full_url(), 
												 headers=newheaders, 
												 origin_req_host=req.get_origin_req_host(), 
												 unverifiable=True))

		# Build our opener
		opener = urllib2.OpenerDirector() 
		for handler in [urllib2.HTTPHandler, urllib2.HTTPDefaultErrorHandler,
						HTTPMethodFallback, HEADRedirectHandler,
						urllib2.HTTPErrorProcessor, urllib2.HTTPSHandler]:
			opener.add_handler(handler())

		response = opener.open(HeadRequest(url))
		new_url = response.geturl()
		
		if url == new_url: return False
		
		self.report_following_redirect(new_url)
		self._downloader.download([new_url])
		return True

	def _real_extract(self, url):
		if self._test_redirect(url): return

		video_id = url.split('/')[-1]
		request = urllib2.Request(url)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return
		except ValueError, err:
			# since this is the last-resort InfoExtractor, if
			# this error is thrown, it'll be thrown here
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		self.report_extraction(video_id)
		# Start with something easy: JW Player in SWFObject
		mobj = re.search(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage)
		if mobj is None:
			# Broaden the search a little bit
			mobj = re.search(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		# It's possible that one of the regexes
		# matched, but returned an empty group:
		if mobj.group(1) is None:
			self._downloader.trouble(u'ERROR: Invalid URL: %s' % url)
			return

		video_url = urllib.unquote(mobj.group(1))
		video_id = os.path.basename(video_url)

		# here's a fun little line of code for you:
		video_extension = os.path.splitext(video_id)[1][1:]
		video_id = os.path.splitext(video_id)[0]

		# it's tempting to parse this further, but you would
		# have to take into account all the variations like
		#   Video Title - Site Name
		#   Site Name | Video Title
		#   Video Title - Tagline | Site Name
		# and so on and so forth; it's just not practical
		mobj = re.search(r'<title>(.*)</title>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		video_title = mobj.group(1).decode('utf-8')

		# video uploader is domain name
		mobj = re.match(r'(?:https?://)?([^/]*)/.*', url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		video_uploader = mobj.group(1).decode('utf-8')

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	video_uploader,
			'upload_date':	u'NA',
			'title':	video_title,
			'ext':		video_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url':	None,
		}]


class YoutubeSearchIE(InfoExtractor):
	"""Information Extractor for YouTube search queries."""
	_VALID_URL = r'ytsearch(\d+|all)?:[\s\S]+'
	_API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc'
	_max_youtube_results = 1000
	IE_NAME = u'youtube:search'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_page(self, query, pagenum):
		"""Report attempt to download search page with given number."""
		query = query.decode(preferredencoding())
		self._downloader.to_screen(u'[youtube] query "%s": Downloading page %s' % (query, pagenum))

	def _real_extract(self, query):
		mobj = re.match(self._VALID_URL, query)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid search query "%s"' % query)
			return

		prefix, query = query.split(':')
		prefix = prefix[8:]
		query = query.encode('utf-8')
		if prefix == '':
			self._download_n_results(query, 1)
			return
		elif prefix == 'all':
			self._download_n_results(query, self._max_youtube_results)
			return
		else:
			try:
				n = long(prefix)
				if n <= 0:
					self._downloader.trouble(u'ERROR: invalid download number %s for query "%s"' % (n, query))
					return
				elif n > self._max_youtube_results:
					self._downloader.to_stderr(u'WARNING: ytsearch returns max %i results (you requested %i)' % (self._max_youtube_results, n))
					n = self._max_youtube_results
				self._download_n_results(query, n)
				return
			except ValueError: # parsing prefix as integer fails
				self._download_n_results(query, 1)
				return

	def _download_n_results(self, query, n):
		"""Downloads a specified number of results for a query"""

		video_ids = []
		pagenum = 0
		limit = n

		while (50 * pagenum) < limit:
			self.report_download_page(query, pagenum+1)
			result_url = self._API_URL % (urllib.quote_plus(query), (50*pagenum)+1)
			request = urllib2.Request(result_url)
			try:
				data = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download API page: %s' % str(err))
				return
			api_response = json.loads(data)['data']

			new_ids = list(video['id'] for video in api_response['items'])
			video_ids += new_ids

			limit = min(n, api_response['totalItems'])
			pagenum += 1

		if len(video_ids) > n:
			video_ids = video_ids[:n]
		for id in video_ids:
			self._downloader.download(['http://www.youtube.com/watch?v=%s' % id])
		return


class GoogleSearchIE(InfoExtractor):
	"""Information Extractor for Google Video search queries."""
	_VALID_URL = r'gvsearch(\d+|all)?:[\s\S]+'
	_TEMPLATE_URL = 'http://video.google.com/videosearch?q=%s+site:video.google.com&start=%s&hl=en'
	_VIDEO_INDICATOR = r'<a href="http://video\.google\.com/videoplay\?docid=([^"\&]+)'
	_MORE_PAGES_INDICATOR = r'class="pn" id="pnnext"'
	_max_google_results = 1000
	IE_NAME = u'video.google:search'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_page(self, query, pagenum):
		"""Report attempt to download playlist page with given number."""
		query = query.decode(preferredencoding())
		self._downloader.to_screen(u'[video.google] query "%s": Downloading page %s' % (query, pagenum))

	def _real_extract(self, query):
		mobj = re.match(self._VALID_URL, query)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid search query "%s"' % query)
			return

		prefix, query = query.split(':')
		prefix = prefix[8:]
		query = query.encode('utf-8')
		if prefix == '':
			self._download_n_results(query, 1)
			return
		elif prefix == 'all':
			self._download_n_results(query, self._max_google_results)
			return
		else:
			try:
				n = long(prefix)
				if n <= 0:
					self._downloader.trouble(u'ERROR: invalid download number %s for query "%s"' % (n, query))
					return
				elif n > self._max_google_results:
					self._downloader.to_stderr(u'WARNING: gvsearch returns max %i results (you requested %i)' % (self._max_google_results, n))
					n = self._max_google_results
				self._download_n_results(query, n)
				return
			except ValueError: # parsing prefix as integer fails
				self._download_n_results(query, 1)
				return

	def _download_n_results(self, query, n):
		"""Downloads a specified number of results for a query"""

		video_ids = []
		pagenum = 0

		while True:
			self.report_download_page(query, pagenum)
			result_url = self._TEMPLATE_URL % (urllib.quote_plus(query), pagenum*10)
			request = urllib2.Request(result_url)
			try:
				page = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download webpage: %s' % str(err))
				return

			# Extract video identifiers
			for mobj in re.finditer(self._VIDEO_INDICATOR, page):
				video_id = mobj.group(1)
				if video_id not in video_ids:
					video_ids.append(video_id)
					if len(video_ids) == n:
						# Specified n videos reached
						for id in video_ids:
							self._downloader.download(['http://video.google.com/videoplay?docid=%s' % id])
						return

			if re.search(self._MORE_PAGES_INDICATOR, page) is None:
				for id in video_ids:
					self._downloader.download(['http://video.google.com/videoplay?docid=%s' % id])
				return

			pagenum = pagenum + 1


class YahooSearchIE(InfoExtractor):
	"""Information Extractor for Yahoo! Video search queries."""
	_VALID_URL = r'yvsearch(\d+|all)?:[\s\S]+'
	_TEMPLATE_URL = 'http://video.yahoo.com/search/?p=%s&o=%s'
	_VIDEO_INDICATOR = r'href="http://video\.yahoo\.com/watch/([0-9]+/[0-9]+)"'
	_MORE_PAGES_INDICATOR = r'\s*Next'
	_max_yahoo_results = 1000
	IE_NAME = u'video.yahoo:search'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_page(self, query, pagenum):
		"""Report attempt to download playlist page with given number."""
		query = query.decode(preferredencoding())
		self._downloader.to_screen(u'[video.yahoo] query "%s": Downloading page %s' % (query, pagenum))

	def _real_extract(self, query):
		mobj = re.match(self._VALID_URL, query)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid search query "%s"' % query)
			return

		prefix, query = query.split(':')
		prefix = prefix[8:]
		query = query.encode('utf-8')
		if prefix == '':
			self._download_n_results(query, 1)
			return
		elif prefix == 'all':
			self._download_n_results(query, self._max_yahoo_results)
			return
		else:
			try:
				n = long(prefix)
				if n <= 0:
					self._downloader.trouble(u'ERROR: invalid download number %s for query "%s"' % (n, query))
					return
				elif n > self._max_yahoo_results:
					self._downloader.to_stderr(u'WARNING: yvsearch returns max %i results (you requested %i)' % (self._max_yahoo_results, n))
					n = self._max_yahoo_results
				self._download_n_results(query, n)
				return
			except ValueError: # parsing prefix as integer fails
				self._download_n_results(query, 1)
				return

	def _download_n_results(self, query, n):
		"""Downloads a specified number of results for a query"""

		video_ids = []
		already_seen = set()
		pagenum = 1

		while True:
			self.report_download_page(query, pagenum)
			result_url = self._TEMPLATE_URL % (urllib.quote_plus(query), pagenum)
			request = urllib2.Request(result_url)
			try:
				page = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download webpage: %s' % str(err))
				return

			# Extract video identifiers
			for mobj in re.finditer(self._VIDEO_INDICATOR, page):
				video_id = mobj.group(1)
				if video_id not in already_seen:
					video_ids.append(video_id)
					already_seen.add(video_id)
					if len(video_ids) == n:
						# Specified n videos reached
						for id in video_ids:
							self._downloader.download(['http://video.yahoo.com/watch/%s' % id])
						return

			if re.search(self._MORE_PAGES_INDICATOR, page) is None:
				for id in video_ids:
					self._downloader.download(['http://video.yahoo.com/watch/%s' % id])
				return

			pagenum = pagenum + 1


class YoutubePlaylistIE(InfoExtractor):
	"""Information Extractor for YouTube playlists."""

	_VALID_URL = r'(?:https?://)?(?:\w+\.)?youtube\.com/(?:(?:course|view_play_list|my_playlists|artist|playlist)\?.*?(p|a|list)=|user/.*?/user/|p/|user/.*?#[pg]/c/)(?:PL)?([0-9A-Za-z-_]+)(?:/.*?/([0-9A-Za-z_-]+))?.*'
	_TEMPLATE_URL = 'http://www.youtube.com/%s?%s=%s&page=%s&gl=US&hl=en'
	_VIDEO_INDICATOR_TEMPLATE = r'/watch\?v=(.+?)&amp;list=(PL)?%s&'
	_MORE_PAGES_INDICATOR = r'yt-uix-pager-next'
	IE_NAME = u'youtube:playlist'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_page(self, playlist_id, pagenum):
		"""Report attempt to download playlist page with given number."""
		self._downloader.to_screen(u'[youtube] PL %s: Downloading page #%s' % (playlist_id, pagenum))

	def _real_extract(self, url):
		# Extract playlist id
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid url: %s' % url)
			return

		# Single video case
		if mobj.group(3) is not None:
			self._downloader.download([mobj.group(3)])
			return

		# Download playlist pages
		# prefix is 'p' as default for playlists but there are other types that need extra care
		playlist_prefix = mobj.group(1)
		if playlist_prefix == 'a':
			playlist_access = 'artist'
		else:
			playlist_prefix = 'p'
			playlist_access = 'view_play_list'
		playlist_id = mobj.group(2)
		video_ids = []
		pagenum = 1

		while True:
			self.report_download_page(playlist_id, pagenum)
			url = self._TEMPLATE_URL % (playlist_access, playlist_prefix, playlist_id, pagenum)
			request = urllib2.Request(url)
			try:
				page = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download webpage: %s' % str(err))
				return

			# Extract video identifiers
			ids_in_page = []
			for mobj in re.finditer(self._VIDEO_INDICATOR_TEMPLATE % playlist_id, page):
				if mobj.group(1) not in ids_in_page:
					ids_in_page.append(mobj.group(1))
			video_ids.extend(ids_in_page)

			if re.search(self._MORE_PAGES_INDICATOR, page) is None:
				break
			pagenum = pagenum + 1

		playliststart = self._downloader.params.get('playliststart', 1) - 1
		playlistend = self._downloader.params.get('playlistend', -1)
		if playlistend == -1:
			video_ids = video_ids[playliststart:]
		else:
			video_ids = video_ids[playliststart:playlistend]

		for id in video_ids:
			self._downloader.download(['http://www.youtube.com/watch?v=%s' % id])
		return


class YoutubeUserIE(InfoExtractor):
	"""Information Extractor for YouTube users."""

	_VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/user/)|ytuser:)([A-Za-z0-9_-]+)'
	_TEMPLATE_URL = 'http://gdata.youtube.com/feeds/api/users/%s'
	_GDATA_PAGE_SIZE = 50
	_GDATA_URL = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d'
	_VIDEO_INDICATOR = r'/watch\?v=(.+?)[\<&]'
	IE_NAME = u'youtube:user'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_page(self, username, start_index):
		"""Report attempt to download user page."""
		self._downloader.to_screen(u'[youtube] user %s: Downloading video ids from %d to %d' %
				(username, start_index, start_index + self._GDATA_PAGE_SIZE))

	def _real_extract(self, url):
		# Extract username
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid url: %s' % url)
			return

		username = mobj.group(1)

		# Download video ids using YouTube Data API. Result size per
		# query is limited (currently to 50 videos) so we need to query
		# page by page until there are no video ids - it means we got
		# all of them.

		video_ids = []
		pagenum = 0

		while True:
			start_index = pagenum * self._GDATA_PAGE_SIZE + 1
			self.report_download_page(username, start_index)

			request = urllib2.Request(self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index))

			try:
				page = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download webpage: %s' % str(err))
				return

			# Extract video identifiers
			ids_in_page = []

			for mobj in re.finditer(self._VIDEO_INDICATOR, page):
				if mobj.group(1) not in ids_in_page:
					ids_in_page.append(mobj.group(1))

			video_ids.extend(ids_in_page)

			# A little optimization - if current page is not
			# "full", ie. does not contain PAGE_SIZE video ids then
			# we can assume that this page is the last one - there
			# are no more ids on further pages - no need to query
			# again.

			if len(ids_in_page) < self._GDATA_PAGE_SIZE:
				break

			pagenum += 1

		all_ids_count = len(video_ids)
		playliststart = self._downloader.params.get('playliststart', 1) - 1
		playlistend = self._downloader.params.get('playlistend', -1)

		if playlistend == -1:
			video_ids = video_ids[playliststart:]
		else:
			video_ids = video_ids[playliststart:playlistend]

		self._downloader.to_screen(u"[youtube] user %s: Collected %d video ids (downloading %d of them)" %
				(username, all_ids_count, len(video_ids)))

		for video_id in video_ids:
			self._downloader.download(['http://www.youtube.com/watch?v=%s' % video_id])


class DepositFilesIE(InfoExtractor):
	"""Information extractor for depositfiles.com"""

	_VALID_URL = r'(?:http://)?(?:\w+\.)?depositfiles\.com/(?:../(?#locale))?files/(.+)'
	IE_NAME = u'DepositFiles'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_webpage(self, file_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[DepositFiles] %s: Downloading webpage' % file_id)

	def report_extraction(self, file_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[DepositFiles] %s: Extracting information' % file_id)

	def _real_extract(self, url):
		file_id = url.split('/')[-1]
		# Rebuild url in english locale
		url = 'http://depositfiles.com/en/files/' + file_id

		# Retrieve file webpage with 'Free download' button pressed
		free_download_indication = { 'gateway_result' : '1' }
		request = urllib2.Request(url, urllib.urlencode(free_download_indication))
		try:
			self.report_download_webpage(file_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve file webpage: %s' % str(err))
			return

		# Search for the real file URL
		mobj = re.search(r'<form action="(http://fileshare.+?)"', webpage)
		if (mobj is None) or (mobj.group(1) is None):
			# Try to figure out reason of the error.
			mobj = re.search(r'<strong>(Attention.*?)</strong>', webpage, re.DOTALL)
			if (mobj is not None) and (mobj.group(1) is not None):
				restriction_message = re.sub('\s+', ' ', mobj.group(1)).strip()
				self._downloader.trouble(u'ERROR: %s' % restriction_message)
			else:
				self._downloader.trouble(u'ERROR: unable to extract download URL from: %s' % url)
			return

		file_url = mobj.group(1)
		file_extension = os.path.splitext(file_url)[1][1:]

		# Search for file title
		mobj = re.search(r'<b title="(.*?)">', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return
		file_title = mobj.group(1).decode('utf-8')

		return [{
			'id':		file_id.decode('utf-8'),
			'url':		file_url.decode('utf-8'),
			'uploader':	u'NA',
			'upload_date':	u'NA',
			'title':	file_title,
			'ext':		file_extension.decode('utf-8'),
			'format':	u'NA',
			'player_url':	None,
		}]


class FacebookIE(InfoExtractor):
	"""Information Extractor for Facebook"""

	_VALID_URL = r'^(?:https?://)?(?:\w+\.)?facebook\.com/(?:video/video|photo)\.php\?(?:.*?)v=(?P<ID>\d+)(?:.*)'
	_LOGIN_URL = 'https://login.facebook.com/login.php?m&next=http%3A%2F%2Fm.facebook.com%2Fhome.php&'
	_NETRC_MACHINE = 'facebook'
	_available_formats = ['video', 'highqual', 'lowqual']
	_video_extensions = {
		'video': 'mp4',
		'highqual': 'mp4',
		'lowqual': 'mp4',
	}
	IE_NAME = u'facebook'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def _reporter(self, message):
		"""Add header and report message."""
		self._downloader.to_screen(u'[facebook] %s' % message)

	def report_login(self):
		"""Report attempt to log in."""
		self._reporter(u'Logging in')

	def report_video_webpage_download(self, video_id):
		"""Report attempt to download video webpage."""
		self._reporter(u'%s: Downloading video webpage' % video_id)

	def report_information_extraction(self, video_id):
		"""Report attempt to extract video information."""
		self._reporter(u'%s: Extracting video information' % video_id)

	def _parse_page(self, video_webpage):
		"""Extract video information from page"""
		# General data
		data = {'title': r'\("video_title", "(.*?)"\)',
			'description': r'<div class="datawrap">(.*?)</div>',
			'owner': r'\("video_owner_name", "(.*?)"\)',
			'thumbnail':  r'\("thumb_url", "(?P<THUMB>.*?)"\)',
			}
		video_info = {}
		for piece in data.keys():
			mobj = re.search(data[piece], video_webpage)
			if mobj is not None:
				video_info[piece] = urllib.unquote_plus(mobj.group(1).decode("unicode_escape"))

		# Video urls
		video_urls = {}
		for fmt in self._available_formats:
			mobj = re.search(r'\("%s_src\", "(.+?)"\)' % fmt, video_webpage)
			if mobj is not None:
				# URL is in a Javascript segment inside an escaped Unicode format within
				# the generally utf-8 page
				video_urls[fmt] = urllib.unquote_plus(mobj.group(1).decode("unicode_escape"))
		video_info['video_urls'] = video_urls

		return video_info

	def _real_initialize(self):
		if self._downloader is None:
			return

		useremail = None
		password = None
		downloader_params = self._downloader.params

		# Attempt to use provided username and password or .netrc data
		if downloader_params.get('username', None) is not None:
			useremail = downloader_params['username']
			password = downloader_params['password']
		elif downloader_params.get('usenetrc', False):
			try:
				info = netrc.netrc().authenticators(self._NETRC_MACHINE)
				if info is not None:
					useremail = info[0]
					password = info[2]
				else:
					raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
			except (IOError, netrc.NetrcParseError), err:
				self._downloader.to_stderr(u'WARNING: parsing .netrc: %s' % str(err))
				return

		if useremail is None:
			return

		# Log in
		login_form = {
			'email': useremail,
			'pass': password,
			'login': 'Log+In'
			}
		request = urllib2.Request(self._LOGIN_URL, urllib.urlencode(login_form))
		try:
			self.report_login()
			login_results = urllib2.urlopen(request).read()
			if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
				self._downloader.to_stderr(u'WARNING: unable to log in: bad username/password, or exceded login rate limit (~3/min). Check credentials or wait.')
				return
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.to_stderr(u'WARNING: unable to log in: %s' % str(err))
			return

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		video_id = mobj.group('ID')

		# Get video webpage
		self.report_video_webpage_download(video_id)
		request = urllib2.Request('https://www.facebook.com/video/video.php?v=%s' % video_id)
		try:
			page = urllib2.urlopen(request)
			video_webpage = page.read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		# Start extracting information
		self.report_information_extraction(video_id)

		# Extract information
		video_info = self._parse_page(video_webpage)

		# uploader
		if 'owner' not in video_info:
			self._downloader.trouble(u'ERROR: unable to extract uploader nickname')
			return
		video_uploader = video_info['owner']

		# title
		if 'title' not in video_info:
			self._downloader.trouble(u'ERROR: unable to extract video title')
			return
		video_title = video_info['title']
		video_title = video_title.decode('utf-8')

		# thumbnail image
		if 'thumbnail' not in video_info:
			self._downloader.trouble(u'WARNING: unable to extract video thumbnail')
			video_thumbnail = ''
		else:
			video_thumbnail = video_info['thumbnail']

		# upload date
		upload_date = u'NA'
		if 'upload_date' in video_info:
			upload_time = video_info['upload_date']
			timetuple = email.utils.parsedate_tz(upload_time)
			if timetuple is not None:
				try:
					upload_date = time.strftime('%Y%m%d', timetuple[0:9])
				except:
					pass

		# description
		video_description = video_info.get('description', 'No description available.')

		url_map = video_info['video_urls']
		if len(url_map.keys()) > 0:
			# Decide which formats to download
			req_format = self._downloader.params.get('format', None)
			format_limit = self._downloader.params.get('format_limit', None)

			if format_limit is not None and format_limit in self._available_formats:
				format_list = self._available_formats[self._available_formats.index(format_limit):]
			else:
				format_list = self._available_formats
			existing_formats = [x for x in format_list if x in url_map]
			if len(existing_formats) == 0:
				self._downloader.trouble(u'ERROR: no known formats available for video')
				return
			if req_format is None:
				video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
			elif req_format == 'worst':
				video_url_list = [(existing_formats[len(existing_formats)-1], url_map[existing_formats[len(existing_formats)-1]])] # worst quality
			elif req_format == '-1':
				video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
			else:
				# Specific format
				if req_format not in url_map:
					self._downloader.trouble(u'ERROR: requested format not available')
					return
				video_url_list = [(req_format, url_map[req_format])] # Specific format

		results = []
		for format_param, video_real_url in video_url_list:
			# Extension
			video_extension = self._video_extensions.get(format_param, 'mp4')

			results.append({
				'id':		video_id.decode('utf-8'),
				'url':		video_real_url.decode('utf-8'),
				'uploader':	video_uploader.decode('utf-8'),
				'upload_date':	upload_date,
				'title':	video_title,
				'ext':		video_extension.decode('utf-8'),
				'format':	(format_param is None and u'NA' or format_param.decode('utf-8')),
				'thumbnail':	video_thumbnail.decode('utf-8'),
				'description':	video_description.decode('utf-8'),
				'player_url':	None,
			})
		return results

class BlipTVIE(InfoExtractor):
	"""Information extractor for blip.tv"""

	_VALID_URL = r'^(?:https?://)?(?:\w+\.)?blip\.tv(/.+)$'
	_URL_EXT = r'^.*\.([a-z0-9]+)$'
	IE_NAME = u'blip.tv'

	def report_extraction(self, file_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, file_id))

	def report_direct_download(self, title):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Direct download detected' % (self.IE_NAME, title))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		if '?' in url:
			cchar = '&'
		else:
			cchar = '?'
		json_url = url + cchar + 'skin=json&version=2&no_wrap=1'
		request = urllib2.Request(json_url)
		self.report_extraction(mobj.group(1))
		info = None
		try:
			urlh = urllib2.urlopen(request)
			if urlh.headers.get('Content-Type', '').startswith('video/'): # Direct download
				basename = url.split('/')[-1]
				title,ext = os.path.splitext(basename)
				title = title.decode('UTF-8')
				ext = ext.replace('.', '')
				self.report_direct_download(title)
				info = {
					'id': title,
					'url': url,
					'title': title,
					'ext': ext,
					'urlhandle': urlh
				}
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video info webpage: %s' % str(err))
			return
		if info is None: # Regular URL
			try:
				json_code = urlh.read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to read video info webpage: %s' % str(err))
				return

			try:
				json_data = json.loads(json_code)
				if 'Post' in json_data:
					data = json_data['Post']
				else:
					data = json_data

				upload_date = datetime.datetime.strptime(data['datestamp'], '%m-%d-%y %H:%M%p').strftime('%Y%m%d')
				video_url = data['media']['url']
				umobj = re.match(self._URL_EXT, video_url)
				if umobj is None:
					raise ValueError('Can not determine filename extension')
				ext = umobj.group(1)

				info = {
					'id': data['item_id'],
					'url': video_url,
					'uploader': data['display_name'],
					'upload_date': upload_date,
					'title': data['title'],
					'ext': ext,
					'format': data['media']['mimeType'],
					'thumbnail': data['thumbnailUrl'],
					'description': data['description'],
					'player_url': data['embedUrl']
				}
			except (ValueError,KeyError), err:
				self._downloader.trouble(u'ERROR: unable to parse video information: %s' % repr(err))
				return

		return [info]


class MyVideoIE(InfoExtractor):
	"""Information Extractor for myvideo.de."""

	_VALID_URL = r'(?:http://)?(?:www\.)?myvideo\.de/watch/([0-9]+)/([^?/]+).*'
	IE_NAME = u'myvideo'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)
	
	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self._downloader.to_screen(u'[myvideo] %s: Downloading webpage' % video_id)

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[myvideo] %s: Extracting information' % video_id)

	def _real_extract(self,url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._download.trouble(u'ERROR: invalid URL: %s' % url)
			return

		video_id = mobj.group(1)

		# Get video webpage
		request = urllib2.Request('http://www.myvideo.de/watch/%s' % video_id)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve video webpage: %s' % str(err))
			return

		self.report_extraction(video_id)
		mobj = re.search(r'<link rel=\'image_src\' href=\'(http://is[0-9].myvideo\.de/de/movie[0-9]+/[a-f0-9]+)/thumbs/[^.]+\.jpg\' />',
				 webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract media URL')
			return
		video_url = mobj.group(1) + ('/%s.flv' % video_id)

		mobj = re.search('<title>([^<]+)</title>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract title')
			return

		video_title = mobj.group(1)

		return [{
			'id':		video_id,
			'url':		video_url,
			'uploader':	u'NA',
			'upload_date':  u'NA',
			'title':	video_title,
			'ext':		u'flv',
			'format':	u'NA',
			'player_url':	None,
		}]

class ComedyCentralIE(InfoExtractor):
	"""Information extractor for The Daily Show and Colbert Report """

	_VALID_URL = r'^(:(?P<shortname>tds|thedailyshow|cr|colbert|colbertnation|colbertreport))|(https?://)?(www\.)?(?P<showname>thedailyshow|colbertnation)\.com/full-episodes/(?P<episode>.*)$'
	IE_NAME = u'comedycentral'

	def report_extraction(self, episode_id):
		self._downloader.to_screen(u'[comedycentral] %s: Extracting information' % episode_id)

	def report_config_download(self, episode_id):
		self._downloader.to_screen(u'[comedycentral] %s: Downloading configuration' % episode_id)

	def report_index_download(self, episode_id):
		self._downloader.to_screen(u'[comedycentral] %s: Downloading show index' % episode_id)

	def report_player_url(self, episode_id):
		self._downloader.to_screen(u'[comedycentral] %s: Determining player URL' % episode_id)

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		if mobj.group('shortname'):
			if mobj.group('shortname') in ('tds', 'thedailyshow'):
				url = u'http://www.thedailyshow.com/full-episodes/'
			else:
				url = u'http://www.colbertnation.com/full-episodes/'
			mobj = re.match(self._VALID_URL, url)
			assert mobj is not None

		dlNewest = not mobj.group('episode')
		if dlNewest:
			epTitle = mobj.group('showname')
		else:
			epTitle = mobj.group('episode')

		req = urllib2.Request(url)
		self.report_extraction(epTitle)
		try:
			htmlHandle = urllib2.urlopen(req)
			html = htmlHandle.read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download webpage: %s' % unicode(err))
			return
		if dlNewest:
			url = htmlHandle.geturl()
			mobj = re.match(self._VALID_URL, url)
			if mobj is None:
				self._downloader.trouble(u'ERROR: Invalid redirected URL: ' + url)
				return
			if mobj.group('episode') == '':
				self._downloader.trouble(u'ERROR: Redirected URL is still not specific: ' + url)
				return
			epTitle = mobj.group('episode')

		mMovieParams = re.findall('(?:<param name="movie" value="|var url = ")(http://media.mtvnservices.com/([^"]*episode.*?:.*?))"', html)
		if len(mMovieParams) == 0:
			self._downloader.trouble(u'ERROR: unable to find Flash URL in webpage ' + url)
			return

		playerUrl_raw = mMovieParams[0][0]
		self.report_player_url(epTitle)
		try:
			urlHandle = urllib2.urlopen(playerUrl_raw)
			playerUrl = urlHandle.geturl()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to find out player URL: ' + unicode(err))
			return

		uri = mMovieParams[0][1]
		indexUrl = 'http://shadow.comedycentral.com/feeds/video_player/mrss/?' + urllib.urlencode({'uri': uri})
		self.report_index_download(epTitle)
		try:
			indexXml = urllib2.urlopen(indexUrl).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download episode index: ' + unicode(err))
			return

		results = []

		idoc = xml.etree.ElementTree.fromstring(indexXml)
		itemEls = idoc.findall('.//item')
		for itemEl in itemEls:
			mediaId = itemEl.findall('./guid')[0].text
			shortMediaId = mediaId.split(':')[-1]
			showId = mediaId.split(':')[-2].replace('.com', '')
			officialTitle = itemEl.findall('./title')[0].text
			officialDate = itemEl.findall('./pubDate')[0].text

			configUrl = ('http://www.comedycentral.com/global/feeds/entertainment/media/mediaGenEntertainment.jhtml?' +
						urllib.urlencode({'uri': mediaId}))
			configReq = urllib2.Request(configUrl)
			self.report_config_download(epTitle)
			try:
				configXml = urllib2.urlopen(configReq).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download webpage: %s' % unicode(err))
				return

			cdoc = xml.etree.ElementTree.fromstring(configXml)
			turls = []
			for rendition in cdoc.findall('.//rendition'):
				finfo = (rendition.attrib['bitrate'], rendition.findall('./src')[0].text)
				turls.append(finfo)

			if len(turls) == 0:
				self._downloader.trouble(u'\nERROR: unable to download ' + mediaId + ': No videos found')
				continue

			# For now, just pick the highest bitrate
			format,video_url = turls[-1]

			effTitle = showId + u'-' + epTitle
			info = {
				'id': shortMediaId,
				'url': video_url,
				'uploader': showId,
				'upload_date': officialDate,
				'title': effTitle,
				'ext': 'mp4',
				'format': format,
				'thumbnail': None,
				'description': officialTitle,
				'player_url': playerUrl
			}

			results.append(info)
			
		return results


class EscapistIE(InfoExtractor):
	"""Information extractor for The Escapist """

	_VALID_URL = r'^(https?://)?(www\.)?escapistmagazine\.com/videos/view/(?P<showname>[^/]+)/(?P<episode>[^/?]+)[/?]?.*$'
	IE_NAME = u'escapist'

	def report_extraction(self, showName):
		self._downloader.to_screen(u'[escapist] %s: Extracting information' % showName)

	def report_config_download(self, showName):
		self._downloader.to_screen(u'[escapist] %s: Downloading configuration' % showName)

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		showName = mobj.group('showname')
		videoId = mobj.group('episode')

		self.report_extraction(showName)
		try:
			webPageBytes = urllib2.urlopen(url).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download webpage: ' + unicode(err))
			return

		webPage = webPageBytes.decode('utf-8')
		descMatch = re.search('<meta name="description" content="([^"]*)"', webPage)
		description = unescapeHTML(descMatch.group(1))
		imgMatch = re.search('<meta property="og:image" content="([^"]*)"', webPage)
		imgUrl = unescapeHTML(imgMatch.group(1))
		playerUrlMatch = re.search('<meta property="og:video" content="([^"]*)"', webPage)
		playerUrl = unescapeHTML(playerUrlMatch.group(1))
		configUrlMatch = re.search('config=(.*)$', playerUrl)
		configUrl = urllib2.unquote(configUrlMatch.group(1))

		self.report_config_download(showName)
		try:
			configJSON = urllib2.urlopen(configUrl).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download configuration: ' + unicode(err))
			return

		# Technically, it's JavaScript, not JSON
		configJSON = configJSON.replace("'", '"')

		try:
			config = json.loads(configJSON)
		except (ValueError,), err:
			self._downloader.trouble(u'ERROR: Invalid JSON in configuration file: ' + unicode(err))
			return

		playlist = config['playlist']
		videoUrl = playlist[1]['url']

		info = {
			'id': videoId,
			'url': videoUrl,
			'uploader': showName,
			'upload_date': None,
			'title': showName,
			'ext': 'flv',
			'format': 'flv',
			'thumbnail': imgUrl,
			'description': description,
			'player_url': playerUrl,
		}

		return [info]


class CollegeHumorIE(InfoExtractor):
	"""Information extractor for collegehumor.com"""

	_VALID_URL = r'^(?:https?://)?(?:www\.)?collegehumor\.com/video/(?P<videoid>[0-9]+)/(?P<shorttitle>.*)$'
	IE_NAME = u'collegehumor'

	def report_webpage(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, video_id))

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		video_id = mobj.group('videoid')

		self.report_webpage(video_id)
		request = urllib2.Request(url)
		try:
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		m = re.search(r'id="video:(?P<internalvideoid>[0-9]+)"', webpage)
		if m is None:
			self._downloader.trouble(u'ERROR: Cannot extract internal video ID')
			return
		internal_video_id = m.group('internalvideoid')

		info = {
			'id': video_id,
			'internal_id': internal_video_id,
		}

		self.report_extraction(video_id)
		xmlUrl = 'http://www.collegehumor.com/moogaloop/video:' + internal_video_id
		try:
			metaXml = urllib2.urlopen(xmlUrl).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video info XML: %s' % str(err))
			return

		mdoc = xml.etree.ElementTree.fromstring(metaXml)
		try:
			videoNode = mdoc.findall('./video')[0]
			info['description'] = videoNode.findall('./description')[0].text
			info['title'] = videoNode.findall('./caption')[0].text
			info['url'] = videoNode.findall('./file')[0].text
			info['thumbnail'] = videoNode.findall('./thumbnail')[0].text
			info['ext'] = info['url'].rpartition('.')[2]
			info['format'] = info['ext']
		except IndexError:
			self._downloader.trouble(u'\nERROR: Invalid metadata XML file')
			return

		return [info]


class XVideosIE(InfoExtractor):
	"""Information extractor for xvideos.com"""

	_VALID_URL = r'^(?:https?://)?(?:www\.)?xvideos\.com/video([0-9]+)(?:.*)'
	IE_NAME = u'xvideos'

	def report_webpage(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, video_id))

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		video_id = mobj.group(1).decode('utf-8')

		self.report_webpage(video_id)

		request = urllib2.Request(r'http://www.xvideos.com/video' + video_id)
		try:
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		self.report_extraction(video_id)


		# Extract video URL
		mobj = re.search(r'flv_url=(.+?)&', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video url')
			return
		video_url = urllib2.unquote(mobj.group(1).decode('utf-8'))


		# Extract title
		mobj = re.search(r'<title>(.*?)\s+-\s+XVID', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video title')
			return
		video_title = mobj.group(1).decode('utf-8')


		# Extract video thumbnail
		mobj = re.search(r'http://(?:img.*?\.)xvideos.com/videos/thumbs/[a-fA-F0-9]/[a-fA-F0-9]/[a-fA-F0-9]/([a-fA-F0-9.]+jpg)', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video thumbnail')
			return
		video_thumbnail = mobj.group(1).decode('utf-8')

		info = {
			'id': video_id,
			'url': video_url,
			'uploader': None,
			'upload_date': None,
			'title': video_title,
			'ext': 'flv',
			'format': 'flv',
			'thumbnail': video_thumbnail,
			'description': None,
			'player_url': None,
		}

		return [info]


class SoundcloudIE(InfoExtractor):
	"""Information extractor for soundcloud.com
	   To access the media, the uid of the song and a stream token
	   must be extracted from the page source and the script must make
	   a request to media.soundcloud.com/crossdomain.xml. Then
	   the media can be grabbed by requesting from an url composed
	   of the stream token and uid
	 """

	_VALID_URL = r'^(?:https?://)?(?:www\.)?soundcloud\.com/([\w\d-]+)/([\w\d-]+)'
	IE_NAME = u'soundcloud'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_webpage(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, video_id))

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		# extract uploader (which is in the url)
		uploader = mobj.group(1).decode('utf-8')
		# extract simple title (uploader + slug of song title)
		slug_title =  mobj.group(2).decode('utf-8')
		simple_title = uploader + u'-' + slug_title

		self.report_webpage('%s/%s' % (uploader, slug_title))

		request = urllib2.Request('http://soundcloud.com/%s/%s' % (uploader, slug_title))
		try:
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		self.report_extraction('%s/%s' % (uploader, slug_title))

		# extract uid and stream token that soundcloud hands out for access
		mobj = re.search('"uid":"([\w\d]+?)".*?stream_token=([\w\d]+)', webpage)
		if mobj:
			video_id = mobj.group(1)
			stream_token = mobj.group(2)

		# extract unsimplified title
		mobj = re.search('"title":"(.*?)",', webpage)
		if mobj:
			title = mobj.group(1).decode('utf-8')
		else:
			title = simple_title

		# construct media url (with uid/token)
		mediaURL = "http://media.soundcloud.com/stream/%s?stream_token=%s"
		mediaURL = mediaURL % (video_id, stream_token)

		# description
		description = u'No description available'
		mobj = re.search('track-description-value"><p>(.*?)</p>', webpage)
		if mobj:
			description = mobj.group(1)
		
		# upload date
		upload_date = None
		mobj = re.search("pretty-date'>on ([\w]+ [\d]+, [\d]+ \d+:\d+)</abbr></h2>", webpage)
		if mobj:
			try:
				upload_date = datetime.datetime.strptime(mobj.group(1), '%B %d, %Y %H:%M').strftime('%Y%m%d')
			except Exception, e:
				self._downloader.to_stderr(str(e))

		# for soundcloud, a request to a cross domain is required for cookies
		request = urllib2.Request('http://media.soundcloud.com/crossdomain.xml', std_headers)

		return [{
			'id':		video_id.decode('utf-8'),
			'url':		mediaURL,
			'uploader':	uploader.decode('utf-8'),
			'upload_date':  upload_date,
			'title':	title,
			'ext':		u'mp3',
			'format':	u'NA',
			'player_url':	None,
			'description': description.decode('utf-8')
		}]


class InfoQIE(InfoExtractor):
	"""Information extractor for infoq.com"""

	_VALID_URL = r'^(?:https?://)?(?:www\.)?infoq\.com/[^/]+/[^/]+$'
	IE_NAME = u'infoq'

	def report_webpage(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, video_id))

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		self.report_webpage(url)

		request = urllib2.Request(url)
		try:
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		self.report_extraction(url)


		# Extract video URL
		mobj = re.search(r"jsclassref='([^']*)'", webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video url')
			return
		video_url = 'rtmpe://video.infoq.com/cfx/st/' + urllib2.unquote(mobj.group(1).decode('base64'))


		# Extract title
		mobj = re.search(r'contentTitle = "(.*?)";', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract video title')
			return
		video_title = mobj.group(1).decode('utf-8')

		# Extract description
		video_description = u'No description available.'
		mobj = re.search(r'<meta name="description" content="(.*)"(?:\s*/)?>', webpage)
		if mobj is not None:
			video_description = mobj.group(1).decode('utf-8')

		video_filename = video_url.split('/')[-1]
		video_id, extension = video_filename.split('.')

		info = {
			'id': video_id,
			'url': video_url,
			'uploader': None,
			'upload_date': None,
			'title': video_title,
			'ext': extension,
			'format': extension, # Extension is always(?) mp4, but seems to be flv
			'thumbnail': None,
			'description': video_description,
			'player_url': None,
		}

		return [info]

class MixcloudIE(InfoExtractor):
	"""Information extractor for www.mixcloud.com"""
	_VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([\w\d-]+)/([\w\d-]+)'
	IE_NAME = u'mixcloud'

	def __init__(self, downloader=None):
		InfoExtractor.__init__(self, downloader)

	def report_download_json(self, file_id):
		"""Report JSON download."""
		self._downloader.to_screen(u'[%s] Downloading json' % self.IE_NAME)

	def report_extraction(self, file_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, file_id))

	def get_urls(self, jsonData, fmt, bitrate='best'):
		"""Get urls from 'audio_formats' section in json"""
		file_url = None
		try:
			bitrate_list = jsonData[fmt]
			if bitrate is None or bitrate == 'best' or bitrate not in bitrate_list:
				bitrate = max(bitrate_list) # select highest

			url_list = jsonData[fmt][bitrate]
		except TypeError: # we have no bitrate info.
			url_list = jsonData[fmt]
		return url_list

	def check_urls(self, url_list):
		"""Returns 1st active url from list"""
		for url in url_list:
			try:
				urllib2.urlopen(url)
				return url
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				url = None

		return None

	def _print_formats(self, formats):
		print 'Available formats:'
		for fmt in formats.keys():
			for b in formats[fmt]:
				try:
					ext = formats[fmt][b][0]
					print '%s\t%s\t[%s]' % (fmt, b, ext.split('.')[-1])
				except TypeError: # we have no bitrate info
					ext = formats[fmt][0]
					print '%s\t%s\t[%s]' % (fmt, '??', ext.split('.')[-1])
					break

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		# extract uploader & filename from url
		uploader = mobj.group(1).decode('utf-8')
		file_id = uploader + "-" + mobj.group(2).decode('utf-8')

		# construct API request
		file_url = 'http://www.mixcloud.com/api/1/cloudcast/' + '/'.join(url.split('/')[-3:-1]) + '.json'
		# retrieve .json file with links to files
		request = urllib2.Request(file_url)
		try:
			self.report_download_json(file_url)
			jsonData = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: Unable to retrieve file: %s' % str(err))
			return

		# parse JSON
		json_data = json.loads(jsonData)
		player_url = json_data['player_swf_url']
		formats = dict(json_data['audio_formats'])

		req_format = self._downloader.params.get('format', None)
		bitrate = None

		if self._downloader.params.get('listformats', None):
			self._print_formats(formats)
			return

		if req_format is None or req_format == 'best':
			for format_param in formats.keys():
				url_list = self.get_urls(formats, format_param)
				# check urls
				file_url = self.check_urls(url_list)
				if file_url is not None:
					break # got it!
		else:
			if req_format not in formats.keys():
				self._downloader.trouble(u'ERROR: format is not available')
				return

			url_list = self.get_urls(formats, req_format)
			file_url = self.check_urls(url_list)
			format_param = req_format

		return [{
			'id': file_id.decode('utf-8'),
			'url': file_url.decode('utf-8'),
			'uploader':	uploader.decode('utf-8'),
			'upload_date': u'NA',
			'title': json_data['name'],
			'ext': file_url.split('.')[-1].decode('utf-8'),
			'format': (format_param is None and u'NA' or format_param.decode('utf-8')),
			'thumbnail': json_data['thumbnail_url'],
			'description': json_data['description'],
			'player_url': player_url.decode('utf-8'),
		}]

class StanfordOpenClassroomIE(InfoExtractor):
	"""Information extractor for Stanford's Open ClassRoom"""

	_VALID_URL = r'^(?:https?://)?openclassroom.stanford.edu(?P<path>/?|(/MainFolder/(?:HomePage|CoursePage|VideoPage)\.php([?]course=(?P<course>[^&]+)(&video=(?P<video>[^&]+))?(&.*)?)?))$'
	IE_NAME = u'stanfordoc'

	def report_download_webpage(self, objid):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, objid))

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return

		if mobj.group('course') and mobj.group('video'): # A specific video
			course = mobj.group('course')
			video = mobj.group('video')
			info = {
				'id': course + '_' + video,
			}

			self.report_extraction(info['id'])
			baseUrl = 'http://openclassroom.stanford.edu/MainFolder/courses/' + course + '/videos/'
			xmlUrl = baseUrl + video + '.xml'
			try:
				metaXml = urllib2.urlopen(xmlUrl).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download video info XML: %s' % unicode(err))
				return
			mdoc = xml.etree.ElementTree.fromstring(metaXml)
			try:
				info['title'] = mdoc.findall('./title')[0].text
				info['url'] = baseUrl + mdoc.findall('./videoFile')[0].text
			except IndexError:
				self._downloader.trouble(u'\nERROR: Invalid metadata XML file')
				return
			info['ext'] = info['url'].rpartition('.')[2]
			info['format'] = info['ext']
			return [info]
		elif mobj.group('course'): # A course page
			course = mobj.group('course')
			info = {
				'id': course,
				'type': 'playlist',
			}

			self.report_download_webpage(info['id'])
			try:
				coursepage = urllib2.urlopen(url).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download course info page: ' + unicode(err))
				return

			m = re.search('<h1>([^<]+)</h1>', coursepage)
			if m:
				info['title'] = unescapeHTML(m.group(1))
			else:
				info['title'] = info['id']

			m = re.search('<description>([^<]+)</description>', coursepage)
			if m:
				info['description'] = unescapeHTML(m.group(1))

			links = orderedSet(re.findall('<a href="(VideoPage.php\?[^"]+)">', coursepage))
			info['list'] = [
				{
					'type': 'reference',
					'url': 'http://openclassroom.stanford.edu/MainFolder/' + unescapeHTML(vpage),
				}
					for vpage in links]
			results = []
			for entry in info['list']:
				assert entry['type'] == 'reference'
				results += self.extract(entry['url'])
			return results
			
		else: # Root page
			info = {
				'id': 'Stanford OpenClassroom',
				'type': 'playlist',
			}

			self.report_download_webpage(info['id'])
			rootURL = 'http://openclassroom.stanford.edu/MainFolder/HomePage.php'
			try:
				rootpage = urllib2.urlopen(rootURL).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self._downloader.trouble(u'ERROR: unable to download course info page: ' + unicode(err))
				return

			info['title'] = info['id']

			links = orderedSet(re.findall('<a href="(CoursePage.php\?[^"]+)">', rootpage))
			info['list'] = [
				{
					'type': 'reference',
					'url': 'http://openclassroom.stanford.edu/MainFolder/' + unescapeHTML(cpage),
				}
					for cpage in links]

			results = []
			for entry in info['list']:
				assert entry['type'] == 'reference'
				results += self.extract(entry['url'])
			return results

class MTVIE(InfoExtractor):
	"""Information extractor for MTV.com"""

	_VALID_URL = r'^(?P<proto>https?://)?(?:www\.)?mtv\.com/videos/[^/]+/(?P<videoid>[0-9]+)/[^/]+$'
	IE_NAME = u'mtv'

	def report_webpage(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Downloading webpage' % (self.IE_NAME, video_id))

	def report_extraction(self, video_id):
		"""Report information extraction."""
		self._downloader.to_screen(u'[%s] %s: Extracting information' % (self.IE_NAME, video_id))

	def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self._downloader.trouble(u'ERROR: invalid URL: %s' % url)
			return
		if not mobj.group('proto'):
			url = 'http://' + url
		video_id = mobj.group('videoid')
		self.report_webpage(video_id)

		request = urllib2.Request(url)
		try:
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video webpage: %s' % str(err))
			return

		mobj = re.search(r'<meta name="mtv_vt" content="([^"]+)"/>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract song name')
			return
		song_name = unescapeHTML(mobj.group(1).decode('iso-8859-1'))
		mobj = re.search(r'<meta name="mtv_an" content="([^"]+)"/>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract performer')
			return
		performer = unescapeHTML(mobj.group(1).decode('iso-8859-1'))
		video_title = performer + ' - ' + song_name 

		mobj = re.search(r'<meta name="mtvn_uri" content="([^"]+)"/>', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to mtvn_uri')
			return
		mtvn_uri = mobj.group(1)

		mobj = re.search(r'MTVN.Player.defaultPlaylistId = ([0-9]+);', webpage)
		if mobj is None:
			self._downloader.trouble(u'ERROR: unable to extract content id')
			return
		content_id = mobj.group(1)

		videogen_url = 'http://www.mtv.com/player/includes/mediaGen.jhtml?uri=' + mtvn_uri + '&id=' + content_id + '&vid=' + video_id + '&ref=www.mtvn.com&viewUri=' + mtvn_uri
		self.report_extraction(video_id)
		request = urllib2.Request(videogen_url)
		try:
			metadataXml = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self._downloader.trouble(u'ERROR: unable to download video metadata: %s' % str(err))
			return

		mdoc = xml.etree.ElementTree.fromstring(metadataXml)
		renditions = mdoc.findall('.//rendition')

		# For now, always pick the highest quality.
		rendition = renditions[-1]

		try:
			_,_,ext = rendition.attrib['type'].partition('/')
			format = ext + '-' + rendition.attrib['width'] + 'x' + rendition.attrib['height'] + '_' + rendition.attrib['bitrate']
			video_url = rendition.find('./src').text
		except KeyError:
			self._downloader.trouble('Invalid rendition field.')
			return

		info = {
			'id': video_id,
			'url': video_url,
			'uploader': performer,
			'title': video_title,
			'ext': ext,
			'format': format,
		}

		return [info]
