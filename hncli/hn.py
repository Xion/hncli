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


def get_user_info(page='/'):
	''' Gets HN user info from given page. '''
	if isinstance(page, basestring):
		page = fetch_hn_page(page)

	top_table = page.find('table').find('table')
	user_td = top_table.find_all('td')[-1]
	user_span = user_td.find('span', {'class': 'pagetop'})
	user_link = user_span.find('a', href=regex(r'user\?id\=.+'))
	if not user_link:
		return # not logged in

	name = user_link.text
	points = regex(r'\((\d+)\)').search(user_span.text).group(1)
	return {'name': name, 'points': points}

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


def get_recent_stories(page='/', count=None):
	''' Gets the most recent stories from HN. '''
	if isinstance(page, basestring):
		page = fetch_hn_page(page)

	news_table = page.find('table').find_all('table')[1]
	news_trs = news_table.find_all('tr')[:-3]	# last 3 is garbage
	del news_trs[2::3]							# every third row is separator
	items = zip(*([iter(news_trs)] * 2))		# stories span two rows
	if count is not None:
		items = items[:count]

	for item in items:
		story = Story.from_html(*item)
		if not story.url.startswith('http'):
			story.url = URL + '/' + story.url
		yield story


## Comments

class Comment(object):
	''' Holds information about single HN comment. '''

	__slots__ = ['story_id', 'author', 'url', 'text', 'time',
				 'level', 'parent', 'replies', 'reply_url']

	def __init__(self, **kw):
		for k in self.__slots__:
			setattr(self, k, kw.get(k, ''))

	def add_reply(self, reply):
		''' Adds given comment as reply to this one. '''
		self.replies.append(reply)
		reply.parent = self

	@staticmethod
	def from_html(story_id, tag):
		''' Constructs the Comment from HN site markup.
		'tag' argument is BeatifulSoup object for
		<span> tag with class=comment.
		'''
		if not (tag.name == 'span' and 'comment' in tag['class']):
			return

		parent_tr = tag.find_parent('tr')
		head_span = parent_tr.find('span', {'class': 'comhead'})
		indent_img = parent_tr.find('img', src=regex(r'.*/images/s\.gif'))

		comment = {
			'story_id': story_id,
			'author': head_span.find('a', href=regex(r'user\?id\=.+')).text,
			'url': head_span.find('a', href=regex(r'item\?id\=\d+'))['href'],
			'text': tag.text.strip(),
			'time': list(head_span.strings)[-2].replace('|', '').strip(),
			'level': int(indent_img['width']) / 40, # magic number of pixels
			'parent': None,
			'replies': [],
			'reply_url': parent_tr.find('a', href=regex(r'reply\?.+'))['href'],
		}
		return Comment(**comment)


def get_comments(item_id, auth_token=None):
	''' Retrieves comments for item of given ID.
	Returns list of top-level comments.
	'''
	url = 'item?id=' + str(item_id)
	page = fetch_hn_page(url, auth_token)
	if not page:
		return

	comments_table = page.find('table').find_all('table')[2]
	comment_spans = comments_table.find_all('span', {'class': 'comment'})
	if not comment_spans:
		return []

	comments = [Comment.from_html(item_id, span)
				for span in comment_spans]

	# use order of comments and their levels
	# to reconstruct hierarchy of replies
	stack = [] ; last = comments[0]
	for comment in comments[1:]:
		if comment.level > last.level: 	# reply to last
			last.add_reply(comment)
			stack.append(last)
		else: 	# reply to parent or top-level comment
			level_diff = last.level - comment.level
			stack = stack[:-level_diff]
			if stack:
				stack[-1].add_reply(comment)
		last = comment

	return [c for c in comments if c.level == 0]