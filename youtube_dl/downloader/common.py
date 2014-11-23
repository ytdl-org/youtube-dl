from __future__ import unicode_literals

import os
import re
import sys
import time

from ..utils import (
    compat_str,
    encodeFilename,
    format_bytes,
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

    Subclasses of this one must re-define the real_download method.
    """

    _TEST_FILE_SIZE = 10241
    params = None

    def __init__(self, ydl, params):
        """Create a FileDownloader object with the given options."""
        self.ydl = ydl
        self._progress_hooks = []
        self.params = params

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
        if current == 0 or dif < 0.001:  # One millisecond
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
        if bytes == 0 or dif < 0.001:  # One millisecond
            return None
        return float(bytes) / dif

    @staticmethod
    def format_speed(speed):
        if speed is None:
            return '%10s' % '---b/s'
        return '%10s' % ('%s/s' % format_bytes(speed))

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        new_min = max(bytes / 2.0, 1.0)
        new_max = min(max(bytes * 2.0, 1.0), 4194304)  # Do not surpass 4 MB
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
        if self.params.get('nopart', False) or filename == '-' or \
                (os.path.exists(encodeFilename(filename)) and not os.path.isfile(encodeFilename(filename))):
            return filename
        return filename + '.part'

    def undo_temp_name(self, filename):
        if filename.endswith('.part'):
            return filename[:-len('.part')]
        return filename

    def try_rename(self, old_filename, new_filename):
        try:
            if old_filename == new_filename:
                return
            os.rename(encodeFilename(old_filename), encodeFilename(new_filename))
        except (IOError, OSError) as err:
            self.report_error('unable to rename file: %s' % compat_str(err))

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
        self.to_screen('[download] Destination: ' + filename)

    def _report_progress_status(self, msg, is_last_line=False):
        fullmsg = '[download] ' + msg
        if self.params.get('progress_with_newline', False):
            self.to_screen(fullmsg)
        else:
            if os.name == 'nt':
                prev_len = getattr(self, '_report_progress_prev_line_length',
                                   0)
                if prev_len > len(fullmsg):
                    fullmsg += ' ' * (prev_len - len(fullmsg))
                self._report_progress_prev_line_length = len(fullmsg)
                clear_line = '\r'
            else:
                clear_line = ('\r\x1b[K' if sys.stderr.isatty() else '\r')
            self.to_screen(clear_line + fullmsg, skip_eol=not is_last_line)
        self.to_console_title('youtube-dl ' + msg)

    def report_progress(self, percent, data_len_str, speed, eta):
        """Report download progress."""
        if self.params.get('noprogress', False):
            return
        if eta is not None:
            eta_str = self.format_eta(eta)
        else:
            eta_str = 'Unknown ETA'
        if percent is not None:
            percent_str = self.format_percent(percent)
        else:
            percent_str = 'Unknown %'
        speed_str = self.format_speed(speed)

        msg = ('%s of %s at %s ETA %s' %
               (percent_str, data_len_str, speed_str, eta_str))
        self._report_progress_status(msg)

    def report_progress_live_stream(self, downloaded_data_len, speed, elapsed):
        if self.params.get('noprogress', False):
            return
        downloaded_str = format_bytes(downloaded_data_len)
        speed_str = self.format_speed(speed)
        elapsed_str = FileDownloader.format_seconds(elapsed)
        msg = '%s at %s (%s)' % (downloaded_str, speed_str, elapsed_str)
        self._report_progress_status(msg)

    def report_finish(self, data_len_str, tot_time):
        """Report download finished."""
        if self.params.get('noprogress', False):
            self.to_screen('[download] Download completed')
        else:
            self._report_progress_status(
                ('100%% of %s in %s' %
                 (data_len_str, self.format_seconds(tot_time))),
                is_last_line=True)

    def report_resuming_byte(self, resume_len):
        """Report attempt to resume at given byte."""
        self.to_screen('[download] Resuming download at byte %s' % resume_len)

    def report_retry(self, count, retries):
        """Report retry in case of HTTP error 5xx"""
        self.to_screen('[download] Got server HTTP error. Retrying (attempt %d of %d)...' % (count, retries))

    def report_file_already_downloaded(self, file_name):
        """Report file has already been fully downloaded."""
        try:
            self.to_screen('[download] %s has already been downloaded' % file_name)
        except UnicodeEncodeError:
            self.to_screen('[download] The file has already been downloaded')

    def report_unable_to_resume(self):
        """Report it was impossible to resume download."""
        self.to_screen('[download] Unable to resume')

    def download(self, filename, info_dict):
        """Download to a filename using the info from info_dict
        Return True on success and False otherwise
        """
        # Check file already present
        if self.params.get('continuedl', False) and os.path.isfile(encodeFilename(filename)) and not self.params.get('nopart', False):
            self.report_file_already_downloaded(filename)
            self._hook_progress({
                'filename': filename,
                'status': 'finished',
                'total_bytes': os.path.getsize(encodeFilename(filename)),
            })
            return True

        return self.real_download(filename, info_dict)

    def real_download(self, filename, info_dict):
        """Real download process. Redefine in subclasses."""
        raise NotImplementedError('This method must be implemented by subclasses')

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
