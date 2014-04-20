#! /usr/bin/env python

# Test stop, pause & resume handlers

from time import sleep
from threading import Thread

from youtube_dl import YoutubeDL

class Downloader(Thread):

	def __init__(self, options, url):
		super(Downloader, self).__init__()
		self.ydl_item = YoutubeDL(options)
		self.url = url

	def run(self):
		self.ydl_item.add_default_info_extractors()
		self.ydl_item.download([self.url])

	@staticmethod
	def format_percent(db, tb):
		if db is None: return None
		pr = float(db) / float(tb) * 100.0
		return '%6s' % ('%3.1f%%' % pr)

	def progress_hook(self, pr):
		print Downloader.format_percent(pr.get('downloaded_bytes'), pr.get('total_bytes'))

	def download(self):
		""" Call self.start() """
		self.start()

	def close(self):
		""" Stop download and join thread """
		self.ydl_item.stop()
		self.join()

	def pause(self):
		""" Pause/Resume download """
		self.ydl_item.pause()

Z = 10 # sleep time

ydl_opts = {'outtmpl': u'%(title)s.%(ext)s'}
test_url = "http://www.youtube.com/watch?v=0KSOMA3QBU0"

dlThread = Downloader(ydl_opts, test_url)
print 'Downloading %s' % test_url
dlThread.download()
print 'Sleep %s secs' % Z
sleep(Z)
print 'Pause download for %s secs' % (Z/2)
dlThread.pause()
sleep(Z/2)
print 'Resume download'
dlThread.pause()
print 'Sleep %s secs' % Z
sleep(Z)
print 'Close downlaod thread'
dlThread.close()
print 'Downloader thread status: %s' % dlThread.isAlive()
print 'Done'
