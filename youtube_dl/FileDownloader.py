import math
import os
import re
import subprocess
import sys
import time

from .utils import (
    compat_urllib_error,
    compat_urllib_request,
    ContentTooShortError,
    determine_ext,
    encodeFilename,
    sanitize_open,
    timeconvert,
)


class FileDownloader(object):
    """File Downloader class.

    File downloader objects are the ones responsible of downloading the
    actual video file and writing it to disk.

    File downloaders accept a lot of parameters. In order not to saturate
    the object constructor with arguments, it receives a dictionary of
    options instead.

    Available options:

    verbose:           Print additional info to stdout.
    quiet:             Do not print messages to stdout.
    ratelimit:         Download speed limit, in bytes/sec.
    retries:           Number of times to retry for HTTP error 5xx
    buffersize:        Size of download buffer in bytes.
    noresizebuffer:    Do not automatically resize the download buffer.
    continuedl:        Try to continue downloads if possible.
    noprogress:        Do not print the progress bar.
    logtostderr:       Log messages to stderr instead of stdout.
    consoletitle:      Display progress in console window's titlebar.
    nopart:            Do not use temporary .part files.
    updatetime:        Use the Last-modified header to set output file timestamps.
    test:              Download only first bytes to test the downloader.
    min_filesize:      Skip files smaller than this size
    max_filesize:      Skip files larger than this size
    """

    params = None

    def __init__(self, ydl, params):
        """Create a FileDownloader object with the given options."""
        self.ydl = ydl
        self._progress_hooks = []
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
            exponent = int(math.log(bytes, 1024.0))
        suffix = ['B','KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'][exponent]
        converted = float(bytes) / float(1024 ** exponent)
        return '%.2f%s' % (converted, suffix)

    @staticmethod
    def format_seconds(seconds):
        (mins, secs) = divmod(seconds, 60)
        (hours, mins) = divmod(mins, 60)
        if hours > 99:
            return '--:--:--'
        if hours == 0:
            return '%02d:%02d' % (mins, secs)
        else:
            return '%02d:%02d:%02d' % (hours, mins, secs)

    @staticmethod
    def calc_percent(byte_counter, data_len):
        if data_len is None:
            return None
        return float(byte_counter) / float(data_len) * 100.0

    @staticmethod
    def format_percent(percent):
        if percent is None:
            return '---.-%'
        return '%6s' % ('%3.1f%%' % percent)

    @staticmethod
    def calc_eta(start, now, total, current):
        if total is None:
            return None
        dif = now - start
        if current == 0 or dif < 0.001: # One millisecond
            return None
        rate = float(current) / dif
        return int((float(total) - float(current)) / rate)

    @staticmethod
    def format_eta(eta):
        if eta is None:
            return '--:--'
        return FileDownloader.format_seconds(eta)

    @staticmethod
    def calc_speed(start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001: # One millisecond
            return None
        return float(bytes) / dif

    @staticmethod
    def format_speed(speed):
        if speed is None:
            return '%10s' % '---b/s'
        return '%10s' % ('%s/s' % FileDownloader.format_bytes(speed))

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
        """Parse a string indicating a byte quantity into an integer."""
        matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]?)$', bytestr)
        if matchobj is None:
            return None
        number = float(matchobj.group(1))
        multiplier = 1024.0 ** 'bkmgtpezy'.index(matchobj.group(2).lower())
        return int(round(number * multiplier))

    def to_screen(self, *args, **kargs):
        self.ydl.to_screen(*args, **kargs)

    def to_stderr(self, message):
        self.ydl.to_screen(message)

    def to_console_title(self, message):
        self.ydl.to_console_title(message)

    def trouble(self, *args, **kargs):
        self.ydl.trouble(*args, **kargs)

    def report_warning(self, *args, **kargs):
        self.ydl.report_warning(*args, **kargs)

    def report_error(self, *args, **kargs):
        self.ydl.report_error(*args, **kargs)

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
        except (IOError, OSError):
            self.report_error(u'unable to rename file')

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
        # Ignore obviously invalid dates
        if filetime == 0:
            return
        try:
            os.utime(filename, (time.time(), filetime))
        except:
            pass
        return filetime

    def report_destination(self, filename):
        """Report destination filename."""
        self.to_screen(u'[download] Destination: ' + filename)

    def report_progress(self, percent, data_len_str, speed, eta):
        """Report download progress."""
        if self.params.get('noprogress', False):
            return
        clear_line = (u'\x1b[K' if sys.stderr.isatty() and os.name != 'nt' else u'')
        if eta is not None:
            eta_str = self.format_eta(eta)
        else:
            eta_str = 'Unknown ETA'
        if percent is not None:
            percent_str = self.format_percent(percent)
        else:
            percent_str = 'Unknown %'
        speed_str = self.format_speed(speed)
        if self.params.get('progress_with_newline', False):
            self.to_screen(u'[download] %s of %s at %s ETA %s' %
                (percent_str, data_len_str, speed_str, eta_str))
        else:
            self.to_screen(u'\r%s[download] %s of %s at %s ETA %s' %
                (clear_line, percent_str, data_len_str, speed_str, eta_str), skip_eol=True)
        self.to_console_title(u'youtube-dl - %s of %s at %s ETA %s' %
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
        except UnicodeEncodeError:
            self.to_screen(u'[download] The file has already been downloaded')

    def report_unable_to_resume(self):
        """Report it was impossible to resume download."""
        self.to_screen(u'[download] Unable to resume')

    def report_finish(self, data_len_str, tot_time):
        """Report download finished."""
        if self.params.get('noprogress', False):
            self.to_screen(u'[download] Download completed')
        else:
            clear_line = (u'\x1b[K' if sys.stderr.isatty() and os.name != 'nt' else u'')
            self.to_screen(u'\r%s[download] 100%% of %s in %s' %
                (clear_line, data_len_str, self.format_seconds(tot_time)))

    def _download_with_rtmpdump(self, filename, url, player_url, page_url, play_path, tc_url, live):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        test = self.params.get('test', False)

        # Check for rtmpdump first
        try:
            subprocess.call(['rtmpdump', '-h'], stdout=(open(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
        except (OSError, IOError):
            self.report_error(u'RTMP download detected but "rtmpdump" could not be run')
            return False
        verbosity_option = '--verbose' if self.params.get('verbose', False) else '--quiet'

        # Download using rtmpdump. rtmpdump returns exit code 2 when
        # the connection was interrumpted and resuming appears to be
        # possible. This is part of rtmpdump's normal usage, AFAIK.
        basic_args = ['rtmpdump', verbosity_option, '-r', url, '-o', tmpfilename]
        if player_url is not None:
            basic_args += ['--swfVfy', player_url]
        if page_url is not None:
            basic_args += ['--pageUrl', page_url]
        if play_path is not None:
            basic_args += ['--playpath', play_path]
        if tc_url is not None:
            basic_args += ['--tcUrl', url]
        if test:
            basic_args += ['--stop', '1']
        if live:
            basic_args += ['--live']
        args = basic_args + [[], ['--resume', '--skip', '1']][self.params.get('continuedl', False)]
        if self.params.get('verbose', False):
            try:
                import pipes
                shell_quote = lambda args: ' '.join(map(pipes.quote, args))
            except ImportError:
                shell_quote = repr
            self.to_screen(u'[debug] rtmpdump command line: ' + shell_quote(args))
        retval = subprocess.call(args)
        while (retval == 2 or retval == 1) and not test:
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
        if retval == 0 or (test and retval == 2):
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen(u'\r[rtmpdump] %s bytes' % fsize)
            self.try_rename(tmpfilename, filename)
            self._hook_progress({
                'downloaded_bytes': fsize,
                'total_bytes': fsize,
                'filename': filename,
                'status': 'finished',
            })
            return True
        else:
            self.to_stderr(u"\n")
            self.report_error(u'rtmpdump exited with code %d' % retval)
            return False

    def _download_with_mplayer(self, filename, url):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        args = ['mplayer', '-really-quiet', '-vo', 'null', '-vc', 'dummy', '-dumpstream', '-dumpfile', tmpfilename, url]
        # Check for mplayer first
        try:
            subprocess.call(['mplayer', '-h'], stdout=(open(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
        except (OSError, IOError):
            self.report_error(u'MMS or RTSP download detected but "%s" could not be run' % args[0] )
            return False

        # Download using mplayer. 
        retval = subprocess.call(args)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen(u'\r[%s] %s bytes' % (args[0], fsize))
            self.try_rename(tmpfilename, filename)
            self._hook_progress({
                'downloaded_bytes': fsize,
                'total_bytes': fsize,
                'filename': filename,
                'status': 'finished',
            })
            return True
        else:
            self.to_stderr(u"\n")
            self.report_error(u'mplayer exited with code %d' % retval)
            return False

    def _download_m3u8_with_ffmpeg(self, filename, url):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        args = ['-y', '-i', url, '-f', 'mp4', '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc', tmpfilename]

        for program in ['avconv', 'ffmpeg']:
            try:
                subprocess.call([program, '-version'], stdout=(open(os.path.devnull, 'w')), stderr=subprocess.STDOUT)
                break
            except (OSError, IOError):
                pass
        else:
            self.report_error(u'm3u8 download detected but ffmpeg or avconv could not be found')
        cmd = [program] + args

        retval = subprocess.call(cmd)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen(u'\r[%s] %s bytes' % (args[0], fsize))
            self.try_rename(tmpfilename, filename)
            self._hook_progress({
                'downloaded_bytes': fsize,
                'total_bytes': fsize,
                'filename': filename,
                'status': 'finished',
            })
            return True
        else:
            self.to_stderr(u"\n")
            self.report_error(u'ffmpeg exited with code %d' % retval)
            return False


    def _do_download(self, filename, info_dict):
        url = info_dict['url']

        # Check file already present
        if self.params.get('continuedl', False) and os.path.isfile(encodeFilename(filename)) and not self.params.get('nopart', False):
            self.report_file_already_downloaded(filename)
            self._hook_progress({
                'filename': filename,
                'status': 'finished',
                'total_bytes': os.path.getsize(encodeFilename(filename)),
            })
            return True

        # Attempt to download using rtmpdump
        if url.startswith('rtmp'):
            return self._download_with_rtmpdump(filename, url,
                                                info_dict.get('player_url', None),
                                                info_dict.get('page_url', None),
                                                info_dict.get('play_path', None),
                                                info_dict.get('tc_url', None),
                                                info_dict.get('rtmp_live', False))

        # Attempt to download using mplayer
        if url.startswith('mms') or url.startswith('rtsp'):
            return self._download_with_mplayer(filename, url)

        # m3u8 manifest are downloaded with ffmpeg
        if determine_ext(url) == u'm3u8':
            return self._download_m3u8_with_ffmpeg(filename, url)

        tmpfilename = self.temp_name(filename)
        stream = None

        # Do not include the Accept-Encoding header
        headers = {'Youtubedl-no-compression': 'True'}
        if 'user_agent' in info_dict:
            headers['Youtubedl-user-agent'] = info_dict['user_agent']
        basic_request = compat_urllib_request.Request(url, None, headers)
        request = compat_urllib_request.Request(url, None, headers)

        if self.params.get('test', False):
            request.add_header('Range','bytes=0-10240')

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
                data = compat_urllib_request.urlopen(request)
                break
            except (compat_urllib_error.HTTPError, ) as err:
                if (err.code < 500 or err.code >= 600) and err.code != 416:
                    # Unexpected HTTP error
                    raise
                elif err.code == 416:
                    # Unable to resume (requested range not satisfiable)
                    try:
                        # Open the connection again without the range header
                        data = compat_urllib_request.urlopen(basic_request)
                        content_length = data.info()['Content-Length']
                    except (compat_urllib_error.HTTPError, ) as err:
                        if err.code < 500 or err.code >= 600:
                            raise
                    else:
                        # Examine the reported length
                        if (content_length is not None and
                                (resume_len - 100 < int(content_length) < resume_len + 100)):
                            # The file had already been fully downloaded.
                            # Explanation to the above condition: in issue #175 it was revealed that
                            # YouTube sometimes adds or removes a few bytes from the end of the file,
                            # changing the file size slightly and causing problems for some users. So
                            # I decided to implement a suggested change and consider the file
                            # completely downloaded if the file size differs less than 100 bytes from
                            # the one in the hard drive.
                            self.report_file_already_downloaded(filename)
                            self.try_rename(tmpfilename, filename)
                            self._hook_progress({
                                'filename': filename,
                                'status': 'finished',
                            })
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
            self.report_error(u'giving up after %s retries' % retries)
            return False

        data_len = data.info().get('Content-length', None)
        if data_len is not None:
            data_len = int(data_len) + resume_len
            min_data_len = self.params.get("min_filesize", None)
            max_data_len =  self.params.get("max_filesize", None)
            if min_data_len is not None and data_len < min_data_len:
                self.to_screen(u'\r[download] File is smaller than min-filesize (%s bytes < %s bytes). Aborting.' % (data_len, min_data_len))
                return False
            if max_data_len is not None and data_len > max_data_len:
                self.to_screen(u'\r[download] File is larger than max-filesize (%s bytes > %s bytes). Aborting.' % (data_len, max_data_len))
                return False

        data_len_str = self.format_bytes(data_len)
        byte_counter = 0 + resume_len
        block_size = self.params.get('buffersize', 1024)
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
                except (OSError, IOError) as err:
                    self.report_error(u'unable to open for writing: %s' % str(err))
                    return False
            try:
                stream.write(data_block)
            except (IOError, OSError) as err:
                self.to_stderr(u"\n")
                self.report_error(u'unable to write data: %s' % str(err))
                return False
            if not self.params.get('noresizebuffer', False):
                block_size = self.best_block_size(after - before, len(data_block))

            # Progress message
            speed = self.calc_speed(start, time.time(), byte_counter - resume_len)
            if data_len is None:
                eta = percent = None
            else:
                percent = self.calc_percent(byte_counter, data_len)
                eta = self.calc_eta(start, time.time(), data_len - resume_len, byte_counter - resume_len)
            self.report_progress(percent, data_len_str, speed, eta)

            self._hook_progress({
                'downloaded_bytes': byte_counter,
                'total_bytes': data_len,
                'tmpfilename': tmpfilename,
                'filename': filename,
                'status': 'downloading',
                'eta': eta,
                'speed': speed,
            })

            # Apply rate limit
            self.slow_down(start, byte_counter - resume_len)

        if stream is None:
            self.to_stderr(u"\n")
            self.report_error(u'Did not get any data blocks')
            return False
        stream.close()
        self.report_finish(data_len_str, (time.time() - start))
        if data_len is not None and byte_counter != data_len:
            raise ContentTooShortError(byte_counter, int(data_len))
        self.try_rename(tmpfilename, filename)

        # Update file modification time
        if self.params.get('updatetime', True):
            info_dict['filetime'] = self.try_utime(filename, data.info().get('last-modified', None))

        self._hook_progress({
            'downloaded_bytes': byte_counter,
            'total_bytes': byte_counter,
            'filename': filename,
            'status': 'finished',
        })

        return True

    def _hook_progress(self, status):
        for ph in self._progress_hooks:
            ph(status)

    def add_progress_hook(self, ph):
        """ ph gets called on download progress, with a dictionary with the entries
        * filename: The final filename
        * status: One of "downloading" and "finished"

        It can also have some of the following entries:

        * downloaded_bytes: Bytes on disks
        * total_bytes: Total bytes, None if unknown
        * tmpfilename: The filename we're currently writing to
        * eta: The estimated time in seconds, None if unknown
        * speed: The download speed in bytes/second, None if unknown

        Hooks are guaranteed to be called at least once (with status "finished")
        if the download is successful.
        """
        self._progress_hooks.append(ph)
