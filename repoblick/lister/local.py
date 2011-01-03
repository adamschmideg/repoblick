import os

def list_repos(host_info, start_page, pages):
    """List subdirectories under host_info.urnpattern as path which seem
    to contain a repository.  Ignore start_page and pages args"""
    #pylint: disable-msg=W0613
    if os.path.isdir(host_info.urnpattern):
        for dirname in os.listdir(host_info.urnpattern):
            if os.path.isdir(os.path.join(host_info.urnpattern, dirname, '.hg')):
                yield dirname, {}
