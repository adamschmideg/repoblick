"""
Store repodata in a persistent format, like a database or csv files
"""
import os, sqlite3, time
from utils import Timer, fileSize

class SqliteStore:

  def __init__(self, path):
    self.path = path
    self.cursor = sqlite3.connect(path).cursor()
    createScript = os.path.join(os.path.dirname(__file__), 'create.sql')
    with open(createScript) as script:
      self.cursor.executescript(script.read())
      
  def project(self, mirror):
    self.cursor.execute('''
      insert into projects (project, host, commits, watchers, forks, language)
      values(:project, :remoteRoot, :commitCount, :watchers, :forks, :language)''',
      mirror.__dict__)
    return self.cursor.lastrowid

  def commit(self, projectid, commit):
    self.cursor.execute('''
      insert into commits(author, date, hash, projectid)
      values(:author, :date, :hash, :projectid)''',
      dict(commit.__dict__, projectid=projectid))
    return self.cursor.lastrowid

  def file(self, commitid, fileChange):
    self.cursor.execute('''
      insert into files(file, commitid, changetype, added, deleted, isbinary)
      values(:filename, :commitid, :changeType, :addedLines, :deletedLines, :isBinary)''',
      dict(fileChange.__dict__, commitid=commitid))
    return self.cursor.lastrowid
    
  def importLog(self, mirror):
    "Import logs of a repoMirror into this store"
    with Timer('Import %s' % mirror.project):
      try:
        projectid = self.project(mirror)
      except sqlite3.IntegrityError:
        # project already exists, delete its logs
        self.cursor.execute('''
          delete from files where commithash in
            (select hash from commits where project=?)''',
          (mirror.project,))
        self.cursor.execute('delete from commits where project=?',
          (mirror.project,))
      try:
        for commit in mirror.commits():
          commitid = self.commit(projectid, commit)
          for fileChange in mirror.changes(commit):
            self.file(commitid, fileChange)
        self.cursor.connection.commit()
      except:
        self.cursor.connection.rollback()
        print 'Failed to import', mirror
        raise
    print 'Storage used:\t%s' % fileSize(self.path)
