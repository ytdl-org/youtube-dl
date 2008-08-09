#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Ricardo Garcia Gonzalez
# License: Public domain code
import htmlentitydefs
import httplib
import math
import netrc
import os
import os.path
import re
import socket
import string
import sys
import time
import urllib
import urllib2

std_headers = {	
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}

simple_title_chars = string.ascii_letters.decode('ascii') + string.digits.decode('ascii')

class DownloadError(Exception):
	"""Download Error exception.
	
	This exception may be thrown by FileDownloader objects if they are not
	configured to continue on errors. They will contain the appropriate
	error message.
	"""
	pass

class SameFileError(Exception):
	"""Same File exception.

	This exception will be thrown by FileDownloader objects if they detect
	multiple files would have to be downloaded to the same file on disk.
	"""
	pass

class PostProcessingError(Exception):
	"""Post Processing exception.

	This exception may be raised by PostProcessor's .run() method to
	indicate an error in the postprocessing task.
	"""
	pass

class FileDownloader(object):
	"""File Downloader class.

	File downloader objects are the ones responsible of downloading the
	actual video file and writing it to disk if the user has requested
	it, among some other tasks. In most cases there should be one per
	program. As, given a video URL, the downloader doesn't know how to
	extract all the needed information, task that InfoExtractors do, it
	has to pass the URL to one of them.

	For this, file downloader objects have a method that allows
	InfoExtractors to be registered in a given order. When it is passed
	a URL, the file downloader handles it to the first InfoExtractor it
	finds that reports being able to handle it. The InfoExtractor returns
	all the information to the FileDownloader and the latter downloads the
	file or does whatever it's instructed to do.

	File downloaders accept a lot of parameters. In order not to saturate
	the object constructor with arguments, it receives a dictionary of
	options instead. These options are available through the get_params()
	method for the InfoExtractors to use. The FileDownloader also registers
	itself as the downloader in charge for the InfoExtractors that are
	added to it, so this is a "mutual registration".

	Available options:

	username:	Username for authentication purposes.
	password:	Password for authentication purposes.
	usenetrc:	Use netrc for authentication instead.
	quiet:		Do not print messages to stdout.
	forceurl:	Force printing final URL.
	forcetitle:	Force printing title.
	simulate:	Do not download the video files.
	format:		Video format code.
	outtmpl:	Template for output names.
	ignoreerrors:	Do not stop on download errors.
	ratelimit:	Download speed limit, in bytes/sec.
	"""

	_params = None
	_ies = []
	_pps = []

	def __init__(self, params):
		"""Create a FileDownloader object with the given options."""
		self._ies = []
		self._pps = []
		self.set_params(params)
	
	@staticmethod
	def pmkdir(filename):
		"""Create directory components in filename. Similar to Unix "mkdir -p"."""
		components = filename.split(os.sep)
		aggregate = [os.sep.join(components[0:x]) for x in xrange(1, len(components))]
		aggregate = ['%s%s' % (x, os.sep) for x in aggregate] # Finish names with separator
		for dir in aggregate:
			if not os.path.exists(dir):
				os.mkdir(dir)
	
	@staticmethod
	def format_bytes(bytes):
		if bytes is None:
			return 'N/A'
		if bytes == 0:
			exponent = 0
		else:
			exponent = long(math.log(float(bytes), 1024.0))
		suffix = 'bkMGTPEZY'[exponent]
		converted = float(bytes) / float(1024**exponent)
		return '%.2f%s' % (converted, suffix)

	@staticmethod
	def calc_percent(byte_counter, data_len):
		if data_len is None:
			return '---.-%'
		return '%6s' % ('%3.1f%%' % (float(byte_counter) / float(data_len) * 100.0))

	@staticmethod
	def calc_eta(start, now, total, current):
		if total is None:
			return '--:--'
		dif = now - start
		if current == 0 or dif < 0.001: # One millisecond
			return '--:--'
		rate = float(current) / dif
		eta = long((float(total) - float(current)) / rate)
		(eta_mins, eta_secs) = divmod(eta, 60)
		if eta_mins > 99:
			return '--:--'
		return '%02d:%02d' % (eta_mins, eta_secs)

 	@staticmethod
	def calc_speed(start, now, bytes):
		dif = now - start
		if bytes == 0 or dif < 0.001: # One millisecond
			return '%10s' % '---b/s'
		return '%10s' % ('%s/s' % FileDownloader.format_bytes(float(bytes) / dif))

	@staticmethod
	def best_block_size(elapsed_time, bytes):
		new_min = max(bytes / 2.0, 1.0)
		new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
		if elapsed_time < 0.001:
			return int(new_max)
		rate = bytes / elapsed_time
		if rate > new_max:
			return int(new_max)
		if rate < new_min:
			return int(new_min)
		return int(rate)

	@staticmethod
	def parse_bytes(bytestr):
		"""Parse a string indicating a byte quantity into a long integer."""
		matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]?)$', bytestr)
		if matchobj is None:
			return None
		number = float(matchobj.group(1))
		multiplier = 1024.0 ** 'bkmgtpezy'.index(matchobj.group(2).lower())
		return long(round(number * multiplier))

	def set_params(self, params):
		"""Sets parameters."""
		if type(params) != dict:
			raise ValueError('params: dictionary expected')
		self._params = params
	
	def get_params(self):
		"""Get parameters."""
		return self._params

	def add_info_extractor(self, ie):
		"""Add an InfoExtractor object to the end of the list."""
		self._ies.append(ie)
		ie.set_downloader(self)
	
	def add_post_processor(self, pp):
		"""Add a PostProcessor object to the end of the chain."""
		self._pps.append(pp)
		pp.set_downloader(self)
	
	def to_stdout(self, message, skip_eol=False):
		"""Print message to stdout if not in quiet mode."""
		if not self._params.get('quiet', False):
			print u'%s%s' % (message, [u'\n', u''][skip_eol]),
			sys.stdout.flush()
	
	def to_stderr(self, message):
		"""Print message to stderr."""
		print >>sys.stderr, message
	
	def fixed_template(self):
		"""Checks if the output template is fixed."""
		return (re.search(ur'(?u)%\(.+?\)s', self._params['outtmpl']) is None)

	def trouble(self, message=None):
		"""Determine action to take when a download problem appears.

		Depending on if the downloader has been configured to ignore
		download errors or not, this method may throw an exception or
		not when errors are found, after printing the message. If it
		doesn't raise, it returns an error code suitable to be returned
		later as a program exit code to indicate error.
		"""
		if message is not None:
			self.to_stderr(message)
		if not self._params.get('ignoreerrors', False):
			raise DownloadError(message)
		return 1

	def slow_down(self, start_time, byte_counter):
		"""Sleep if the download speed is over the rate limit."""
		rate_limit = self._params.get('ratelimit', None)
		if rate_limit is None or byte_counter == 0:
			return
		now = time.time()
		elapsed = now - start_time
		if elapsed <= 0.0:
			return
		speed = float(byte_counter) / elapsed
		if speed > rate_limit:
			time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)

	def report_destination(self, filename):
		"""Report destination filename."""
		self.to_stdout(u'[download] Destination: %s' % filename)
	
	def report_progress(self, percent_str, data_len_str, speed_str, eta_str):
		"""Report download progress."""
		self.to_stdout(u'\r[download] %s of %s at %s ETA %s' %
				(percent_str, data_len_str, speed_str, eta_str), skip_eol=True)
	
	def report_finish(self):
		"""Report download finished."""
		self.to_stdout(u'')

	def download(self, url_list):
		"""Download a given list of URLs."""
		retcode = 0
		if len(url_list) > 1 and self.fixed_template():
			raise SameFileError(self._params['outtmpl'])

		for url in url_list:
			suitable_found = False
			for ie in self._ies:
				if not ie.suitable(url):
					continue
				# Suitable InfoExtractor found
				suitable_found = True
				all_results = ie.extract(url)
				results = [x for x in all_results if x is not None]
				if len(results) != len(all_results):
					retcode = self.trouble()

				if len(results) > 1 and self.fixed_template():
					raise SameFileError(self._params['outtmpl'])

				for result in results:
					# Forced printings
					if self._params.get('forcetitle', False):
						print result['title']
					if self._params.get('forceurl', False):
						print result['url']
						
					# Do nothing else if in simulate mode
					if self._params.get('simulate', False):
						continue

					try:
						filename = self._params['outtmpl'] % result
						self.report_destination(filename)
					except (ValueError, KeyError), err:
						retcode = self.trouble('ERROR: invalid output template or system charset: %s' % str(err))
						continue
					try:
						self.pmkdir(filename)
					except (OSError, IOError), err:
						retcode = self.trouble('ERROR: unable to create directories: %s' % str(err))
						continue
					try:
						outstream = open(filename, 'wb')
					except (OSError, IOError), err:
						retcode = self.trouble('ERROR: unable to open for writing: %s' % str(err))
						continue
					try:
						self._do_download(outstream, result['url'])
						outstream.close()
					except (OSError, IOError), err:
						retcode = self.trouble('ERROR: unable to write video data: %s' % str(err))
						continue
					except (urllib2.URLError, httplib.HTTPException, socket.error), err:
						retcode = self.trouble('ERROR: unable to download video data: %s' % str(err))
						continue
					try:
						self.post_process(filename, result)
					except (PostProcessingError), err:
						retcode = self.trouble('ERROR: postprocessing: %s' % str(err))
						continue

				break
			if not suitable_found:
				retcode = self.trouble('ERROR: no suitable InfoExtractor: %s' % url)

		return retcode

	def post_process(self, filename, ie_info):
		"""Run the postprocessing chain on the given file."""
		info = dict(ie_info)
		info['filepath'] = filename
		for pp in self._pps:
			info = pp.run(info)
			if info is None:
				break
	
	def _do_download(self, stream, url):
		request = urllib2.Request(url, None, std_headers)
		data = urllib2.urlopen(request)
		data_len = data.info().get('Content-length', None)
		data_len_str = self.format_bytes(data_len)
		byte_counter = 0
		block_size = 1024
		start = time.time()
		while True:
			# Progress message
			percent_str = self.calc_percent(byte_counter, data_len)
			eta_str = self.calc_eta(start, time.time(), data_len, byte_counter)
			speed_str = self.calc_speed(start, time.time(), byte_counter)
			self.report_progress(percent_str, data_len_str, speed_str, eta_str)

			# Download and write
			before = time.time()
			data_block = data.read(block_size)
			after = time.time()
			data_block_len = len(data_block)
			if data_block_len == 0:
				break
			byte_counter += data_block_len
			stream.write(data_block)
			block_size = self.best_block_size(after - before, data_block_len)

			# Apply rate limit
			self.slow_down(start, byte_counter)

		self.report_finish()
		if data_len is not None and str(byte_counter) != data_len:
			raise ValueError('Content too short: %s/%s bytes' % (byte_counter, data_len))

class InfoExtractor(object):
	"""Information Extractor class.

	Information extractors are the classes that, given a URL, extract
	information from the video (or videos) the URL refers to. This
	information includes the real video URL, the video title and simplified
	title, author and others. It is returned in a list of dictionaries when
	calling its extract() method. It is a list because a URL can refer to
	more than one video (think of playlists). The dictionaries must include
	the following fields:

	id:		Video identifier.
	url:		Final video URL.
	uploader:	Nickname of the video uploader.
	title:		Literal title.
	stitle:		Simplified title.
	ext:		Video filename extension.

	Subclasses of this one should re-define the _real_initialize() and
	_real_extract() methods, as well as the suitable() static method.
	Probably, they should also be instantiated and added to the main
	downloader.
	"""

	_ready = False
	_downloader = None

	def __init__(self, downloader=None):
		"""Constructor. Receives an optional downloader."""
		self._ready = False
		self.set_downloader(downloader)

	@staticmethod
	def suitable(url):
		"""Receives a URL and returns True if suitable for this IE."""
		return False

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
	
	def to_stdout(self, message):
		"""Print message to stdout if downloader is not in quiet mode."""
		if self._downloader is None or not self._downloader.get_params().get('quiet', False):
			print message
	
	def to_stderr(self, message):
		"""Print message to stderr."""
		print >>sys.stderr, message

	def _real_initialize(self):
		"""Real initialization process. Redefine in subclasses."""
		pass

	def _real_extract(self, url):
		"""Real extraction process. Redefine in subclasses."""
		pass

class YoutubeIE(InfoExtractor):
	"""Information extractor for youtube.com."""

	_VALID_URL = r'^((?:http://)?(?:\w+\.)?youtube\.com/(?:(?:v/)|(?:(?:watch(?:\.php)?)?\?(?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'
	_LOGIN_URL = 'http://www.youtube.com/login?next=/'
	_AGE_URL = 'http://www.youtube.com/verify_age?next_url=/'
	_NETRC_MACHINE = 'youtube'

	@staticmethod
	def suitable(url):
		return (re.match(YoutubeIE._VALID_URL, url) is not None)

	def report_login(self):
		"""Report attempt to log in."""
		self.to_stdout(u'[youtube] Logging in')
	
	def report_age_confirmation(self):
		"""Report attempt to confirm age."""
		self.to_stdout(u'[youtube] Confirming age')
	
	def report_webpage_download(self, video_id):
		"""Report attempt to download webpage."""
		self.to_stdout(u'[youtube] %s: Downloading video webpage' % video_id)
	
	def report_information_extraction(self, video_id):
		"""Report attempt to extract video information."""
		self.to_stdout(u'[youtube] %s: Extracting video information' % video_id)
	
	def report_video_url(self, video_id, video_real_url):
		"""Report extracted video URL."""
		self.to_stdout(u'[youtube] %s: URL: %s' % (video_id, video_real_url))

	def _real_initialize(self):
		if self._downloader is None:
			return

		username = None
		password = None
		downloader_params = self._downloader.get_params()

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
				self.to_stderr(u'WARNING: parsing .netrc: %s' % str(err))
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
		request = urllib2.Request(self._LOGIN_URL, urllib.urlencode(login_form), std_headers)
		try:
			self.report_login()
			login_results = urllib2.urlopen(request).read()
			if re.search(r'(?i)<form[^>]* name="loginForm"', login_results) is not None:
				self.to_stderr(u'WARNING: unable to log in: bad username or password')
				return
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self.to_stderr(u'WARNING: unable to log in: %s' % str(err))
			return
	
		# Confirm age
		age_form = {
				'next_url':		'/',
				'action_confirm':	'Confirm',
				}
		request = urllib2.Request(self._AGE_URL, urllib.urlencode(age_form), std_headers)
		try:
			self.report_age_confirmation()
			age_results = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self.to_stderr(u'ERROR: unable to confirm age: %s' % str(err))
			return

	def _real_extract(self, url):
		# Extract video id from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self.to_stderr(u'ERROR: invalid URL: %s' % url)
			return [None]
		video_id = mobj.group(2)

		# Downloader parameters
		format_param = None
		if self._downloader is not None:
			params = self._downloader.get_params()
			format_param = params.get('format', None)

		# Extension
		video_extension = {'18': 'mp4', '17': '3gp'}.get(format_param, 'flv')

		# Normalize URL, including format
		normalized_url = 'http://www.youtube.com/watch?v=%s' % video_id
		if format_param is not None:
			normalized_url = '%s&fmt=%s' % (normalized_url, format_param)
		request = urllib2.Request(normalized_url, None, std_headers)
		try:
			self.report_webpage_download(video_id)
			video_webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self.to_stderr(u'ERROR: unable to download video webpage: %s' % str(err))
			return [None]
		self.report_information_extraction(video_id)
		
		# "t" param
		mobj = re.search(r', "t": "([^"]+)"', video_webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract "t" parameter')
			return [None]
		video_real_url = 'http://www.youtube.com/get_video?video_id=%s&t=%s' % (video_id, mobj.group(1))
		if format_param is not None:
			video_real_url = '%s&fmt=%s' % (video_real_url, format_param)
		self.report_video_url(video_id, video_real_url)

		# uploader
		mobj = re.search(r"var watchUsername = '([^']+)';", video_webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract uploader nickname')
			return [None]
		video_uploader = mobj.group(1)

		# title
		mobj = re.search(r'(?im)<title>YouTube - ([^<]*)</title>', video_webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract video title')
			return [None]
		video_title = mobj.group(1).decode('utf-8')
		video_title = re.sub(ur'(?u)&(.+?);', lambda x: unichr(htmlentitydefs.name2codepoint[x.group(1)]), video_title)
		video_title = video_title.replace(os.sep, u'%')

		# simplified title
		simple_title = re.sub(ur'(?u)([^%s]+)' % simple_title_chars, ur'_', video_title)
		simple_title = simple_title.strip(ur'_')

		# Return information
		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_real_url.decode('utf-8'),
			'uploader':	video_uploader.decode('utf-8'),
			'title':	video_title,
			'stitle':	simple_title,
			'ext':		video_extension.decode('utf-8'),
			}]

class MetacafeIE(InfoExtractor):
	"""Information Extractor for metacafe.com."""

	_VALID_URL = r'(?:http://)?(?:www\.)?metacafe\.com/watch/([^/]+)/([^/]+)/.*'
	_DISCLAIMER = 'http://www.metacafe.com/disclaimer'
	_youtube_ie = None

	def __init__(self, youtube_ie, downloader=None):
		InfoExtractor.__init__(self, downloader)
		self._youtube_ie = youtube_ie

	@staticmethod
	def suitable(url):
		return (re.match(MetacafeIE._VALID_URL, url) is not None)

	def report_disclaimer(self):
		"""Report disclaimer retrieval."""
		self.to_stdout(u'[metacafe] Retrieving disclaimer')

	def report_age_confirmation(self):
		"""Report attempt to confirm age."""
		self.to_stdout(u'[metacafe] Confirming age')
	
	def report_download_webpage(self, video_id):
		"""Report webpage download."""
		self.to_stdout(u'[metacafe] %s: Downloading webpage' % video_id)
	
	def report_extraction(self, video_id):
		"""Report information extraction."""
		self.to_stdout(u'[metacafe] %s: Extracting information' % video_id)

	def _real_initialize(self):
		# Retrieve disclaimer
		request = urllib2.Request(self._DISCLAIMER, None, std_headers)
		try:
			self.report_disclaimer()
			disclaimer = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self.to_stderr(u'ERROR: unable to retrieve disclaimer: %s' % str(err))
			return

		# Confirm age
		disclaimer_form = {
			'allowAdultContent': '1',
			'submit': "Continue - I'm over 18",
			}
		request = urllib2.Request('http://www.metacafe.com/watch/', urllib.urlencode(disclaimer_form), std_headers)
		try:
			self.report_age_confirmation()
			disclaimer = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self.to_stderr(u'ERROR: unable to confirm age: %s' % str(err))
			return
	
	def _real_extract(self, url):
		# Extract id and simplified title from URL
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self.to_stderr(u'ERROR: invalid URL: %s' % url)
			return [None]

		video_id = mobj.group(1)

		# Check if video comes from YouTube
		mobj2 = re.match(r'^yt-(.*)$', video_id)
		if mobj2 is not None:
			return self._youtube_ie.extract('http://www.youtube.com/watch?v=%s' % mobj2.group(1))

		simple_title = mobj.group(2).decode('utf-8')
		video_extension = 'flv'

		# Retrieve video webpage to extract further information
		request = urllib2.Request('http://www.metacafe.com/watch/%s/' % video_id)
		try:
			self.report_download_webpage(video_id)
			webpage = urllib2.urlopen(request).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			self.to_stderr(u'ERROR: unable retrieve video webpage: %s' % str(err))
			return [None]

		# Extract URL, uploader and title from webpage
		self.report_extraction(video_id)
		mobj = re.search(r'(?m)"mediaURL":"(http.*?\.flv)"', webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract media URL')
			return [None]
		mediaURL = mobj.group(1).replace('\\', '')

		mobj = re.search(r'(?m)"gdaKey":"(.*?)"', webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract gdaKey')
			return [None]
		gdaKey = mobj.group(1)

		video_url = '%s?__gda__=%s' % (mediaURL, gdaKey)

		mobj = re.search(r'(?im)<meta name="title" content="Metacafe - ([^"]+)"', webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract title')
			return [None]
		video_title = mobj.group(1).decode('utf-8')

		mobj = re.search(r'(?m)<li id="ChnlUsr">.*?Submitter:<br />(.*?)</li>', webpage)
		if mobj is None:
			self.to_stderr(u'ERROR: unable to extract uploader nickname')
			return [None]
		video_uploader = re.sub(r'<.*?>', '', mobj.group(1))

		# Return information
		return [{
			'id':		video_id.decode('utf-8'),
			'url':		video_url.decode('utf-8'),
			'uploader':	video_uploader.decode('utf-8'),
			'title':	video_title,
			'stitle':	simple_title,
			'ext':		video_extension.decode('utf-8'),
			}]

class YoutubePlaylistIE(InfoExtractor):
	"""Information Extractor for YouTube playlists."""

	_VALID_URL = r'(?:http://)?(?:\w+\.)?youtube.com/view_play_list\?p=(.+)'
	_TEMPLATE_URL = 'http://www.youtube.com/view_play_list?p=%s&page=%s'
	_VIDEO_INDICATOR = r'/watch\?v=(.+?)&'
	_MORE_PAGES_INDICATOR = r'/view_play_list?p=%s&amp;page=%s'
	_youtube_ie = None

	def __init__(self, youtube_ie, downloader=None):
		InfoExtractor.__init__(self, downloader)
		self._youtube_ie = youtube_ie
	
	@staticmethod
	def suitable(url):
		return (re.match(YoutubePlaylistIE._VALID_URL, url) is not None)

	def report_download_page(self, playlist_id, pagenum):
		"""Report attempt to download playlist page with given number."""
		self.to_stdout(u'[youtube] PL %s: Downloading page #%s' % (playlist_id, pagenum))

	def _real_initialize(self):
		self._youtube_ie.initialize()
	
	def _real_extract(self, url):
		# Extract playlist id
		mobj = re.match(self._VALID_URL, url)
		if mobj is None:
			self.to_stderr(u'ERROR: invalid url: %s' % url)
			return [None]

		# Download playlist pages
		playlist_id = mobj.group(1)
		video_ids = []
		pagenum = 1

		while True:
			self.report_download_page(playlist_id, pagenum)
			request = urllib2.Request(self._TEMPLATE_URL % (playlist_id, pagenum), None, std_headers)
			try:
				page = urllib2.urlopen(request).read()
			except (urllib2.URLError, httplib.HTTPException, socket.error), err:
				self.to_stderr(u'ERROR: unable to download webpage: %s' % str(err))
				return [None]

			# Extract video identifiers
			ids_in_page = set()
			for mobj in re.finditer(self._VIDEO_INDICATOR, page):
				ids_in_page.add(mobj.group(1))
			video_ids.extend(list(ids_in_page))

			if (self._MORE_PAGES_INDICATOR % (playlist_id, pagenum + 1)) not in page:
				break
			pagenum = pagenum + 1

		information = []
		for id in video_ids:
			information.extend(self._youtube_ie.extract('http://www.youtube.com/watch?v=%s' % id))
		return information

class PostProcessor(object):
	"""Post Processor class.

	PostProcessor objects can be added to downloaders with their
	add_post_processor() method. When the downloader has finished a
	successful download, it will take its internal chain of PostProcessors
	and start calling the run() method on each one of them, first with
	an initial argument and then with the returned value of the previous
	PostProcessor.

	The chain will be stopped if one of them ever returns None or the end
	of the chain is reached.

	PostProcessor objects follow a "mutual registration" process similar
	to InfoExtractor objects.
	"""

	_downloader = None

	def __init__(self, downloader=None):
		self._downloader = downloader

	def to_stdout(self, message):
		"""Print message to stdout if downloader is not in quiet mode."""
		if self._downloader is None or not self._downloader.get_params().get('quiet', False):
			print message
	
	def to_stderr(self, message):
		"""Print message to stderr."""
		print >>sys.stderr, message

	def set_downloader(self, downloader):
		"""Sets the downloader for this PP."""
		self._downloader = downloader
	
	def run(self, information):
		"""Run the PostProcessor.

		The "information" argument is a dictionary like the ones
		returned by InfoExtractors. The only difference is that this
		one has an extra field called "filepath" that points to the
		downloaded file.

		When this method returns None, the postprocessing chain is
		stopped. However, this method may return an information
		dictionary that will be passed to the next postprocessing
		object in the chain. It can be the one it received after
		changing some fields.

		In addition, this method may raise a PostProcessingError
		exception that will be taken into account by the downloader
		it was called from.
		"""
		return information # by default, do nothing
	
### MAIN PROGRAM ###
if __name__ == '__main__':
	try:
		# Modules needed only when running the main program
		import getpass
		import optparse

		# General configuration
		urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))
		urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor()))
		socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

		# Parse command line
		parser = optparse.OptionParser(
				usage='Usage: %prog [options] url...',
				version='2008.08.09',
				conflict_handler='resolve',
				)
		parser.add_option('-h', '--help',
				action='help', help='print this help text and exit')
		parser.add_option('-v', '--version',
				action='version', help='print program version and exit')
		parser.add_option('-u', '--username',
				dest='username', metavar='UN', help='account username')
		parser.add_option('-p', '--password',
				dest='password', metavar='PW', help='account password')
		parser.add_option('-o', '--output',
				dest='outtmpl', metavar='TPL', help='output filename template')
		parser.add_option('-q', '--quiet',
				action='store_true', dest='quiet', help='activates quiet mode', default=False)
		parser.add_option('-s', '--simulate',
				action='store_true', dest='simulate', help='do not download video', default=False)
		parser.add_option('-t', '--title',
				action='store_true', dest='usetitle', help='use title in file name', default=False)
		parser.add_option('-l', '--literal',
				action='store_true', dest='useliteral', help='use literal title in file name', default=False)
		parser.add_option('-n', '--netrc',
				action='store_true', dest='usenetrc', help='use .netrc authentication data', default=False)
		parser.add_option('-g', '--get-url',
				action='store_true', dest='geturl', help='simulate, quiet but print URL', default=False)
		parser.add_option('-e', '--get-title',
				action='store_true', dest='gettitle', help='simulate, quiet but print title', default=False)
		parser.add_option('-f', '--format',
				dest='format', metavar='FMT', help='video format code')
		parser.add_option('-b', '--best-quality',
				action='store_const', dest='format', help='alias for -f 18', const='18')
		parser.add_option('-m', '--mobile-version',
				action='store_const', dest='format', help='alias for -f 17', const='17')
		parser.add_option('-i', '--ignore-errors',
				action='store_true', dest='ignoreerrors', help='continue on download errors', default=False)
		parser.add_option('-r', '--rate-limit',
				dest='ratelimit', metavar='L', help='download rate limit (e.g. 50k or 44.6m)')
		(opts, args) = parser.parse_args()

		# Conflicting, missing and erroneous options
		if len(args) < 1:
			sys.exit(u'ERROR: you must provide at least one URL')
		if opts.usenetrc and (opts.username is not None or opts.password is not None):
			sys.exit(u'ERROR: using .netrc conflicts with giving username/password')
		if opts.password is not None and opts.username is None:
			sys.exit(u'ERROR: account username missing')
		if opts.outtmpl is not None and (opts.useliteral or opts.usetitle):
			sys.exit(u'ERROR: using output template conflicts with using title or literal title')
		if opts.usetitle and opts.useliteral:
			sys.exit(u'ERROR: using title conflicts with using literal title')
		if opts.username is not None and opts.password is None:
			opts.password = getpass.getpass(u'Type account password and press return:')
		if opts.ratelimit is not None:
			numeric_limit = FileDownloader.parse_bytes(opts.ratelimit)
			if numeric_limit is None:
				sys.exit(u'ERROR: invalid rate limit specified')
			opts.ratelimit = numeric_limit

		# Information extractors
		youtube_ie = YoutubeIE()
		metacafe_ie = MetacafeIE(youtube_ie)
		youtube_pl_ie = YoutubePlaylistIE(youtube_ie)

		# File downloader
		fd = FileDownloader({
			'usenetrc': opts.usenetrc,
			'username': opts.username,
			'password': opts.password,
			'quiet': (opts.quiet or opts.geturl or opts.gettitle),
			'forceurl': opts.geturl,
			'forcetitle': opts.gettitle,
			'simulate': (opts.simulate or opts.geturl or opts.gettitle),
			'format': opts.format,
			'outtmpl': ((opts.outtmpl is not None and opts.outtmpl.decode())
				or (opts.usetitle and u'%(stitle)s-%(id)s.%(ext)s')
				or (opts.useliteral and u'%(title)s-%(id)s.%(ext)s')
				or u'%(id)s.%(ext)s'),
			'ignoreerrors': opts.ignoreerrors,
			'ratelimit': opts.ratelimit,
			})
		fd.add_info_extractor(youtube_pl_ie)
		fd.add_info_extractor(metacafe_ie)
		fd.add_info_extractor(youtube_ie)
		retcode = fd.download(args)
		sys.exit(retcode)

	except DownloadError:
		sys.exit(1)
	except SameFileError:
		sys.exit(u'ERROR: fixed output name but more than one file to download')
	except KeyboardInterrupt:
		sys.exit(u'\nERROR: Interrupted by user')
