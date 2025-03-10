"""
Client
======

The embedly object that interacts with the service
"""

import json
import re
from urllib.parse import quote, urlencode

import httplib2

from .models import Url


def get_user_agent():
    from . import __version__
    return 'Mozilla/5.0 (compatible; embedly-python/%s;)' % __version__


class Embedly(object):
    """
    Client

    """
    def __init__(self, key=None, user_agent=None, timeout=60):
        """
        Initialize the Embedly client

        :param key: Embedly Pro key
        :type key: str
        :param user_agent: User Agent passed to Embedly
        :type user_agent: str
        :param timeout: timeout for HTTP connection attempts
        :type timeout: int

        :returns: None
        """
        self.key = key
        self.user_agent = user_agent or get_user_agent()
        self.timeout = timeout

        self.services = []
        self._regex = None

    def get_services(self):
        """
        get_services makes call to services end point of api.embed.ly to fetch
        the list of supported providers and their regexes
        """

        if self.services:
            return self.services

        url = 'http://api.embed.ly/1/services/python'

        http = httplib2.Http(timeout=self.timeout)
        headers = {'User-Agent': self.user_agent,
                   'Connection': 'close'}
        resp, content = http.request(url, headers=headers)

        if resp['status'] == '200':
            resp_data = json.loads(content.decode('utf-8'))
            self.services = resp_data

            # build the regex that we can use later
            _regex = []
            for each in self.services:
                _regex.append('|'.join(each.get('regex', [])))

            self._regex = re.compile('|'.join(_regex))

        return self.services

    def is_supported(self, url):
        """
        ``is_supported`` is a shortcut for client.regex.match(url)
        """
        return self.regex.match(url) is not None

    @property
    def regex(self):
        """
        ``regex`` property just so we can call get_services if the _regex is
        not yet filled.
        """
        if not self._regex:
            self.get_services()

        return self._regex

    def _get(self, version, method, url_or_urls, **kwargs):
        """
        _get makes the actual call to api.embed.ly
        """
        if not url_or_urls:
            raise ValueError('%s requires a url or a list of urls given: %s' %
                             (method.title(), url_or_urls))

        # a flag we can use instead of calling isinstance() all the time
        multi = isinstance(url_or_urls, list)

        # throw an error early for too many URLs
        if multi and len(url_or_urls) > 20:
            raise ValueError('Embedly accepts only 20 urls at a time. Url '
                             'Count:%s' % len(url_or_urls))

        query = ''

        key = kwargs.get('key', self.key)

        # make sure that a key was set on the client or passed in
        if not key:
            raise ValueError('Requires a key. None given: %s' % key)

        kwargs['key'] = key

        query += urlencode(kwargs)

        if multi:
            query += '&urls=%s&' % ','.join([quote(url) for url in url_or_urls])
        else:
            query += '&url=%s' % quote(url_or_urls)

        url = 'http://api.embed.ly/%s/%s?%s' % (version, method, query)

        http = httplib2.Http(timeout=self.timeout)

        headers = {'User-Agent': self.user_agent,
                   'Connection': 'close'}

        resp, content = http.request(url, headers=headers)

        if resp['status'] == '200':
            data = json.loads(content.decode('utf-8'))

            if kwargs.get('raw', False):
                data['raw'] = content
        else:
            try:
                resp_body = json.loads(content.decode('utf-8'))
            except:
                resp_body = {}

            data = {'type': 'error',
                    'error': True,
                    'error_code': int(resp['status']),
                    'error_message': resp_body.get("error_message"),
                    }

        if multi:
            return list(map(lambda url, data: Url(data, method, url),
                       url_or_urls, data))

        return Url(data, method, url_or_urls)

    def oembed(self, url_or_urls, **kwargs):
        """
        oembed
        """
        return self._get(1, 'oembed', url_or_urls, **kwargs)

    def preview(self, url_or_urls, **kwargs):
        """
        oembed
        """
        return self._get(1, 'preview', url_or_urls, **kwargs)

    def objectify(self, url_or_urls, **kwargs):
        """
        oembed
        """
        return self._get(2, 'objectify', url_or_urls, **kwargs)

    def extract(self, url_or_urls, **kwargs):
        """
        oembed
        """
        return self._get(1, 'extract', url_or_urls, **kwargs)
