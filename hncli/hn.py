'''
Interacting with Hacker News site.
'''
import requests
from bs4 import BeautifulSoup

from story import Story


URL = "http://news.ycombinator.com"


def get_recent_stories(count=10, page='/'):
	''' Gets the most recent stories from HN. '''
	if not page.startswith('/'):
		page = '/' + page
	url = URL + page
	soup = BeautifulSoup(requests.get(url).text)

	news_table = soup.find('table').find_all('table')[1]
	news_trs = news_table.find_all('tr')[:-3]	# last 3 is garbage
	del news_trs[2::3]							# every third row is separator
	items = zip(*([iter(news_trs)] * 2))		# stories span two rows

	for item in items[:count]:
		story = Story.from_html(*item)
		if not story.url.startswith('http'):
			story.url = URL + '/' + story.url
		yield story
