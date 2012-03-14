'''
Interacting with Hacker News site.
'''
from collections import namedtuple
from re import compile as regex
import requests
from bs4 import BeautifulSoup


URL = "http://news.ycombinator.com/"

Story = namedtuple('Story',
				   ['title', 'url', 'author', 'points', 'time', 
				    'comments_count', 'comments_url',
				    'upvote_url', 'downvote_url'])


def get_recent_stories(count=10):
	''' Gets the most recent stories from HN. '''
	soup = BeautifulSoup(requests.get(URL).text)

	news_table = soup.find('table').find_all('table')[1]
	news_trs = news_table.find_all('tr')[:-3]	# last 3 is garbage
	del news_trs[2::3]							# every third row is separator
	items = zip(*([iter(news_trs)] * 2))		# stories span two rows

	# dive into the soup, extract information...
	# import ipdb ; ipdb.set_trace()
	for first_tr, second_tr in items[:count]:
		link = first_tr.find_all('td')[2].a
		vote_td = first_tr.find_all('td')[1]
		subtext = second_tr.find('td', {'class': 'subtext'})
		comments_link = subtext.find('a', href=regex(r'item\?id\=.+'))
		not_job = bool(comments_link)

		# ...and live to tell the Story!
		print list(subtext.strings)
		yield Story(
			title=link.text,
			url=link['href'],
			author=subtext.find('a', href=regex(r'user\?id\=.+')).text if not_job else '',
			points=subtext.find('span', id=regex(r'score_\d+')).text.split()[0] if not_job else '',
			time='' if not_job else subtext.text,
			comments_count=comments_link.text.split()[0] if not_job else 0,
			comments_url=comments_link['href'] if not_job else '',
			upvote_url=(vote_td.find('a', id=regex(r'up_\d+'))['href']
						if not_job else ''),
			downvote_url='', # NYI
		)
