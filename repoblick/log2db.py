from datetime import datetime, timedelta
from optparse import OptionParser
from mercurial import hg, patch, ui, util
from subprocess import Popen, PIPE
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from repoblick.store import SqliteStore
from repoblick.utils import Timer
from repoblick import repolist

ADD = 'A'
MOD = 'M'
DEL = 'D'

class Commit:
    "Info for one changeset"
    def __init__(self, hash_, date, author, message, file_changes):
        self.hash = hash_
        self.date = date
        self.author = unicode(author, errors='replace')
        self.message = unicode(message, errors='replace')
        self.file_changes = file_changes

    def __unicode__(self):
        return unicode(self.__dict__)


class FileChange:
    "Info about how a file was changed"
    def __init__(self, filename, change_type, added_lines, deleted_lines, is_binary):
        self.filename = unicode(filename, errors='replace')
        self.change_type = change_type
        self.added_lines = added_lines
        self.deleted_lines = deleted_lines
        self.is_binary = is_binary
