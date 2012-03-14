#!/usr/bin/env python
'''
hncli -- Main entry point
'''
import cmd
import sys
import webbrowser

from . import hn


class HackerNews(cmd.Cmd):
	''' Command-line shell for Hacker News. '''

	def __init__(self, *args, **kwargs):
		cmd.Cmd.__init__(self, *args, **kwargs)	# cmd.Cmd is old-style class!
		self.stories = []

	def do_new(self, count):
		''' Retrieves the most recent stories. '''
		if not count or len(str(count).strip()) == 0:
			count = 10
		count = int(count)
		
		self.stories = []
		stories = hn.get_recent_stories(count)
		for i, story in enumerate(stories):
			number = str(i) + ". "
			print "%s%s (%s)" % (number, story.title, story.url)
			print " " * len(number) + story.subtext
			self.stories.append(story)

	def do_open(self, story):
		story_idx = int(story)
		if 0 <= story_idx < len(self.stories):
			webbrowser.open(self.stories[story_idx].url)
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