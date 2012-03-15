'''
Handling Hacker News stories.
'''
from re import compile as regex

from .utils import cast


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
		''' Constructs Story from HN site markup elements.
		Arguments are <tr> elements obtained with BeautifulSoup.
		'''
		link = main_row.find_all('td')[2].a
		vote_td = main_row.find_all('td')[1]
		subtext = subtext_row.find('td', {'class': 'subtext'})
		comments_link = subtext.find('a', href=regex(r'item\?id\=.+'))
		not_job = bool(comments_link)

		story = {'title': link.text, 'url': link['href']}
		if not_job:
			comments_count = cast(int, comments_link.text.split()[0],
								  default=0)
			points = cast(int, subtext.find('span', id=regex(r'score_\d+')
											).text.split()[0], default=0)
			story.update({
				'author': subtext.find('a', href=regex(r'user\?id\=.+')).text,
				'points': points,
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
