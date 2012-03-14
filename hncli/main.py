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

	def default(self, command):
		if command in ['exit', 'quit']:
			sys.exit()
		else:
			cmd.Cmd.default(self, command)


def main():
	hncli = HackerNews()
	hncli.prompt = "hn$ "
	hncli.cmdloop()


if __name__ == '__main__':
	main()