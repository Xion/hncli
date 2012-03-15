#!/usr/bin/env python
'''
hncli -- Main entry point
'''
import cmd
import sys
import os
import re
import getpass
import webbrowser

from . import hn
from .utils import cast


class HackerNews(cmd.Cmd):
	''' Command-line shell for Hacker News. '''
	PROMPT = "hn$"

	def __init__(self, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)	# cmd.Cmd is old-style class!
		self.last_page = None
		self.stories = {}
		self.user = {}

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

	def _get_stories(self, page, count=None):
		if isinstance(count, basestring):
			count = count.strip() or None
		if count is not None:
			count = cast(int, count, default=10)

		page = hn.fetch_hn_page(page, self.user.get('token'))
		if page:
			self.last_page = page
			return list(hn.get_recent_stories(page, count))

	def _print_stories(self, stories):
		stories = stories or []
		number_width = len(hex(len(stories) - 1)[2:])	# for zero-padding
		for i, story in enumerate(stories):
			number = hex(i)[2:].rjust(number_width, '0') + ": "
			print "%s%s (%s)" % (number, story.title, story.url)
			print " " * len(number) + story.subtext

	def do_top(self, count):
		''' Retrieves the recent top stories (front page). '''
		stories = self._get_stories('/news', count)
		self._print_stories(stories)
		self.stories['top'] = stories

	def do_new(self, count):
		''' Retrieves the newest stories. '''
		stories = self._get_stories('/newest', count)
		self._print_stories(stories)
		self.stories['new'] = stories

	def do_auth(self, user):
		''' Login to Hacker News as given user. '''
		user = user.strip()
		if not user:
			print "*** No username provided"
			return

		password = getpass.getpass()
		auth_token = hn.login(user, password)
		if auth_token:
			self.user['token'] = auth_token
			self.last_page = hn.fetch_hn_page('/', auth_token)	# for prompt
		else:
			print "Authentication failed."

	def postcmd(self, stop, line):
		''' Post-command hook. Modifies the prompt to show
		information about HN user, if any.
		'''
		if not self.last_page:
			return
		user = hn.get_user_info(self.last_page) or {}
		if user:
			self.user.update(user)
			self.prompt = "%s:%s@%s " % (
				self.user['name'], self.user['points'], self.PROMPT)
		else:
			self.user = {}
			self.prompt = self.PROMPT + " "

	def do_open(self, story):
		''' Opens given story in a browser.
		Story is identified as an index, optionally preceeded
		by 'top' or 'new' and colon, e.g. top:5.
		'''
		try:
			col, idx = re.split(story,  r'\s+|(\s*\:\s*)')
		except ValueError:
			col, idx = 'top', story

		idx = cast(lambda v: int(v, 16), idx, None)
		if idx is not None:
			stories = self.stories.get(col)
			if 0 <= idx < len(stories):
				webbrowser.open(stories[idx].url)
				return

		print "*** Unkown story: %s" % story

	def do_help(self, command):
		''' Display help for given command. '''
		if command:
			help = self._help(command.strip())
			if help:
				print help
				return
		cmd.Cmd.do_help(self, command)

	def default(self, command):
		if command in ['exit', 'quit']:
			sys.exit()
		else:
			cmd.Cmd.default(self, command)

	def emptyline(self):
		pass # do nothing (and don't repeat last command)


def main():
	hncli = HackerNews()
	hncli.intro = "\n".join([
		"hncli :: command-line interface for Hacker News",
		"[Python %s on %s]" % (sys.version.splitlines()[0], sys.platform),
		"Use 'help' or type 'top' for front page stories.",
	])
	hncli.prompt = hncli.PROMPT + " "

	hncli.doc_header = "Supported commands"
	hncli.undoc_header = "Other commands"
	hncli.misc_header = "Help topics"
	hncli.ruler = "*"

	hncli.cmdloop()


if __name__ == '__main__':
	main()