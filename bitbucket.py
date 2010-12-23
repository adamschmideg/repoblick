from lxml import html
from urllib2 import urlopen
from subprocess import Popen, PIPE
import os, re

def list_repos(subpage='all/commits', count=20):
  for p in range(count / 20):
    url = 'https://bitbucket.org/repo/%s/%s' % (subpage, p + 1)
    page = html.parse(urlopen(url))
    projects = page.xpath("/html/body/div/div/ul[@id='repositories']/li/dl")
    for prj in projects:
      link = prj.xpath("dd[@class='name']/a[2]/@href")[0]
      commits = prj.xpath("dd[@class='commits']/div/span[1]/a/text()")[0]
      commits = int(commits.replace(',', ''))
      if link.startswith('http'):
        schema, _, domain, user, project, _ = link.split('/')
      else:
        _, user, project, _ = link.split('/')
      yield (user, project, commits)

def repo_inits(user, project, dir='/tmp', count=2):
  """Get count number of initial changes [(files, lines_added, lines_removed)]"""
  result = []
  user_dir = os.path.join(dir, user)
  if not os.path.exists(user_dir):
    os.mkdir(user_dir)
  orig_repo = 'https://bitbucket.org/%s/%s' % (user, project)
  clone_repo = os.path.join(user_dir, project)
  if os.path.exists(clone_repo):
    p = Popen(['hg', 'pull', '-r', str(count - 1), '-R', clone_repo], stdout=PIPE)
  else:
    p = Popen(['hg', 'clone', '-r', str(count - 1), orig_repo, clone_repo], stdout=PIPE)
  p = Popen(['hg', 'log', '-R', clone_repo, '--template', '{diffstat}\n'], stdout=PIPE)
  for line in p.stdout.readlines():
    m = re.match('([0-9]+):\s*\+([0-9]+)/\-([0-9]+)', line)
    result.append([int(n) for n in m.groups()])
  return result
