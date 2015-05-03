import os
import hashlib

#Hash the file names to drop unicode characters for FFMPEG
def hashRename(fileN):
    ext = os.path.splitext(fileN)
    fileHash = hashlib.sha224(fileN.encode('utf-8')).hexdigest()
    hash_name = fileHash+ext[1]
    return hash_name