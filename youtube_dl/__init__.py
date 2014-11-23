#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

__license__ = 'Public Domain'

import codecs
import io
import os
import random
import sys


from .options import (
    parseOpts,
)
from .compat import (
    compat_expanduser,
    compat_getpass,
    compat_print,
    workaround_optparse_bug9161,
)
from .utils import (
    DateRange,
    DEFAULT_OUTTMPL,
    decodeOption,
    DownloadError,
    MaxDownloadsReached,
    preferredencoding,
    read_batch_urls,
    SameFileError,
    setproctitle,
    std_headers,
    write_string,
)
from .update import update_self
from .downloader import (
    FileDownloader,
)
from .extractor import gen_extractors
from .YoutubeDL import YoutubeDL
from .postprocessor import (
    AtomicParsleyPP,
    FFmpegAudioFixPP,
    FFmpegMetadataPP,
    FFmpegVideoConvertor,
    FFmpegExtractAudioPP,
    FFmpegEmbedSubtitlePP,
    XAttrMetadataPP,
    ExecAfterDownloadPP,
)


def _real_main(argv=None):
    # Compatibility fixes for Windows
    if sys.platform == 'win32':
        # https://github.com/rg3/youtube-dl/issues/820
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

    workaround_optparse_bug9161()

    setproctitle('youtube-dl')

    parser, opts, args = parseOpts(argv)

    # Set user agent
    if opts.user_agent is not None:
        std_headers['User-Agent'] = opts.user_agent

    # Set referer
    if opts.referer is not None:
        std_headers['Referer'] = opts.referer

    # Custom HTTP headers
    if opts.headers is not None:
        for h in opts.headers:
            if h.find(':', 1) < 0:
                parser.error('wrong header formatting, it should be key:value, not "%s"' % h)
            key, value = h.split(':', 2)
            if opts.verbose:
                write_string('[debug] Adding header from command line option %s:%s\n' % (key, value))
            std_headers[key] = value

    # Dump user agent
    if opts.dump_user_agent:
        compat_print(std_headers['User-Agent'])
        sys.exit(0)

    # Batch file verification
    batch_urls = []
    if opts.batchfile is not None:
        try:
            if opts.batchfile == '-':
                batchfd = sys.stdin
            else:
                batchfd = io.open(opts.batchfile, 'r', encoding='utf-8', errors='ignore')
            batch_urls = read_batch_urls(batchfd)
            if opts.verbose:
                write_string('[debug] Batch file urls: ' + repr(batch_urls) + '\n')
        except IOError:
            sys.exit('ERROR: batch file could not be read')
    all_urls = batch_urls + args
    all_urls = [url.strip() for url in all_urls]
    _enc = preferredencoding()
    all_urls = [url.decode(_enc, 'ignore') if isinstance(url, bytes) else url for url in all_urls]

    extractors = gen_extractors()

    if opts.list_extractors:
        for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
            compat_print(ie.IE_NAME + (' (CURRENTLY BROKEN)' if not ie._WORKING else ''))
            matchedUrls = [url for url in all_urls if ie.suitable(url)]
            for mu in matchedUrls:
                compat_print('  ' + mu)
        sys.exit(0)
    if opts.list_extractor_descriptions:
        for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
            if not ie._WORKING:
                continue
            desc = getattr(ie, 'IE_DESC', ie.IE_NAME)
            if desc is False:
                continue
            if hasattr(ie, 'SEARCH_KEY'):
                _SEARCHES = ('cute kittens', 'slithering pythons', 'falling cat', 'angry poodle', 'purple fish', 'running tortoise', 'sleeping bunny')
                _COUNTS = ('', '5', '10', 'all')
                desc += ' (Example: "%s%s:%s" )' % (ie.SEARCH_KEY, random.choice(_COUNTS), random.choice(_SEARCHES))
            compat_print(desc)
        sys.exit(0)

    # Conflicting, missing and erroneous options
    if opts.usenetrc and (opts.username is not None or opts.password is not None):
        parser.error('using .netrc conflicts with giving username/password')
    if opts.password is not None and opts.username is None:
        parser.error('account username missing\n')
    if opts.outtmpl is not None and (opts.usetitle or opts.autonumber or opts.useid):
        parser.error('using output template conflicts with using title, video ID or auto number')
    if opts.usetitle and opts.useid:
        parser.error('using title conflicts with using video ID')
    if opts.username is not None and opts.password is None:
        opts.password = compat_getpass('Type account password and press [Return]: ')
    if opts.ratelimit is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.ratelimit)
        if numeric_limit is None:
            parser.error('invalid rate limit specified')
        opts.ratelimit = numeric_limit
    if opts.min_filesize is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.min_filesize)
        if numeric_limit is None:
            parser.error('invalid min_filesize specified')
        opts.min_filesize = numeric_limit
    if opts.max_filesize is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.max_filesize)
        if numeric_limit is None:
            parser.error('invalid max_filesize specified')
        opts.max_filesize = numeric_limit
    if opts.retries is not None:
        try:
            opts.retries = int(opts.retries)
        except (TypeError, ValueError):
            parser.error('invalid retry count specified')
    if opts.buffersize is not None:
        numeric_buffersize = FileDownloader.parse_bytes(opts.buffersize)
        if numeric_buffersize is None:
            parser.error('invalid buffer size specified')
        opts.buffersize = numeric_buffersize
    if opts.playliststart <= 0:
        raise ValueError('Playlist start must be positive')
    if opts.playlistend not in (-1, None) and opts.playlistend < opts.playliststart:
        raise ValueError('Playlist end must be greater than playlist start')
    if opts.extractaudio:
        if opts.audioformat not in ['best', 'aac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
            parser.error('invalid audio format specified')
    if opts.audioquality:
        opts.audioquality = opts.audioquality.strip('k').strip('K')
        if not opts.audioquality.isdigit():
            parser.error('invalid audio quality specified')
    if opts.recodevideo is not None:
        if opts.recodevideo not in ['mp4', 'flv', 'webm', 'ogg', 'mkv']:
            parser.error('invalid video recode format specified')
    if opts.date is not None:
        date = DateRange.day(opts.date)
    else:
        date = DateRange(opts.dateafter, opts.datebefore)

    # Do not download videos when there are audio-only formats
    if opts.extractaudio and not opts.keepvideo and opts.format is None:
        opts.format = 'bestaudio/best'

    # --all-sub automatically sets --write-sub if --write-auto-sub is not given
    # this was the old behaviour if only --all-sub was given.
    if opts.allsubtitles and not opts.writeautomaticsub:
        opts.writesubtitles = True

    if sys.version_info < (3,):
        # In Python 2, sys.argv is a bytestring (also note http://bugs.python.org/issue2128 for Windows systems)
        if opts.outtmpl is not None:
            opts.outtmpl = opts.outtmpl.decode(preferredencoding())
    outtmpl = ((opts.outtmpl is not None and opts.outtmpl)
               or (opts.format == '-1' and opts.usetitle and '%(title)s-%(id)s-%(format)s.%(ext)s')
               or (opts.format == '-1' and '%(id)s-%(format)s.%(ext)s')
               or (opts.usetitle and opts.autonumber and '%(autonumber)s-%(title)s-%(id)s.%(ext)s')
               or (opts.usetitle and '%(title)s-%(id)s.%(ext)s')
               or (opts.useid and '%(id)s.%(ext)s')
               or (opts.autonumber and '%(autonumber)s-%(id)s.%(ext)s')
               or DEFAULT_OUTTMPL)
    if not os.path.splitext(outtmpl)[1] and opts.extractaudio:
        parser.error('Cannot download a video and extract audio into the same'
                     ' file! Use "{0}.%(ext)s" instead of "{0}" as the output'
                     ' template'.format(outtmpl))

    any_printing = opts.geturl or opts.gettitle or opts.getid or opts.getthumbnail or opts.getdescription or opts.getfilename or opts.getformat or opts.getduration or opts.dumpjson or opts.dump_single_json
    download_archive_fn = compat_expanduser(opts.download_archive) if opts.download_archive is not None else opts.download_archive

    ydl_opts = {
        'usenetrc': opts.usenetrc,
        'username': opts.username,
        'password': opts.password,
        'twofactor': opts.twofactor,
        'videopassword': opts.videopassword,
        'quiet': (opts.quiet or any_printing),
        'no_warnings': opts.no_warnings,
        'forceurl': opts.geturl,
        'forcetitle': opts.gettitle,
        'forceid': opts.getid,
        'forcethumbnail': opts.getthumbnail,
        'forcedescription': opts.getdescription,
        'forceduration': opts.getduration,
        'forcefilename': opts.getfilename,
        'forceformat': opts.getformat,
        'forcejson': opts.dumpjson,
        'dump_single_json': opts.dump_single_json,
        'simulate': opts.simulate or any_printing,
        'skip_download': opts.skip_download,
        'format': opts.format,
        'format_limit': opts.format_limit,
        'listformats': opts.listformats,
        'outtmpl': outtmpl,
        'autonumber_size': opts.autonumber_size,
        'restrictfilenames': opts.restrictfilenames,
        'ignoreerrors': opts.ignoreerrors,
        'ratelimit': opts.ratelimit,
        'nooverwrites': opts.nooverwrites,
        'retries': opts.retries,
        'buffersize': opts.buffersize,
        'noresizebuffer': opts.noresizebuffer,
        'continuedl': opts.continue_dl,
        'noprogress': opts.noprogress,
        'progress_with_newline': opts.progress_with_newline,
        'playliststart': opts.playliststart,
        'playlistend': opts.playlistend,
        'noplaylist': opts.noplaylist,
        'logtostderr': opts.outtmpl == '-',
        'consoletitle': opts.consoletitle,
        'nopart': opts.nopart,
        'updatetime': opts.updatetime,
        'writedescription': opts.writedescription,
        'writeannotations': opts.writeannotations,
        'writeinfojson': opts.writeinfojson,
        'writethumbnail': opts.writethumbnail,
        'writesubtitles': opts.writesubtitles,
        'writeautomaticsub': opts.writeautomaticsub,
        'allsubtitles': opts.allsubtitles,
        'listsubtitles': opts.listsubtitles,
        'subtitlesformat': opts.subtitlesformat,
        'subtitleslangs': opts.subtitleslangs,
        'matchtitle': decodeOption(opts.matchtitle),
        'rejecttitle': decodeOption(opts.rejecttitle),
        'max_downloads': opts.max_downloads,
        'prefer_free_formats': opts.prefer_free_formats,
        'verbose': opts.verbose,
        'dump_intermediate_pages': opts.dump_intermediate_pages,
        'write_pages': opts.write_pages,
        'test': opts.test,
        'keepvideo': opts.keepvideo,
        'min_filesize': opts.min_filesize,
        'max_filesize': opts.max_filesize,
        'min_views': opts.min_views,
        'max_views': opts.max_views,
        'daterange': date,
        'cachedir': opts.cachedir,
        'youtube_print_sig_code': opts.youtube_print_sig_code,
        'age_limit': opts.age_limit,
        'download_archive': download_archive_fn,
        'cookiefile': opts.cookiefile,
        'nocheckcertificate': opts.no_check_certificate,
        'prefer_insecure': opts.prefer_insecure,
        'proxy': opts.proxy,
        'socket_timeout': opts.socket_timeout,
        'bidi_workaround': opts.bidi_workaround,
        'debug_printtraffic': opts.debug_printtraffic,
        'prefer_ffmpeg': opts.prefer_ffmpeg,
        'include_ads': opts.include_ads,
        'default_search': opts.default_search,
        'youtube_include_dash_manifest': opts.youtube_include_dash_manifest,
        'encoding': opts.encoding,
        'exec_cmd': opts.exec_cmd,
        'extract_flat': opts.extract_flat,
    }

    with YoutubeDL(ydl_opts) as ydl:
        # PostProcessors
        # Add the metadata pp first, the other pps will copy it
        if opts.addmetadata:
            ydl.add_post_processor(FFmpegMetadataPP())
        if opts.extractaudio:
            ydl.add_post_processor(FFmpegExtractAudioPP(preferredcodec=opts.audioformat, preferredquality=opts.audioquality, nopostoverwrites=opts.nopostoverwrites))
        if opts.recodevideo:
            ydl.add_post_processor(FFmpegVideoConvertor(preferedformat=opts.recodevideo))
        if opts.embedsubtitles:
            ydl.add_post_processor(FFmpegEmbedSubtitlePP(subtitlesformat=opts.subtitlesformat))
        if opts.xattrs:
            ydl.add_post_processor(XAttrMetadataPP())
        if opts.embedthumbnail:
            if not opts.addmetadata:
                ydl.add_post_processor(FFmpegAudioFixPP())
            ydl.add_post_processor(AtomicParsleyPP())

        # Please keep ExecAfterDownload towards the bottom as it allows the user to modify the final file in any way.
        # So if the user is able to remove the file before your postprocessor runs it might cause a few problems.
        if opts.exec_cmd:
            ydl.add_post_processor(ExecAfterDownloadPP(
                verboseOutput=opts.verbose, exec_cmd=opts.exec_cmd))

        # Update version
        if opts.update_self:
            update_self(ydl.to_screen, opts.verbose)

        # Remove cache dir
        if opts.rm_cachedir:
            ydl.cache.remove()

        # Maybe do nothing
        if (len(all_urls) < 1) and (opts.load_info_filename is None):
            if opts.update_self or opts.rm_cachedir:
                sys.exit()

            ydl.warn_if_short_id(sys.argv[1:] if argv is None else argv)
            parser.error('you must provide at least one URL')

        try:
            if opts.load_info_filename is not None:
                retcode = ydl.download_with_info_file(opts.load_info_filename)
            else:
                retcode = ydl.download(all_urls)
        except MaxDownloadsReached:
            ydl.to_screen('--max-download limit reached, aborting.')
            retcode = 101

    sys.exit(retcode)


def main(argv=None):
    try:
        _real_main(argv)
    except DownloadError:
        sys.exit(1)
    except SameFileError:
        sys.exit('ERROR: fixed output name but more than one file to download')
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')
