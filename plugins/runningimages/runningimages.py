import os
import json
from pelican import signals


def article_generator_write_article(article_generator, content):
    # Extract people, event, sponsors, production, direction
    article_tags = dict((tag.name, tag.url) for tag in content.metadata.get('tags', []))

    article_info = {
        'people': [],
        'events': [],
        'sponsors': [],
        'production': [],
        'direction': []
    }

    for key in article_info.keys():
        if key not in content.metadata:
            continue
        for name in content.metadata[key].split(';'):
            article_info[key].append({'name': name, 'url': article_tags.get(name, None)})

    content.info_items = article_info

    # Flatten all info fields to generate the keywords (using in meta & page title)
    content.keywords = ', '.join(item['name'] for items in article_info.values() for item in items)


def register():
    signals.article_generator_write_article.connect(article_generator_write_article)


