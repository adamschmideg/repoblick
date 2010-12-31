import matplotlib
matplotlib.use('Agg') #Default use Agg backend we don't need any interactive display
import matplotlib.pyplot as plt

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
    select projectid, date(date), author, rank, ncommits, round(days) as days, lines, files
    from joininfo
    order by projectid, rank''', [])
  lines = []
  rank = []
  for rec in store.cursor:
    lines.append(rec['lines'])
    rank.append(rec['rank'])
  fig = plt.figure()
  subplot = fig.add_subplot(111)
  subplot.plot(rank, lines, 'o')
  fig.savefig('/tmp/plot.png')


if __name__ == '__main__':
  first_commits('/tmp/lof.sqlite')
