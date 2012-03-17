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
	PROMPT = "hn$"

	def __init__(self, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)	# cmd.Cmd is old-style class!
		self.prompt = self.PROMPT + " "
		self.hn_client = hn.Client()
		self.stories = {}

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

		stories = self.hn_client.get_stores(page, count)
		return list(stories)

	def _print_stories(self, stories):
		stories = stories or []
		number_width = len(hex(len(stories) - 1)[2:])	# for zero-padding
		for i, story in enumerate(stories):
			number = hex(i)[2:].rjust(number_width, '0') + ": "
			print "%s%s (%s)" % (number, story.title, story.url)
			print " " * len(number) + story.subtext

	def _get_story(self, story):
		''' Returns a story for given "pointer", e.g. top:5
		gives the one from recent results of 'top' command with index 5.
		None is returned if story cannot be found.
		'''
		try:
			col, idx = re.split(story,  r'\s+|(\s*\:\s*)')
		except ValueError:
			col, idx = 'top', story

		idx = cast(lambda v: int(v, 16), idx, None)
		if idx is not None:
			stories = self.stories.get(col, [])
			if 0 <= idx < len(stories):
				return stories[idx]


	def do_top(self, count):
		''' Retrieves the recent top stories (front page). '''
		stories = self._retrieve_stories('/news', count)
		self._print_stories(stories)
		self.stories['top'] = stories

	def do_new(self, count):
		''' Retrieves the newest stories. '''
		stories = self._retrieve_stories('/newest', count)
		self._print_stories(stories)
		self.stories['new'] = stories

	def do_auth(self, user):
		''' Login to Hacker News as given user. '''
		user = user.strip()
		if not user:
			print "*** No username provided"
			return

		password = getpass.getpass()
		success = self.hn_client.login(user, password)
		if not success:
			print "Authentication failed."

	def postcmd(self, stop, line):
		''' Post-command hook. Modifies the prompt to show
		information about HN user, if any.
		'''
		if self.hn_client.authenticated:
			self.prompt = "%s:%s@%s " % (self.hn_client.user_name,
				self.hn_client.user_points, self.PROMPT)
		else:
			self.prompt = self.PROMPT + " "

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

	def do_comments(self, s):
		''' Shows top-level comments for given story. '''
		story = self._get_story(s)
		if not story:
			print "*** Unknown story: " + s
			return
		
		comments = self.hn_client.get_comments(story.id)
		if not comments:
			print "No comments for this story"

		console_width, _ = get_terminal_size()
		for i, c in enumerate(comments):
			last = i + 1 == len(comments)
			level = c.level + 1 # sometimes you actually want to count from 1
			
			line_indent = ("|" if not last else " ") + " " * (3 * level - 1)
			lines = break_lines(c.text,
								int(console_width * 0.95) - len(line_indent))
			indented_text = "\n".join(line_indent + line
									  for line in lines)
			header_indent = "+" + "-" * (3 * level - 2) + " "

			print "%s%s (%s):\n%s" % (header_indent,
				c.author, c.time, indented_text)
			if not last:
				print "|"

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
