
from subprocess import Popen, PIPE
from os import path
import csv, sys

def extract(repo, todir):
  style = path.join(path.dirname(__file__), 'style')
  p = Popen(['hg', 'log', '-R', repo, '--style', style, '-p'], stdout=PIPE)
  commits = csv.writer(open(path.join(todir, 'commits.txt'), 'w'))
  commits.writerow(['hash', 'date', 'author'])
  files = csv.writer(open(path.join(todir, 'files.txt'), 'w'))
  files.writerow(['hash', 'change', 'file'])
  chunks = csv.writer(open(path.join(todir, 'chunks.txt'), 'w'))
  chunks.writerow(['hash', 'file', 'firstLine', 'adds', 'dels'])
  inChunk = False
  for line in p.stdout.readlines():
    line = line.strip()
    if line.startswith('commit '):
      if inChunk:
        chunks.writerow([hash, file, firstLine, adds, dels])
        inChunk = False
      row = line[len('commit '):].split('|')
      hash = row[0]
      commits.writerow(row)
    elif line.startswith('file '):
      row = line[len('file '):].split('|')
      files.writerow([hash] + row) 
    elif line.startswith('diff '):
      if inChunk:
        chunks.writerow([hash, file, firstLine, adds, dels])
        inChunk = False
      file = line.split(' ')[-1]
    elif line.startswith('@@'):
      if inChunk:
        chunks.writerow([hash, file, firstLine, adds, dels])
      inChunk = True
      firstLine = int(line[len('@@ -'):].split(',', 1)[0])
      adds = 0
      dels = 0
    elif line.startswith('+++') or line.startswith('---'):
      pass
    elif line.startswith('+'):
      adds += 1
    elif line.startswith('-'):
      dels += 1



if __name__ == '__main__':
  extract(sys.argv[1], sys.argv[2])
