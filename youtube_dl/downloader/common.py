from __future__ import division, unicode_literals

import os
import re
import sys
import time
import random
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable, Union

from ..compat import compat_os_name
from ..utils import (
    decodeArgument,
    encodeFilename,
    error_to_compat_str,
    format_bytes,
    shell_quote,
    timeconvert,
)

# Constantes
TEST_FILE_SIZE = 10241
MAX_BLOCK_SIZE = 4194304  # 4 MB
MIN_BLOCK_SIZE = 1.0

@dataclass
class DownloadProgress:
    """Classe para representar o progresso do download."""
    status: str
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    total_bytes_estimate: Optional[int] = None
    speed: Optional[float] = None
    eta: Optional[int] = None
    elapsed: Optional[float] = None

class ProgressFormatter:
    """Classe responsável por formatar informações de progresso."""
    
    @staticmethod
    def format_seconds(seconds: float) -> str:
        """Formata segundos em formato HH:MM:SS."""
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        
        if hours > 99:
            return '--:--:--'
        if hours == 0:
            return f'{mins:02d}:{secs:02d}'
        return f'{hours:02d}:{mins:02d}:{secs:02d}'

    @staticmethod
    def format_percent(percent: Optional[float]) -> str:
        """Formata porcentagem."""
        if percent is None:
            return '---.-%'
        return f'{percent:6.1f}%'

    @staticmethod
    def format_speed(speed: Optional[float]) -> str:
        """Formata velocidade de download."""
        if speed is None:
            return '%10s' % '---b/s'
        return f'{format_bytes(speed):10s}/s'

    @staticmethod
    def format_eta(eta: Optional[int]) -> str:
        """Formata tempo estimado."""
        if eta is None:
            return '--:--'
        return ProgressFormatter.format_seconds(eta)

class FileDownloader:
    """Classe base para download de arquivos.
    
    Responsável por gerenciar o download de arquivos e fornecer feedback
    sobre o progresso.
    """

    def __init__(self, ydl: Any, params: Dict[str, Any]):
        """Inicializa o downloader.
        
        Args:
            ydl: Instância do YoutubeDL
            params: Dicionário com parâmetros de configuração
        """
        self.ydl = ydl
        self._progress_hooks: List[Callable] = []
        self.params = params
        self.formatter = ProgressFormatter()
        self.add_progress_hook(self.report_progress)

    def add_progress_hook(self, hook: Callable) -> None:
        """Adiciona um hook de progresso."""
        self._progress_hooks.append(hook)

    def _hook_progress(self, status: Dict[str, Any]) -> None:
        """Executa todos os hooks de progresso registrados."""
        for hook in self._progress_hooks:
            hook(status)

    def report_progress(self, status: Dict[str, Any]) -> None:
        """Reporta o progresso do download."""
        if status['status'] == 'finished':
            self._report_finished(status)
            return

        if self.params.get('noprogress') or status['status'] != 'downloading':
            return

        self._report_downloading(status)

    def _report_finished(self, status: Dict[str, Any]) -> None:
        """Reporta conclusão do download."""
        if self.params.get('noprogress', False):
            self.to_screen('[download] Download completed')
            return

        msg_template = '100%%'
        if status.get('total_bytes') is not None:
            status['_total_bytes_str'] = format_bytes(status['total_bytes'])
            msg_template += ' of %(_total_bytes_str)s'
        if status.get('elapsed') is not None:
            status['_elapsed_str'] = self.formatter.format_seconds(status['elapsed'])
            msg_template += ' in %(_elapsed_str)s'

        self._report_progress_status(msg_template % status, is_last_line=True)

    def _report_downloading(self, status: Dict[str, Any]) -> None:
        """Reporta progresso durante o download."""
        status.update({
            '_eta_str': self.formatter.format_eta(status.get('eta')),
            '_speed_str': self.formatter.format_speed(status.get('speed')),
        })

        if status.get('total_bytes') and status.get('downloaded_bytes') is not None:
            percent = 100 * status['downloaded_bytes'] / status['total_bytes']
            status['_percent_str'] = self.formatter.format_percent(percent)
            status['_total_bytes_str'] = format_bytes(status['total_bytes'])
            msg_template = '%(_percent_str)s of %(_total_bytes_str)s at %(_speed_str)s ETA %(_eta_str)s'
        else:
            msg_template = self._get_progress_template(status)

        self._report_progress_status(msg_template % status)

    def _get_progress_template(self, status: Dict[str, Any]) -> str:
        """Retorna o template apropriado para o progresso."""
        if status.get('total_bytes_estimate') is not None:
            status['_total_bytes_estimate_str'] = format_bytes(status['total_bytes_estimate'])
            return '%(_percent_str)s of ~%(_total_bytes_estimate_str)s at %(_speed_str)s ETA %(_eta_str)s'
        
        if status.get('downloaded_bytes') is not None:
            status['_downloaded_bytes_str'] = format_bytes(status['downloaded_bytes'])
            if status.get('elapsed'):
                status['_elapsed_str'] = self.formatter.format_seconds(status['elapsed'])
                return '%(_downloaded_bytes_str)s at %(_speed_str)s (%(_elapsed_str)s)'
            return '%(_downloaded_bytes_str)s at %(_speed_str)s'
        
        return '%(_percent_str)s % at %(_speed_str)s ETA %(_eta_str)s'

    def _report_progress_status(self, msg: str, is_last_line: bool = False) -> None:
        """Reporta o status do progresso."""
        fullmsg = '[download] ' + msg
        
        if self.params.get('progress_with_newline', False):
            self.to_screen(fullmsg)
            return

        if compat_os_name == 'nt':
            prev_len = getattr(self, '_report_progress_prev_line_length', 0)
            if prev_len > len(fullmsg):
                fullmsg += ' ' * (prev_len - len(fullmsg))
            self._report_progress_prev_line_length = len(fullmsg)
            clear_line = '\r'
        else:
            clear_line = '\r\x1b[K' if sys.stderr.isatty() else '\r'

        self.to_screen(clear_line + fullmsg, skip_eol=not is_last_line)
        self.to_console_title('youtube-dl ' + msg)

    def download(self, filename: str, info_dict: Dict[str, Any]) -> bool:
        """Inicia o download do arquivo.
        
        Args:
            filename: Nome do arquivo de destino
            info_dict: Dicionário com informações do download
            
        Returns:
            bool: True se o download foi bem sucedido, False caso contrário
        """
        if self._should_skip_download(filename):
            return True

        self._handle_sleep_interval()
        return self.real_download(filename, info_dict)

    def _should_skip_download(self, filename: str) -> bool:
        """Verifica se o download deve ser pulado."""
        if hasattr(filename, 'write'):
            return False

        nooverwrites_and_exists = (
            self.params.get('nooverwrites', False)
            and os.path.exists(encodeFilename(filename))
        )

        continuedl_and_exists = (
            self.params.get('continuedl', True)
            and os.path.isfile(encodeFilename(filename))
            and not self.params.get('nopart', False)
        )

        if filename != '-' and (nooverwrites_and_exists or continuedl_and_exists):
            self.report_file_already_downloaded(filename)
            self._hook_progress({
                'filename': filename,
                'status': 'finished',
                'total_bytes': os.path.getsize(encodeFilename(filename)),
            })
            return True

        return False

    def _handle_sleep_interval(self) -> None:
        """Gerencia o intervalo de sono entre downloads."""
        min_sleep_interval = self.params.get('sleep_interval')
        if not min_sleep_interval:
            return

        max_sleep_interval = self.params.get('max_sleep_interval', min_sleep_interval)
        sleep_interval = random.uniform(min_sleep_interval, max_sleep_interval)
        
        self.to_screen(
            '[download] Sleeping %s seconds...' % (
                int(sleep_interval) if sleep_interval.is_integer()
                else '%.2f' % sleep_interval))
        time.sleep(sleep_interval)

    def real_download(self, filename: str, info_dict: Dict[str, Any]) -> bool:
        """Implementação real do download. Deve ser sobrescrita por subclasses."""
        raise NotImplementedError('This method must be implemented by subclasses')

    # Métodos de utilidade
    def to_screen(self, *args: Any, **kwargs: Any) -> None:
        """Envia mensagem para a tela."""
        self.ydl.to_screen(*args, **kwargs)

    def to_stderr(self, message: str) -> None:
        """Envia mensagem para stderr."""
        self.ydl.to_screen(message)

    def to_console_title(self, message: str) -> None:
        """Atualiza o título do console."""
        self.ydl.to_console_title(message)

    def trouble(self, *args: Any, **kwargs: Any) -> None:
        """Reporta um problema."""
        self.ydl.trouble(*args, **kwargs)

    def report_warning(self, *args: Any, **kwargs: Any) -> None:
        """Reporta um aviso."""
        self.ydl.report_warning(*args, **kwargs)

    def report_error(self, *args: Any, **kwargs: Any) -> None:
        """Reporta um erro."""
        self.ydl.report_error(*args, **kwargs)

    def report_file_already_downloaded(self, file_name):
        """Report file has already been fully downloaded."""
        try:
            self.to_screen('[download] %s has already been downloaded' % file_name)
        except UnicodeEncodeError:
            self.to_screen('[download] The file has already been downloaded')

    def report_unable_to_resume(self):
        """Report it was impossible to resume download."""
        self.to_screen('[download] Unable to resume')

    def slow_down(self, start_time, now, byte_counter):
        """Sleep if the download speed is over the rate limit."""
        rate_limit = self.params.get('ratelimit')
        if rate_limit is None or byte_counter == 0:
            return
        if now is None:
            now = time.time()
        elapsed = now - start_time
        if elapsed <= 0.0:
            return
        speed = float(byte_counter) / elapsed
        if speed > rate_limit:
            sleep_time = float(byte_counter) / rate_limit - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

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

    def ytdl_filename(self, filename):
        return filename + '.ytdl'

    def try_rename(self, old_filename, new_filename):
        try:
            if old_filename == new_filename:
                return
            os.rename(encodeFilename(old_filename), encodeFilename(new_filename))
        except (IOError, OSError) as err:
            self.report_error('unable to rename file: %s' % error_to_compat_str(err))

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
        except Exception:
            pass
        return filetime

    def report_destination(self, filename):
        """Report destination filename."""
        self.to_screen('[download] Destination: ' + filename)

    def report_resuming_byte(self, resume_len):
        """Report attempt to resume at given byte."""
        self.to_screen('[download] Resuming download at byte %s' % resume_len)

    def report_retry(self, err, count, retries):
        """Report retry in case of HTTP error 5xx"""
        self.to_screen(
            '[download] Got server HTTP error: %s. Retrying (attempt %d of %s)...'
            % (error_to_compat_str(err), count, self.format_retries(retries)))

    def format_retries(self, retries):
        return 'inf' if retries == float('inf') else '%.0f' % retries

    def format_eta(self, eta):
        if eta is None:
            return '--:--'
        return self.formatter.format_eta(eta)

    def format_speed(self, speed):
        if speed is None:
            return '%10s' % '---b/s'
        return self.formatter.format_speed(speed)

    def format_percent(self, percent):
        if percent is None:
            return '---.-%'
        return self.formatter.format_percent(percent)

    def format_seconds(self, seconds):
        (mins, secs) = divmod(seconds, 60)
        (hours, mins) = divmod(mins, 60)
        if hours > 99:
            return '--:--:--'
        if hours == 0:
            return '%02d:%02d' % (mins, secs)
        else:
            return '%02d:%02d:%02d' % (hours, mins, secs)

    def calc_percent(self, byte_counter, data_len):
        if data_len is None:
            return None
        return float(byte_counter) / float(data_len) * 100.0

    def calc_eta(self, start_or_rate, now_or_remaining, *args):
        if len(args) < 2:
            rate, remaining = (start_or_rate, now_or_remaining)
            if None in (rate, remaining):
                return None
            return int(float(remaining) / rate)
        start, now = (start_or_rate, now_or_remaining)
        total, current = args[:2]
        if total is None:
            return None
        if now is None:
            now = time.time()
        rate = self.calc_speed(start, now, current)
        return rate and int((float(total) - float(current)) / rate)

    def calc_speed(self, start, now, bytes):
        dif = now - start
        if bytes == 0 or dif < 0.001:  # One millisecond
            return None
        return float(bytes) / dif

    def filesize_or_none(self, unencoded_filename):
        fn = encodeFilename(unencoded_filename)
        if os.path.isfile(fn):
            return os.path.getsize(fn)

    def best_block_size(self, elapsed_time, bytes):
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

    def parse_bytes(self, bytestr):
        """Parse a string indicating a byte quantity into an integer."""
        matchobj = re.match(r'(?i)^(\d+(?:\.\d+)?)([kMGTPEZY]?)$', bytestr)
        if matchobj is None:
            return None
        number = float(matchobj.group(1))
        multiplier = 1024.0 ** 'bkmgtpezy'.index(matchobj.group(2).lower())
        return int(round(number * multiplier))

    def _debug_cmd(self, args, exe=None):
        if not self.params.get('verbose', False):
            return

        str_args = [decodeArgument(a) for a in args]

        if exe is None:
            exe = os.path.basename(str_args[0])

        self.to_screen('[debug] %s command line: %s' % (
            exe, shell_quote(str_args)))
