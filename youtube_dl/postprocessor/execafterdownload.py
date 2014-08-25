from __future__ import unicode_literals
from .common import PostProcessor
from ..utils import PostProcessingError
import subprocess
import shlex


class ExecAfterDownloadPP(PostProcessor):
    def __init__(self, downloader=None, verboseOutput=None, commandString=None):
        self.verboseOutput = verboseOutput
        self.commandString = commandString

    def run(self, information):
        self.targetFile = information['filepath'].replace('\'', '\'\\\'\'')  # Replace single quotes with '\''
        self.commandList = shlex.split(self.commandString)
        self.commandString = ''

        # Replace all instances of '{}' with the file name and convert argument list to single string.
        for index, arg in enumerate(self.commandList):
            if(arg == '{}'):
                self.commandString += '\'' + self.targetFile + '\' '
            else:
                self.commandString += arg + ' '

        if self.targetFile not in self.commandString:  # Assume user wants the file appended to the end of the command if no {}'s were given.
            self.commandString += '\'' + self.targetFile + '\''

        print("[exec] Executing command: " + self.commandString)
        self.retCode = subprocess.call(self.commandString, shell=True)
        if(self.retCode < 0):
            print("[exec] WARNING: Command exited with a negative return code, the process was killed externally. Your command may not of completed succesfully!")
        elif(self.verboseOutput):
            print("[exec] Command exited with return code: " + str(self.retCode))

        return None, information  # by default, keep file and do nothing


class PostProcessingExecError(PostProcessingError):
    pass
