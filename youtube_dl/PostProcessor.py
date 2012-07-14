#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import time

from utils import *


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

	def set_downloader(self, downloader):
		"""Sets the downloader for this PP."""
		self._downloader = downloader

	def run(self, information):
		"""Run the PostProcessor.

		The "information" argument is a dictionary like the ones
		composed by InfoExtractors. The only difference is that this
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

class AudioConversionError(BaseException):
	def __init__(self, message):
		self.message = message

class FFmpegExtractAudioPP(PostProcessor):
	def __init__(self, downloader=None, preferredcodec=None, preferredquality=None, keepvideo=False):
		PostProcessor.__init__(self, downloader)
		if preferredcodec is None:
			preferredcodec = 'best'
		self._preferredcodec = preferredcodec
		self._preferredquality = preferredquality
		self._keepvideo = keepvideo
		self._exes = self.detect_executables()

	@staticmethod
	def detect_executables():
		available = {'avprobe' : False, 'avconv' : False, 'ffmpeg' : False, 'ffprobe' : False}
		for path in os.environ["PATH"].split(os.pathsep):
			for program in available.keys():
				exe_file = os.path.join(path, program)
				if os.path.isfile(exe_file) and os.access(exe_file, os.X_OK):
					available[program] = exe_file
		return available

	def get_audio_codec(self, path):
		if not self._exes['ffprobe'] and not self._exes['avprobe']: return None
		try:
			cmd = [self._exes['avprobe'] or self._exes['ffprobe'], '-show_streams', '--', encodeFilename(path)]
			handle = subprocess.Popen(cmd, stderr=file(os.path.devnull, 'w'), stdout=subprocess.PIPE)
			output = handle.communicate()[0]
			if handle.wait() != 0:
				return None
		except (IOError, OSError):
			return None
		audio_codec = None
		for line in output.split('\n'):
			if line.startswith('codec_name='):
				audio_codec = line.split('=')[1].strip()
			elif line.strip() == 'codec_type=audio' and audio_codec is not None:
				return audio_codec
		return None

	def run_ffmpeg(self, path, out_path, codec, more_opts):
		if not self._exes['ffmpeg'] and not self._exes['avconv']:
			raise AudioConversionError('ffmpeg or avconv not found. Please install one.')	
		if codec is None:
			acodec_opts = []
		else:
			acodec_opts = ['-acodec', codec]
		cmd = ([self._exes['avconv'] or self._exes['ffmpeg'], '-y', '-i', encodeFilename(path), '-vn']
			   + acodec_opts + more_opts +
			   ['--', encodeFilename(out_path)])
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout,stderr = p.communicate()
		if p.returncode != 0:
			msg = stderr.strip().split('\n')[-1]
			raise AudioConversionError(msg)

	def run(self, information):
		path = information['filepath']

		filecodec = self.get_audio_codec(path)
		if filecodec is None:
			self._downloader.to_stderr(u'WARNING: unable to obtain file audio codec with ffprobe')
			return None

		more_opts = []
		if self._preferredcodec == 'best' or self._preferredcodec == filecodec or (self._preferredcodec == 'm4a' and filecodec == 'aac'):
			if self._preferredcodec == 'm4a' and filecodec == 'aac':
				# Lossless, but in another container
				acodec = 'copy'
				extension = self._preferredcodec
				more_opts = [self._exes['avconv'] and '-bsf:a' or '-absf', 'aac_adtstoasc']
			elif filecodec in ['aac', 'mp3', 'vorbis']:
				# Lossless if possible
				acodec = 'copy'
				extension = filecodec
				if filecodec == 'aac':
					more_opts = ['-f', 'adts']
				if filecodec == 'vorbis':
					extension = 'ogg'
			else:
				# MP3 otherwise.
				acodec = 'libmp3lame'
				extension = 'mp3'
				more_opts = []
				if self._preferredquality is not None:
					more_opts += [self._exes['avconv'] and '-b:a' or '-ab', self._preferredquality]
		else:
			# We convert the audio (lossy)
			acodec = {'mp3': 'libmp3lame', 'aac': 'aac', 'm4a': 'aac', 'vorbis': 'libvorbis', 'wav': None}[self._preferredcodec]
			extension = self._preferredcodec
			more_opts = []
			if self._preferredquality is not None:
				more_opts += [self._exes['avconv'] and '-b:a' or '-ab', self._preferredquality]
			if self._preferredcodec == 'aac':
				more_opts += ['-f', 'adts']
			if self._preferredcodec == 'm4a':
				more_opts += [self._exes['avconv'] and '-bsf:a' or '-absf', 'aac_adtstoasc']
			if self._preferredcodec == 'vorbis':
				extension = 'ogg'
			if self._preferredcodec == 'wav':
				extension = 'wav'
				more_opts += ['-f', 'wav']

		prefix, sep, ext = path.rpartition(u'.') # not os.path.splitext, since the latter does not work on unicode in all setups
		new_path = prefix + sep + extension
		self._downloader.to_screen(u'[' + (self._exes['avconv'] and 'avconv' or 'ffmpeg') + '] Destination: ' + new_path)
		try:
			self.run_ffmpeg(path, new_path, acodec, more_opts)
		except:
			etype,e,tb = sys.exc_info()
			if isinstance(e, AudioConversionError):
				self._downloader.to_stderr(u'ERROR: audio conversion failed: ' + e.message)
			else:
				self._downloader.to_stderr(u'ERROR: error running ' + (self._exes['avconv'] and 'avconv' or 'ffmpeg'))
			return None

 		# Try to update the date time for extracted audio file.
		if information.get('filetime') is not None:
			try:
				os.utime(encodeFilename(new_path), (time.time(), information['filetime']))
			except:
				self._downloader.to_stderr(u'WARNING: Cannot update utime of audio file')

		if not self._keepvideo:
			try:
				os.remove(encodeFilename(path))
			except (IOError, OSError):
				self._downloader.to_stderr(u'WARNING: Unable to remove downloaded video file')
				return None

		information['filepath'] = new_path
		return information
