# ExecAfterDownload written by AaronM / mcd1992.
# If there are any issues with this postprocessor please contact me via github or admin@fgthou.se

import os, re, shlex
from ..utils import PostProcessingError

class ExecAfterDownload( object ):
    _downloader = None

    def __init__( self, downloader = None, commandString = None ):
        self._downloader = downloader
        self.commandString = commandString

    def set_downloader( self, downloader ):
        """Sets the downloader for this PP."""
        self._downloader = downloader

    def run( self, information ):
        self.targetFile = information["filepath"]
        self.finalCommand = None;

        if( re.search( '{}', self.commandString ) ): # Find and replace all occurrences of {} with the file name.
            self.finalCommand = re.sub( "{}", '\'' + self.targetFile + '\'', self.commandString )
        else:
            self.finalCommand = self.commandString + ' \'' + self.targetFile + '\''

        if( self.finalCommand ):
            print( "[exec] Executing command: " + self.finalCommand )
            os.system( self.finalCommand )
        else:
            raise PostProcessingExecError( "Invalid syntax for --exec post processor" )

        return None, information  # by default, keep file and do nothing

class PostProcessingExecError( PostProcessingError ):
    pass
