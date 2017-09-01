from __future__ import unicode_literals

import errno
import os
import socket
import time
import re

from .common import FileDownloader
from ..compat import compat_urllib_error
from ..utils import (
    ContentTooShortError,
    encodeFilename,
    sanitize_open,
    sanitized_Request,
    write_xattr,
    XAttrMetadataError,
    XAttrUnavailableError,
)


class HttpFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']

        class DownloadContext(dict):
            __getattr__ = dict.get
            __setattr__ = dict.__setitem__
            __delattr__ = dict.__delitem__

        ctx = DownloadContext()
        ctx.filename = filename
        ctx.tmpfilename = self.temp_name(filename)
        ctx.stream = None

        # Do not include the Accept-Encoding header
        headers = {'Youtubedl-no-compression': 'True'}
        add_headers = info_dict.get('http_headers')
        if add_headers:
            headers.update(add_headers)
        basic_request = sanitized_Request(url, None, headers)
        request = sanitized_Request(url, None, headers)

        is_test = self.params.get('test', False)

        if is_test:
            request.add_header('Range', 'bytes=0-%s' % str(self._TEST_FILE_SIZE - 1))

        ctx.open_mode = 'wb'
        ctx.resume_len = 0

        if self.params.get('continuedl', True):
            # Establish possible resume length
            if os.path.isfile(encodeFilename(ctx.tmpfilename)):
                ctx.resume_len = os.path.getsize(encodeFilename(ctx.tmpfilename))

        count = 0
        retries = self.params.get('retries', 0)

        class SucceedDownload(Exception):
            pass

        class RetryDownload(Exception):
            def __init__(self, source_error):
                self.source_error = source_error

        def establish_connection():
            if ctx.resume_len != 0:
                self.report_resuming_byte(ctx.resume_len)
                request.add_header('Range', 'bytes=%d-' % ctx.resume_len)
                ctx.open_mode = 'ab'
            # Establish connection
            try:
                ctx.data = self.ydl.urlopen(request)
                # When trying to resume, Content-Range HTTP header of response has to be checked
                # to match the value of requested Range HTTP header. This is due to a webservers
                # that don't support resuming and serve a whole file with no Content-Range
                # set in response despite of requested Range (see
                # https://github.com/rg3/youtube-dl/issues/6057#issuecomment-126129799)
                if ctx.resume_len > 0:
                    content_range = ctx.data.headers.get('Content-Range')
                    if content_range:
                        content_range_m = re.search(r'bytes (\d+)-', content_range)
                        # Content-Range is present and matches requested Range, resume is possible
                        if content_range_m and ctx.resume_len == int(content_range_m.group(1)):
                            return
                    # Content-Range is either not present or invalid. Assuming remote webserver is
                    # trying to send the whole file, resume is not possible, so wiping the local file
                    # and performing entire redownload
                    self.report_unable_to_resume()
                    ctx.resume_len = 0
                    ctx.open_mode = 'wb'
                return
            except (compat_urllib_error.HTTPError, ) as err:
                if (err.code < 500 or err.code >= 600) and err.code != 416:
                    # Unexpected HTTP error
                    raise
                elif err.code == 416:
                    # Unable to resume (requested range not satisfiable)
                    try:
                        # Open the connection again without the range header
                        ctx.data = self.ydl.urlopen(basic_request)
                        content_length = ctx.data.info()['Content-Length']
                    except (compat_urllib_error.HTTPError, ) as err:
                        if err.code < 500 or err.code >= 600:
                            raise
                    else:
                        # Examine the reported length
                        if (content_length is not None and
                                (ctx.resume_len - 100 < int(content_length) < ctx.resume_len + 100)):
                            # The file had already been fully downloaded.
                            # Explanation to the above condition: in issue #175 it was revealed that
                            # YouTube sometimes adds or removes a few bytes from the end of the file,
                            # changing the file size slightly and causing problems for some users. So
                            # I decided to implement a suggested change and consider the file
                            # completely downloaded if the file size differs less than 100 bytes from
                            # the one in the hard drive.
                            self.report_file_already_downloaded(ctx.filename)
                            self.try_rename(ctx.tmpfilename, ctx.filename)
                            self._hook_progress({
                                'filename': ctx.filename,
                                'status': 'finished',
                                'downloaded_bytes': ctx.resume_len,
                                'total_bytes': ctx.resume_len,
                            })
                            raise SucceedDownload()
                        else:
                            # The length does not match, we start the download over
                            self.report_unable_to_resume()
                            ctx.resume_len = 0
                            ctx.open_mode = 'wb'
                            return
                raise RetryDownload(err)
            except socket.error as err:
                if err.errno != errno.ECONNRESET:
                    # Connection reset is no problem, just retry
                    raise
                raise RetryDownload(err)

        def download():
            data_len = ctx.data.info().get('Content-length', None)

            # Range HTTP header may be ignored/unsupported by a webserver
            # (e.g. extractor/scivee.py, extractor/bambuser.py).
            # However, for a test we still would like to download just a piece of a file.
            # To achieve this we limit data_len to _TEST_FILE_SIZE and manually control
            # block size when downloading a file.
            if is_test and (data_len is None or int(data_len) > self._TEST_FILE_SIZE):
                data_len = self._TEST_FILE_SIZE

            if data_len is not None:
                data_len = int(data_len) + ctx.resume_len
                min_data_len = self.params.get('min_filesize')
                max_data_len = self.params.get('max_filesize')
                if min_data_len is not None and data_len < min_data_len:
                    self.to_screen('\r[download] File is smaller than min-filesize (%s bytes < %s bytes). Aborting.' % (data_len, min_data_len))
                    return False
                if max_data_len is not None and data_len > max_data_len:
                    self.to_screen('\r[download] File is larger than max-filesize (%s bytes > %s bytes). Aborting.' % (data_len, max_data_len))
                    return False

            byte_counter = 0 + ctx.resume_len
            block_size = self.params.get('buffersize', 1024)
            start = time.time()

            # measure time over whole while-loop, so slow_down() and best_block_size() work together properly
            now = None  # needed for slow_down() in the first loop run
            before = start  # start measuring

            def retry(e):
                if ctx.tmpfilename != '-':
                    ctx.stream.close()
                ctx.stream = None
                ctx.resume_len = os.path.getsize(encodeFilename(ctx.tmpfilename))
                raise RetryDownload(e)

            while True:
                try:
                    # Download and write
                    data_block = ctx.data.read(block_size if not is_test else min(block_size, data_len - byte_counter))
                # socket.timeout is a subclass of socket.error but may not have
                # errno set
                except socket.timeout as e:
                    retry(e)
                except socket.error as e:
                    if e.errno not in (errno.ECONNRESET, errno.ETIMEDOUT):
                        raise
                    retry(e)

                byte_counter += len(data_block)

                # exit loop when download is finished
                if len(data_block) == 0:
                    break

                # Open destination file just in time
                if ctx.stream is None:
                    try:
                        ctx.stream, ctx.tmpfilename = sanitize_open(
                            ctx.tmpfilename, ctx.open_mode)
                        assert ctx.stream is not None
                        ctx.filename = self.undo_temp_name(ctx.tmpfilename)
                        self.report_destination(ctx.filename)
                    except (OSError, IOError) as err:
                        self.report_error('unable to open for writing: %s' % str(err))
                        return False

                    if self.params.get('xattr_set_filesize', False) and data_len is not None:
                        try:
                            write_xattr(ctx.tmpfilename, 'user.ytdl.filesize', str(data_len).encode('utf-8'))
                        except (XAttrUnavailableError, XAttrMetadataError) as err:
                            self.report_error('unable to set filesize xattr: %s' % str(err))

                try:
                    ctx.stream.write(data_block)
                except (IOError, OSError) as err:
                    self.to_stderr('\n')
                    self.report_error('unable to write data: %s' % str(err))
                    return False

                # Apply rate limit
                self.slow_down(start, now, byte_counter - ctx.resume_len)

                # end measuring of one loop run
                now = time.time()
                after = now

                # Adjust block size
                if not self.params.get('noresizebuffer', False):
                    block_size = self.best_block_size(after - before, len(data_block))

                before = after

                # Progress message
                speed = self.calc_speed(start, now, byte_counter - ctx.resume_len)
                if data_len is None:
                    eta = None
                else:
                    eta = self.calc_eta(start, time.time(), data_len - ctx.resume_len, byte_counter - ctx.resume_len)

                self._hook_progress({
                    'status': 'downloading',
                    'downloaded_bytes': byte_counter,
                    'total_bytes': data_len,
                    'tmpfilename': ctx.tmpfilename,
                    'filename': ctx.filename,
                    'eta': eta,
                    'speed': speed,
                    'elapsed': now - start,
                })

                if is_test and byte_counter == data_len:
                    break

            if ctx.stream is None:
                self.to_stderr('\n')
                self.report_error('Did not get any data blocks')
                return False
            if ctx.tmpfilename != '-':
                ctx.stream.close()

            if data_len is not None and byte_counter != data_len:
                err = ContentTooShortError(byte_counter, int(data_len))
                if count <= retries:
                    retry(err)
                raise err

            self.try_rename(ctx.tmpfilename, ctx.filename)

            # Update file modification time
            if self.params.get('updatetime', True):
                info_dict['filetime'] = self.try_utime(ctx.filename, ctx.data.info().get('last-modified', None))

            self._hook_progress({
                'downloaded_bytes': byte_counter,
                'total_bytes': byte_counter,
                'filename': ctx.filename,
                'status': 'finished',
                'elapsed': time.time() - start,
            })

            return True

        while count <= retries:
            try:
                establish_connection()
                download()
                return True
            except RetryDownload as e:
                count += 1
                if count <= retries:
                    self.report_retry(e.source_error, count, retries)
                continue
            except SucceedDownload:
                return True

        self.report_error('giving up after %s retries' % retries)
        return False
