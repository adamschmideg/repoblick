"""
Store repodata in a persistent format, like a database or csv files
"""
import sqlite3, time
from utils import Timer

class SqliteStore:

  def __init__(self, path):
    self.path = path
    self.connection = sqlite3.connect(path)
    tables = (
      '''
      projects (
        project text primary key
      )''',
      '''
      commits (
        author text,
        date timestamp,
        hash text primary key,
        project text,
        foreign key(project) references projects(project)
      )''',
      '''
      files (
        commithash text,
        changetype char(1),
        added integer,
        deleted integer,
        file text,
        isbinary boolean,
        foreign key(commithash) references commits(hash)
      )''',
    )
    for t in tables:
      try:
        self.connection.execute('create table if not exists %s;' % t)
      except sqlite3.OperationalError, e:
        print e, t
      
  def project(self, owner, name):
    project = '%s/%s' % (owner, name)
    self.connection.execute('insert into projects values(?)', (project,))
    return project

  def commit(self, commit):
    self.connection.execute('''
      insert into commits(author, date, hash, project)
      values(:author, :date, :hash, :project)''',
      commit.__dict__)
    return hash

  def file(self, fileChange):
    self.connection.execute('''
      insert into files(file, commithash, changetype, added, deleted, isbinary)
      values(:filename, :commitHash, :changeType, :addedLines, :deletedLines, :isBinary)''',
      fileChange.__dict__)
    
  def importLog(self, mirror):
    "Import logs of a repoMirror into this store"
    with Timer('Import %s' % mirror.project):
      try:
        project = self.project(mirror.owner, mirror.project)
      except sqlite3.IntegrityError:
        # project already exists, delete its logs
        project = '%s/%s' % (mirror.owner, mirror.project)
        self.connection.execute('''
          delete from files where commithash in
            (select hash from commits where project=?)''',
          (project,))
        self.connection.execute('delete from commits where project=?',
          (project,))
      cnt = 0
      for commit in mirror.commits():
        cnt += 1
        commit.project = project
        self.commit(commit)
        for fileChange in mirror.changes(commit):
          self.file(fileChange)
      self.connection.commit()
