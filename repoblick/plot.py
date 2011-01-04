import os

import matplotlib
matplotlib.use('Agg') #Default use Agg backend we don't need any interactive display
import matplotlib.pyplot as plt

from store import SqliteStore
from utils import relative_file

def first_commits(store, image_dir):
    '''
    When contributors made their first commits in each project.
    '''
    store.cursor.execute('select days from stat.joininfo order by days')
    days = [x[0] for x in store.cursor]
    store.cursor.execute('select ncommits from stat.joininfo order by ncommits')
    ncommits = [x[0] for x in store.cursor]
    store.cursor.execute('select lines/100 as lines from stat.joininfo order by lines')
    lines = [x[0] for x in store.cursor]
    fig = plt.figure()
    subplot = fig.add_subplot(111)
    subplot.plot(days, label='days')
    subplot.plot(ncommits, label='ncommits')
    subplot.plot(lines, label='1k lines')
    subplot.legend()
    image_path = os.path.join(image_dir, 'first-commits.png')
    fig.savefig(image_path)


if __name__ == '__main__':
    first_commits('/tmp/lof.sqlite')
