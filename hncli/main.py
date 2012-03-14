#!/usr/bin/env python
'''
hncli -- Main entry point
'''
import cmd
import sys
import re
import webbrowser

from . import hn


class HackerNews(cmd.Cmd):
	''' Command-line shell for Hacker News. '''

	def __init__(self, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)	# cmd.Cmd is old-style class!
		self.stories = {}

	def _help(self, command):
		''' Returns the help text for given command. '''
		method = getattr(self, 'do_' + command, None)
		if not method:
			return None
		help = method.__doc__.strip()
		return re.sub('\n\\s+', '\n', help)	# collapse some whitespace

	def _get_stories(self, count, page):
		if not count or len(str(count).strip()) == 0:
			count = 10
		count = int(count)
		return hn.get_recent_stories(count, page)

	def _print_stories(self, stories):
		for i, story in enumerate(stories):
			number = str(i) + ". "
			print "%s%s (%s)" % (number, story.title, story.url)
			print " " * len(number) + story.subtext

	def do_top(self, count):
		''' Retrieves the recent top stories (front page). '''
		stories = self._get_stories(count, '/news')
		self._print_stories(stories)
		self.stories['top'] = stories

	def do_new(self, count):
		''' Retrieves the newest stories. '''
		stories = self._get_stories(count, '/newest')
		self._print_stories(stories)
		self.stories['new'] = stories

	def do_open(self, story):
		''' Opens given story in a browser.
		Story is identified as an index, optionally preceeded
		by 'top' or 'new' and colon, e.g. top:5.
		'''
		try:
			col, idx = re.split(story,  r'\s+|(\s*\:\s*)')
		except ValueError:
			col, idx = 'top', int(story)

		stories = self.stories.get(col)
		if 0 <= story_idx < len(stories):
			webbrowser.open(stories[story_idx].url)
		else:
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
	hncli.prompt = "hn$ "

	hncli.doc_header = "Supported commands"
	hncli.undoc_header = "Other commands"
	hncli.misc_header = "Help topics"
	hncli.ruler = "*"

	hncli.cmdloop()


if __name__ == '__main__':
	main()