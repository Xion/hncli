'''
Interacting with Hacker News site.
'''
from re import compile as regex
import requests
from bs4 import BeautifulSoup

from .story import Story


URL = "http://news.ycombinator.com"


def fetch_hn_page(page='/'):
	''' Retrieves given Hacker News page.
	Returns the BeautifulSoup object with parsed HTML.
	'''
	if not page.startswith('/'):
		page = '/' + page
	url = URL + page
	return BeautifulSoup(requests.get(url).text)


def get_recent_stories(count=10, page='/'):
	''' Gets the most recent stories from HN. '''
	if isinstance(page, basestring):
		page = fetch_hn_page(page)

	news_table = page.find('table').find_all('table')[1]
	news_trs = news_table.find_all('tr')[:-3]	# last 3 is garbage
	del news_trs[2::3]							# every third row is separator
	items = zip(*([iter(news_trs)] * 2))		# stories span two rows

	for item in items[:count]:
		story = Story.from_html(*item)
		if not story.url.startswith('http'):
			story.url = URL + '/' + story.url
		yield story


def get_user_info(page='/'):
	''' Gets HN user info from given page. '''
	if isinstance(page, basestring):
		page = fetch_hn_page(page)

	user_span = page.find('span', {'class': 'pagetop'})
	user_link = user_span.find('a', href=regex(r'user\?id\=.+'))
	if not user_link:
		return # not logged in

	name = user_link.text
	points = regex(r'\((\d+)\)').match(user_span.text).group(1)
	return {'name': name, 'points': points}