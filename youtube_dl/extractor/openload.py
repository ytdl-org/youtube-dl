# coding: utf-8
from __future__ import unicode_literals

import base64
import subprocess

from ..utils import (
    check_executable,
    encodeArgument,
    ExtractorError,
    get_exe_version,
)


class NodejsWrapper(object):
    """Node.js wrapper class"""

    @staticmethod
    def version():
        return get_exe_version('nodejs', version_re=r'([0-9.]+)')

    def __init__(self):
        self.exe = check_executable('nodejs', ['-v'])
        if not self.exe:
            raise ExtractorError('Node.js executable not found in PATH, '
                                 'download it from http://nodejs.org',
                                 expected=True)

    def run_in_sandbox(self, jscode, timeout=10000):
        """
        Executes JS in a sandbox

        Params:
            jscode: code to be executed
            timeout: number of milliseconds before execution is cancelled

        """
        jscode_wrapper = (
            'const vm = require("vm");'
            'const jscode = Buffer.from("{jscode_b64}", "base64").toString("binary");'
            'const options = {{timeout: {timeout:d}}};'
            'process.stdout.write(String(vm.runInNewContext(jscode, {{}}, options)));').format(
                jscode_b64=base64.b64encode(jscode.encode('utf-8')).decode(),
                timeout=timeout)
        args = [encodeArgument(a) for a in [self.exe, '-e', jscode_wrapper]]
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise ExtractorError(stderr.decode('utf-8', 'replace'))
        return stdout.decode('utf-8')
