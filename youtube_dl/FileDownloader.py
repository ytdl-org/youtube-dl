#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib
import math
import os
import re
import socket
import subprocess
import sys
import time
import urllib2

if os.name == 'nt':
	import ctypes
	
from utils import *


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
	finds that reports being able to handle it. The InfoExtractor extracts
	all the information about the video or videos the URL refers to, and
	asks the FileDownloader to process the video information, possibly
	downloading the video.

	File downloaders accept a lot of parameters. In order not to saturate
	the object constructor with arguments, it receives a dictionary of
	options instead. These options are available through the params
	attribute for the InfoExtractors to use. The FileDownloader also
	registers itself as the downloader in charge for the InfoExtractors
	that are added to it, so this is a "mutual registration".

	Available options:

	username:         Username for authentication purposes.
	password:         Password for authentication purposes.
	usenetrc:         Use netrc for authentication instead.
	quiet:            Do not print messages to stdout.
	forceurl:         Force printing final URL.
	forcetitle:       Force printing title.
	forcethumbnail:   Force printing thumbnail URL.
	forcedescription: Force printing description.
	forcefilename:    Force printing final filename.
	simulate:         Do not download the video files.
	format:           Video format code.
	format_limit:     Highest quality format to try.
	outtmpl:          Template for output names.
	ignoreerrors:     Do not stop on download errors.
	ratelimit:        Download speed limit, in bytes/sec.
	nooverwrites:     Prevent overwriting files.
	retries:          Number of times to retry for HTTP error 5xx
	continuedl:       Try to continue downloads if possible.
	noprogress:       Do not print the progress bar.
	playliststart:    Playlist item to start at.
	playlistend:      Playlist item to end at.
	matchtitle:       Download only matching titles.
	rejecttitle:      Reject downloads for matching titles.
	logtostderr:      Log messages to stderr instead of stdout.
	consoletitle:     Display progress in console window's titlebar.
	nopart:           Do not use temporary .part files.
	updatetime:       Use the Last-modified header to set output file timestamps.
	writedescription: Write the video description to a .description file
	writeinfojson:    Write the video description to a .info.json file
	writesubtitles:   Write the video subtitles to a .srt file
	subtitleslang:    Language of the subtitles to download
	"""

	params = None
	_ies = []
	_pps = []
	_download_retcode = None
	_num_downloads = None
	_screen_file = None

	def __init__(self, params):
		"""Create a FileDownloader object with the given options."""
		self._ies = []
		self._pps = []
		self._download_retcode = 0
		self._num_downloads = 0
		self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]
		self.params = params

	@staticmethod
	def format_bytes(bytes):
		if bytes is None:
			return 'N/A'
		if type(bytes) is str:
			bytes = float(bytes)
		if bytes == 0.0:
			exponent = 0
		else:
			exponent = long(math.log(bytes, 1024.0))
		suffix = 'bkMGTPEZY'[exponent]
		converted = float(bytes) / float(1024 ** exponent)
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
			return long(new_max)
		rate = bytes / elapsed_time
		if rate > new_max:
			return long(new_max)
		if rate < new_min:
			return long(new_min)
		return long(rate)

	@staticmethod
	def parse_bytes(bytestr):
		"""Parse a string indicating a byte quantity into a long integer."""
		matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]?)$', bytestr)
		if matchobj is None:
			return None
		number = float(matchobj.group(1))
		multiplier = 1024.0 ** 'bkmgtpezy'.index(matchobj.group(2).lower())
		return long(round(number * multiplier))

	def add_info_extractor(self, ie):
		"""Add an InfoExtractor object to the end of the list."""
		self._ies.append(ie)
		ie.set_downloader(self)

	def add_post_processor(self, pp):
		"""Add a PostProcessor object to the end of the chain."""
		self._pps.append(pp)
		pp.set_downloader(self)

	def to_screen(self, message, skip_eol=False):
		"""Print message to stdout if not in quiet mode."""
		assert type(message) == type(u'')
		if not self.params.get('quiet', False):
			terminator = [u'\n', u''][skip_eol]
			output = message + terminator

			if 'b' not in self._screen_file.mode or sys.version_info[0] < 3: # Python 2 lies about the mode of sys.stdout/sys.stderr
				output = output.encode(preferredencoding(), 'ignore')
			self._screen_file.write(output)
			self._screen_file.flush()

	def to_stderr(self, message):
		"""Print message to stderr."""
		print >>sys.stderr, message.encode(preferredencoding())

	def to_cons_title(self, message):
		"""Set console/terminal window title to message."""
		if not self.params.get('consoletitle', False):
			return
		if os.name == 'nt' and ctypes.windll.kernel32.GetConsoleWindow():
			# c_wchar_p() might not be necessary if `message` is
			# already of type unicode()
			ctypes.windll.kernel32.SetConsoleTitleW(ctypes.c_wchar_p(message))
		elif 'TERM' in os.environ:
			sys.stderr.write('\033]0;%s\007' % message.encode(preferredencoding()))

	def fixed_template(self):
		"""Checks if the output template is fixed."""
		return (re.search(ur'(?u)%\(.+?\)s', self.params['outtmpl']) is None)

	def trouble(self, message=None):
		"""Determine action to take when a download problem appears.

		Depending on if the downloader has been configured to ignore
		download errors or not, this method may throw an exception or
		not when errors are found, after printing the message.
		"""
		if message is not None:
			self.to_stderr(message)
		if not self.params.get('ignoreerrors', False):
			raise DownloadError(message)
		self._download_retcode = 1

	def slow_down(self, start_time, byte_counter):
		"""Sleep if the download speed is over the rate limit."""
		rate_limit = self.params.get('ratelimit', None)
		if rate_limit is None or byte_counter == 0:
			return
		now = time.time()
		elapsed = now - start_time
		if elapsed <= 0.0:
			return
		speed = float(byte_counter) / elapsed
		if speed > rate_limit:
			time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)

	def temp_name(self, filename):
		"""Returns a temporary filename for the given filename."""
		if self.params.get('nopart', False) or filename == u'-' or \
				(os.path.exists(encodeFilename(filename)) and not os.path.isfile(encodeFilename(filename))):
			return filename
		return filename + u'.part'

	def undo_temp_name(self, filename):
		if filename.endswith(u'.part'):
			return filename[:-len(u'.part')]
		return filename

	def try_rename(self, old_filename, new_filename):
		try:
			if old_filename == new_filename:
				return
			os.rename(encodeFilename(old_filename), encodeFilename(new_filename))
		except (IOError, OSError), err:
			self.trouble(u'ERROR: unable to rename file')

	def try_utime(self, filename, last_modified_hdr):
		"""Try to set the last-modified time of the given file."""
		if last_modified_hdr is None:
			return
		if not os.path.isfile(encodeFilename(filename)):
			return
		timestr = last_modified_hdr
		if timestr is None:
			return
		filetime = timeconvert(timestr)
		if filetime is None:
			return filetime
		try:
			os.utime(filename, (time.time(), filetime))
		except:
			pass
		return filetime

	def report_writedescription(self, descfn):
		""" Report that the description file is being written """
		self.to_screen(u'[info] Writing video description to: ' + descfn)

	def report_writesubtitles(self, srtfn):
		""" Report that the subtitles file is being written """
		self.to_screen(u'[info] Writing video subtitles to: ' + srtfn)

	def report_writeinfojson(self, infofn):
		""" Report that the metadata file has been written """
		self.to_screen(u'[info] Video description metadata as JSON to: ' + infofn)

	def report_destination(self, filename):
		"""Report destination filename."""
		self.to_screen(u'[download] Destination: ' + filename)

	def report_progress(self, percent_str, data_len_str, speed_str, eta_str):
		"""Report download progress."""
		if self.params.get('noprogress', False):
			return
		self.to_screen(u'\r[download] %s of %s at %s ETA %s' %
				(percent_str, data_len_str, speed_str, eta_str), skip_eol=True)
		self.to_cons_title(u'youtube-dl - %s of %s at %s ETA %s' %
				(percent_str.strip(), data_len_str.strip(), speed_str.strip(), eta_str.strip()))

	def report_resuming_byte(self, resume_len):
		"""Report attempt to resume at given byte."""
		self.to_screen(u'[download] Resuming download at byte %s' % resume_len)

	def report_retry(self, count, retries):
		"""Report retry in case of HTTP error 5xx"""
		self.to_screen(u'[download] Got server HTTP error. Retrying (attempt %d of %d)...' % (count, retries))

	def report_file_already_downloaded(self, file_name):
		"""Report file has already been fully downloaded."""
		try:
			self.to_screen(u'[download] %s has already been downloaded' % file_name)
		except (UnicodeEncodeError), err:
			self.to_screen(u'[download] The file has already been downloaded')

	def report_unable_to_resume(self):
		"""Report it was impossible to resume download."""
		self.to_screen(u'[download] Unable to resume')

	def report_finish(self):
		"""Report download finished."""
		if self.params.get('noprogress', False):
			self.to_screen(u'[download] Download completed')
		else:
			self.to_screen(u'')

	def increment_downloads(self):
		"""Increment the ordinal that assigns a number to each file."""
		self._num_downloads += 1

	def prepare_filename(self, info_dict):
		"""Generate the output filename."""
		try:
			template_dict = dict(info_dict)
			template_dict['epoch'] = unicode(long(time.time()))
			template_dict['autonumber'] = unicode('%05d' % self._num_downloads)
			filename = self.params['outtmpl'] % template_dict
			return filename
		except (ValueError, KeyError), err:
			self.trouble(u'ERROR: invalid system charset or erroneous output template')
			return None

	def _match_entry(self, info_dict):
		""" Returns None iff the file should be downloaded """

		title = info_dict['title']
		matchtitle = self.params.get('matchtitle', False)
		if matchtitle and not re.search(matchtitle, title, re.IGNORECASE):
			return u'[download] "' + title + '" title did not match pattern "' + matchtitle + '"'
		rejecttitle = self.params.get('rejecttitle', False)
		if rejecttitle and re.search(rejecttitle, title, re.IGNORECASE):
			return u'"' + title + '" title matched reject pattern "' + rejecttitle + '"'
		return None

	def process_info(self, info_dict):
		"""Process a single dictionary returned by an InfoExtractor."""

		info_dict['stitle'] = sanitize_filename(info_dict['title'])

		reason = self._match_entry(info_dict)
		if reason is not None:
			self.to_screen(u'[download] ' + reason)
			return

		max_downloads = self.params.get('max_downloads')
		if max_downloads is not None:
			if self._num_downloads > int(max_downloads):
				raise MaxDownloadsReached()

		filename = self.prepare_filename(info_dict)
		
		# Forced printings
		if self.params.get('forcetitle', False):
			print info_dict['title'].encode(preferredencoding(), 'xmlcharrefreplace')
		if self.params.get('forceurl', False):
			print info_dict['url'].encode(preferredencoding(), 'xmlcharrefreplace')
		if self.params.get('forcethumbnail', False) and 'thumbnail' in info_dict:
			print info_dict['thumbnail'].encode(preferredencoding(), 'xmlcharrefreplace')
		if self.params.get('forcedescription', False) and 'description' in info_dict:
			print info_dict['description'].encode(preferredencoding(), 'xmlcharrefreplace')
		if self.params.get('forcefilename', False) and filename is not None:
			print filename.encode(preferredencoding(), 'xmlcharrefreplace')
		if self.params.get('forceformat', False):
			print info_dict['format'].encode(preferredencoding(), 'xmlcharrefreplace')

		# Do nothing else if in simulate mode
		if self.params.get('simulate', False):
			return

		if filename is None:
			return

		try:
			dn = os.path.dirname(encodeFilename(filename))
			if dn != '' and not os.path.exists(dn): # dn is already encoded
				os.makedirs(dn)
		except (OSError, IOError), err:
			self.trouble(u'ERROR: unable to create directory ' + unicode(err))
			return

		if self.params.get('writedescription', False):
			try:
				descfn = filename + u'.description'
				self.report_writedescription(descfn)
				descfile = open(encodeFilename(descfn), 'wb')
				try:
					descfile.write(info_dict['description'].encode('utf-8'))
				finally:
					descfile.close()
			except (OSError, IOError):
				self.trouble(u'ERROR: Cannot write description file ' + descfn)
				return
				
		if self.params.get('writesubtitles', False) and 'subtitles' in info_dict and info_dict['subtitles']:
			# subtitles download errors are already managed as troubles in relevant IE
			# that way it will silently go on when used with unsupporting IE 
			try:
				srtfn = filename.rsplit('.', 1)[0] + u'.srt'
				self.report_writesubtitles(srtfn)
				srtfile = open(encodeFilename(srtfn), 'wb')
				try:
					srtfile.write(info_dict['subtitles'].encode('utf-8'))
				finally:
					srtfile.close()
			except (OSError, IOError):
				self.trouble(u'ERROR: Cannot write subtitles file ' + descfn)
				return

		if self.params.get('writeinfojson', False):
			infofn = filename + u'.info.json'
			self.report_writeinfojson(infofn)
			try:
				json.dump
			except (NameError,AttributeError):
				self.trouble(u'ERROR: No JSON encoder found. Update to Python 2.6+, setup a json module, or leave out --write-info-json.')
				return
			try:
				infof = open(encodeFilename(infofn), 'wb')
				try:
					json_info_dict = dict((k,v) for k,v in info_dict.iteritems() if not k in ('urlhandle',))
					json.dump(json_info_dict, infof)
				finally:
					infof.close()
			except (OSError, IOError):
				self.trouble(u'ERROR: Cannot write metadata to JSON file ' + infofn)
				return

		if not self.params.get('skip_download', False):
			if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(filename)):
				success = True
			else:
				try:
					success = self._do_download(filename, info_dict)
				except (OSError, IOError), err:
					raise UnavailableVideoError
				except (urllib2.URLError, httplib.HTTPException, socket.error), err:
					self.trouble(u'ERROR: unable to download video data: %s' % str(err))
					return
				except (ContentTooShortError, ), err:
					self.trouble(u'ERROR: content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded))
					return
	
			if success:
				try:
					self.post_process(filename, info_dict)
				except (PostProcessingError), err:
					self.trouble(u'ERROR: postprocessing: %s' % str(err))
					return

	def download(self, url_list):
		"""Download a given list of URLs."""
		if len(url_list) > 1 and self.fixed_template():
			raise SameFileError(self.params['outtmpl'])

		for url in url_list:
			suitable_found = False
			for ie in self._ies:
				# Go to next InfoExtractor if not suitable
				if not ie.suitable(url):
					continue

				# Suitable InfoExtractor found
				suitable_found = True

				# Extract information from URL and process it
				videos = ie.extract(url)
				for video in videos or []:
					try:
						self.increment_downloads()
						self.process_info(video)
					except UnavailableVideoError:
						self.trouble(u'\nERROR: unable to download video')

				# Suitable InfoExtractor had been found; go to next URL
				break

			if not suitable_found:
				self.trouble(u'ERROR: no suitable InfoExtractor: %s' % url)

		return self._download_retcode

	def post_process(self, filename, ie_info):
		"""Run the postprocessing chain on the given file."""
		info = dict(ie_info)
		info['filepath'] = filename
		for pp in self._pps:
			info = pp.run(info)
			if info is None:
				break

	def _download_with_rtmpdump(self, filename, url, player_url):
		self.report_destination(filename)
		tmpfilename = self.temp_name(filename)

		# Check for rtmpdump first
		try:
			subprocess.call(['rtmpdump', '-h'], stdout=(file(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
		except (OSError, IOError):
			self.trouble(u'ERROR: RTMP download detected but "rtmpdump" could not be run')
			return False

		# Download using rtmpdump. rtmpdump returns exit code 2 when
		# the connection was interrumpted and resuming appears to be
		# possible. This is part of rtmpdump's normal usage, AFAIK.
		basic_args = ['rtmpdump', '-q'] + [[], ['-W', player_url]][player_url is not None] + ['-r', url, '-o', tmpfilename]
		args = basic_args + [[], ['-e', '-k', '1']][self.params.get('continuedl', False)]
		if self.params.get('verbose', False):
			try:
				import pipes
				shell_quote = lambda args: ' '.join(map(pipes.quote, args))
			except ImportError:
				shell_quote = repr
			self.to_screen(u'[debug] rtmpdump command line: ' + shell_quote(args))
		retval = subprocess.call(args)
		while retval == 2 or retval == 1:
			prevsize = os.path.getsize(encodeFilename(tmpfilename))
			self.to_screen(u'\r[rtmpdump] %s bytes' % prevsize, skip_eol=True)
			time.sleep(5.0) # This seems to be needed
			retval = subprocess.call(basic_args + ['-e'] + [[], ['-k', '1']][retval == 1])
			cursize = os.path.getsize(encodeFilename(tmpfilename))
			if prevsize == cursize and retval == 1:
				break
			 # Some rtmp streams seem abort after ~ 99.8%. Don't complain for those
			if prevsize == cursize and retval == 2 and cursize > 1024:
				self.to_screen(u'\r[rtmpdump] Could not download the whole video. This can happen for some advertisements.')
				retval = 0
				break
		if retval == 0:
			self.to_screen(u'\r[rtmpdump] %s bytes' % os.path.getsize(encodeFilename(tmpfilename)))
			self.try_rename(tmpfilename, filename)
			return True
		else:
			self.trouble(u'\nERROR: rtmpdump exited with code %d' % retval)
			return False

	def _do_download(self, filename, info_dict):
		url = info_dict['url']
		player_url = info_dict.get('player_url', None)

		# Check file already present
		if self.params.get('continuedl', False) and os.path.isfile(encodeFilename(filename)) and not self.params.get('nopart', False):
			self.report_file_already_downloaded(filename)
			return True

		# Attempt to download using rtmpdump
		if url.startswith('rtmp'):
			return self._download_with_rtmpdump(filename, url, player_url)

		tmpfilename = self.temp_name(filename)
		stream = None

		# Do not include the Accept-Encoding header
		headers = {'Youtubedl-no-compression': 'True'}
		basic_request = urllib2.Request(url, None, headers)
		request = urllib2.Request(url, None, headers)

		# Establish possible resume length
		if os.path.isfile(encodeFilename(tmpfilename)):
			resume_len = os.path.getsize(encodeFilename(tmpfilename))
		else:
			resume_len = 0

		open_mode = 'wb'
		if resume_len != 0:
			if self.params.get('continuedl', False):
				self.report_resuming_byte(resume_len)
				request.add_header('Range','bytes=%d-' % resume_len)
				open_mode = 'ab'
			else:
				resume_len = 0

		count = 0
		retries = self.params.get('retries', 0)
		while count <= retries:
			# Establish connection
			try:
				if count == 0 and 'urlhandle' in info_dict:
					data = info_dict['urlhandle']
				data = urllib2.urlopen(request)
				break
			except (urllib2.HTTPError, ), err:
				if (err.code < 500 or err.code >= 600) and err.code != 416:
					# Unexpected HTTP error
					raise
				elif err.code == 416:
					# Unable to resume (requested range not satisfiable)
					try:
						# Open the connection again without the range header
						data = urllib2.urlopen(basic_request)
						content_length = data.info()['Content-Length']
					except (urllib2.HTTPError, ), err:
						if err.code < 500 or err.code >= 600:
							raise
					else:
						# Examine the reported length
						if (content_length is not None and
								(resume_len - 100 < long(content_length) < resume_len + 100)):
							# The file had already been fully downloaded.
							# Explanation to the above condition: in issue #175 it was revealed that
							# YouTube sometimes adds or removes a few bytes from the end of the file,
							# changing the file size slightly and causing problems for some users. So
							# I decided to implement a suggested change and consider the file
							# completely downloaded if the file size differs less than 100 bytes from
							# the one in the hard drive.
							self.report_file_already_downloaded(filename)
							self.try_rename(tmpfilename, filename)
							return True
						else:
							# The length does not match, we start the download over
							self.report_unable_to_resume()
							open_mode = 'wb'
							break
			# Retry
			count += 1
			if count <= retries:
				self.report_retry(count, retries)

		if count > retries:
			self.trouble(u'ERROR: giving up after %s retries' % retries)
			return False

		data_len = data.info().get('Content-length', None)
		if data_len is not None:
			data_len = long(data_len) + resume_len
		data_len_str = self.format_bytes(data_len)
		byte_counter = 0 + resume_len
		block_size = 1024
		start = time.time()
		while True:
			# Download and write
			before = time.time()
			data_block = data.read(block_size)
			after = time.time()
			if len(data_block) == 0:
				break
			byte_counter += len(data_block)

			# Open file just in time
			if stream is None:
				try:
					(stream, tmpfilename) = sanitize_open(tmpfilename, open_mode)
					assert stream is not None
					filename = self.undo_temp_name(tmpfilename)
					self.report_destination(filename)
				except (OSError, IOError), err:
					self.trouble(u'ERROR: unable to open for writing: %s' % str(err))
					return False
			try:
				stream.write(data_block)
			except (IOError, OSError), err:
				self.trouble(u'\nERROR: unable to write data: %s' % str(err))
				return False
			block_size = self.best_block_size(after - before, len(data_block))

			# Progress message
			speed_str = self.calc_speed(start, time.time(), byte_counter - resume_len)
			if data_len is None:
				self.report_progress('Unknown %', data_len_str, speed_str, 'Unknown ETA')
			else:
				percent_str = self.calc_percent(byte_counter, data_len)
				eta_str = self.calc_eta(start, time.time(), data_len - resume_len, byte_counter - resume_len)
				self.report_progress(percent_str, data_len_str, speed_str, eta_str)

			# Apply rate limit
			self.slow_down(start, byte_counter - resume_len)

		if stream is None:
			self.trouble(u'\nERROR: Did not get any data blocks')
			return False
		stream.close()
		self.report_finish()
		if data_len is not None and byte_counter != data_len:
			raise ContentTooShortError(byte_counter, long(data_len))
		self.try_rename(tmpfilename, filename)

		# Update file modification time
		if self.params.get('updatetime', True):
			info_dict['filetime'] = self.try_utime(filename, data.info().get('last-modified', None))

		return True
