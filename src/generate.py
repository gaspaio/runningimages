import shutil
import os
import logging
import numpy as np
import re
import textwrap
import json
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


def media_metas(video):
    # Generate video links
    player = None
    link_vod = None
    link_fm = None

    free = video['free_access'] if video['free_access'] is not np.NaN else False

    def qualify_stream(link):
        if link is np.NaN:
            return {'type': 'no_link'}
        linfo = parse_stream_url(link, link)
        if linfo is None:
            return {'type': 'unsupported'}
        return linfo
    link_stream = qualify_stream(video['link_stream'])
    link_trailer = qualify_stream(video['link_trailer'])

    if not free:
        # S'il y a un lien de stream, proposer comme VOD
        if link_stream['type'] != 'no_link':
            link_vod = video['link_stream']
        # Si le lien trailer est supporté, le mettre dans le player, sinon on ignore
        if link_trailer['type'] not in ['no_link', 'unsupported']:
            player = link_trailer
    else:
        # stream supporté => player
        if link_stream['type'] not in ['no_link', 'unsupported']:
            player = link_stream
        # Stream non supporté => lien full movie
        if link_stream['type'] == 'unsupported':
            link_fm = video['link_stream']
        # trailer supporté et rien dans le player => trailer dans le player
        if link_trailer['type'] not in ['no_link', 'unsupported'] and player is None:
            player = link_trailer

    out = {}
    if player is not None:
        out['player_vid'] = player['vid']
        out['player_type'] = player['type']
        out['player_url'] = player['url'].geturl()
    if link_vod is not None:
        out['link_vod'] = link_vod
    if link_fm is not None:
        out['link_fm'] = link_fm

    return out


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

    if images is not None:
        img_main = images.get('main', None)
        img_thumb = images.get('thumb', None)
        if img_main is not None:
            metas['img_main'] = f'images/{img_main}'
            metas['img_thumb'] = f'images/{img_main}'
        if img_thumb is not None:
            metas['img_thumb'] = f'images/{img_thumb}'
            if img_main is None:
                metas['img_main'] = f'images/{img_thumb}'

    metas.update(media_metas(video))

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
    print(f'Wrote {len(videos)} video files')

    kwd_items = {}
    for kwdtype, kwds in keywords.items():
        kwd_items[kwdtype] = [name for name, info in kwds.items() if info['is_tag']]

    with open(os.path.join(BASEDIR, 'sitemeta.json'), 'w') as f:
        json.dump({ 'tags': kwd_items }, f, indent=2)

    return

