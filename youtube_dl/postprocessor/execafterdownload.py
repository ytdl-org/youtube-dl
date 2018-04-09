from __future__ import unicode_literals

import collections
import random
import re
import subprocess
import sys
import time

from .common import PostProcessor
from ..compat import (
    compat_numeric_types,
    compat_shlex_quote,
    compat_str,
)
from string import ascii_letters
from ..utils import (
    encodeArgument,
    encodeFilename,
    expand_path,
    preferredencoding,
    sanitize_filename,
    PostProcessingError,
)

class ExecAfterDownloadPP(PostProcessor):
    def __init__(self, downloader, exec_cmd):
        super(ExecAfterDownloadPP, self).__init__(downloader)
        self.exec_cmd = exec_cmd

    def prepare_cmd(self, info_dict, extras):
        """Generate the command."""
        try:
            template_dict = dict(info_dict)

            template_dict['epoch'] = int(time.time())
            autonumber_size = extras['params'].get('autonumber_size')
            if autonumber_size is None:
                autonumber_size = 5
            template_dict['autonumber'] = extras['params'].get('autonumber_start', 1) - 1 + extras['_num_downloads']
            if template_dict.get('resolution') is None:
                if template_dict.get('width') and template_dict.get('height'):
                    template_dict['resolution'] = '%dx%d' % (template_dict['width'], template_dict['height'])
                elif template_dict.get('height'):
                    template_dict['resolution'] = '%sp' % template_dict['height']
                elif template_dict.get('width'):
                    template_dict['resolution'] = '%dx?' % template_dict['width']

            sanitize = lambda k, v: sanitize_filename(
                compat_shlex_quote(compat_str(v)),
                restricted=extras['params'].get('restrictfilenames'),
                is_id=(k == 'id' or k.endswith('_id')))
            template_dict = dict((k, v if isinstance(v, compat_numeric_types) else sanitize(k, v))
                                 for k, v in template_dict.items()
                                 if v is not None and not isinstance(v, (list, tuple, dict)))
            template_dict = collections.defaultdict(lambda: 'NA', template_dict)

            cmdtmpl = self.exec_cmd
            cmdtmpl = cmdtmpl.replace('{}', '%(filepath)s')
            if '%(filepath)s' not in cmdtmpl:
                cmdtmpl += ' %(filepath)s'

            # For fields playlist_index and autonumber convert all occurrences
            # of %(field)s to %(field)0Nd for backward compatibility
            field_size_compat_map = {
                'playlist_index': len(str(template_dict['n_entries'])),
                'autonumber': autonumber_size,
            }
            FIELD_SIZE_COMPAT_RE = r'(?<!%)%\((?P<field>autonumber|playlist_index)\)s'
            mobj = re.search(FIELD_SIZE_COMPAT_RE, cmdtmpl)
            if mobj:
                cmdtmpl = re.sub(
                    FIELD_SIZE_COMPAT_RE,
                    r'%%(\1)0%dd' % field_size_compat_map[mobj.group('field')],
                    cmdtmpl)

            # Missing numeric fields used together with integer presentation types
            # in format specification will break the argument substitution since
            # string 'NA' is returned for missing fields. We will patch output
            # template for missing fields to meet string presentation type.
            for numeric_field in extras['_NUMERIC_FIELDS']:
                if numeric_field not in template_dict:
                    # As of [1] format syntax is:
                    #  %[mapping_key][conversion_flags][minimum_width][.precision][length_modifier]type
                    # 1. https://docs.python.org/2/library/stdtypes.html#string-formatting
                    FORMAT_RE = r'''(?x)
                        (?<!%)
                        %
                        \({0}\)  # mapping key
                        (?:[#0\-+ ]+)?  # conversion flags (optional)
                        (?:\d+)?  # minimum field width (optional)
                        (?:\.\d+)?  # precision (optional)
                        [hlL]?  # length modifier (optional)
                        [diouxXeEfFgGcrs%]  # conversion type
                    '''
                    cmdtmpl = re.sub(
                        FORMAT_RE.format(numeric_field),
                        r'%({0})s'.format(numeric_field), cmdtmpl)

            # expand_path translates '%%' into '%' and '$$' into '$'
            # correspondingly that is not what we want since we need to keep
            # '%%' intact for template dict substitution step. Working around
            # with boundary-alike separator hack.
            sep = ''.join([random.choice(ascii_letters) for _ in range(32)])
            cmdtmpl = cmdtmpl.replace('%%', '%{0}%'.format(sep)).replace('$$', '${0}$'.format(sep))

            # cmdtmpl should be expand_path'ed before template dict substitution
            # because meta fields may contain env variables we don't want to
            # be expanded. For example, for cmdtmpl "%(title)s.%(ext)s" and
            # title "Hello $PATH", we don't want `$PATH` to be expanded.
            cmd = expand_path(cmdtmpl).replace(sep, '') % template_dict

            # Temporary fix for #4787
            # 'Treat' all problem characters by passing filename through preferredencoding
            # to workaround encoding issues with subprocess on python2 @ Windows
            if sys.version_info < (3, 0) and sys.platform == 'win32':
                cmd = encodeFilename(cmd, True).decode(preferredencoding())
            return cmd
        except ValueError as err:
            raise PostProcessingError(err.message)

    def run(self, information):
        extras = dict(information['pp_extras'])
        del information['pp_extras']

        cmd = self.prepare_cmd(information, extras)

        self._downloader.to_screen('[exec] Executing command: %s' % cmd)
        retCode = subprocess.call(encodeArgument(cmd), shell=True)
        if retCode != 0:
            raise PostProcessingError(
                'Command returned error code %d' % retCode)

        return [], information
