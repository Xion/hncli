'''
Interacting with Hacker News site.
'''
from re import compile as regex
import requests
from bs4 import BeautifulSoup


URL = "http://news.ycombinator.com/"


class Story(object):
	''' Holds information about single HN story. '''

	__slots__ = ['title', 'url', 'author', 'points', 'time', 
				 'comments_count', 'comments_url',
				 'upvote_url', 'downvote_url']

	def __init__(self, **kw):
		for k in self.__slots__:
			setattr(self, k, kw.get(k, ''))

	@staticmethod
	def from_html(main_row, subtext_row):
		''' Constructs Story from HN site markup elements. '''
		link = main_row.find_all('td')[2].a
		vote_td = main_row.find_all('td')[1]
		subtext = subtext_row.find('td', {'class': 'subtext'})
		comments_link = subtext.find('a', href=regex(r'item\?id\=.+'))
		not_job = bool(comments_link)

		story = {'title': link.text, 'url': link['href']}
		if not_job:
			comments_count = comments_link.text.split()[0]
			if comments_count.strip() == 'discuss':
				comments_count = 0
			story.update({
				'author': subtext.find('a', href=regex(r'user\?id\=.+')).text,
				'points': int(subtext.find('span', id=regex(r'score_\d+')
							).text.split()[0]),
				'time': list(subtext.strings)[-2].replace('|', '').strip(),
				'comments_count': comments_count,
				'comments_url': comments_link['href'],
				'upvote_url': vote_td.find('a', id=regex(r'up_\d+'))['href'],
			})
		else:
			story['time'] = subtext.text

		return Story(**story)

	@property
	def job_post(self):
		''' Is this story a job posting? '''
		return not bool(self.comments_url)

	@property
	def subtext(self):
		if self.job_post:
			return self.time
		return "%s points by %s %s | %s comments" % (
			self.points, self.author, self.time, self.comments_count)


def get_recent_stories(count=10):
	''' Gets the most recent stories from HN. '''
	soup = BeautifulSoup(requests.get(URL).text)

	news_table = soup.find('table').find_all('table')[1]
	news_trs = news_table.find_all('tr')[:-3]	# last 3 is garbage
	del news_trs[2::3]							# every third row is separator
	items = zip(*([iter(news_trs)] * 2))		# stories span two rows

	for item in items[:count]:
		yield Story.from_html(*item)
