import shutil
import os
import logging
import numpy as np
import re
import textwrap
from .media import parse_stream_url

from . import *


def clean_content():
    articles_path = os.path.join(BASEDIR, 'content', 'videos')
    for item in os.listdir(articles_path):
        path = os.path.join(articles_path, item)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        print(f'Removed:    {path}')


def format_duration(tt):
    hours, remainder = divmod(tt.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    out = []
    if hours > 0: out.append(f'{int(hours)}h')
    mins = 0
    if minutes > 0:
        mins = int(minutes)
    if seconds > 30:
        mins += 1
    if mins > 0:
        out.append(f'{mins} min')
    return ' '.join(out)


def player_metas(link):
    vinfo = parse_stream_url(link, link)
    if vinfo is None:
        return {}
    return {
        'player_type': vinfo['type'],
        'player_vid': vinfo['vid'],
        'player_url': link
    }


def video_build_metadata(video, keywords, images):
    metas = {}
    metas['slug'] = video['slug_web']
    metas['date'] = video['created'].strftime('%Y-%m-%d')
    # metas['category'] = video['category']
    metas['summary'] = textwrap.shorten(video['description'], width=SUMMARY_LENGTH, placeholder="...")
    metas['release_year'] = video['release_year']
    if video['duration'] is not np.NaN:
        metas['duration'] = format_duration(video['duration'])
    if video['language'] is not np.NaN:
        metas['language'] = video['language']
    if video['country'] is not np.NaN:
        metas['country'] = video['country']

    free = video['free_access'] if video['free_access'] is not np.NaN else False

    if images is not None:
        img_main = images.get('main', None)
        img_thumb = images.get('thumb', None)
        if img_main is not None:
            metas['img_main'] = f'images/{img_main}'
            metas['img_thumb'] =i f'images/{img_main}'
        if img_thumb is not None:
            metas['img_thumb'] = f'images/{img_thumb}'
            if img_main is None:
                metas['img_main'] = f'images/{img_thumb}'

    # Generate video links
    player_link = None
    if not free:
        if video['link_stream'] is not np.NaN:
            metas['link_vod'] = video['link_stream']
        if video['link_trailer'] is not np.NaN:
            player_link = video['link_trailer']
    else:
        if video['link_stream'] is not np.NaN:
            player_link = video['link_stream']
        elif video['link_trailer'] is not np.NaN:
            player_link = video['link_trailer']

    if player_link:
        metas.update(player_metas(player_link))

    if video['link_official'] is not np.NaN:
        metas['link_official'] = video['link_official']

    for key in keywords.keys():
        if video[key] is not np.NaN:
            metas[key] = TAG_SEPARATOR.join(video[key])

    tags = []
    for name, info in keywords.items():
        if video[name] is np.NaN: continue
        tags += [elem for elem in video[name] if info.get(elem, {}).get('is_tag', False)]
    if tags:
        metas['tags'] = TAG_SEPARATOR.join(tags)

    return metas


def to_video_page(video, keywords, images):

    out = [video['title']]
    out.append('#'*len(video['title']))
    out.append('')

    for key, value in video_build_metadata(video, keywords, images).items():
        out.append(f":{key}: {value}")

    out.append('')
    out.append(video["description"])
    out.append('')

    return '\n'.join(out)


def build_site_content(videos, keywords, images):
    clean_content()

    for video in videos:
        content = to_video_page(video, keywords, images.get(video['slug_fs'], None))

        if video['category'] is not np.NaN:
            filepath = os.path.join(BASEDIR, 'content', 'videos', video['category'], f"{video['slug_fs']}.rst")
        else:
            filepath = os.path.join(BASEDIR, 'content', 'videos', f"{video['slug_fs']}.rst")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f'Wrote:   {filepath}')

    return

