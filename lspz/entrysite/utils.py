
import datetime
import urllib
import os


def escape_url(url):
    return urllib.parse.quote_plus(url)

def peek(f, length=1):
    pos = f.tell()
    data = f.read(length) # Might try/except this line, and finally: f.seek(pos)
    f.seek(pos)
    return data

def get_file_chunk(filelike, byte1=0, byte2=None, maxchunksize=None):
    """Returns the binary chunk of a file-like object:
    return: (chunk, chunk_start, chunk_length, total_file_size)

    Winds the file position back to zero after operation
    """
    filelike.seek(0,2)
    f_length = filelike.tell()
    start = 0

    if byte1 < f_length:
        start = byte1
    if byte2:
        bytes_to_read = byte2 + 1 - start
    else:
        bytes_to_read = f_length - start

    if maxchunksize and bytes_to_read > maxchunksize:
        bytes_to_read = maxchunksize

    filelike.seek(start, 0) # 0 means from file head
    chunk = filelike.read(bytes_to_read)

    filelike.seek(0, 0)
    return (chunk, start, len(chunk), f_length)
