from datetime import timedelta
import os, time

class Timer:
    """Context manager for timing a code block, for example:

        with Timer('Foo'):
            foo(42)
    """
    def __init__(self, name):
        self.name =name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        end = time.time()
        print("%s:\t%0.11s" % (self.name, timedelta(seconds=elapsed)))

def fileSize(fileOrSize):
    """Human readable format of file size"""
    if type(fileOrSize) == str:
        size = os.stat(fileOrSize).st_size
    for x in ['bytes','KB','MB','GB','TB']:
        if size < 1024.0:
            return "%3.1f%s" % (size, x)
        size /= 1024.0

def makeInt(numStr):
    "Make an int from a string with thousands-separator"
    return int(numStr.replace(',', ''))

def relative_file(file, path):
    """Get a path relative to file"""
    return os.path.join(os.path.dirname(file), path)
