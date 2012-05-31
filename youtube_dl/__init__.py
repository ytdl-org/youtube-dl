#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__  = (
	'Ricardo Garcia Gonzalez',
	'Danny Colligan',
	'Benjamin Johnson',
	'Vasyl\' Vavrychuk',
	'Witold Baryluk',
	'Paweł Paprota',
	'Gergely Imreh',
	'Rogério Brito',
	'Philipp Hagemeister',
	'Sören Schulze',
	'Kevin Ngo',
	'Ori Avtalion',
	'shizeeg',
	'Filippo Valsorda',
	)

__license__ = 'Public Domain'
__version__ = '2012.02.27'

UPDATE_URL = 'https://raw.github.com/rg3/youtube-dl/master/youtube-dl'
UPDATE_URL_VERSION = 'https://raw.github.com/rg3/youtube-dl/master/LATEST_VERSION'
UPDATE_URL_EXE = 'https://raw.github.com/rg3/youtube-dl/master/youtube-dl.exe'


import cookielib
import getpass
import optparse
import os
import re
import shlex
import socket
import subprocess
import sys
import urllib2
import warnings

from utils import *
from FileDownloader import *
from InfoExtractors import *
from PostProcessor import *

def updateSelf(downloader, filename):
	''' Update the program file with the latest version from the repository '''
	# Note: downloader only used for options
	
	if not os.access(filename, os.W_OK):
		sys.exit('ERROR: no write permissions on %s' % filename)

	downloader.to_screen(u'Updating to latest version...')

	urlv = urllib2.urlopen(UPDATE_URL_VERSION)
	newversion = urlv.read().strip()
	if newversion == __version__:
		downloader.to_screen(u'youtube-dl is up-to-date (' + __version__ + ')')
		return
	urlv.close()

	if hasattr(sys, "frozen"): #py2exe
		exe = os.path.abspath(filename)
		directory = os.path.dirname(exe)
		if not os.access(directory, os.W_OK):
			sys.exit('ERROR: no write permissions on %s' % directory)
			
		try:
			urlh = urllib2.urlopen(UPDATE_URL_EXE)
			newcontent = urlh.read()
			urlh.close()
			with open(exe + '.new', 'wb') as outf:
				outf.write(newcontent)
		except (IOError, OSError), err:
			sys.exit('ERROR: unable to download latest version')
			
		try:
			bat = os.path.join(directory, 'youtube-dl-updater.bat')
			b = open(bat, 'w')
			
			print >> b, """
echo Updating youtube-dl...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "%s.new" "%s"
del "%s"
			""" %(exe, exe, bat)
			
			b.close()
			
			os.startfile(bat)
		except (IOError, OSError), err:
			sys.exit('ERROR: unable to overwrite current version')

	else:
		try:
			urlh = urllib2.urlopen(UPDATE_URL)
			newcontent = urlh.read()
			urlh.close()
		except (IOError, OSError), err:
			sys.exit('ERROR: unable to download latest version')

		try:
			with open(filename, 'wb') as outf:
				outf.write(newcontent)
		except (IOError, OSError), err:
			sys.exit('ERROR: unable to overwrite current version')

	downloader.to_screen(u'Updated youtube-dl. Restart youtube-dl to use the new version.')

def parseOpts():
	def _readOptions(filename_bytes):
		try:
			optionf = open(filename_bytes)
		except IOError:
			return [] # silently skip if file is not present
		try:
			res = []
			for l in optionf:
				res += shlex.split(l, comments=True)
		finally:
			optionf.close()
		return res

	def _format_option_string(option):
		''' ('-o', '--option') -> -o, --format METAVAR'''

		opts = []

		if option._short_opts: opts.append(option._short_opts[0])
		if option._long_opts: opts.append(option._long_opts[0])
		if len(opts) > 1: opts.insert(1, ', ')

		if option.takes_value(): opts.append(' %s' % option.metavar)

		return "".join(opts)

	def _find_term_columns():
		columns = os.environ.get('COLUMNS', None)
		if columns:
			return int(columns)

		try:
			sp = subprocess.Popen(['stty', 'size'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out,err = sp.communicate()
			return int(out.split()[1])
		except:
			pass
		return None

	max_width = 80
	max_help_position = 80

	# No need to wrap help messages if we're on a wide console
	columns = _find_term_columns()
	if columns: max_width = columns

	fmt = optparse.IndentedHelpFormatter(width=max_width, max_help_position=max_help_position)
	fmt.format_option_strings = _format_option_string

	kw = {
		'version'   : __version__,
		'formatter' : fmt,
		'usage' : '%prog [options] url [url...]',
		'conflict_handler' : 'resolve',
	}

	parser = optparse.OptionParser(**kw)

	# option groups
	general        = optparse.OptionGroup(parser, 'General Options')
	selection      = optparse.OptionGroup(parser, 'Video Selection')
	authentication = optparse.OptionGroup(parser, 'Authentication Options')
	video_format   = optparse.OptionGroup(parser, 'Video Format Options')
	postproc       = optparse.OptionGroup(parser, 'Post-processing Options')
	filesystem     = optparse.OptionGroup(parser, 'Filesystem Options')
	verbosity      = optparse.OptionGroup(parser, 'Verbosity / Simulation Options')

	general.add_option('-h', '--help',
			action='help', help='print this help text and exit')
	general.add_option('-v', '--version',
			action='version', help='print program version and exit')
	general.add_option('-U', '--update',
			action='store_true', dest='update_self', help='update this program to latest version')
	general.add_option('-i', '--ignore-errors',
			action='store_true', dest='ignoreerrors', help='continue on download errors', default=False)
	general.add_option('-r', '--rate-limit',
			dest='ratelimit', metavar='LIMIT', help='download rate limit (e.g. 50k or 44.6m)')
	general.add_option('-R', '--retries',
			dest='retries', metavar='RETRIES', help='number of retries (default is 10)', default=10)
	general.add_option('--dump-user-agent',
			action='store_true', dest='dump_user_agent',
			help='display the current browser identification', default=False)
	general.add_option('--list-extractors',
			action='store_true', dest='list_extractors',
			help='List all supported extractors and the URLs they would handle', default=False)

	selection.add_option('--playlist-start',
			dest='playliststart', metavar='NUMBER', help='playlist video to start at (default is 1)', default=1)
	selection.add_option('--playlist-end',
			dest='playlistend', metavar='NUMBER', help='playlist video to end at (default is last)', default=-1)
	selection.add_option('--match-title', dest='matchtitle', metavar='REGEX',help='download only matching titles (regex or caseless sub-string)')
	selection.add_option('--reject-title', dest='rejecttitle', metavar='REGEX',help='skip download for matching titles (regex or caseless sub-string)')
	selection.add_option('--max-downloads', metavar='NUMBER', dest='max_downloads', help='Abort after downloading NUMBER files', default=None)

	authentication.add_option('-u', '--username',
			dest='username', metavar='USERNAME', help='account username')
	authentication.add_option('-p', '--password',
			dest='password', metavar='PASSWORD', help='account password')
	authentication.add_option('-n', '--netrc',
			action='store_true', dest='usenetrc', help='use .netrc authentication data', default=False)


	video_format.add_option('-f', '--format',
			action='store', dest='format', metavar='FORMAT', help='video format code')
	video_format.add_option('--all-formats',
			action='store_const', dest='format', help='download all available video formats', const='all')
	video_format.add_option('--prefer-free-formats',
			action='store_true', dest='prefer_free_formats', default=False, help='prefer free video formats unless a specific one is requested')
	video_format.add_option('--max-quality',
			action='store', dest='format_limit', metavar='FORMAT', help='highest quality format to download')
	video_format.add_option('-F', '--list-formats',
			action='store_true', dest='listformats', help='list all available formats (currently youtube only)')
	video_format.add_option('--write-srt',
			action='store_true', dest='writesubtitles',
			help='write video closed captions to a .srt file (currently youtube only)', default=False)
	video_format.add_option('--srt-lang',
			action='store', dest='subtitleslang', metavar='LANG',
			help='language of the closed captions to download (optional) use IETF language tags like \'en\'')


	verbosity.add_option('-q', '--quiet',
			action='store_true', dest='quiet', help='activates quiet mode', default=False)
	verbosity.add_option('-s', '--simulate',
			action='store_true', dest='simulate', help='do not download the video and do not write anything to disk', default=False)
	verbosity.add_option('--skip-download',
			action='store_true', dest='skip_download', help='do not download the video', default=False)
	verbosity.add_option('-g', '--get-url',
			action='store_true', dest='geturl', help='simulate, quiet but print URL', default=False)
	verbosity.add_option('-e', '--get-title',
			action='store_true', dest='gettitle', help='simulate, quiet but print title', default=False)
	verbosity.add_option('--get-thumbnail',
			action='store_true', dest='getthumbnail',
			help='simulate, quiet but print thumbnail URL', default=False)
	verbosity.add_option('--get-description',
			action='store_true', dest='getdescription',
			help='simulate, quiet but print video description', default=False)
	verbosity.add_option('--get-filename',
			action='store_true', dest='getfilename',
			help='simulate, quiet but print output filename', default=False)
	verbosity.add_option('--get-format',
			action='store_true', dest='getformat',
			help='simulate, quiet but print output format', default=False)
	verbosity.add_option('--no-progress',
			action='store_true', dest='noprogress', help='do not print progress bar', default=False)
	verbosity.add_option('--console-title',
			action='store_true', dest='consoletitle',
			help='display progress in console titlebar', default=False)
	verbosity.add_option('-v', '--verbose',
			action='store_true', dest='verbose', help='print various debugging information', default=False)


	filesystem.add_option('-t', '--title',
			action='store_true', dest='usetitle', help='use title in file name', default=False)
	filesystem.add_option('-l', '--literal',
			action='store_true', dest='useliteral', help='use literal title in file name', default=False)
	filesystem.add_option('-A', '--auto-number',
			action='store_true', dest='autonumber',
			help='number downloaded files starting from 00000', default=False)
	filesystem.add_option('-o', '--output',
			dest='outtmpl', metavar='TEMPLATE', help='output filename template. Use %(stitle)s to get the title, %(uploader)s for the uploader name, %(autonumber)s to get an automatically incremented number, %(ext)s for the filename extension, %(upload_date)s for the upload date (YYYYMMDD), and %% for a literal percent. Use - to output to stdout.')
	filesystem.add_option('-a', '--batch-file',
			dest='batchfile', metavar='FILE', help='file containing URLs to download (\'-\' for stdin)')
	filesystem.add_option('-w', '--no-overwrites',
			action='store_true', dest='nooverwrites', help='do not overwrite files', default=False)
	filesystem.add_option('-c', '--continue',
			action='store_true', dest='continue_dl', help='resume partially downloaded files', default=True)
	filesystem.add_option('--no-continue',
			action='store_false', dest='continue_dl',
			help='do not resume partially downloaded files (restart from beginning)')
	filesystem.add_option('--cookies',
			dest='cookiefile', metavar='FILE', help='file to read cookies from and dump cookie jar in')
	filesystem.add_option('--no-part',
			action='store_true', dest='nopart', help='do not use .part files', default=False)
	filesystem.add_option('--no-mtime',
			action='store_false', dest='updatetime',
			help='do not use the Last-modified header to set the file modification time', default=True)
	filesystem.add_option('--write-description',
			action='store_true', dest='writedescription',
			help='write video description to a .description file', default=False)
	filesystem.add_option('--write-info-json',
			action='store_true', dest='writeinfojson',
			help='write video metadata to a .info.json file', default=False)


	postproc.add_option('--extract-audio', action='store_true', dest='extractaudio', default=False,
			help='convert video files to audio-only files (requires ffmpeg or avconv and ffprobe or avprobe)')
	postproc.add_option('--audio-format', metavar='FORMAT', dest='audioformat', default='best',
			help='"best", "aac", "vorbis", "mp3", "m4a", or "wav"; best by default')
	postproc.add_option('--audio-quality', metavar='QUALITY', dest='audioquality', default='128K',
			help='ffmpeg/avconv audio bitrate specification, 128k by default')
	postproc.add_option('-k', '--keep-video', action='store_true', dest='keepvideo', default=False,
			help='keeps the video file on disk after the post-processing; the video is erased by default')


	parser.add_option_group(general)
	parser.add_option_group(selection)
	parser.add_option_group(filesystem)
	parser.add_option_group(verbosity)
	parser.add_option_group(video_format)
	parser.add_option_group(authentication)
	parser.add_option_group(postproc)

	xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
	if xdg_config_home:
		userConf = os.path.join(xdg_config_home, 'youtube-dl.conf')
	else:
		userConf = os.path.join(os.path.expanduser('~'), '.config', 'youtube-dl.conf')
	argv = _readOptions('/etc/youtube-dl.conf') + _readOptions(userConf) + sys.argv[1:]
	opts, args = parser.parse_args(argv)

	return parser, opts, args

def gen_extractors():
	""" Return a list of an instance of every supported extractor.
	The order does matter; the first extractor matched is the one handling the URL.
	"""
	return [
		YoutubePlaylistIE(),
		YoutubeUserIE(),
		YoutubeSearchIE(),
		YoutubeIE(),
		MetacafeIE(),
		DailymotionIE(),
		GoogleIE(),
		GoogleSearchIE(),
		PhotobucketIE(),
		YahooIE(),
		YahooSearchIE(),
		DepositFilesIE(),
		FacebookIE(),
		BlipTVIE(),
		VimeoIE(),
		MyVideoIE(),
		ComedyCentralIE(),
		EscapistIE(),
		CollegeHumorIE(),
		XVideosIE(),
		SoundcloudIE(),
		InfoQIE(),
		MixcloudIE(),
		StanfordOpenClassroomIE(),
		MTVIE(),

		GenericIE()
	]

def _real_main():
	parser, opts, args = parseOpts()

	# Open appropriate CookieJar
	if opts.cookiefile is None:
		jar = cookielib.CookieJar()
	else:
		try:
			jar = cookielib.MozillaCookieJar(opts.cookiefile)
			if os.path.isfile(opts.cookiefile) and os.access(opts.cookiefile, os.R_OK):
				jar.load()
		except (IOError, OSError), err:
			sys.exit(u'ERROR: unable to open cookie file')

	# Dump user agent
	if opts.dump_user_agent:
		print std_headers['User-Agent']
		sys.exit(0)

	# Batch file verification
	batchurls = []
	if opts.batchfile is not None:
		try:
			if opts.batchfile == '-':
				batchfd = sys.stdin
			else:
				batchfd = open(opts.batchfile, 'r')
			batchurls = batchfd.readlines()
			batchurls = [x.strip() for x in batchurls]
			batchurls = [x for x in batchurls if len(x) > 0 and not re.search(r'^[#/;]', x)]
		except IOError:
			sys.exit(u'ERROR: batch file could not be read')
	all_urls = batchurls + args
	all_urls = map(lambda url: url.strip(), all_urls)

	# General configuration
	cookie_processor = urllib2.HTTPCookieProcessor(jar)
	proxy_handler = urllib2.ProxyHandler()
	opener = urllib2.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
	urllib2.install_opener(opener)
	socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

	extractors = gen_extractors()

	if opts.list_extractors:
		for ie in extractors:
			print(ie.IE_NAME)
			matchedUrls = filter(lambda url: ie.suitable(url), all_urls)
			all_urls = filter(lambda url: url not in matchedUrls, all_urls)
			for mu in matchedUrls:
				print(u'  ' + mu)
		sys.exit(0)

	# Conflicting, missing and erroneous options
	if opts.usenetrc and (opts.username is not None or opts.password is not None):
		parser.error(u'using .netrc conflicts with giving username/password')
	if opts.password is not None and opts.username is None:
		parser.error(u'account username missing')
	if opts.outtmpl is not None and (opts.useliteral or opts.usetitle or opts.autonumber):
		parser.error(u'using output template conflicts with using title, literal title or auto number')
	if opts.usetitle and opts.useliteral:
		parser.error(u'using title conflicts with using literal title')
	if opts.username is not None and opts.password is None:
		opts.password = getpass.getpass(u'Type account password and press return:')
	if opts.ratelimit is not None:
		numeric_limit = FileDownloader.parse_bytes(opts.ratelimit)
		if numeric_limit is None:
			parser.error(u'invalid rate limit specified')
		opts.ratelimit = numeric_limit
	if opts.retries is not None:
		try:
			opts.retries = long(opts.retries)
		except (TypeError, ValueError), err:
			parser.error(u'invalid retry count specified')
	try:
		opts.playliststart = int(opts.playliststart)
		if opts.playliststart <= 0:
			raise ValueError(u'Playlist start must be positive')
	except (TypeError, ValueError), err:
		parser.error(u'invalid playlist start number specified')
	try:
		opts.playlistend = int(opts.playlistend)
		if opts.playlistend != -1 and (opts.playlistend <= 0 or opts.playlistend < opts.playliststart):
			raise ValueError(u'Playlist end must be greater than playlist start')
	except (TypeError, ValueError), err:
		parser.error(u'invalid playlist end number specified')
	if opts.extractaudio:
		if opts.audioformat not in ['best', 'aac', 'mp3', 'vorbis', 'm4a', 'wav']:
			parser.error(u'invalid audio format specified')

	# File downloader
	fd = FileDownloader({
		'usenetrc': opts.usenetrc,
		'username': opts.username,
		'password': opts.password,
		'quiet': (opts.quiet or opts.geturl or opts.gettitle or opts.getthumbnail or opts.getdescription or opts.getfilename or opts.getformat),
		'forceurl': opts.geturl,
		'forcetitle': opts.gettitle,
		'forcethumbnail': opts.getthumbnail,
		'forcedescription': opts.getdescription,
		'forcefilename': opts.getfilename,
		'forceformat': opts.getformat,
		'simulate': opts.simulate,
		'skip_download': (opts.skip_download or opts.simulate or opts.geturl or opts.gettitle or opts.getthumbnail or opts.getdescription or opts.getfilename or opts.getformat),
		'format': opts.format,
		'format_limit': opts.format_limit,
		'listformats': opts.listformats,
		'outtmpl': ((opts.outtmpl is not None and opts.outtmpl.decode(preferredencoding()))
			or (opts.format == '-1' and opts.usetitle and u'%(stitle)s-%(id)s-%(format)s.%(ext)s')
			or (opts.format == '-1' and opts.useliteral and u'%(title)s-%(id)s-%(format)s.%(ext)s')
			or (opts.format == '-1' and u'%(id)s-%(format)s.%(ext)s')
			or (opts.usetitle and opts.autonumber and u'%(autonumber)s-%(stitle)s-%(id)s.%(ext)s')
			or (opts.useliteral and opts.autonumber and u'%(autonumber)s-%(title)s-%(id)s.%(ext)s')
			or (opts.usetitle and u'%(stitle)s-%(id)s.%(ext)s')
			or (opts.useliteral and u'%(title)s-%(id)s.%(ext)s')
			or (opts.autonumber and u'%(autonumber)s-%(id)s.%(ext)s')
			or u'%(id)s.%(ext)s'),
		'ignoreerrors': opts.ignoreerrors,
		'ratelimit': opts.ratelimit,
		'nooverwrites': opts.nooverwrites,
		'retries': opts.retries,
		'continuedl': opts.continue_dl,
		'noprogress': opts.noprogress,
		'playliststart': opts.playliststart,
		'playlistend': opts.playlistend,
		'logtostderr': opts.outtmpl == '-',
		'consoletitle': opts.consoletitle,
		'nopart': opts.nopart,
		'updatetime': opts.updatetime,
		'writedescription': opts.writedescription,
		'writeinfojson': opts.writeinfojson,
		'writesubtitles': opts.writesubtitles,
		'subtitleslang': opts.subtitleslang,
		'matchtitle': opts.matchtitle,
		'rejecttitle': opts.rejecttitle,
		'max_downloads': opts.max_downloads,
		'prefer_free_formats': opts.prefer_free_formats,
		'verbose': opts.verbose,
		})

	if opts.verbose:
		fd.to_screen(u'[debug] Proxy map: ' + str(proxy_handler.proxies))

	for extractor in extractors:
		fd.add_info_extractor(extractor)

	# PostProcessors
	if opts.extractaudio:
		fd.add_post_processor(FFmpegExtractAudioPP(preferredcodec=opts.audioformat, preferredquality=opts.audioquality, keepvideo=opts.keepvideo))

	# Update version
	if opts.update_self:
		updateSelf(fd, sys.argv[0])

	# Maybe do nothing
	if len(all_urls) < 1:
		if not opts.update_self:
			parser.error(u'you must provide at least one URL')
		else:
			sys.exit()
	
	try:
		retcode = fd.download(all_urls)
	except MaxDownloadsReached:
		fd.to_screen(u'--max-download limit reached, aborting.')
		retcode = 101

	# Dump cookie jar if requested
	if opts.cookiefile is not None:
		try:
			jar.save()
		except (IOError, OSError), err:
			sys.exit(u'ERROR: unable to save cookie jar')

	sys.exit(retcode)

def main():
	try:
		_real_main()
	except DownloadError:
		sys.exit(1)
	except SameFileError:
		sys.exit(u'ERROR: fixed output name but more than one file to download')
	except KeyboardInterrupt:
		sys.exit(u'\nERROR: Interrupted by user')
