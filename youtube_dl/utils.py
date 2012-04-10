#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import htmlentitydefs
import HTMLParser
import locale
import os
import re
import sys
import zlib
import urllib2
import email.utils

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO
		
try:
	import json
except ImportError: # Python <2.6, use trivialjson (https://github.com/phihag/trivialjson):
	import trivialjson as json

std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:5.0.1) Gecko/20100101 Firefox/5.0.1',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Encoding': 'gzip, deflate',
	'Accept-Language': 'en-us,en;q=0.5',
}

def preferredencoding():
	"""Get preferred encoding.

	Returns the best encoding scheme for the system, based on
	locale.getpreferredencoding() and some further tweaks.
	"""
	def yield_preferredencoding():
		try:
			pref = locale.getpreferredencoding()
			u'TEST'.encode(pref)
		except:
			pref = 'UTF-8'
		while True:
			yield pref
	return yield_preferredencoding().next()


def htmlentity_transform(matchobj):
	"""Transforms an HTML entity to a Unicode character.

	This function receives a match object and is intended to be used with
	the re.sub() function.
	"""
	entity = matchobj.group(1)

	# Known non-numeric HTML entity
	if entity in htmlentitydefs.name2codepoint:
		return unichr(htmlentitydefs.name2codepoint[entity])

	# Unicode character
	mobj = re.match(ur'(?u)#(x?\d+)', entity)
	if mobj is not None:
		numstr = mobj.group(1)
		if numstr.startswith(u'x'):
			base = 16
			numstr = u'0%s' % numstr
		else:
			base = 10
		return unichr(long(numstr, base))

	# Unknown entity in name, return its literal representation
	return (u'&%s;' % entity)


def sanitize_title(utitle):
	"""Sanitizes a video title so it could be used as part of a filename."""
	utitle = re.sub(ur'(?u)&(.+?);', htmlentity_transform, utitle)
	return utitle.replace(unicode(os.sep), u'%')


def sanitize_open(filename, open_mode):
	"""Try to open the given filename, and slightly tweak it if this fails.

	Attempts to open the given filename. If this fails, it tries to change
	the filename slightly, step by step, until it's either able to open it
	or it fails and raises a final exception, like the standard open()
	function.

	It returns the tuple (stream, definitive_file_name).
	"""
	try:
		if filename == u'-':
			if sys.platform == 'win32':
				import msvcrt
				msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
			return (sys.stdout, filename)
		stream = open(encodeFilename(filename), open_mode)
		return (stream, filename)
	except (IOError, OSError), err:
		# In case of error, try to remove win32 forbidden chars
		filename = re.sub(ur'[/<>:"\|\?\*]', u'#', filename)

		# An exception here should be caught in the caller
		stream = open(encodeFilename(filename), open_mode)
		return (stream, filename)


def timeconvert(timestr):
	"""Convert RFC 2822 defined time string into system timestamp"""
	timestamp = None
	timetuple = email.utils.parsedate_tz(timestr)
	if timetuple is not None:
		timestamp = email.utils.mktime_tz(timetuple)
	return timestamp

def simplify_title(title):
	expr = re.compile(ur'[^\w\d_\-]+', flags=re.UNICODE)
	return expr.sub(u'_', title).strip(u'_')

def orderedSet(iterable):
	""" Remove all duplicates from the input iterable """
	res = []
	for el in iterable:
		if el not in res:
			res.append(el)
	return res

def unescapeHTML(s):
	"""
	@param s a string (of type unicode)
	"""
	assert type(s) == type(u'')

	htmlParser = HTMLParser.HTMLParser()
	return htmlParser.unescape(s)

def encodeFilename(s):
	"""
	@param s The name of the file (of type unicode)
	"""

	assert type(s) == type(u'')

	if sys.platform == 'win32' and sys.getwindowsversion().major >= 5:
		# Pass u'' directly to use Unicode APIs on Windows 2000 and up
		# (Detecting Windows NT 4 is tricky because 'major >= 4' would
		# match Windows 9x series as well. Besides, NT 4 is obsolete.)
		return s
	else:
		return s.encode(sys.getfilesystemencoding(), 'ignore')

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

class MaxDownloadsReached(Exception):
	""" --max-downloads limit has been reached. """
	pass


class UnavailableVideoError(Exception):
	"""Unavailable Format exception.

	This exception will be thrown when a video is requested
	in a format that is not available for that video.
	"""
	pass


class ContentTooShortError(Exception):
	"""Content Too Short exception.

	This exception may be raised by FileDownloader objects when a file they
	download is too small for what the server announced first, indicating
	the connection was probably interrupted.
	"""
	# Both in bytes
	downloaded = None
	expected = None

	def __init__(self, downloaded, expected):
		self.downloaded = downloaded
		self.expected = expected


class YoutubeDLHandler(urllib2.HTTPHandler):
	"""Handler for HTTP requests and responses.

	This class, when installed with an OpenerDirector, automatically adds
	the standard headers to every HTTP request and handles gzipped and
	deflated responses from web servers. If compression is to be avoided in
	a particular request, the original request in the program code only has
	to include the HTTP header "Youtubedl-No-Compression", which will be
	removed before making the real request.

	Part of this code was copied from:

	http://techknack.net/python-urllib2-handlers/

	Andrew Rowls, the author of that code, agreed to release it to the
	public domain.
	"""

	@staticmethod
	def deflate(data):
		try:
			return zlib.decompress(data, -zlib.MAX_WBITS)
		except zlib.error:
			return zlib.decompress(data)

	@staticmethod
	def addinfourl_wrapper(stream, headers, url, code):
		if hasattr(urllib2.addinfourl, 'getcode'):
			return urllib2.addinfourl(stream, headers, url, code)
		ret = urllib2.addinfourl(stream, headers, url)
		ret.code = code
		return ret

	def http_request(self, req):
		for h in std_headers:
			if h in req.headers:
				del req.headers[h]
			req.add_header(h, std_headers[h])
		if 'Youtubedl-no-compression' in req.headers:
			if 'Accept-encoding' in req.headers:
				del req.headers['Accept-encoding']
			del req.headers['Youtubedl-no-compression']
		return req

	def http_response(self, req, resp):
		old_resp = resp
		# gzip
		if resp.headers.get('Content-encoding', '') == 'gzip':
			gz = gzip.GzipFile(fileobj=StringIO.StringIO(resp.read()), mode='r')
			resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
			resp.msg = old_resp.msg
		# deflate
		if resp.headers.get('Content-encoding', '') == 'deflate':
			gz = StringIO.StringIO(self.deflate(resp.read()))
			resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
			resp.msg = old_resp.msg
		return resp
