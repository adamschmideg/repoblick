from datetime import datetime, timedelta
from mercurial import patch, util
from subprocess import Popen, PIPE
import os

ADD = 'A'
MOD = 'M'
DEL = 'D'

class HgMirror:
  "Local mirror of a remote hg repo"

  def __init__(self, user, project, remoteRoot='https://bitbucket.org/', localRoot='/tmp'):
    self.remoteRoot = remoteRoot
    self.localRoot = localRoot
    self.user = user
    self.project = project

  @property
  def localRepo(self):
    return os.path.join(self.localRoot, self.user, self.project)

  @property
  def remoteRepo(self):
    return '%s/%s/%s' % (self.remoteRoot, self.user, self.project)

  def mirror(self, count=2):
    "Mirror count number of commits from remote to local"
    userDir = os.path.join(self.localRoot, self.user)
    if not os.path.exists(userDir):
      os.mkdir(userDir)
    if os.path.exists(self.localRepo):
      p = Popen(['hg', 'pull', '-r', str(count - 1), '-R', self.localRepo])
    else:
      p = Popen(['hg', 'clone', '-r', str(count - 1), self.remoteRepo, self.localRepo])
    p.wait()

  def commits(self):
    """Return (hash, date, author, message, files)
      where files is a dict mapping file name to change type"""
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
      yield hash, date, author, message, files
      

  def changes(self, rev, fileChanges):
    "Return (filename, changeType, addedLines, deletedLines, isBinary)"
    p = Popen(['hg', 'diff', '-R', self.localRepo, '-c', rev], stdout=PIPE)
    lines = util.iterlines(p.stdout.readlines())
    for f in patch.diffstatdata(lines):
      yield f[0], fileChanges[f[0]], f[1], f[2], f[3]
