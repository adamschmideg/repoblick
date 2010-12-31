from store import SqliteStore

from utils import relative_file

def first_commits(dbpath):
  '''
  When contributors made their first commits in each project.
  '''
  store = SqliteStore(dbpath)
  script = relative_file(__file__, 'stat.sql')
  with open(script) as query:
    store.cursor.executescript(query.read())
  store.cursor.execute('''
    select projectid, date(date), author, rank, ncommits, round(days), lines, files
    from joininfo
    order by projectid, rank''', [])
  for rec in store.cursor:
    print rec


if __name__ == '__main__':
  first_commits('/tmp/lof.sqlite')
