from optparse import OptionParser
from subprocess import Popen, PIPE
from urllib2 import urlopen
import os, re
from lxml import html
from utils import Timer, makeInt

class LocalLister:
  """List repos located in local file system, used mainly for testing."""

  def __init__(self, urnPattern):
    self.urnPattern = urnPattern
    self.name = 'local'

  def listRepos(self, startPage, pages):
    for dir in os.listdir(self.urnPattern):
      if os.path.isdir(dir):
        yield dir


class BitbucketWeb:
  """List repos reading bitbucket web pages and parsing them"""

  def __init__(self):
    self.urnPattern = 'https://bitbucket.org/%s'
    self.name = 'bitbucket'
    
  def listRepos(self, startPage, pages):
    subpage='all/commits'
    for p in range(startPage, startPage + pages):
      url = 'https://bitbucket.org/repo/%s/%s' % (subpage, p)
      with Timer('Read %s' % url):
        page = html.parse(urlopen(url))
      projects = page.xpath("/html/body/div/div/ul[@id='repositories']/li/dl")
      for prj in projects:
        commits = makeInt(prj.xpath("dd[@class='commits']/div/span[1]/a/text()")[0])
        followers = makeInt(prj.xpath("dd[@class='followers']/div/span[1]/a/text()")[0])
        forks = makeInt(prj.xpath("dd[@class='forks']/div/span[1]/a/text()")[0])
        link = prj.xpath("dd[@class='name']/a[2]/@href")[0]
        if link.startswith('http'):
          schema, _, domain, user, project, _ = link.split('/')
        else:
          _, user, project, _ = link.split('/')
        yield (user, project, commits, followers, forks)


KNOWN_HOSTS = {
  'bitbucket': BitbucketWeb,
  'bb': BitbucketWeb,
}

def listRepos(host, dbPath=None, startPage=1, pages=1):
  """List repos using lister.  If host is in KNOWN_HOSTS, use the class
  there.  Otherwise handle host as a local path.  If dbPath is None, print them to screen."""
  try:
    lister = KNOWN_HOSTS[host]()
  except KeyError:
    lister = LocalLister(host)
  if dbPath:
    pass
  else:
    print lister.name, lister.urnPattern
    for repo in lister.listRepos(startPage, pages):
      print repo

def main():
  parser = OptionParser(usage='usage: %prog [options] <host>',
    description='<host> is either a local path, or any of %s' % ','.join(KNOWN_HOSTS.keys()))
  parser.add_option('-d', '--dbpath', dest='dbPath',
    help='If not given, print repos on stdout')
  parser.add_option('-s', '--start', dest='startPage', default=1)
  parser.add_option('-p', '--pages', dest='pages', default=1)
  (options, args) = parser.parse_args()
  if (len(args) < 1):
    print 'Missing arguments.  Use --help for details'
  else:
    listRepos(args[0], dbPath=options.dbPath,
      startPage=options.startPage, pages=options.pages)


if __name__ == '__main__':
  main()
