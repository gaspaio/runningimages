#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = 'Rodolfo Ripado'
SITENAME = 'Running Images'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'https://getpelican.com/'),
         ('Python.org', 'https://www.python.org/'),
         ('Jinja2', 'https://palletsprojects.com/p/jinja/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 20

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Paths
ARCHIVES_SAVE_AS = ''
ARTICLE_PATHS = ['videos']
ARTICLE_EXCLUDES: []
ARTICLE_SAVE_AS = 'video/{slug}.html'
AUTHOR_SAVE_AS = ''
TAG_SAVE_AS = 'entity/{slug}.html'
TAGS_SAVE_AS = 'entities.html'
