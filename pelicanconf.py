#!/usr/bin/env python
# -*- coding: utf-8 -*- #
import os
import json

PLUGIN_PATHS = ['plugins']
PLUGINS = ['runningimages']

LOAD_CONTENT_CACHE = False
DELETE_OUTPUT_DIRECTORY = True
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
ARTICLE_ORDER_BY = "reversed-release_year"

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Paths
ARCHIVES_SAVE_AS = ''
ARTICLE_PATHS = ['videos']
ARTICLE_EXCLUDES: []
ARTICLE_SAVE_AS = 'videos/{slug}.html'
ARTICLE_URL = 'videos/{slug}.html'
AUTHOR_SAVE_AS = ''
TAG_SAVE_AS = 'tags/{slug}.html'
TAGS_SAVE_AS = 'tags.html'
TAG_URL = 'tags/{slug}.html'
CATEGORY_SAVE_AS = 'years/{slug}.html'
CATEGORIES_SAVE_AS = ''
CATEGORY_URL = 'years/{slug}.html'
INDEX_SAVE_AS = 'videos.html'

THEME = 'themes/runningimages'
THEME_CATEGORIES = {
    'x-1999':    { 'title': 'before 1999'},
    '2000-2004': { 'title': 'from 2000 to 2005' },
    '2005-2009': { 'title': 'from 2005 to 2009' },
    '2010-2014': { 'title': 'from 2010 to 2014' },
    '2015-x':    { 'title': 'after 2015' }
}
THEME_CATEGORIES_ORDERED = ['x-1999', '2000-2004', '2005-2009', '2010-2014', '2015-x']
with open('sitemeta.json') as f:
    sitemeta = json.load(f)
TAG_TYPES = sitemeta['tags']
