from datetime import datetime, timedelta
from mercurial import patch, util
from subprocess import Popen, PIPE
import os

ADD = 'A'
MOD = 'M'
DEL = 'D'

class Commit:
  "Info for one changeset"
  def __init__(self, hash, date, author, message, fileChanges):
    self.hash = hash
    self.date = date
    self.author = author
    self.message = message
    self.fileChanges = fileChanges


class FileChange:
  "Info about how a file was changed"
  def __init__(self, filename, commitHash, changeType, addedLines, deletedLines, isBinary):
    self.filename = filename
    self.commitHash = commitHash
    self.changeType = changeType
    self.addedLines = addedLines
    self.deletedLines = deletedLines
    self.isBinary = isBinary


class HgMirror:
  "Local mirror of a remote hg repo"

  def __init__(self, owner, project, remoteRoot='https://bitbucket.org/', localRoot='/tmp'):
    self.remoteRoot = remoteRoot
    self.localRoot = localRoot
    self.owner = owner
    self.project = project

  @property
  def localRepo(self):
    return os.path.join(self.localRoot, self.owner, self.project)

  @property
  def remoteRepo(self):
    return '%s/%s/%s' % (self.remoteRoot, self.owner, self.project)

  def mirror(self, count=2):
    "Mirror count number of commits from remote to local"
    ownerDir = os.path.join(self.localRoot, self.owner)
    if not os.path.exists(ownerDir):
      os.mkdir(ownerDir)
    devnull = open(os.devnull, 'w')
    if os.path.exists(self.localRepo):
      if count:
        p = Popen(['hg', 'pull', '-r', str(count - 1), '-R', self.localRepo], stdout=devnull)
      else:
        p = Popen(['hg', 'pull', '-R', self.localRepo], stdout=devnull)
    else:
      if count:
        p = Popen(['hg', 'clone', '-r', str(count - 1), self.remoteRepo, self.localRepo], stdout=devnull)
      else:
        p = Popen(['hg', 'clone', self.remoteRepo, self.localRepo], stdout=devnull)
    p.wait()
    devnull.close()

  def commits(self):
    """Return Commit instances"""
    dir = os.path.dirname(__file__)
    style = os.path.join(dir, 'hg/style')
    p = Popen(['hg', 'log', '-R', self.localRepo, '--style', style], stdout=PIPE)
    def fileSplit(line):
      if line:
        return line.split(';')
      else:
        return ()
    for line in p.stdout.readlines():
      line = line.rstrip()
      hash, date, author, message, files_add, files_mod, files_del = line.split('|')
      ts, offset = [int(d) for d in date.split(' ')]
      date = datetime.fromtimestamp(ts) + timedelta(seconds=offset)
      files = {}
      for f in fileSplit(files_add):
        files[f] = ADD
      for f in fileSplit(files_mod):
        files[f] = MOD
      for f in fileSplit(files_del):
        files[f] = DEL
      yield Commit(hash, date, author, message, files)

  def changes(self, commit):
    "Return FileChange instances"
    p = Popen(['hg', 'diff', '-R', self.localRepo, '-c', commit.hash], stdout=PIPE)
    lines = util.iterlines(p.stdout.readlines())
    for f in patch.diffstatdata(lines):
      yield FileChange(f[0], commit.hash, commit.fileChanges[f[0]], f[1], f[2], f[3])
