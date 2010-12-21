from lxml import html
from urllib2 import urlopen

def list_repos(subpage='all/commits', count=20):
  repos = []
  for p in range(count / 20):
    url = 'https://bitbucket.org/repo/%s/%s' % (subpage, p + 1)
    print 'Opening', url
    page = html.parse(urlopen(url))
    links = page.xpath("/html/body/div/div/ul[@id='repositories']/li/dl/dd[@class='name']/a[2]/@href")
    for l in links:
      if l.startswith('http'):
        schema, _, domain, user, project, _ = l.split('/')
      else:
        _, user, project, _ = l.split('/')
      repos.append((user, project))
  return repos
