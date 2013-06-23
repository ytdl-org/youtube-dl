import os
import subprocess
import sys
import time

from .utils import *


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

        This method returns a tuple, the first element of which describes
        whether the original file should be kept (i.e. not deleted - None for
        no preference), and the second of which is the updated information.

        In addition, this method may raise a PostProcessingError
        exception if post processing fails.
        """
        return None, information # by default, keep file and do nothing

class FFmpegPostProcessorError(PostProcessingError):
    pass

class AudioConversionError(PostProcessingError):
    pass

class FFmpegPostProcessor(PostProcessor):
    def __init__(self,downloader=None):
        PostProcessor.__init__(self, downloader)
        self._exes = self.detect_executables()

    @staticmethod
    def detect_executables():
        def executable(exe):
            try:
                subprocess.Popen([exe, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            except OSError:
                return False
            return exe
        programs = ['avprobe', 'avconv', 'ffmpeg', 'ffprobe']
        return dict((program, executable(program)) for program in programs)

    def run_ffmpeg(self, path, out_path, opts):
        if not self._exes['ffmpeg'] and not self._exes['avconv']:
            raise FFmpegPostProcessorError(u'ffmpeg or avconv not found. Please install one.')
        cmd = ([self._exes['avconv'] or self._exes['ffmpeg'], '-y', '-i', encodeFilename(path)]
               + opts +
               [encodeFilename(self._ffmpeg_filename_argument(out_path))])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout,stderr = p.communicate()
        if p.returncode != 0:
            stderr = stderr.decode('utf-8', 'replace')
            msg = stderr.strip().split('\n')[-1]
            raise FFmpegPostProcessorError(msg)

    def _ffmpeg_filename_argument(self, fn):
        # ffmpeg broke --, see https://ffmpeg.org/trac/ffmpeg/ticket/2127 for details
        if fn.startswith(u'-'):
            return u'./' + fn
        return fn

class FFmpegExtractAudioPP(FFmpegPostProcessor):
    def __init__(self, downloader=None, preferredcodec=None, preferredquality=None, nopostoverwrites=False):
        FFmpegPostProcessor.__init__(self, downloader)
        if preferredcodec is None:
            preferredcodec = 'best'
        self._preferredcodec = preferredcodec
        self._preferredquality = preferredquality
        self._nopostoverwrites = nopostoverwrites

    def get_audio_codec(self, path):
        if not self._exes['ffprobe'] and not self._exes['avprobe']: return None
        try:
            cmd = [self._exes['avprobe'] or self._exes['ffprobe'], '-show_streams', encodeFilename(self._ffmpeg_filename_argument(path))]
            handle = subprocess.Popen(cmd, stderr=compat_subprocess_get_DEVNULL(), stdout=subprocess.PIPE)
            output = handle.communicate()[0]
            if handle.wait() != 0:
                return None
        except (IOError, OSError):
            return None
        audio_codec = None
        for line in output.decode('ascii', 'ignore').split('\n'):
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
        opts = ['-vn'] + acodec_opts + more_opts
        try:
            FFmpegPostProcessor.run_ffmpeg(self, path, out_path, opts)
        except FFmpegPostProcessorError as err:
            raise AudioConversionError(err.message)

    def run(self, information):
        path = information['filepath']

        filecodec = self.get_audio_codec(path)
        if filecodec is None:
            raise PostProcessingError(u'WARNING: unable to obtain file audio codec with ffprobe')

        more_opts = []
        if self._preferredcodec == 'best' or self._preferredcodec == filecodec or (self._preferredcodec == 'm4a' and filecodec == 'aac'):
            if filecodec == 'aac' and self._preferredcodec in ['m4a', 'best']:
                # Lossless, but in another container
                acodec = 'copy'
                extension = 'm4a'
                more_opts = [self._exes['avconv'] and '-bsf:a' or '-absf', 'aac_adtstoasc']
            elif filecodec in ['aac', 'mp3', 'vorbis', 'opus']:
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
                    if int(self._preferredquality) < 10:
                        more_opts += [self._exes['avconv'] and '-q:a' or '-aq', self._preferredquality]
                    else:
                        more_opts += [self._exes['avconv'] and '-b:a' or '-ab', self._preferredquality + 'k']
        else:
            # We convert the audio (lossy)
            acodec = {'mp3': 'libmp3lame', 'aac': 'aac', 'm4a': 'aac', 'opus': 'opus', 'vorbis': 'libvorbis', 'wav': None}[self._preferredcodec]
            extension = self._preferredcodec
            more_opts = []
            if self._preferredquality is not None:
                if int(self._preferredquality) < 10:
                    more_opts += [self._exes['avconv'] and '-q:a' or '-aq', self._preferredquality]
                else:
                    more_opts += [self._exes['avconv'] and '-b:a' or '-ab', self._preferredquality + 'k']
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

        # If we download foo.mp3 and convert it to... foo.mp3, then don't delete foo.mp3, silly.
        if new_path == path:
            self._nopostoverwrites = True

        try:
            if self._nopostoverwrites and os.path.exists(encodeFilename(new_path)):
                self._downloader.to_screen(u'[youtube] Post-process file %s exists, skipping' % new_path)
            else:
                self._downloader.to_screen(u'[' + (self._exes['avconv'] and 'avconv' or 'ffmpeg') + '] Destination: ' + new_path)
                self.run_ffmpeg(path, new_path, acodec, more_opts)
        except:
            etype,e,tb = sys.exc_info()
            if isinstance(e, AudioConversionError):
                msg = u'audio conversion failed: ' + e.message
            else:
                msg = u'error running ' + (self._exes['avconv'] and 'avconv' or 'ffmpeg')
            raise PostProcessingError(msg)

        # Try to update the date time for extracted audio file.
        if information.get('filetime') is not None:
            try:
                os.utime(encodeFilename(new_path), (time.time(), information['filetime']))
            except:
                self._downloader.to_stderr(u'WARNING: Cannot update utime of audio file')

        information['filepath'] = new_path
        return self._nopostoverwrites,information

class FFmpegVideoConvertor(FFmpegPostProcessor):
    def __init__(self, downloader=None,preferedformat=None):
        super(FFmpegVideoConvertor, self).__init__(downloader)
        self._preferedformat=preferedformat

    def run(self, information):
        path = information['filepath']
        prefix, sep, ext = path.rpartition(u'.')
        outpath = prefix + sep + self._preferedformat
        if information['ext'] == self._preferedformat:
            self._downloader.to_screen(u'[ffmpeg] Not converting video file %s - already is in target format %s' % (path, self._preferedformat))
            return True,information
        self._downloader.to_screen(u'['+'ffmpeg'+'] Converting video from %s to %s, Destination: ' % (information['ext'], self._preferedformat) +outpath)
        self.run_ffmpeg(path, outpath, [])
        information['filepath'] = outpath
        information['format'] = self._preferedformat
        information['ext'] = self._preferedformat
        return False,information
