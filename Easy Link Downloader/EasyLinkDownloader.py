from __future__ import unicode_literals
from pip._vendor.distlib.compat import raw_input
from urllib import request
from unidecode import unidecode
import time
import os
import youtube_dl
import sys
import json
'''This receives a search parameter of type string
    Then, it escapes that string, example "Hey Jude" -> "Hey%20Jude"
    It makes a URL request to 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='+search' a google API tool
    Then it takes the result from the query (A number of website google has found, takes the first link, and returns the link to be downloaded
'''

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')
            
class NotYoutubeLinkError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NotValidSongError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def getURL(search):
    final = None
    original = search
    search = unidecode(search)
    try:
        print("The item to be searched: ",search)
        search = search.replace(' ', '%20')
        print("Converted string: ", search)
        
        rawdata = request.urlopen("http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q="+(search))
        result = json.loads(rawdata.readall().decode('utf-8'))
        searchResults = result['responseData']['results']
        
        final = searchResults[0]['unescapedUrl']
    except Exception as e:
        if (search == "\n"):
            printEnd()
        else:
            print(e)
            print("You need to switch your VPN! Start next download with :", original)
        raw_input()
        getURL(search)
        
    return final

def printEnd():
    print("All songs searched, check Faliure.txt and Success.txt for more info")  
    print("Press enter to exit")
    raw_input()
    sys.exit()


'''Begin Main'''
 
print("Press enter to search \"Download.txt\". PLEASE READ THE README FILE:")
raw_input()
print("Enter number to specify where you want to get your song from (Press enter if you don't care)")
print("1. Youtube \n2. Soundcloud")
x = raw_input()

#Opens text file, Download = source               
f1 = open("Download.txt", "r")
songs = []
       
for i, line in enumerate(f1):
    line = line[:-1]
    songs.append(line)

f1.close()

currentDate = time.strftime("%Y-%m-%d - %H-%M-%S")
for element in songs:
    #Options for Youtube_DL, read the documentation on github
    ydl_opts = {'outtmpl': os.getcwd()+'/links/'+element+'.%(ext)s',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
        
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if (x == 1):
            element += " youtube"
        if (x == 2):
            element += " soundcloud" 
            
        url = getURL(element)
        print("URL: ",url,"\n")
        
        try:
            if not 'youtube' in url:
                raise NotYoutubeLinkError("NotYoutubeLinkError: Not a youtube Link!")
            
            ydl.download([url])
        except Exception as ex:
            print(ex)
printEnd()
