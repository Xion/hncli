#!/usr/bin/env python
'''
hncli -- Main entry point
'''
import cmd
from . import hn


class HackerNews(cmd.Cmd):
	''' Command-line shell for Hacker News. '''

	def do_new(self, count):
		''' Retrieves the most recent stories. '''
		if not count or len(str(count).strip()) == 0:
			count = 10
		count = int(count)
		
		stories = hn.get_recent_stories(count)
		for i, story in enumerate(stories, 1):
			number = str(i) + ". "
			print "%s%s (%s)" % (number, story.title, story.url)
			print (" " * len(number) + 
				   "by %s (%s comments)" % (story.author,
				   							story.comments_count))




def main():
	hncli = HackerNews()
	hncli.prompt = "hn$ "
	hncli.cmdloop()


if __name__ == '__main__':
	main()