from lxml import html
from urllib2 import urlopen

def list_repos(subpage='all/commits', count=20):
  repos = []
  for p in range(count / 20):
    url = 'https://bitbucket.org/repo/%s/%s' % (subpage, p + 1)
    print 'Opening', url
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
      repos.append((user, project, commits))
  return repos
