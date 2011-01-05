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

def custom_queries(store, image_dir, queries):
    '''Plot custom sql queries in a line chart'''
    fig = plt.figure()
    subplot = fig.add_subplot(111)
    for query in queries:
        store.cursor.execute(query, [])
        data =[rec[0] for rec in store.cursor]
        label = store.cursor.description[0][0]
        subplot.plot(data, label=label)
    subplot.legend()
    image_path = os.path.join(image_dir, 'custom.png')
    fig.savefig(image_path)
