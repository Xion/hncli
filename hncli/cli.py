'''
Command line interface.
'''
import cmd
import os
import sys
import re
import getpass
import webbrowser

from . import hn
from .utils import cast, get_terminal_size, break_lines


class HackerNews(cmd.Cmd):
    ''' Command-line shell for Hacker News. '''
    ROOT_DIRS = ['top', 'new', 'threads', 'comments', 'ask', 'jobs']
    ALL_STORIES_DIRS = ['all', 'stories', 's']

    def __init__(self, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs) # cmd.Cmd is old-style class!
        self.hn_client = hn.Client()
        self.story_dirs = {}    # root_dir -> list of IDs
        self.stories = {}       # story_id -> Story object

        self.pwd = "/"
        self.prompt = self._format_prompt()

    def _format_prompt(self):
        ''' Formats the prompt, showing current user (if any)
        and "path" within the Hacker News website.
        '''
        if self.hn_client.authenticated:
            user = self.hn_client.user_name
            points = "(%s)" % self.hn_client.user_points
        else:
            user, points = "guest", ""
        pwd = self.pwd

        prompt = "{user}{points}@hn:{pwd}$ "
        return prompt.format(**locals())

    def _absolute_path(self, path):
        ''' Converts given path into absolute one,
        based on current "directory".
        Does nothing if path is already absolute.
        '''
        path = path.strip()
        if not path:
            path = '.'

        if path.startswith('/'):
            pwd = path
        else:
            pwd = os.path.join(self.pwd, path)
            pwd = os.path.normpath(pwd)

        return pwd

    def postcmd(self, stop, line):
        ''' Post-command hook. Modifies the prompt to show
        information about HN user, if any.
        '''
        self.prompt = self._format_prompt()

    def onecmd(self, line):
        ''' Executing single command. But actually, there might
        be multiple commands separated by && so we support it here.
        '''
        if not '&&' in line:
            return cmd.Cmd.onecmd(self, line)

        cmds = [s.strip() for s in line.split('&&')]
        retvals = map(self.onecmd, cmds)
        return retvals[-1]

    def _help(self, command):
        ''' Returns the help text for given command. '''
        method = getattr(self, 'do_' + command, None)
        if not method:
            return None

        help = method.__doc__.splitlines()
        help = os.linesep.join('\t' + line.strip()
                               for line in help)
        help = command + ":" + os.linesep + help
        return help

    def _retrieve_stories(self, page, count=None):
        if isinstance(count, basestring):
            count = count.strip() or None
        if count is not None:
            count = cast(int, count, default=10)

        stories = self.hn_client.get_stories(page, count)
        return list(stories)

    def _get_story(self, dir, s):
        ''' Retrieves a Story object based on its Hacker News ID
        or position within one of the root "directories".
        '''
        if dir is None or dir in self.ALL_STORIES_DIRS:
            story_id = cast(int, s, None)    # actual HN story ID
            return self.stories.get(story_id)

        # here we assume we deal with index (position) within a directory
        idx = cast(lambda v: int(v, 16), s, None)
        if idx is not None:
            stories = self.story_dirs.get(dir, [])
            if 0 <= idx < len(stories):
                return stories[idx]


    def do_cd(self, path):
        ''' Goes to specified path within Hacker News website.
        This command should behave like regular shell's cd
        and handle both absolute and relative paths with .. and .
        '''
        self.pwd = self._absolute_path(path)

    def do_ls(self, args):
        ''' Lists items in current "directory". Depending on where
        we are, this can output several different types of results,
        including stories and comments.
        '''
        def ls(pwd):
            if pwd == '/':
                return '\t'.join(self.ROOT_DIRS)
            pwd = pwd.lstrip('/')
            
            # handle root "directories"
            story_pages = {
                'top': '/news',
                'new': '/newest',
                'ask': '/ask',
                'jobs': '/jobs',
            }
            if pwd in story_pages:
                stories = self._retrieve_stories(story_pages[pwd])
                for story in stories:
                    self.stories[story.id] = story
                self.stories[pwd] = [s.id for s in stories]
                return format_stories(stories)

            # handle stories, displaying their comments
            story_dirs = story_pages.keys() + self.ALL_STORIES_DIRS
            if any(pwd.startswith(sp + '/') for sp in story_dirs):
                story = self._get_story(*pwd.split('/', 1))
                if not story:
                    return "ls: cannot list items at this location"
                comments = self.hn_client.get_comments(story.id)
                if not comments:
                    print "ls: no comments for this story"
                return format_comments(comments)

        pwd = self._absolute_path(args)
        res = ls(pwd)
        if res: print res


    def do_su(self, user):
        ''' Login to Hacker News as given user. '''
        user = user.strip()
        if not user:
            print "*** No username provided"
            return

        password = getpass.getpass()
        success = self.hn_client.login(user, password)
        if not success:
            print "Authentication failed."

    def do_open(self, s):
        ''' Opens given story in a browser.
        Story is identified by a path that includes
        "directory" name and a hexademical index, e.g. /top/1e.
        '''
        pwd = self._absolute_path(s)[1:]
        story = self._get_story(*pwd.split('/', 1))
        if story:
            webbrowser.open(story.url)
        else:
            print "*** Unkown story: " + s

    def do_help(self, command):
        ''' Display help for given command. '''
        if command:
            help = self._help(command.strip())
            if help:
                print help
                return
        cmd.Cmd.do_help(self, command)

    def do_exit(self, _):
        ''' Exits the CLI. '''
        sys.exit()

    def emptyline(self):
        pass # do nothing (and don't repeat last command)


def format_stories(stories):
    ''' Formats a list Story objects, producing text output. '''
    if not stories:
        return ""

    lines = []
    number_width = len(hex(len(stories) - 1)[2:])   # for zero-padding
    for i, story in enumerate(stories):
        number = hex(i)[2:].rjust(number_width, '0') + ": "
        lines.append("%s%s (%s)" % (number, story.title, story.url))
        lines.append("%s%s | id=%s" % (" " * len(number), story.subtext, story.id))

    return os.linesep.join(lines)

def format_comments(comments, indent_width=4, recursive=True):
    ''' Formats a list of Comment objects, producing text output. '''
    if not comments:
        return ""

    console_width, _ = get_terminal_size()
    def format_comment(comment):
        ''' Helper function to format a single comment. '''
        indent = " " * (indent_width * comment.level)
        line_length = int(console_width * 0.95) - len(indent)
        comment_lines = break_lines(comment.text, line_length)
        indented_text = os.linesep.join(indent + line
                                        for line in comment_lines)

        return "%s%s (%s):\n%s\n" % (indent,
            comment.author, comment.time, indented_text)

    lines = []
    for i, comment in enumerate(comments):
        lines.append(format_comment(comment))
        if comment.replies:
            lines.append(format_comments(comment.replies))
            
    return os.linesep.join(lines)