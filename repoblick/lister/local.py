import os

def list_repos(host_info, start_index, index_count):
    """List subdirectories under host_info.urnpattern as path which seem
    to contain a repository."""
    idx = 1
    if os.path.isdir(host_info.urnpattern):
        for dirname in os.listdir(host_info.urnpattern):
            if os.path.isdir(os.path.join(host_info.urnpattern, dirname, '.hg')):
                idx += 1
                if start_index <= idx < index_count:
                    yield dirname, {}
