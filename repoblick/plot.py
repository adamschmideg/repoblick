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
    store.cursor.execute('select days from joininfo order by days')
    days = [x[0] for x in store.cursor]
    store.cursor.execute('select ncommits from joininfo order by ncommits')
    ncommits = [x[0] for x in store.cursor]
    store.cursor.execute('select lines/100 as lines from joininfo order by lines')
    lines = [x[0] for x in store.cursor]
    fig = plt.figure()
    subplot = fig.add_subplot(111)
    subplot.plot(days, label='days')
    subplot.plot(ncommits, label='ncommits')
    subplot.plot(lines, label='1k lines')
    subplot.legend()
    fig.savefig('/tmp/plot.png')


if __name__ == '__main__':
    first_commits('/tmp/lof.sqlite')
