import os
import sys
from git import Repo
from git.exc import InvalidGitRepositoryError,NoSuchPathError
import re
from collections import namedtuple
import webbrowser


urlPatterns=[
  {
    # git@github.com:okar1/git_web_link.git
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
    # https://github.com/okar1/git_web_link.git
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


arg1=sys.argv[1] if len(sys.argv)>=2 else os.getcwd()
arg2=sys.argv[2] if len(sys.argv)>=3 else ''

absPath=(os.path.abspath(arg1))
lineToHighlight = False
if os.path.isfile(absPath) and arg2.isdigit():
    lineToHighlight=arg2

try:
  repo=Repo(absPath, search_parent_directories=True)
except (InvalidGitRepositoryError, NoSuchPathError):
  print(f"ERROR specified path {absPath} is not a part of valid git repository")
  print(f'''This script opens gitlab site for local file or directory
Usage: {os.path.basename(sys.argv[0])} [path] [line_number]
  path: local file or directory within git repo (default is current dir)
  line_number: file line number to highlight (default in no highlight)''')
  sys.exit(1)

if not repo.remotes:
  print('ERROR current repo does not have any remote origin')
  sys.exit(1)

remoteUrls = [url for url in [remote.url for remote in repo.remotes]]
if not remoteUrls:
  print('ERROR cant find any url in repo remotes list, check repo coonfig')
  sys.exit(1)
remoteUrl = remoteUrls[0]

if not absPath.startswith(repo.working_dir):
  print(f'ERROR something is wrong. Path to process "{absPath}" is not starting from git working dir "{repo.working_dir}"')
  sys.exit(1)

relativePath='' if absPath==repo.working_dir else absPath[len(repo.working_dir)+1:]
banchName = repo.active_branch.name


UrlPattern=namedtuple('UrlPattern','name findWhat replaceWith linkTypeFile linkTypeDir lineNumberSection')

for patternName, findWhat, replaceWith, linkTypeFile, linkTypeDir, lineNumberSection in map(lambda a: UrlPattern(**a), urlPatterns):
  webUrl = re.sub(findWhat, replaceWith, remoteUrl, flags=re.VERBOSE)
  if webUrl != remoteUrl:
    # replacement found
    webUrl = webUrl.format(
      branchName = banchName,
      path = relativePath,
      lineNumberSection = lineNumberSection.format(linenumber = lineToHighlight) if lineToHighlight else '',
      linkType = linkTypeFile if os.path.isfile(absPath) else linkTypeDir
    )
    print("found remote url", remoteUrl)
    print(f'converted to web url using pattern "{patternName}":', webUrl)
    webbrowser.open(webUrl)
    break
else:
  print(f'ERROR could not find replacement for origin "{remoteUrl}", check regex of urlPatterns')
  sys.exit(1)
