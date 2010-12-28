"""
Store repodata in a persistent format, like a database or csv files
"""
import sqlite3, time
from utils import Timer, fileSize

class SqliteStore:

  def __init__(self, path):
    self.path = path
    self.cursor = sqlite3.connect(path).cursor()
    tables = (
      '''
      projects (
        id integer primary key autoincrement,
        project text,
        host text,
        commits integer,
        watchers integer,
        forks integer,
        language text,
        cloned integer
      )''',
      '''
      commits (
        id integer primary key autoincrement,
        author text,
        date timestamp,
        hash text,
        projectid integer,
        foreign key(projectid) references projects(id)
      )''',
      '''
      files (
        id integer primary key autoincrement,
        commitid integer,
        changetype char(1),
        added integer,
        deleted integer,
        file text,
        isbinary boolean,
        foreign key(commitid) references commits(id)
      )''',
    )
    for t in tables:
      try:
        self.cursor.execute('create table if not exists %s;' % t)
      except sqlite3.OperationalError, e:
        print e, t
      
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
      for commit in mirror.commits():
        commitid = self.commit(projectid, commit)
        for fileChange in mirror.changes(commit):
          self.file(commitid, fileChange)
      self.cursor.connection.commit()
    print 'Storage used:\t%s' % fileSize(self.path)
