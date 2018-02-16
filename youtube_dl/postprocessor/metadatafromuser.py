"""
Created on Fri Feb  9 16:23:16 2018
"""
from __future__ import unicode_literals
from .common import PostProcessor
import re


class MetadataFromUserPP(PostProcessor):
    def __init__(self, downloader, metadata):
        super(MetadataFromUserPP, self).__init__(downloader)
        self._metadata = metadata
        

    def run(self, info):
        lastpos = 0
        attribute = None
        # Search for key words
        for match in re.finditer(r'(\w+) *=', self._metadata):
            if attribute is not None:
                # The data exists between previous math end and new match start
                value = self._metadata[lastpos:match.start()].strip()
                self._downloader.to_screen(
                    '[fromuser] %s: %s'
                    %(attribute, value if value else 'NA'))
                info[attribute] = value
            attribute = match.group(1)    
            lastpos = match.end()

        if attribute is None:
            # No attributes is given user, default assume the text as album name
            attribute = 'album' 
        # Add the last key
        value = self._metadata[lastpos:].strip()
        self._downloader.to_screen(
            '[fromuser] %s: %s'
            %(attribute, value if value else 'NA'))
        info[attribute] = value

        # If nothing specified for artist, extract from comments/description
        if (('artist' not in info) and ('description' in info)):
            artist = re.findall('music(?![ia]).*$', info['description'], re.MULTILINE | re.IGNORECASE)
            artist = artist + re.findall('sing.*$', info['description'], re.MULTILINE | re.IGNORECASE)
            artist = ', '.join(artist).title().strip()
            
            self._downloader.to_screen(
                    '[artist] : %s : parsed from description' %(artist if artist else 'NA'))
            info['artist'] = artist
        
        return [], info
