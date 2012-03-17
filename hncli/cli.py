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

    def __init__(self, *args, **kwargs):
        cmd.Cmd.__init__(self, *args, **kwargs) # cmd.Cmd is old-style class!
        self.hn_client = hn.Client()
        self.stories = {}
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
        idx = cast(lambda v: int(v, 16), s, None)
        if idx is not None:
            stories = self.stories.get(dir, [])
            if 0 <= idx < len(stories):
                return stories[idx]


    def do_cd(self, path):
        ''' Goes to specified path within Hacker News website.
        This command should behave like regular shell's cd
        and handle both absolute and relative paths with .. and .
        '''
        path = path.strip()
        if not path:
            path = '.'

        if path.startswith('/'):
            pwd = path
        else:
            pwd = os.path.join(self.pwd, path)
            pwd = os.path.normpath(pwd)

        self.pwd = pwd

    def do_ls(self, args):
        ''' Lists items in current "directory". Dependning on where
        we are, this can output several different types of results,
        including stories and comments.
        '''
        def ls(pwd):
            if pwd == '/':
                return '\t'.join(self.ROOT_DIRS)
            pwd = pwd.lstrip('/')
            
            # handle root "directories" and stories inside them
            story_pages = {
                'top': '/news',
                'new': '/newest',
                'ask': '/ask',
                'jobs': '/jobs',
            }
            if pwd in story_pages:
                stories = self._retrieve_stories(story_pages[pwd])
                self.stories[pwd] = stories
                return format_stories(stories)
            if any(pwd.startswith(sp) for sp in story_pages):
                story = self._get_story(*pwd.split('/', 1))
                if not story:
                    return "ls: cannot list items at this location"
                comments = self.hn_client.get_comments(story.id)
                if not comments:
                    print "ls: no comments for this story"
                return format_comments(comments)

        res = ls(self.pwd)
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
        Story is identified as an index, optionally preceeded
        by 'top' or 'new' and colon, e.g. top:5.
        '''
        story = self._get_story(s)
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

    def default(self, command):
        ''' Executed when command cannot be (easily) recognized.
        It first tries to make a simple prefix-based match
        and delegates execution to base Cmd logic should it fail.
        '''
        def make_cmd_func(name):
            return lambda arg: self.onecmd('%s %s' % (name, arg))

        # not quite a prefix tree :)
        commands = {}
        commands['exit'] = commands['quit'] = lambda _: sys.exit()
        for name, m in self.__class__.__dict__.iteritems():
            if not (callable(m) and name.startswith('do_')):
                continue
            name = name[len('do_'):]
            commands[name] = make_cmd_func(name)

        # look for a single match and call it
        parts = command.split()
        matches = [c for c in commands if c.startswith(parts[0])]
        if len(matches) == 1:
            cmd_func = commands[matches[0]]
            arg = parts[1] if len(parts) > 1 else ''
            cmd_func(arg)
        else:
            cmd.Cmd.default(self, command)

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
        lines.append(" " * len(number) + story.subtext)

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