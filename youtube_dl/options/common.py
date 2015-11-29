from __future__ import unicode_literals

import os

from youtube_dl.compat import (
    compat_expanduser,
    compat_getenv,
    compat_shlex_split,
)

__all__ = ['_readOptions', '_readUserConf', '_format_option_string',
           '_comma_separated_values_options_callback', '_hide_login_info']

def _readOptions(filename_bytes, default=[]):
    try:
        optionf = open(filename_bytes)
    except IOError:
        return default  # silently skip if file is not present
    try:
        res = []
        for l in optionf:
            res += compat_shlex_split(l, comments=True)
    finally:
        optionf.close()
    return res

def _readUserConf():
    xdg_config_home = compat_getenv('XDG_CONFIG_HOME')
    if xdg_config_home:
        userConfFile = os.path.join(xdg_config_home, 'youtube-dl', 'config')
        if not os.path.isfile(userConfFile):
            userConfFile = os.path.join(xdg_config_home, 'youtube-dl.conf')
    else:
        userConfFile = os.path.join(compat_expanduser('~'), '.config', 'youtube-dl', 'config')
        if not os.path.isfile(userConfFile):
            userConfFile = os.path.join(compat_expanduser('~'), '.config', 'youtube-dl.conf')
    userConf = _readOptions(userConfFile, None)

    if userConf is None:
        appdata_dir = compat_getenv('appdata')
        if appdata_dir:
            userConf = _readOptions(
                os.path.join(appdata_dir, 'youtube-dl', 'config'),
                default=None)
            if userConf is None:
                userConf = _readOptions(
                    os.path.join(appdata_dir, 'youtube-dl', 'config.txt'),
                    default=None)

    if userConf is None:
        userConf = _readOptions(
            os.path.join(compat_expanduser('~'), 'youtube-dl.conf'),
            default=None)
    if userConf is None:
        userConf = _readOptions(
            os.path.join(compat_expanduser('~'), 'youtube-dl.conf.txt'),
            default=None)

    if userConf is None:
        userConf = []

    return userConf

def _format_option_string(option):
    ''' ('-o', '--option') -> -o, --format METAVAR'''

    opts = []

    if option._short_opts:
        opts.append(option._short_opts[0])
    if option._long_opts:
        opts.append(option._long_opts[0])
    if len(opts) > 1:
        opts.insert(1, ', ')

    if option.takes_value():
        opts.append(' %s' % option.metavar)

    return "".join(opts)

def _comma_separated_values_options_callback(option, opt_str, value, parser):
    setattr(parser.values, option.dest, value.split(','))

def _hide_login_info(opts):
    opts = list(opts)
    for private_opt in ['-p', '--password', '-u', '--username', '--video-password']:
        try:
            i = opts.index(private_opt)
            opts[i + 1] = 'PRIVATE'
        except ValueError:
            pass
    return opts

