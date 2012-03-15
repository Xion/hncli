'''
Interacting with Hacker News site.
'''
from re import compile as regex
import requests
from bs4 import BeautifulSoup

from .story import Story


URL = "http://news.ycombinator.com"


def fetch_hn_page(page='/', auth_token=None):
	''' Retrieves given Hacker News page.
	Returns the BeautifulSoup object with parsed HTML.
	'''
	if not page.startswith('/'):
		page = '/' + page
	url = URL + page

	request_args = {'url': url}
	if auth_token:
		request_args['cookies'] = {'user': auth_token}
	html = requests.get(**request_args).text
	return BeautifulSoup(html)

def login(user, password):
	''' Attempts to login to Hacker News.
	Returns authentication token (from cookie)
	or None if unsuccessful.
	'''
	# we need login page to get 'fnid' which
	# looks like a kind of CSRF/expiration token
	login_page = fetch_hn_page('/newslogin')
	if not login_page:
		return
	fnid = login_page.find('input', {'name': 'fnid'})['value']

	data = {'fnid': fnid, 'u': user, 'p': password}
	resp = requests.post(URL + '/y', data=data)
	return resp.cookies.get('user')

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

	top_table = page.find('table').find_all('table')[0]
	user_td = top_table.find_all('td')[-1]
	user_span = user_td.find('span', {'class': 'pagetop'})
	user_link = user_span.find('a', href=regex(r'user\?id\=.+'))
	if not user_link:
		return # not logged in

	name = user_link.text
	points = regex(r'\((\d+)\)').search(user_span.text).group(1)
	return {'name': name, 'points': points}