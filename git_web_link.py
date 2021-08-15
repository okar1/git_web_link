# Script opens gitlab/github/stash/etc web page for current local file/dir within your repo.


# use "pip install GitPython" to install this external module
from git import Repo
import os
import sys
from git.exc import InvalidGitRepositoryError, NoSuchPathError
import re
from collections import namedtuple
import webbrowser
import argparse

# Configurable regex patterns for subversion systems. First matched pattern will be used.
urlPatterns = [
    {
        # like git@github.com:okar1/git_web_link.git
        "name": "github ssh",
        "findWhat": r"""^
        # ssh
        (ssh://)?
        # git@, optional
        ((\w|_|-|\.)+@)?
        # github.com
        (?P<host>github(\w|_|-|\.)+)
        # :okar1
        :
        (?P<login>(\w|_|-|\.)+)
        /
        # git_web_link.git
        (?P<group_and_repo>(\w|_|-|\.|/)+)
        .git
        $""",
        "replaceWith": r"https://\g<host>/\g<login>/\g<group_and_repo>/{linkType}/{branchName}/{path}{lineNumberSection}",
        "lineNumberSection": "#L{linenumber}",
        "linkTypeFile": "blob",
        "linkTypeDir": "tree"
    },
    {
        # like https://github.com/okar1/git_web_link.git
        "name": "github https",
        "findWhat": r"""^
        # https
        (https://)?
        # github.com
        (?P<host>github(\w|_|-|\.)+)
        # :okar1
        /
        (?P<login>(\w|_|-|\.)+)
        /
        # git_web_link.git
        (?P<group_and_repo>(\w|_|-|\.|/)+)
        .git
        $""",
        "replaceWith": r"https://\g<host>/\g<login>/\g<group_and_repo>/{linkType}/{branchName}/{path}{lineNumberSection}",
        "lineNumberSection": "#L{linenumber}",
        "linkTypeFile": "blob",
        "linkTypeDir": "tree"
    },
    {
        "name": "stash ssh and https",
        "findWhat": r"""^
        # ssh
        (?P<proto>ssh|http|https)
        ://
        # git@, optional
        (?P<user>(\w|_|-|\.)+@)?
        # stash.mysite.com
        (?P<host>stash(\w|_|-|\.)+)
        # :7999, optional
        (?P<port>:\d+)?
        /
        # project
        (?P<project>(\w|_|-|\.)+)
        /
        # path/to/my/repo
        (?P<group_and_repo>(\w|_|-|\.|/)+)
        .git
        $""",
        "replaceWith": r"https://\g<host>/projects/\g<project>/repos/\g<group_and_repo>/browse/{path}?at=refs%2Fheads%2F{branchName}{lineNumberSection}",
        "lineNumberSection": "#{linenumber}",
        "linkTypeFile": None,
        "linkTypeDir": None
    },
    {
        "name": "gitlab ssh and https",
        "findWhat": r"""^
        # ssh
        (?P<proto>ssh|http|https)
        ://
        # git@, optional
        (?P<user>(\w|_|-|\.)+@)?
        # stash.mysite.com
        (?P<host>(\w|_|-|\.)+)
        # :7999, optional
        (?P<port>:\d+)?
        /
        # project
        (?P<project>(\w|_|-|\.)+)
        /
        # path/to/my/repo
        (?P<group_and_repo>(\w|_|-|\.|/)+)
        .git
        $""",
        "replaceWith": r"https://\g<host>/\g<project>/\g<group_and_repo>/-/{linkType}/{branchName}/{path}{lineNumberSection}",
        "lineNumberSection": "#L{linenumber}",
        "linkTypeFile": "blob",
        "linkTypeDir": "tree"
    },
]


parser = argparse.ArgumentParser(
    description='Script opens gitlab/github/stash/etc web page for current local file/dir within your repo.')
parser.add_argument('path', type=str, nargs='?', default=os.getcwd(), help='path to local file or dir within repo')
parser.add_argument('lineToHighlight', type=int, nargs='?', default=0, help='line number to highlight in git site')

args = parser.parse_args()

absPath = os.path.abspath(args.path)
lineToHighlight = args.lineToHighlight if os.path.isfile(absPath) else 0

try:
  repo = Repo(absPath, search_parent_directories=True)
except (InvalidGitRepositoryError, NoSuchPathError):
  parser.print_help()
  print(
      f"ERROR specified path {absPath} is not a part of valid git repository")
  sys.exit(1)

if not repo.remotes:
  parser.print_help()
  print('ERROR current repo does not have any remote origin')
  sys.exit(1)

remoteUrls = [url for url in [remote.url for remote in repo.remotes]]
if not remoteUrls:
  parser.print_help()
  print('ERROR cant find any url in repo remotes list, check repo coonfig')
  sys.exit(1)
remoteUrl = remoteUrls[0]

if not absPath.startswith(repo.working_dir):
  parser.print_help()
  print(
      f'ERROR something is wrong. Path to process "{absPath}" is not starting from git working dir "{repo.working_dir}"')
  sys.exit(1)

relativePath = '' if absPath == repo.working_dir else absPath[len(
    repo.working_dir) + 1:]
banchName = repo.active_branch.name


UrlPattern = namedtuple(
    'UrlPattern', 'name findWhat replaceWith linkTypeFile linkTypeDir lineNumberSection')

for patternName, findWhat, replaceWith, linkTypeFile, linkTypeDir, lineNumberSection in map(lambda a: UrlPattern(**a), urlPatterns):
  webUrl = re.sub(findWhat, replaceWith, remoteUrl, flags=re.VERBOSE)
  if webUrl != remoteUrl:
    # replacement found
    webUrl = webUrl.format(
        branchName=banchName,
        path=relativePath,
        lineNumberSection=lineNumberSection.format(
            linenumber=lineToHighlight) if lineToHighlight else '',
        linkType=linkTypeFile if os.path.isfile(absPath) else linkTypeDir
    )
    print("found remote url", remoteUrl)
    print(f'converted to web url using pattern "{patternName}":', webUrl)
    webbrowser.open(webUrl)
    break
else:
  print(
      f'ERROR could not find replacement for origin "{remoteUrl}", check regex of urlPatterns')
  sys.exit(1)
