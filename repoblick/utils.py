from contextlib import contextmanager
from datetime import timedelta
import os
import tempfile
import time

class Timer:
    """Context manager for timing a code block, for example:

        with Timer('Foo'):
            foo(42)
    """
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        elapsed = time.time() - self.start
        print("%s:\t%0.11s" % (self.name, timedelta(seconds=elapsed)))


@contextmanager
def TempDir(suffix='', prefix='tmp'):
    "Context manager creating a temp dir, then deleting it on exit"
    dirname = tempfile.mkdtemp(suffix=self.suffix, prefix=self.prefix)
    yield dirname
    os.removedirs(self.dirname)


def file_size(file_or_size):
    """Human readable format of file size"""
    if type(file_or_size) == str:
        size = os.stat(file_or_size).st_size
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f%s" % (size, x)
        size /= 1024.0

def make_int(num_str):
    "Make an int from a string with thousands-separator"
    return int(num_str.replace(',', ''))

def relative_file(fname, path):
    """Get a path relative to file"""
    return os.path.join(os.path.dirname(fname), path)

def mkdirs(path):
    """Make possibly directories if they don't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
