
from subprocess import Popen, PIPE
from os import path
import sys

def extract(repo):
  style = path.join(path.dirname(__file__), 'style')
  p = Popen(['hg', 'log', '-R', repo, '--style', style, '-p'], stdout=PIPE)
  for line in p.stdout.readlines():
    print line 


if __name__ == '__main__':
  print 'hej'
  extract(sys.argv[1])
