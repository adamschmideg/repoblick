from mercurial import patch, util
from subprocess import Popen, PIPE
import os

ADD = 'A'
MOD = 'M'
DEL = 'D'

def commits(repo):
  """Return (hash, date, author, message, files)
    where files is a dict mapping file name to change type"""
  dir = os.path.dirname(__file__)
  style = os.path.join(dir, 'hg/style')
  p = Popen(['hg', 'log', '-R', repo, '--style', style], stdout=PIPE)
  def fileSplit(line):
    if line:
      return line.split(';')
    else:
      return ()
  for line in p.stdout.readlines():
    line = line.rstrip()
    hash, date, author, message, files_add, files_mod, files_del = line.split('|')
    files = {}
    for f in fileSplit(files_add):
      files[f] = ADD
    for f in fileSplit(files_mod):
      files[f] = MOD
    for f in fileSplit(files_del):
      files[f] = DEL
    yield hash, date, author, message, files
    

def changes(repo, rev, fileChanges):
  "Return (filename, changeType, addedLines, deletedLines, isBinary)"
  p = Popen(['hg', 'diff', '-R', repo, '-c', rev], stdout=PIPE)
  lines = util.iterlines(p.stdout.readlines())
  for f in patch.diffstatdata(lines):
    yield f[0], fileChanges[f[0]], f[1], f[2], f[3]
