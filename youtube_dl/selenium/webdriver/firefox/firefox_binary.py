# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


import os
import platform
from subprocess import Popen, STDOUT
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common import utils
import time


class FirefoxBinary(object):

    NO_FOCUS_LIBRARY_NAME = "x_ignore_nofocus.so"

    def __init__(self, firefox_path=None, log_file=None):
        """
        Creates a new instance of Firefox binary.

        :Args:
         - firefox_path - Path to the Firefox executable. By default, it will be detected from the standard locations.
         - log_file - A file object to redirect the firefox process output to. It can be sys.stdout.
                      Please note that with parallel run the output won't be synchronous.
                      By default, it will be redirected to /dev/null.
        """
        self._start_cmd = firefox_path
        # We used to default to subprocess.PIPE instead of /dev/null, but after
        # a while the pipe would fill up and Firefox would freeze.
        self._log_file = log_file or open(os.devnull, "wb")
        self.command_line = None
        if self._start_cmd is None:
            self._start_cmd = self._get_firefox_start_cmd()
        if not self._start_cmd.strip():
            raise WebDriverException(
                "Failed to find firefox binary. You can set it by specifying "
                "the path to 'firefox_binary':\n\nfrom "
                "selenium.webdriver.firefox.firefox_binary import "
                "FirefoxBinary\n\nbinary = "
                "FirefoxBinary('/path/to/binary')\ndriver = "
                "webdriver.Firefox(firefox_binary=binary)")
        # Rather than modifying the environment of the calling Python process
        # copy it and modify as needed.
        self._firefox_env = os.environ.copy()
        self._firefox_env["MOZ_CRASHREPORTER_DISABLE"] = "1"
        self._firefox_env["MOZ_NO_REMOTE"] = "1"
        self._firefox_env["NO_EM_RESTART"] = "1"

    def add_command_line_options(self, *args):
        self.command_line = args

    def launch_browser(self, profile, timeout=30):
        """Launches the browser for the given profile name.
        It is assumed the profile already exists.
        """
        self.profile = profile

        self._start_from_profile_path(self.profile.path)
        self._wait_until_connectable(timeout=timeout)

    def kill(self):
        """Kill the browser.

        This is useful when the browser is stuck.
        """
        if self.process:
            self.process.kill()
            self.process.wait()

    def _start_from_profile_path(self, path):
        self._firefox_env["XRE_PROFILE_PATH"] = path

        if platform.system().lower() == 'linux':
            self._modify_link_library_path()
        command = [self._start_cmd, "-foreground"]
        if self.command_line is not None:
            for cli in self.command_line:
                command.append(cli)
        self.process = Popen(
            command, stdout=self._log_file, stderr=STDOUT,
            env=self._firefox_env)

    def _wait_until_connectable(self, timeout=30):
        """Blocks until the extension is connectable in the firefox."""
        count = 0
        while not utils.is_connectable(self.profile.port):
            if self.process.poll() is not None:
                # Browser has exited
                raise WebDriverException(
                    "The browser appears to have exited "
                    "before we could connect. If you specified a log_file in "
                    "the FirefoxBinary constructor, check it for details.")
            if count >= timeout:
                self.kill()
                raise WebDriverException(
                    "Can't load the profile. Possible firefox version mismatch. "
                    "You must use GeckoDriver instead for Firefox 48+. Profile "
                    "Dir: %s If you specified a log_file in the "
                    "FirefoxBinary constructor, check it for details."
                    % (self.profile.path))
            count += 1
            time.sleep(1)
        return True

    def _find_exe_in_registry(self):
        try:
            from _winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER
        except ImportError:
            from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE, HKEY_CURRENT_USER
        import shlex
        keys = (r"SOFTWARE\Classes\FirefoxHTML\shell\open\command",
                r"SOFTWARE\Classes\Applications\firefox.exe\shell\open\command")
        command = ""
        for path in keys:
            try:
                key = OpenKey(HKEY_LOCAL_MACHINE, path)
                command = QueryValue(key, "")
                break
            except OSError:
                try:
                    key = OpenKey(HKEY_CURRENT_USER, path)
                    command = QueryValue(key, "")
                    break
                except OSError:
                    pass
        else:
            return ""

        if not command:
            return ""

        return shlex.split(command)[0]

    def _get_firefox_start_cmd(self):
        """Return the command to start firefox."""
        start_cmd = ""
        if platform.system() == "Darwin":
            start_cmd = "/Applications/Firefox.app/Contents/MacOS/firefox-bin"
            # fallback to homebrew installation for mac users
            if not os.path.exists(start_cmd):
                start_cmd = os.path.expanduser("~") + start_cmd
        elif platform.system() == "Windows":
            start_cmd = (self._find_exe_in_registry() or self._default_windows_location())
        elif platform.system() == 'Java' and os._name == 'nt':
            start_cmd = self._default_windows_location()
        else:
            for ffname in ["firefox", "iceweasel"]:
                start_cmd = self.which(ffname)
                if start_cmd is not None:
                    break
            else:
                # couldn't find firefox on the system path
                raise RuntimeError(
                    "Could not find firefox in your system PATH." +
                    " Please specify the firefox binary location or install firefox")
        return start_cmd

    def _default_windows_location(self):
        program_files = [os.getenv("PROGRAMFILES", r"C:\Program Files"),
                         os.getenv("PROGRAMFILES(X86)", r"C:\Program Files (x86)")]
        for path in program_files:
            binary_path = os.path.join(path, r"Mozilla Firefox\firefox.exe")
            if os.access(binary_path, os.X_OK):
                return binary_path
        return ""

    def _modify_link_library_path(self):
        existing_ld_lib_path = os.environ.get('LD_LIBRARY_PATH', '')

        new_ld_lib_path = self._extract_and_check(
            self.profile, self.NO_FOCUS_LIBRARY_NAME, "x86", "amd64")

        new_ld_lib_path += existing_ld_lib_path

        self._firefox_env["LD_LIBRARY_PATH"] = new_ld_lib_path
        self._firefox_env['LD_PRELOAD'] = self.NO_FOCUS_LIBRARY_NAME

    def _extract_and_check(self, profile, no_focus_so_name, x86, amd64):

        paths = [x86, amd64]
        built_path = ""
        for path in paths:
            library_path = os.path.join(profile.path, path)
            if not os.path.exists(library_path):
                os.makedirs(library_path)
            import shutil
            shutil.copy(os.path.join(
                os.path.dirname(__file__),
                path,
                self.NO_FOCUS_LIBRARY_NAME),
                library_path)
            built_path += library_path + ":"

        return built_path

    def which(self, fname):
        """Returns the fully qualified path by searching Path of the given
        name"""
        for pe in os.environ['PATH'].split(os.pathsep):
            checkname = os.path.join(pe, fname)
            if os.access(checkname, os.X_OK) and not os.path.isdir(checkname):
                return checkname
        return None
