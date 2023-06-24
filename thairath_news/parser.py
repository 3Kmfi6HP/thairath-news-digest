# coding: utf-8
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup as BS
from null import Null

from thairath_news.news import News
from page_content_extractor import ParseError

logger = logging.getLogger(__name__)

from config import sites_for_users
from page_content_extractor.http import session


class ThairathNewsParser(object):
    end_point = 'https://thairath-api.chronisftl.workers.dev/news/local/bangkok/'

    def parse_news_list(self):
        response = requests.get(self.end_point)
        if response.status_code != 200:
            raise ValueError(f"Unable to fetch data from API, status code: {response.status_code}")

        news_data = response.json()
        items = []

        for rank, news_item in enumerate(news_data):
            title = news_item['title']
            logger.info('Gotta %s', title)
            url = news_item['canonical']
            comhead = news_item['sectionEn']
            score = "21"
            author = "thairath"
            author_link = "https://www.thairath.co.th/"
            submit_time = self.convert_timestamp_to_utc_datetime(news_item['publishTs'])
            comment_cnt = None
            comment_url = None
            full_path = news_item['fullPath']

            items.append(News(
                rank=rank,
                title=title,
                url=url,
                comhead=comhead,
                score=score,
                author=author,
                author_link=author_link,
                submit_time=submit_time,
                comment_cnt=comment_cnt,
                comment_url=comment_url,
                full_path=full_path
            ))

        if len(items) == 0:
            raise ValueError('failed to parse hacker news page, got 0 item')

        return items
    def convert_timestamp_to_utc_datetime(self, timestamp):
        return datetime.utcfromtimestamp(timestamp)
    
    def parse_comhead(self, url):
        if not url.startswith('http'):
            url = 'http://' + url
        us = urlsplit(url.lower())
        comhead = us.hostname
        hs = comhead.split('.')
        if len(hs) > 2 and hs[0] == 'www':
            comhead = comhead[4:]
        if comhead in sites_for_users:
            ps = us.path.split('/')
            if len(ps) > 1 and ps[1]:
                comhead = '%s/%s' % (comhead, ps[1])
        return comhead

    def get_comment_url(self, path):
        if not isinstance(path, str):
            return None
        return 'https://news.ycombinator.com/item?id=%s' % re.search(r'\d+', path).group()

    def human2datetime(self, text):
        """Convert human readable time strings to datetime
        >>> self.human2datetime('2 minutes ago')
        datetime.datetime(2015, 11, 1, 14, 42, 24, 910863)

        """
        day_ago = hour_ago = minute_ago = 0
        m = re.search(r'(?P<day>\d+) day', text, re.I)
        if m:
            day_ago = int(m.group('day'))
        m = re.search(r'(?P<hour>\d+) hour', text, re.I)
        if m:
            hour_ago = int(m.group('hour'))
        m = re.search(r'(?P<minute>\d+) minute', text, re.I)
        if m:
            minute_ago = int(m.group('minute'))
        return datetime.utcnow() - \
            timedelta(days=day_ago, hours=hour_ago, minutes=minute_ago)
