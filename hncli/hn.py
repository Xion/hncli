'''
Interacting with Hacker News site.
'''
from re import compile as regex
import requests
from bs4 import BeautifulSoup

from .items import Story, Comment
from .utils import cast


class Client(object):
    ''' A client for Hacker News website, accessing it via HTTP
    and parsing incoming HTML to extract useful information.
    '''
    BASE_URL = "http://news.ycombinator.com"

    def __init__(self):
        self._reset_user_info()

    def _reset_user_info(self):
        self.auth_token = None
        self.user_name = None
        self.user_points = None

    def _hn_url(self, url):
        ''' Converts relative Hacker News URLs into absolute ones,
        using BASE_URL ase base.
        '''
        if url.startswith('http'):
            return url
        if not url.startswith('/'):
            url = '/' + url
        return self.BASE_URL + url

    def _request(self, method, page, **kwargs):
        ''' Performs a HTTP request to Hacker News.
        If the user is logged in, the authentication cookie
        is attached automatically.
        Returns the python-requests Response object.
        '''
        method = method.lower()
        if not method in ['get', 'post']:
            return None

        request_args = {'url': self._hn_url(page)}
        if self.authenticated:
            request_args['cookies'] = {'user': self.auth_token}
        request_args.update(kwargs)

        func = getattr(requests, method)
        return func(**request_args)

    def _fetch_page(self, page='/'):
        ''' Retrieves given Hacker News page.
        Returns the BeautifulSoup object with parsed HTML.
        '''
        html = self._request('get', page).text
        soup = BeautifulSoup(html)

        if self.authenticated:
            self._retrieve_user_info(soup)
        return soup

    def _fetch_item_page(self, item_id):
        ''' Retrieves page for given Hacker News item
        (either a story or comment).
        Returns the BeautifulSoup object with parsed HTML.
        '''
        url = 'item?id=' + str(item_id)
        return self._fetch_page(url)

    def _obtain_fnid(self, page):
        ''' Retrieves the 'fnid' token from given Hacker News page.
        fnid is a kind of CSRF token which has quite short expiration time
        (few minutes tops), so it's required that we obtain it
        before performing a POST.
        '''
        if isinstance(page, basestring):
            page = self._fetch_page(page)

        fnid = page.find('input', {'name': 'fnid'})
        if not fnid:
            return None
        return fnid['value']

    def _retrieve_user_info(self, page='/'):
        ''' Gets HN user info from given page.
        A page is either an URL or BeautifulSoup object.
        Returns True of False, depending on whether user info
        could be found.
        '''
        if isinstance(page, basestring):
            page = self._fetch_page(page)

        top_table = page.find('table').find('table')
        user_td = top_table.find_all('td')[-1]
        user_span = user_td.find('span', {'class': 'pagetop'})
        user_link = user_span.find('a', href=regex(r'user\?id\=.+'))
        if not user_link:
            return False

        name = user_link.text
        points = regex(r'\((\d+)\)').search(user_span.text).group(1)
        if not (name or points):
            return False

        self.user_name = name
        self.user_points = points
        return True

    @property
    def authenticated(self):
        return bool(self.auth_token)

    def login(self, user, password, retrieve_info=True):
        ''' Attempts to login to Hacker News and returns boolean success flag.
        `retrieve_info` parameter indicates whether we should automatically
        obtain user information after successful login.
        '''
        fnid = self._obtain_fnid('/newslogin')
        if not fnid:
            return False

        data = {'fnid': fnid, 'u': user, 'p': password}
        resp = requests.post(self._hn_url('y'), data=data)
        token = resp.cookies.get('user')
        if not token:
            return False

        self.auth_token = token
        if retrieve_info:
            self._retrieve_user_info()
        return True

    def logout(self):
        ''' Logs out from Hacker News, forgetting the authentication token
        and related user information. '''
        self._reset_user_info()

    def get_stories(self, page='/', count=None):
        ''' Retrieves stories from given Hacker News page.
        Yields a sequence of Story objects. '''
        if isinstance(page, basestring):
            page = self._fetch_page(page)

        news_table = page.find('table').find_all('table')[1]
        news_trs = news_table.find_all('tr')[:-3]   # last 3 is garbage
        del news_trs[2::3]                          # every 3rd is separator
        items = zip(*([iter(news_trs)] * 2))        # stories span two rows
        if count is not None:
            items = items[:count]

        for item in items:
            story = Story.from_html(*item)
            story.url = self._hn_url(story.url)
            yield story

    def get_comments(self, item_or_url):
        ''' Retrieves comments from given page or item (story) of given ID.
        Returns list of top-level Comment objects,
        in the order they appear on page.
        '''
        if isinstance(item_or_url, (basestring, int, long)):
            item_id = cast(int, item_or_url)
            url = 'item?id=' + str(item_id) if item_id else item_or_url
            page = self._fetch_page(url)

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
            if comment.level > last.level:  # reply to last
                last.add_reply(comment)
                stack.append(last)
            else:   # reply to parent or top-level comment
                level_diff = last.level - comment.level
                stack = stack[:-level_diff]
                if stack:
                    stack[-1].add_reply(comment)
            last = comment

        return [c for c in comments if c.level == 0]

    def post_comment(self, item_id, text):
        ''' Posts a comment in reply to given item. The item can be
        either a story or some other comment we'll be replying to.
        Returns True or False, depending on whether posting succeeded.
        Note that user must be logged in to perform this action.
        '''
        if not self.authenticated:
            return False

        # retrieve the 'fnid' CSRF token
        page = self._fetch_item_page(item_id)
        if not page:
            return False
        fnid = self._obtain_fnid(page)
        if not fnid:
            return False

        data = {'fnid': fnid, 'text': text}
        resp = self._request('post', '/r', data=data)
        return True
