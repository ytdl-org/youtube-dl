#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import errno
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
    writeannotations:  Write the video annotations to a .annotations.xml file
    writethumbnail:    Write the thumbnail image to a file
    writesubtitles:    Write the video subtitles to a file
    writeautomaticsub: Write the automatic subtitles to a file
    allsubtitles:      Downloads all the subtitles of the video
                       (requires writesubtitles or writeautomaticsub)
    listsubtitles:     Lists all available subtitles for the video
    subtitlesformat:   Subtitle format [srt/sbv/vtt] (default=srt)
    subtitleslangs:    List of languages of the subtitles to download
    keepvideo:         Keep the video file after post-processing
    daterange:         A DateRange object, download only if the upload_date is in the range.
    skip_download:     Skip the actual download of the video file
    cachedir:          Location of the cache files in the filesystem.
                       None to disable filesystem cache.
    noplaylist:        Download single video instead of a playlist if in doubt.
    age_limit:         An integer representing the user's age in years.
                       Unsuitable videos for the given age are skipped.
    downloadarchive:   File name of a file where all downloads are recorded.
                       Videos already present in the file are not downloaded
                       again.

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
        self._ies_instances = {}
        self._pps = []
        self._progress_hooks = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]

        if (sys.version_info >= (3,) and sys.platform != 'win32' and
                sys.getfilesystemencoding() in ['ascii', 'ANSI_X3.4-1968']
                and not params['restrictfilenames']):
            # On Python 3, the Unicode filesystem API will throw errors (#1474)
            self.report_warning(
                u'Assuming --restrict-filenames since file system encoding '
                u'cannot encode all charactes. '
                u'Set the LC_ALL environment variable to fix this.')
            params['restrictfilenames'] = True

        self.params = params
        self.fd = FileDownloader(self, self.params)

        if '%(stitle)s' in self.params['outtmpl']:
            self.report_warning(u'%(stitle)s is deprecated. Use the %(title)s and the --restrict-filenames flag(which also secures %(uploader)s et al) instead.')

    def add_info_extractor(self, ie):
        """Add an InfoExtractor object to the end of the list."""
        self._ies.append(ie)
        self._ies_instances[ie.ie_key()] = ie
        ie.set_downloader(self)

    def get_info_extractor(self, ie_key):
        """
        Get an instance of an IE with name ie_key, it will try to get one from
        the _ies list, if there's no instance it will create a new one and add
        it to the extractor list.
        """
        ie = self._ies_instances.get(ie_key)
        if ie is None:
            ie = get_info_extractor(ie_key)()
            self.add_info_extractor(ie)
        return ie

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
        if not self.params.get('quiet', False):
            terminator = [u'\n', u''][skip_eol]
            output = message + terminator
            write_string(output, self._screen_file)

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
            _msg_header = u'\033[0;33mWARNING:\033[0m'
        else:
            _msg_header = u'WARNING:'
        warning_message = u'%s %s' % (_msg_header, message)
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

    def report_writedescription(self, descfn):
        """ Report that the description file is being written """
        self.to_screen(u'[info] Writing video description to: ' + descfn)

    def report_writesubtitles(self, sub_filename):
        """ Report that the subtitles file is being written """
        self.to_screen(u'[info] Writing video subtitles to: ' + sub_filename)

    def report_writeinfojson(self, infofn):
        """ Report that the metadata file has been written """
        self.to_screen(u'[info] Video description metadata as JSON to: ' + infofn)

    def report_writeannotations(self, annofn):
        """ Report that the annotations file has been written. """
        self.to_screen(u'[info] Writing video annotations to: ' + annofn)

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
            if template_dict.get('playlist_index') is not None:
                template_dict['playlist_index'] = u'%05d' % template_dict['playlist_index']

            sanitize = lambda k, v: sanitize_filename(
                u'NA' if v is None else compat_str(v),
                restricted=self.params.get('restrictfilenames'),
                is_id=(k == u'id'))
            template_dict = dict((k, sanitize(k, v))
                                 for k, v in template_dict.items())

            tmpl = os.path.expanduser(self.params['outtmpl'])
            filename = tmpl % template_dict
            return filename
        except KeyError as err:
            self.report_error(u'Erroneous output template')
            return None
        except ValueError as err:
            self.report_error(u'Error in output template: ' + str(err) + u' (encoding: ' + repr(preferredencoding()) + ')')
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
        age_limit = self.params.get('age_limit')
        if age_limit is not None:
            if age_limit < info_dict.get('age_limit', 0):
                return u'Skipping "' + title + '" because it is age restricted'
        if self.in_download_archive(info_dict):
            return (u'%(title)s has already been recorded in archive'
                    % info_dict)
        return None

    @staticmethod
    def add_extra_info(info_dict, extra_info):
        '''Set the keys from extra_info in info dict if they are missing'''
        for key, value in extra_info.items():
            info_dict.setdefault(key, value)

    def extract_info(self, url, download=True, ie_key=None, extra_info={}):
        '''
        Returns a list with a dictionary for each video we find.
        If 'download', also downloads the videos.
        extra_info is a dict containing the extra values to add to each result
         '''

        if ie_key:
            ies = [self.get_info_extractor(ie_key)]
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
                    ie_result = {
                        '_type': 'compat_list',
                        'entries': ie_result,
                    }
                self.add_extra_info(ie_result,
                    {
                        'extractor': ie.IE_NAME,
                        'webpage_url': url,
                        'extractor_key': ie.ie_key(),
                    })
                return self.process_ie_result(ie_result, download, extra_info)
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
            self.add_extra_info(ie_result, extra_info)
            return self.process_video_result(ie_result)
        elif result_type == 'url':
            # We have to add extra_info to the results because it may be
            # contained in a playlist
            return self.extract_info(ie_result['url'],
                                     download,
                                     ie_key=ie_result.get('ie_key'),
                                     extra_info=extra_info)
        elif result_type == 'playlist':
            self.add_extra_info(ie_result, extra_info)
            # We process each entry in the playlist
            playlist = ie_result.get('title', None) or ie_result.get('id', None)
            self.to_screen(u'[download] Downloading playlist: %s' % playlist)

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

            for i, entry in enumerate(entries, 1):
                self.to_screen(u'[download] Downloading video #%s of %s' % (i, n_entries))
                extra = {
                    'playlist': playlist,
                    'playlist_index': i + playliststart,
                    'extractor': ie_result['extractor'],
                    'webpage_url': ie_result['webpage_url'],
                    'extractor_key': ie_result['extractor_key'],
                }
                entry_result = self.process_ie_result(entry,
                                                      download=download,
                                                      extra_info=extra)
                playlist_results.append(entry_result)
            ie_result['entries'] = playlist_results
            return ie_result
        elif result_type == 'compat_list':
            def _fixup(r):
                self.add_extra_info(r,
                    {
                        'extractor': ie_result['extractor'],
                        'webpage_url': ie_result['webpage_url'],
                        'extractor_key': ie_result['extractor_key'],
                    })
                return r
            ie_result['entries'] = [
                self.process_ie_result(_fixup(r), download, extra_info)
                for r in ie_result['entries']
            ]
            return ie_result
        else:
            raise Exception('Invalid result type: %s' % result_type)

    def select_format(self, format_spec, available_formats):
        if format_spec == 'best' or format_spec is None:
            return available_formats[-1]
        elif format_spec == 'worst':
            return available_formats[0]
        else:
            extensions = [u'mp4', u'flv', u'webm', u'3gp']
            if format_spec in extensions:
                filter_f = lambda f: f['ext'] == format_spec
            else:
                filter_f = lambda f: f['format_id'] == format_spec
            matches = list(filter(filter_f, available_formats))
            if matches:
                return matches[-1]
        return None

    def process_video_result(self, info_dict, download=True):
        assert info_dict.get('_type', 'video') == 'video'

        if 'playlist' not in info_dict:
            # It isn't part of a playlist
            info_dict['playlist'] = None
            info_dict['playlist_index'] = None

        # This extractors handle format selection themselves
        if info_dict['extractor'] in [u'youtube', u'Youku']:
            if download:
                self.process_info(info_dict)
            return info_dict

        # We now pick which formats have to be downloaded
        if info_dict.get('formats') is None:
            # There's only one format available
            formats = [info_dict]
        else:
            formats = info_dict['formats']

        # We check that all the formats have the format and format_id fields
        for (i, format) in enumerate(formats):
            if format.get('format_id') is None:
                format['format_id'] = compat_str(i)
            if format.get('format') is None:
                format['format'] = u'{id} - {res}{note}'.format(
                    id=format['format_id'],
                    res=self.format_resolution(format),
                    note=u' ({0})'.format(format['format_note']) if format.get('format_note') is not None else '',
                )
            # Automatically determine file extension if missing
            if 'ext' not in format:
                format['ext'] = determine_ext(format['url'])

        if self.params.get('listformats', None):
            self.list_formats(info_dict)
            return

        format_limit = self.params.get('format_limit', None)
        if format_limit:
            formats = list(takewhile_inclusive(
                lambda f: f['format_id'] != format_limit, formats
            ))
        if self.params.get('prefer_free_formats'):
            def _free_formats_key(f):
                try:
                    ext_ord = [u'flv', u'mp4', u'webm'].index(f['ext'])
                except ValueError:
                    ext_ord = -1
                # We only compare the extension if they have the same height and width
                return (f.get('height'), f.get('width'), ext_ord)
            formats = sorted(formats, key=_free_formats_key)

        req_format = self.params.get('format', 'best')
        if req_format is None:
            req_format = 'best'
        formats_to_download = []
        # The -1 is for supporting YoutubeIE
        if req_format in ('-1', 'all'):
            formats_to_download = formats
        else:
            # We can accept formats requestd in the format: 34/5/best, we pick
            # the first that is available, starting from left
            req_formats = req_format.split('/')
            for rf in req_formats:
                selected_format = self.select_format(rf, formats)
                if selected_format is not None:
                    formats_to_download = [selected_format]
                    break
        if not formats_to_download:
            raise ExtractorError(u'requested format not available',
                                 expected=True)

        if download:
            if len(formats_to_download) > 1:
                self.to_screen(u'[info] %s: downloading video in %s formats' % (info_dict['id'], len(formats_to_download)))
            for format in formats_to_download:
                new_info = dict(info_dict)
                new_info.update(format)
                self.process_info(new_info)
        # We update the info dict with the best quality format (backwards compatibility)
        info_dict.update(formats_to_download[-1])
        return info_dict

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
            # For RTMP URLs, also include the playpath
            compat_print(info_dict['url'] + info_dict.get('play_path', u''))
        if self.params.get('forcethumbnail', False) and info_dict.get('thumbnail') is not None:
            compat_print(info_dict['thumbnail'])
        if self.params.get('forcedescription', False) and info_dict.get('description') is not None:
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
            except (KeyError, TypeError):
                self.report_warning(u'There\'s no description to write.')
            except (OSError, IOError):
                self.report_error(u'Cannot write description file ' + descfn)
                return

        if self.params.get('writeannotations', False):
            try:
                annofn = filename + u'.annotations.xml'
                self.report_writeannotations(annofn)
                with io.open(encodeFilename(annofn), 'w', encoding='utf-8') as annofile:
                    annofile.write(info_dict['annotations'])
            except (KeyError, TypeError):
                self.report_warning(u'There are no annotations to write.')
            except (OSError, IOError):
                self.report_error(u'Cannot write annotations file: ' + annofn)
                return

        subtitles_are_requested = any([self.params.get('writesubtitles', False),
                                       self.params.get('writeautomaticsub')])

        if subtitles_are_requested and 'subtitles' in info_dict and info_dict['subtitles']:
            # subtitles download errors are already managed as troubles in relevant IE
            # that way it will silently go on when used with unsupporting IE
            subtitles = info_dict['subtitles']
            sub_format = self.params.get('subtitlesformat')
            for sub_lang in subtitles.keys():
                sub = subtitles[sub_lang]
                if sub is None:
                    continue
                try:
                    sub_filename = subtitles_filename(filename, sub_lang, sub_format)
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
                json_info_dict = dict((k, v) for k, v in info_dict.items() if not k in ['urlhandle'])
                write_json_file(json_info_dict, encodeFilename(infofn))
            except (OSError, IOError):
                self.report_error(u'Cannot write metadata to JSON file ' + infofn)
                return

        if self.params.get('writethumbnail', False):
            if info_dict.get('thumbnail') is not None:
                thumb_format = determine_ext(info_dict['thumbnail'], u'jpg')
                thumb_filename = filename.rpartition('.')[0] + u'.' + thumb_format
                self.to_screen(u'[%s] %s: Downloading thumbnail ...' %
                               (info_dict['extractor'], info_dict['id']))
                try:
                    uf = compat_urllib_request.urlopen(info_dict['thumbnail'])
                    with open(thumb_filename, 'wb') as thumbf:
                        shutil.copyfileobj(uf, thumbf)
                    self.to_screen(u'[%s] %s: Writing thumbnail to: %s' %
                        (info_dict['extractor'], info_dict['id'], thumb_filename))
                except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                    self.report_warning(u'Unable to download thumbnail "%s": %s' %
                        (info_dict['thumbnail'], compat_str(err)))

        if not self.params.get('skip_download', False):
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(filename)):
                success = True
            else:
                try:
                    success = self.fd._do_download(filename, info_dict)
                except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                    self.report_error(u'unable to download video data: %s' % str(err))
                    return
                except (OSError, IOError) as err:
                    raise UnavailableVideoError(err)
                except (ContentTooShortError, ) as err:
                    self.report_error(u'content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded))
                    return

            if success:
                try:
                    self.post_process(filename, info_dict)
                except (PostProcessingError) as err:
                    self.report_error(u'postprocessing: %s' % str(err))
                    return

        self.record_download_archive(info_dict)

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
                keep_video_wish, new_info = pp.run(info)
                if keep_video_wish is not None:
                    if keep_video_wish:
                        keep_video = keep_video_wish
                    elif keep_video is None:
                        # No clear decision yet, let IE decide
                        keep_video = keep_video_wish
            except PostProcessingError as e:
                self.report_error(e.msg)
        if keep_video is False and not self.params.get('keepvideo', False):
            try:
                self.to_screen(u'Deleting original file %s (pass -k to keep)' % filename)
                os.remove(encodeFilename(filename))
            except (IOError, OSError):
                self.report_warning(u'Unable to remove downloaded video file')

    def in_download_archive(self, info_dict):
        fn = self.params.get('download_archive')
        if fn is None:
            return False
        vid_id = info_dict['extractor'] + u' ' + info_dict['id']
        try:
            with locked_file(fn, 'r', encoding='utf-8') as archive_file:
                for line in archive_file:
                    if line.strip() == vid_id:
                        return True
        except IOError as ioe:
            if ioe.errno != errno.ENOENT:
                raise
        return False

    def record_download_archive(self, info_dict):
        fn = self.params.get('download_archive')
        if fn is None:
            return
        vid_id = info_dict['extractor'] + u' ' + info_dict['id']
        with locked_file(fn, 'a', encoding='utf-8') as archive_file:
            archive_file.write(vid_id + u'\n')

    @staticmethod
    def format_resolution(format, default='unknown'):
        if format.get('_resolution') is not None:
            return format['_resolution']
        if format.get('height') is not None:
            if format.get('width') is not None:
                res = u'%sx%s' % (format['width'], format['height'])
            else:
                res = u'%sp' % format['height']
        else:
            res = default
        return res

    def list_formats(self, info_dict):
        def line(format):
            return (u'%-20s%-10s%-12s%s' % (
                format['format_id'],
                format['ext'],
                self.format_resolution(format),
                format.get('format_note', ''),
                )
            )

        formats = info_dict.get('formats', [info_dict])
        formats_s = list(map(line, formats))
        if len(formats) > 1:
            formats_s[0] += (' ' if formats[0].get('format_note') else '') + '(worst)'
            formats_s[-1] += (' ' if formats[-1].get('format_note') else '') + '(best)'

        header_line = line({
            'format_id': u'format code', 'ext': u'extension',
            '_resolution': u'resolution', 'format_note': u'note'})
        self.to_screen(u'[info] Available formats for %s:\n%s\n%s' %
                       (info_dict['id'], header_line, u"\n".join(formats_s)))
