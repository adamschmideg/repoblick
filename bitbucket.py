from lxml import html
from urllib2 import urlopen
from subprocess import Popen, PIPE
import os, re
from utils import Timer

def makeInt(numStr):
  "Make an int from a string with thousands-separator"
  return int(numStr.replace(',', ''))

def listRepos(subpage='all/commits', count=20):
  for p in range(count / 20):
    url = 'https://bitbucket.org/repo/%s/%s' % (subpage, p + 1)
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

