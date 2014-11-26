from __future__ import unicode_literals

import os
import time

from .common import FileDownloader
from ..utils import (
    compat_urllib_request,
    compat_urllib_error,
    ContentTooShortError,

    encodeFilename,
    sanitize_open,
    format_bytes,
)


class HttpFD(FileDownloader):
    def real_download(self, filename, info_dict):
        url = info_dict['url']
        tmpfilename = self.temp_name(filename)
        stream = None

        # Do not include the Accept-Encoding header
        headers = {'Youtubedl-no-compression': 'True'}
        if 'user_agent' in info_dict:
            headers['Youtubedl-user-agent'] = info_dict['user_agent']
        if 'http_referer' in info_dict:
            headers['Referer'] = info_dict['http_referer']
        add_headers = info_dict.get('http_headers')
        if add_headers:
            headers.update(add_headers)
        data = info_dict.get('http_post_data')
        http_method = info_dict.get('http_method')
        basic_request = compat_urllib_request.Request(url, data, headers)
        request = compat_urllib_request.Request(url, data, headers)
        if http_method is not None:
            basic_request.get_method = lambda: http_method
            request.get_method = lambda: http_method

        is_test = self.params.get('test', False)

        if is_test:
            request.add_header('Range', 'bytes=0-%s' % str(self._TEST_FILE_SIZE - 1))

        # Establish possible resume length
        if os.path.isfile(encodeFilename(tmpfilename)):
            resume_len = os.path.getsize(encodeFilename(tmpfilename))
        else:
            resume_len = 0

        open_mode = 'wb'
        if resume_len != 0:
            if self.params.get('continuedl', False):
                self.report_resuming_byte(resume_len)
                request.add_header('Range', 'bytes=%d-' % resume_len)
                open_mode = 'ab'
            else:
                resume_len = 0

        count = 0
        retries = self.params.get('retries', 0)
        while count <= retries:
            # Establish connection
            try:
                data = self.ydl.urlopen(request)
                break
            except (compat_urllib_error.HTTPError, ) as err:
                if (err.code < 500 or err.code >= 600) and err.code != 416:
                    # Unexpected HTTP error
                    raise
                elif err.code == 416:
                    # Unable to resume (requested range not satisfiable)
                    try:
                        # Open the connection again without the range header
                        data = self.ydl.urlopen(basic_request)
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
                            resume_len = 0
                            open_mode = 'wb'
                            break
            # Retry
            count += 1
            if count <= retries:
                self.report_retry(count, retries)

        if count > retries:
            self.report_error('giving up after %s retries' % retries)
            return False

        data_len = data.info().get('Content-length', None)

        # Range HTTP header may be ignored/unsupported by a webserver
        # (e.g. extractor/scivee.py, extractor/bambuser.py).
        # However, for a test we still would like to download just a piece of a file.
        # To achieve this we limit data_len to _TEST_FILE_SIZE and manually control
        # block size when downloading a file.
        if is_test and (data_len is None or int(data_len) > self._TEST_FILE_SIZE):
            data_len = self._TEST_FILE_SIZE

        if data_len is not None:
            data_len = int(data_len) + resume_len
            min_data_len = self.params.get("min_filesize", None)
            max_data_len = self.params.get("max_filesize", None)
            if min_data_len is not None and data_len < min_data_len:
                self.to_screen('\r[download] File is smaller than min-filesize (%s bytes < %s bytes). Aborting.' % (data_len, min_data_len))
                return False
            if max_data_len is not None and data_len > max_data_len:
                self.to_screen('\r[download] File is larger than max-filesize (%s bytes > %s bytes). Aborting.' % (data_len, max_data_len))
                return False

        data_len_str = format_bytes(data_len)
        byte_counter = 0 + resume_len
        block_size = self.params.get('buffersize', 1024)
        start = time.time()
        while True:
            # Download and write
            before = time.time()
            data_block = data.read(block_size if not is_test else min(block_size, data_len - byte_counter))
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
                    self.report_error('unable to open for writing: %s' % str(err))
                    return False
            try:
                stream.write(data_block)
            except (IOError, OSError) as err:
                self.to_stderr('\n')
                self.report_error('unable to write data: %s' % str(err))
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

            if is_test and byte_counter == data_len:
                break

            # Apply rate limit
            self.slow_down(start, byte_counter - resume_len)

        if stream is None:
            self.to_stderr('\n')
            self.report_error('Did not get any data blocks')
            return False
        if tmpfilename != '-':
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
