'''
Objects representing Hacker News items: stories and comments.
'''
from re import compile as regex

from .utils import cast


class Story(object):
    ''' Holds information about single HN story. '''
    __slots__ = ['id', 'title', 'url', 'author', 'points', 'time', 
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
            points = cast(int, subtext.find('span', id=regex(r'score_\d+')
                                            ).text.split()[0], default=0)
            comments_count = cast(int, comments_link.text.split()[0],
                                  default=0)
            story.update({
                'author': subtext.find('a', href=regex(r'user\?id\=.+')).text,
                'points': points,
                'time': list(subtext.strings)[-2].replace('|', '').strip(),
                'comments_count': comments_count,
                'comments_url': comments_link['href'],
                'upvote_url': vote_td.find('a', id=regex(r'up_\d+'))['href'],
            })
            url = story['comments_url']
        else:
            story['time'] = subtext.text
            url = story['url']

        story['id'] = int(url[url.find('=')+1:])
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

    def __str__(self):
        return "story:" + str(self.id)


class Comment(object):
    ''' Holds information about single HN comment. '''
    __slots__ = ['story_id', 'id', 'url', 'author', 'text', 'time',
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
        reply_link = parent_tr.find('a', href=regex(r'reply\?.+'))

        comment = {
            'story_id': story_id,
            'url': head_span.find('a', href=regex(r'item\?id\=\d+'))['href'],
            'author': head_span.find('a', href=regex(r'user\?id\=.+')).text,
            'text': tag.text.strip(),
            'time': list(head_span.strings)[-2].replace('|', '').strip(),
            'level': int(indent_img['width']) / 40, # magic number of pixels
            'parent': None,
            'replies': [],
            'reply_url': reply_link['href'] if reply_link else None,
        }

        url = comment['url']
        comment['id'] = int(url[url.find('=')+1:]),
        return Comment(**comment)

    def __str__(self):
        return "comment:" + str(self.id)