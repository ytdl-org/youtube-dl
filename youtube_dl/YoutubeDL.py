#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import io
import os
import re
import shutil
import socket
import sys
import time
import traceback

from .utils import *
from .extractor import get_info_extractor, gen_extractors
from .FileDownloader import FileDownloader


class YoutubeDL(object):
    """YoutubeDL class.

    YoutubeDL objects are the ones responsible of downloading the
    actual video file and writing it to disk if the user has requested
    it, among some other tasks. In most cases there should be one per
    program. As, given a video URL, the downloader doesn't know how to
    extract all the needed information, task that InfoExtractors do, it
    has to pass the URL to one of them.

    For this, YoutubeDL objects have a method that allows
    InfoExtractors to be registered in a given order. When it is passed
    a URL, the YoutubeDL object handles it to the first InfoExtractor it
    finds that reports being able to handle it. The InfoExtractor extracts
    all the information about the video or videos the URL refers to, and
    YoutubeDL process the extracted information, possibly using a File
    Downloader to download the video.

    YoutubeDL objects accept a lot of parameters. In order not to saturate
    the object constructor with arguments, it receives a dictionary of
    options instead. These options are available through the params
    attribute for the InfoExtractors to use. The YoutubeDL also
    registers itself as the downloader in charge for the InfoExtractors
    that are added to it, so this is a "mutual registration".

    Available options:

    username:          Username for authentication purposes.
    password:          Password for authentication purposes.
    videopassword:     Password for acces a video.
    usenetrc:          Use netrc for authentication instead.
    verbose:           Print additional info to stdout.
    quiet:             Do not print messages to stdout.
    forceurl:          Force printing final URL.
    forcetitle:        Force printing title.
    forceid:           Force printing ID.
    forcethumbnail:    Force printing thumbnail URL.
    forcedescription:  Force printing description.
    forcefilename:     Force printing final filename.
    simulate:          Do not download the video files.
    format:            Video format code.
    format_limit:      Highest quality format to try.
    outtmpl:           Template for output names.
    restrictfilenames: Do not allow "&" and spaces in file names
    ignoreerrors:      Do not stop on download errors.
    nooverwrites:      Prevent overwriting files.
    playliststart:     Playlist item to start at.
    playlistend:       Playlist item to end at.
    matchtitle:        Download only matching titles.
    rejecttitle:       Reject downloads for matching titles.
    logtostderr:       Log messages to stderr instead of stdout.
    writedescription:  Write the video description to a .description file
    writeinfojson:     Write the video description to a .info.json file
    writethumbnail:    Write the thumbnail image to a file
    writesubtitles:    Write the video subtitles to a file
    writeautomaticsub: Write the automatic subtitles to a file
    allsubtitles:      Downloads all the subtitles of the video
    listsubtitles:     Lists all available subtitles for the video
    subtitlesformat:   Subtitle format [srt/sbv/vtt] (default=srt)
    subtitleslang:     Language of the subtitles to download
    keepvideo:         Keep the video file after post-processing
    daterange:         A DateRange object, download only if the upload_date is in the range.
    skip_download:     Skip the actual download of the video file
    
    The following parameters are not used by YoutubeDL itself, they are used by
    the FileDownloader:
    nopart, updatetime, buffersize, ratelimit, min_filesize, max_filesize, test,
    noresizebuffer, retries, continuedl, noprogress, consoletitle
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
        self._progress_hooks = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]
        self.params = params
        self.fd = FileDownloader(self, self.params)

        if '%(stitle)s' in self.params['outtmpl']:
            self.report_warning(u'%(stitle)s is deprecated. Use the %(title)s and the --restrict-filenames flag(which also secures %(uploader)s et al) instead.')

    def add_info_extractor(self, ie):
        """Add an InfoExtractor object to the end of the list."""
        self._ies.append(ie)
        ie.set_downloader(self)

    def add_default_info_extractors(self):
        """
        Add the InfoExtractors returned by gen_extractors to the end of the list
        """
        for ie in gen_extractors():
            self.add_info_extractor(ie)

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
            if 'b' in getattr(self._screen_file, 'mode', '') or sys.version_info[0] < 3: # Python 2 lies about the mode of sys.stdout/sys.stderr
                output = output.encode(preferredencoding(), 'ignore')
            self._screen_file.write(output)
            self._screen_file.flush()

    def to_stderr(self, message):
        """Print message to stderr."""
        assert type(message) == type(u'')
        output = message + u'\n'
        if 'b' in getattr(self._screen_file, 'mode', '') or sys.version_info[0] < 3: # Python 2 lies about the mode of sys.stdout/sys.stderr
            output = output.encode(preferredencoding())
        sys.stderr.write(output)

    def fixed_template(self):
        """Checks if the output template is fixed."""
        return (re.search(u'(?u)%\\(.+?\\)s', self.params['outtmpl']) is None)

    def trouble(self, message=None, tb=None):
        """Determine action to take when a download problem appears.

        Depending on if the downloader has been configured to ignore
        download errors or not, this method may throw an exception or
        not when errors are found, after printing the message.

        tb, if given, is additional traceback information.
        """
        if message is not None:
            self.to_stderr(message)
        if self.params.get('verbose'):
            if tb is None:
                if sys.exc_info()[0]:  # if .trouble has been called from an except block
                    tb = u''
                    if hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                        tb += u''.join(traceback.format_exception(*sys.exc_info()[1].exc_info))
                    tb += compat_str(traceback.format_exc())
                else:
                    tb_data = traceback.format_list(traceback.extract_stack())
                    tb = u''.join(tb_data)
            self.to_stderr(tb)
        if not self.params.get('ignoreerrors', False):
            if sys.exc_info()[0] and hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                exc_info = sys.exc_info()[1].exc_info
            else:
                exc_info = sys.exc_info()
            raise DownloadError(message, exc_info)
        self._download_retcode = 1

    def report_warning(self, message):
        '''
        Print the message to stderr, it will be prefixed with 'WARNING:'
        If stderr is a tty file the 'WARNING:' will be colored
        '''
        if sys.stderr.isatty() and os.name != 'nt':
            _msg_header=u'\033[0;33mWARNING:\033[0m'
        else:
            _msg_header=u'WARNING:'
        warning_message=u'%s %s' % (_msg_header,message)
        self.to_stderr(warning_message)

    def report_error(self, message, tb=None):
        '''
        Do the same as trouble, but prefixes the message with 'ERROR:', colored
        in red if stderr is a tty file.
        '''
        if sys.stderr.isatty() and os.name != 'nt':
            _msg_header = u'\033[0;31mERROR:\033[0m'
        else:
            _msg_header = u'ERROR:'
        error_message = u'%s %s' % (_msg_header, message)
        self.trouble(error_message, tb)

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

    def report_writedescription(self, descfn):
        """ Report that the description file is being written """
        self.to_screen(u'[info] Writing video description to: ' + descfn)

    def report_writesubtitles(self, sub_filename):
        """ Report that the subtitles file is being written """
        self.to_screen(u'[info] Writing video subtitles to: ' + sub_filename)

    def report_writeinfojson(self, infofn):
        """ Report that the metadata file has been written """
        self.to_screen(u'[info] Video description metadata as JSON to: ' + infofn)

    def report_file_already_downloaded(self, file_name):
        """Report file has already been fully downloaded."""
        try:
            self.to_screen(u'[download] %s has already been downloaded' % file_name)
        except (UnicodeEncodeError) as err:
            self.to_screen(u'[download] The file has already been downloaded')

    def increment_downloads(self):
        """Increment the ordinal that assigns a number to each file."""
        self._num_downloads += 1

    def prepare_filename(self, info_dict):
        """Generate the output filename."""
        try:
            template_dict = dict(info_dict)

            template_dict['epoch'] = int(time.time())
            autonumber_size = self.params.get('autonumber_size')
            if autonumber_size is None:
                autonumber_size = 5
            autonumber_templ = u'%0' + str(autonumber_size) + u'd'
            template_dict['autonumber'] = autonumber_templ % self._num_downloads
            if template_dict['playlist_index'] is not None:
                template_dict['playlist_index'] = u'%05d' % template_dict['playlist_index']

            sanitize = lambda k,v: sanitize_filename(
                u'NA' if v is None else compat_str(v),
                restricted=self.params.get('restrictfilenames'),
                is_id=(k==u'id'))
            template_dict = dict((k, sanitize(k, v)) for k,v in template_dict.items())

            filename = self.params['outtmpl'] % template_dict
            return filename
        except KeyError as err:
            self.report_error(u'Erroneous output template')
            return None
        except ValueError as err:
            self.report_error(u'Insufficient system charset ' + repr(preferredencoding()))
            return None

    def _match_entry(self, info_dict):
        """ Returns None iff the file should be downloaded """

        title = info_dict['title']
        matchtitle = self.params.get('matchtitle', False)
        if matchtitle:
            if not re.search(matchtitle, title, re.IGNORECASE):
                return u'[download] "' + title + '" title did not match pattern "' + matchtitle + '"'
        rejecttitle = self.params.get('rejecttitle', False)
        if rejecttitle:
            if re.search(rejecttitle, title, re.IGNORECASE):
                return u'"' + title + '" title matched reject pattern "' + rejecttitle + '"'
        date = info_dict.get('upload_date', None)
        if date is not None:
            dateRange = self.params.get('daterange', DateRange())
            if date not in dateRange:
                return u'[download] %s upload date is not in range %s' % (date_from_str(date).isoformat(), dateRange)
        return None
        
    def extract_info(self, url, download=True, ie_key=None, extra_info={}):
        '''
        Returns a list with a dictionary for each video we find.
        If 'download', also downloads the videos.
        extra_info is a dict containing the extra values to add to each result
         '''
        
        if ie_key:
            ie = get_info_extractor(ie_key)()
            ie.set_downloader(self)
            ies = [ie]
        else:
            ies = self._ies

        for ie in ies:
            if not ie.suitable(url):
                continue

            if not ie.working():
                self.report_warning(u'The program functionality for this site has been marked as broken, '
                                    u'and will probably not work.')

            try:
                ie_result = ie.extract(url)
                if ie_result is None: # Finished already (backwards compatibility; listformats and friends should be moved here)
                    break
                if isinstance(ie_result, list):
                    # Backwards compatibility: old IE result format
                    for result in ie_result:
                        result.update(extra_info)
                    ie_result = {
                        '_type': 'compat_list',
                        'entries': ie_result,
                    }
                else:
                    ie_result.update(extra_info)
                if 'extractor' not in ie_result:
                    ie_result['extractor'] = ie.IE_NAME
                return self.process_ie_result(ie_result, download=download)
            except ExtractorError as de: # An error we somewhat expected
                self.report_error(compat_str(de), de.format_traceback())
                break
            except Exception as e:
                if self.params.get('ignoreerrors', False):
                    self.report_error(compat_str(e), tb=compat_str(traceback.format_exc()))
                    break
                else:
                    raise
        else:
            self.report_error(u'no suitable InfoExtractor: %s' % url)
        
    def process_ie_result(self, ie_result, download=True, extra_info={}):
        """
        Take the result of the ie(may be modified) and resolve all unresolved
        references (URLs, playlist items).

        It will also download the videos if 'download'.
        Returns the resolved ie_result.
        """

        result_type = ie_result.get('_type', 'video') # If not given we suppose it's a video, support the default old system
        if result_type == 'video':
            if 'playlist' not in ie_result:
                # It isn't part of a playlist
                ie_result['playlist'] = None
                ie_result['playlist_index'] = None
            if download:
                self.process_info(ie_result)
            return ie_result
        elif result_type == 'url':
            # We have to add extra_info to the results because it may be
            # contained in a playlist
            return self.extract_info(ie_result['url'],
                                     download,
                                     ie_key=ie_result.get('ie_key'),
                                     extra_info=extra_info)
        elif result_type == 'playlist':
            # We process each entry in the playlist
            playlist = ie_result.get('title', None) or ie_result.get('id', None)
            self.to_screen(u'[download] Downloading playlist: %s'  % playlist)

            playlist_results = []

            n_all_entries = len(ie_result['entries'])
            playliststart = self.params.get('playliststart', 1) - 1
            playlistend = self.params.get('playlistend', -1)

            if playlistend == -1:
                entries = ie_result['entries'][playliststart:]
            else:
                entries = ie_result['entries'][playliststart:playlistend]

            n_entries = len(entries)

            self.to_screen(u"[%s] playlist '%s': Collected %d video ids (downloading %d of them)" %
                (ie_result['extractor'], playlist, n_all_entries, n_entries))

            for i,entry in enumerate(entries,1):
                self.to_screen(u'[download] Downloading video #%s of %s' %(i, n_entries))
                extra = {
                         'playlist': playlist, 
                         'playlist_index': i + playliststart,
                         }
                if not 'extractor' in entry:
                    # We set the extractor, if it's an url it will be set then to
                    # the new extractor, but if it's already a video we must make
                    # sure it's present: see issue #877
                    entry['extractor'] = ie_result['extractor']
                entry_result = self.process_ie_result(entry,
                                                      download=download,
                                                      extra_info=extra)
                playlist_results.append(entry_result)
            ie_result['entries'] = playlist_results
            return ie_result
        elif result_type == 'compat_list':
            def _fixup(r):
                r.setdefault('extractor', ie_result['extractor'])
                return r
            ie_result['entries'] = [
                self.process_ie_result(_fixup(r), download=download)
                for r in ie_result['entries']
            ]
            return ie_result
        else:
            raise Exception('Invalid result type: %s' % result_type)

    def process_info(self, info_dict):
        """Process a single resolved IE result."""

        assert info_dict.get('_type', 'video') == 'video'
        #We increment the download the download count here to match the previous behaviour.
        self.increment_downloads()

        info_dict['fulltitle'] = info_dict['title']
        if len(info_dict['title']) > 200:
            info_dict['title'] = info_dict['title'][:197] + u'...'

        # Keep for backwards compatibility
        info_dict['stitle'] = info_dict['title']

        if not 'format' in info_dict:
            info_dict['format'] = info_dict['ext']

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
            compat_print(info_dict['title'])
        if self.params.get('forceid', False):
            compat_print(info_dict['id'])
        if self.params.get('forceurl', False):
            compat_print(info_dict['url'])
        if self.params.get('forcethumbnail', False) and 'thumbnail' in info_dict:
            compat_print(info_dict['thumbnail'])
        if self.params.get('forcedescription', False) and 'description' in info_dict:
            compat_print(info_dict['description'])
        if self.params.get('forcefilename', False) and filename is not None:
            compat_print(filename)
        if self.params.get('forceformat', False):
            compat_print(info_dict['format'])

        # Do nothing else if in simulate mode
        if self.params.get('simulate', False):
            return

        if filename is None:
            return

        try:
            dn = os.path.dirname(encodeFilename(filename))
            if dn != '' and not os.path.exists(dn):
                os.makedirs(dn)
        except (OSError, IOError) as err:
            self.report_error(u'unable to create directory ' + compat_str(err))
            return

        if self.params.get('writedescription', False):
            try:
                descfn = filename + u'.description'
                self.report_writedescription(descfn)
                with io.open(encodeFilename(descfn), 'w', encoding='utf-8') as descfile:
                    descfile.write(info_dict['description'])
            except (OSError, IOError):
                self.report_error(u'Cannot write description file ' + descfn)
                return

        if (self.params.get('writesubtitles', False) or self.params.get('writeautomaticsub')) and 'subtitles' in info_dict and info_dict['subtitles']:
            # subtitles download errors are already managed as troubles in relevant IE
            # that way it will silently go on when used with unsupporting IE
            subtitle = info_dict['subtitles'][0]
            (sub_error, sub_lang, sub) = subtitle
            sub_format = self.params.get('subtitlesformat')
            if sub_error:
                self.report_warning("Some error while getting the subtitles")
            else:
                try:
                    sub_filename = filename.rsplit('.', 1)[0] + u'.' + sub_lang + u'.' + sub_format
                    self.report_writesubtitles(sub_filename)
                    with io.open(encodeFilename(sub_filename), 'w', encoding='utf-8') as subfile:
                        subfile.write(sub)
                except (OSError, IOError):
                    self.report_error(u'Cannot write subtitles file ' + descfn)
                    return

        if self.params.get('allsubtitles', False) and 'subtitles' in info_dict and info_dict['subtitles']:
            subtitles = info_dict['subtitles']
            sub_format = self.params.get('subtitlesformat')
            for subtitle in subtitles:
                (sub_error, sub_lang, sub) = subtitle
                if sub_error:
                    self.report_warning("Some error while getting the subtitles")
                else:
                    try:
                        sub_filename = filename.rsplit('.', 1)[0] + u'.' + sub_lang + u'.' + sub_format
                        self.report_writesubtitles(sub_filename)
                        with io.open(encodeFilename(sub_filename), 'w', encoding='utf-8') as subfile:
                                subfile.write(sub)
                    except (OSError, IOError):
                        self.report_error(u'Cannot write subtitles file ' + descfn)
                        return

        if self.params.get('writeinfojson', False):
            infofn = filename + u'.info.json'
            self.report_writeinfojson(infofn)
            try:
                json_info_dict = dict((k, v) for k,v in info_dict.items() if not k in ['urlhandle'])
                write_json_file(json_info_dict, encodeFilename(infofn))
            except (OSError, IOError):
                self.report_error(u'Cannot write metadata to JSON file ' + infofn)
                return

        if self.params.get('writethumbnail', False):
            if 'thumbnail' in info_dict:
                thumb_format = info_dict['thumbnail'].rpartition(u'/')[2].rpartition(u'.')[2]
                if not thumb_format:
                    thumb_format = 'jpg'
                thumb_filename = filename.rpartition('.')[0] + u'.' + thumb_format
                self.to_screen(u'[%s] %s: Downloading thumbnail ...' %
                               (info_dict['extractor'], info_dict['id']))
                uf = compat_urllib_request.urlopen(info_dict['thumbnail'])
                with open(thumb_filename, 'wb') as thumbf:
                    shutil.copyfileobj(uf, thumbf)
                self.to_screen(u'[%s] %s: Writing thumbnail to: %s' %
                               (info_dict['extractor'], info_dict['id'], thumb_filename))

        if not self.params.get('skip_download', False):
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(filename)):
                success = True
            else:
                try:
                    success = self.fd._do_download(filename, info_dict)
                except (OSError, IOError) as err:
                    raise UnavailableVideoError()
                except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                    self.report_error(u'unable to download video data: %s' % str(err))
                    return
                except (ContentTooShortError, ) as err:
                    self.report_error(u'content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded))
                    return

            if success:
                try:
                    self.post_process(filename, info_dict)
                except (PostProcessingError) as err:
                    self.report_error(u'postprocessing: %s' % str(err))
                    return

    def download(self, url_list):
        """Download a given list of URLs."""
        if len(url_list) > 1 and self.fixed_template():
            raise SameFileError(self.params['outtmpl'])

        for url in url_list:
            try:
                #It also downloads the videos
                videos = self.extract_info(url)
            except UnavailableVideoError:
                self.report_error(u'unable to download video')
            except MaxDownloadsReached:
                self.to_screen(u'[info] Maximum number of downloaded files reached.')
                raise

        return self._download_retcode

    def post_process(self, filename, ie_info):
        """Run all the postprocessors on the given file."""
        info = dict(ie_info)
        info['filepath'] = filename
        keep_video = None
        for pp in self._pps:
            try:
                keep_video_wish,new_info = pp.run(info)
                if keep_video_wish is not None:
                    if keep_video_wish:
                        keep_video = keep_video_wish
                    elif keep_video is None:
                        # No clear decision yet, let IE decide
                        keep_video = keep_video_wish
            except PostProcessingError as e:
                self.to_stderr(u'ERROR: ' + e.msg)
        if keep_video is False and not self.params.get('keepvideo', False):
            try:
                self.to_screen(u'Deleting original file %s (pass -k to keep)' % filename)
                os.remove(encodeFilename(filename))
            except (IOError, OSError):
                self.report_warning(u'Unable to remove downloaded video file')
